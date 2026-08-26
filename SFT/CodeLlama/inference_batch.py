import numpy as np
import torch
import os
import sys
import json
import copy
import pandas as pd
import argparse
from peft import PeftModel
from transformers import GenerationConfig
from transformers import LlamaTokenizer, CodeLlamaTokenizer, LlamaForCausalLM,AutoTokenizer,AutoModelForCausalLM
from datasets import load_dataset
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
#
MODEL_CLASSES = {
    'llama': (LlamaForCausalLM, LlamaTokenizer),
    'codellama': (LlamaForCausalLM, CodeLlamaTokenizer)
}
PROMPT_DICT = {
    "prompt_input": (
        "Below is an instruction that describes a task, paired with an input that provides further context. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\n{instruction}\n\n### Input:\n{input}\n\n### Response:"
    ),
    "prompt_no_input": (
        "Below is an instruction that describes a task. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\n{instruction}\n\n### Response:"
    ),
}

def fpr_fnr_score(y_true, y_pred):
    y_true, y_pred = np.array(y_true, dtype=np.int32), np.array(y_pred, dtype=np.int32)
    TP = sum((y_true == 1) & (y_pred == 1))
    FP = sum((y_true == 0) & (y_pred == 1))
    TN = sum((y_true == 0) & (y_pred == 0))
    FN = sum((y_true == 1) & (y_pred == 0))

    # if (FP + TN) == 0:
    #     return 0.
    # else:
    #     FPR = FP / (FP + TN)
    #     return FPR
    FPR = FP / (FP + TN) if (FP + TN) > 0 else 0.0 # Denominator includes all samples with label 0: 0->1 and 0->0 (label on the left, prediction on the right)
    FNR = FN / (FN + TP) if (FN + TP) > 0 else 0.0 # Denominator includes all samples with label 1: 1->0 and 1->1 (label on the left, prediction on the right)
    return FPR, FNR

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate code vulnerability detection")
    parser.add_argument("--model_type", default="llama", type=str,
                        help="The model architecture to be fine-tuned.")
    parser.add_argument("--base_model", required=True, help="Path to the base model.")
    parser.add_argument("--tuned_model", required=True, help="Path to the tuned model.")
    parser.add_argument("--data_file", required=True, help="Path to the json file containing test dataset.")
    parser.add_argument("--csv_path", default='results.csv', help="Path to save the CSV results.")
    parser.add_argument("--batch_size", default=10, help="batch_size of inference", type=int)
    return parser.parse_args()

def main():
    args = parse_args()
    model_class, tokenizer_class = MODEL_CLASSES[args.model_type]
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, padding_side='left')
    tokenizer.pad_token_id = tokenizer.eos_token_id
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        load_in_8bit=True,
        torch_dtype=torch.float16,
        device_map="auto",
        pad_token_id=tokenizer.eos_token_id
    )
    print("Base model loaded!")

    model = PeftModel.from_pretrained(model, args.tuned_model)
    print("Tuned model loaded!")

    model.eval()
    if torch.__version__ >= "2" and sys.platform != "win32":
        model = torch.compile(model)

    with open(args.data_file, "r") as file:
        data = json.load(file)
    print(len(data))
    
    # Create the CSV header if file doesn't exist
    processed_indices = set()
    if not os.path.exists(args.csv_path):
        with open(args.csv_path, 'w') as f:
            f.write('Index,Idx,Code,Label,Prediction,Prob,Response\n')
    else:
        existing_df = pd.read_csv(args.csv_path)
        processed_indices = set(existing_df['Index'].tolist())
        print(f"Resuming from previous run. Found {len(processed_indices)} processed samples.")
    #batch_size = 16
    label_list = []
    prediction_list = []
    batch_size = args.batch_size

    all_indices = set(range(len(data)))
    unprocessed_indices = sorted(list(all_indices - processed_indices))
    current_pos = 0
    while current_pos < len(unprocessed_indices): # Resume inference from breakpoint: when OOM occurs during inference and causes exit, reduce batch_size and resume from last index
        batch_indices = unprocessed_indices[current_pos:current_pos + batch_size]
        batch_data = [data[idx] for idx in batch_indices]
        prompts = []
        labels = []

        for example_content in batch_data:
            if example_content.get("input", "") == "":
                prompt = PROMPT_DICT["prompt_no_input"].format_map(example_content)
            else:
                prompt = PROMPT_DICT["prompt_input"].format_map(example_content)
            prompts.append(prompt)
            # Record ground truth labels
            expected_response = example_content.get("output", "").strip()
            labels.append(1 if expected_response == '1' else 0)

        print(f"prompts: {len(prompts)}")
        print(f"labels: {len(labels)}")
        model_inputs = tokenizer(prompts, return_tensors="pt", padding=True, truncation=True).to(device)

        with torch.no_grad():
            generation_output = model.generate(
                input_ids=model_inputs['input_ids'],
                attention_mask=model_inputs['attention_mask'],
                return_dict_in_generate=True,
                output_scores=True,
                max_new_tokens=8,
            )

        logits = generation_output.scores
        probabilities = [torch.softmax(logit, dim=-1) for logit in logits]

        # Ensure prob_dists doesn't go out of bounds
        if len(probabilities) >= 2:
            prob_dists = probabilities[-2]
        else:
            prob_dists = torch.zeros((len(batch_indices), tokenizer.vocab_size), device=device)
        confidence_scores, predicted_token_ids = torch.max(prob_dists, dim=-1)
        responses = tokenizer.batch_decode(generation_output.sequences, skip_special_tokens=True)

        batch_predictions = []
        batch_confidences = []

        for response, confidence in zip(responses, confidence_scores):
            prediction = 0
            parsed_response = response.split("### Response:")[-1].strip()

            if len(parsed_response) > 0 and parsed_response[0] == '1':
                prediction = 1

            batch_predictions.append(prediction)
            batch_confidences.append(confidence.item())

        # Ensure indices match the data length
        temp_df = pd.DataFrame({
            'Index': batch_indices,
            'idx': [example_content.get("idx", "") for example_content in batch_data],
            'Code': [example_content.get("input", "") for example_content in batch_data],
            'Label': labels,
            'Prediction': batch_predictions,
            'Prob': batch_confidences,
            'Response': responses
        })
        temp_df.to_csv(args.csv_path, index=False, mode='a', header=False)
        prediction_list.extend(batch_predictions)
        label_list.extend(labels)
        print(f"Processed {batch_indices[-1] + 1}/{len(data)} samples...")
        current_pos += batch_size
    
    final_df = pd.read_csv(args.csv_path)
    all_labels = final_df['Label'].tolist()
    all_predictions = final_df['Prediction'].tolist()
    # Calculate final evaluation metrics
    print_metrics(all_labels, all_predictions)


def print_metrics(label_list, prediction_list):
    accuracy = accuracy_score(label_list, prediction_list)
    print(f'accuracy：{accuracy:.4f}')

    precision = precision_score(label_list, prediction_list)
    print(f'precision：{precision:.4f}')

    recall = recall_score(label_list, prediction_list)
    print(f'recall：{recall:.4f}')

    f1 = f1_score(label_list, prediction_list)
    print(f'F1：{f1:.4f}')

    fpr,fnr = fpr_fnr_score(label_list, prediction_list)
    print(f'FPR：{fpr:.4f}')
    print(f'FNR：{fnr:.4f}')

if __name__ == "__main__":
    main()
