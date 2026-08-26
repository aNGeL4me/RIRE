import numpy as np
from regex import F
import torch
import os
import re
import sys
import json
import pandas as pd
import argparse
from peft import PeftModel
from transformers import LlamaTokenizer, LlamaForCausalLM, AutoTokenizer, AutoModelForCausalLM
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Model types and corresponding tokenizer/model classes
MODEL_CLASSES = {
    'llama': (LlamaForCausalLM, LlamaTokenizer),
    'codellama': (LlamaForCausalLM, AutoTokenizer)
}

# Prompt templates
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

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate code vulnerability detection")
    parser.add_argument("--model_type", default="llama", type=str,
                        help="The model architecture to be fine-tuned.")
    parser.add_argument("--base_model", required=True, help="Path to the base model.")
    parser.add_argument("--tuned_model", required=True, help="Path to the tuned model.")
    parser.add_argument("--data_file", required=True, help="Path to the JSON file containing test dataset.")
    parser.add_argument("--csv_path", default='results.csv', help="Path to save the CSV results.")
    parser.add_argument("--batch_size", default=10, help="Batch size for inference", type=int)
    # If using a single GPU fully, batch_size can be set to 20
    return parser.parse_args()


# Extract final decision [Vulnerable] or [Secure] from CoT-generated response and convert to 1/0
def extract_final_decision(response):
    match = re.search(r'\[(Vulnerable|Secure)\]', response, re.IGNORECASE)
    if match:
        return 1 if match.group(1).lower() == 'vulnerable' else 0
    # Case 2: If response contains "Vulnerable line: None", return 0 (i.e., Secure)
    if "Vulnerable line: None" in response:
        return 0
    # Case 3: If "Vulnerable line: None" not present (likely contains actual vulnerable line), return 1
    if "Vulnerable line: None" not in response:
        return 1
    # Case 4: If unable to parse, return None
    return None

def fpr_fnr_score(y_true, y_pred):
    y_true, y_pred = np.array(y_true, dtype=np.int32), np.array(y_pred, dtype=np.int32)
    TP = sum((y_true == 1) & (y_pred == 1))
    FP = sum((y_true == 0) & (y_pred == 1))
    TN = sum((y_true == 0) & (y_pred == 0))
    FN = sum((y_true == 1) & (y_pred == 0))

    FPR = FP / (FP + TN) if (FP + TN) > 0 else 0.0  # Denominator: all samples with label 0 → (0->1 and 0->0)
    FNR = FN / (FN + TP) if (FN + TP) > 0 else 0.0  # Denominator: all samples with label 1 → (1->0 and 1->1)
    return FPR, FNR
    
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

    print(f"Total samples: {len(data)}")

    # Create CSV file if it does not exist, otherwise load processed indices for resuming
    processed_indices = set()
    if not os.path.exists(args.csv_path):
        with open(args.csv_path, 'w') as f:
            f.write('Index,Idx,Code,Label,Prediction,Prob,Response\n')
    else:
        existing_df = pd.read_csv(args.csv_path)
        processed_indices = set(existing_df['Index'].tolist())
        print(f"Resuming from previous run. Found {len(processed_indices)} processed samples.")

    label_list = []
    prediction_list = []
    batch_size = args.batch_size  # Set batch size

    # Get list of unprocessed indices
    all_indices = set(range(len(data)))
    unprocessed_indices = sorted(list(all_indices - processed_indices))
    current_pos = 0
    while current_pos < len(unprocessed_indices):
        # Resume inference from last unprocessed sample (supports batch_size change after OOM)
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

            expected_response = example_content.get("output", "").strip()
            labels.append(1 if expected_response == '1' else 0)

        print(f"prompts: {len(prompts)}")
        print(f"labels: {len(labels)}")

        # Batch encode inputs
        model_inputs = tokenizer(prompts, return_tensors="pt", padding=True, truncation=True).to(device)

        with torch.no_grad():
            generation_output = model.generate(
                input_ids=model_inputs['input_ids'],
                attention_mask=model_inputs['attention_mask'],
                return_dict_in_generate=True,
                output_scores=True,
                max_new_tokens=256,
            )

        logits = generation_output.scores
        probabilities = [torch.softmax(logit, dim=-1) for logit in logits]
        if len(probabilities) >= 2:
            prob_dists = probabilities[-2]
        else:
            prob_dists = torch.zeros((len(batch_indices), tokenizer.vocab_size), device=device)
        confidence_scores, predicted_token_ids = torch.max(prob_dists, dim=-1)

        responses = tokenizer.batch_decode(generation_output.sequences, skip_special_tokens=True)

        batch_predictions = []
        batch_confidences = []

        for response, confidence in zip(responses, confidence_scores):
            response = response.split("### Response:")[-1].strip()
            prediction = extract_final_decision(response)
            prediction = prediction if prediction is not None else -1
            batch_predictions.append(prediction)
            batch_confidences.append(confidence.item())

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

    # Read final results from full CSV for evaluation
    final_df = pd.read_csv(args.csv_path)
    all_labels = final_df['Label'].tolist()
    all_predictions = final_df['Prediction'].tolist()

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

    fpr, fnr = fpr_fnr_score(label_list, prediction_list)
    print(f'FPR：{fpr:.4f}')
    print(f'FNR：{fnr:.4f}')


if __name__ == "__main__":
    main()
