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
from transformers import LlamaTokenizer,  LlamaForCausalLM,AutoTokenizer,AutoModelForCausalLM # CodeLlamaTokenizer,
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
#
MODEL_CLASSES = {
    'llama': (LlamaForCausalLM, LlamaTokenizer),
    'codellama': (LlamaForCausalLM, AutoTokenizer)
}
# PROMPT_DICT = {
#     "prompt_input": (
#         "Below is an instruction that describes a task, paired with an input that provides further context. "
#         "Write a response that appropriately completes the request.\n\n"
#         "### Instruction:\n{instruction}\n\n### Input:\n{input}\n\n### Response:"
#     ),
#     # "prompt_input": (
#     #     "### Instruction:\nAnalyze the following function to determine whether it contains vulnerabilities. Provide reasoning before the final answer.\n\n"
#     #     "### Input:\n{input}\n\n### Response:"
#     # ),
#     "prompt_no_input": (
#         "Below is an instruction that describes a task. "
#         "Write a response that appropriately completes the request.\n\n"
#         "### Instruction:\n{instruction}\n\n### Response:"
#     ),
# }
PROMPT_DICT = {
    "prompt_input": (
        "<|im_start|>user\n"
        "Below is an instruction that describes a task, paired with an input that provides further context. "
        "Write a response that appropriately completes the request.\n\n"
        "Instruction: {instruction}\n\n"
        "Input: {input}\n"
        "<|im_end|>\n"
        "<|im_start|>assistant\n"  # Qwen 需要明确 assistant 角色
    ),
    "prompt_no_input": (
        "<|im_start|>user\n"
        "Below is an instruction that describes a task. "
        "Write a response that appropriately completes the request.\n\n"
        "Instruction: {instruction}\n"
        "<|im_end|>\n"
        "<|im_start|>assistant\n"
    ),
}
def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate code vulnerability detection")
    parser.add_argument("--model_type", default="llama", type=str,
                        help="The model architecture to be fine-tuned.")
    parser.add_argument("--base_model", required=True, help="Path to the base model.")
    parser.add_argument("--tuned_model", required=True, help="Path to the tuned model.")
    parser.add_argument("--data_file", required=True, help="Path to the json file containing test dataset.")
    parser.add_argument("--csv_path", default='results.csv', help="Path to save the CSV results.")
    parser.add_argument("--batch_size", default=10, help="batch_size of inference", type=int)
    # 如果是单卡全用的话，可以将batch设置为20
    return parser.parse_args()


# 从 CoT 生成的回答中提取 [Vulnerable] 或 [No Vulnerability] 并转换为 1/0
def extract_final_decision(response):
    match = re.search(r'\[(Vulnerable|Secure)\]', response, re.IGNORECASE)
    if match:
        return 1 if match.group(1).lower() == 'vulnerable' else 0
    # 2. 如果包含 "Analysis of the function:"，返回 0
    if "Vulnerable line: None" in response: # Analysis of the function
        return 0
    # 3. 如果包含 "Vulnerable line of the function:"，返回 1
    if "Vulnerable line: None" not in response:
        return 1
    # 4. 无法解析时返回 None
    return None

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
    FPR = FP / (FP + TN) if (FP + TN) > 0 else 0.0 # 分母是所有label为0的样本： 0->1 和 0->0（前面为label 后面为预测）
    FNR = FN / (FN + TP) if (FN + TP) > 0 else 0.0 # 分母是所有label为1的样本： 1->0 和 1->1（前面为label 后面为预测）
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
    # if not os.path.exists(args.csv_path):
    #     with open(args.csv_path, 'w') as f:
    #         f.write('Index,Code,Label,Prediction,Prob,Response\n')
    # 创建 CSV 文件，如果不存在则新建，否则读取已完成的 Index 列表
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
    batch_size = args.batch_size  # 设置批处理大小

    # 获取未处理的 index 列表
    all_indices = set(range(len(data)))
    unprocessed_indices = sorted(list(all_indices - processed_indices))
    current_pos = 0
    while current_pos < len(unprocessed_indices): # 断点续inference，当inference阶段出现OOM导致退出时，调整batch_size后可以从上次结束的index处开始
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
        # 批量编码
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

        # s = generation_output.sequences[0]
        # generated_response = tokenizer.decode(s)
        # print(f"generated_response --> {generated_response}")
        # response = generated_response.split("### Response:")[-1].strip()
        # # print(f"response --> {response}")
        # prediction_result = extract_final_decision(response)

        responses = tokenizer.batch_decode(generation_output.sequences, skip_special_tokens=True)

        batch_predictions = []
        batch_confidences = []

        for response, confidence in zip(responses, confidence_scores):
            response = response.split("assistant")[-1].strip()
            prediction = extract_final_decision(response)
            prediction = prediction if prediction is not None else -1
            batch_predictions.append(prediction)
            batch_confidences.append(confidence.item())

        temp_df = pd.DataFrame({
            'Index': batch_indices, # range(batch_start, batch_end),
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
    # 计算最终评估指标
    # print_metrics(label_list, prediction_list)
    # 从完整 CSV 文件中读取所有已完成样本
    final_df = pd.read_csv(args.csv_path)
    all_labels = final_df['Label'].tolist()
    all_predictions = final_df['Prediction'].tolist()

    # 最终评估所有推理样本
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
