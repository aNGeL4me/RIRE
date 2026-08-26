# -*- coding: utf-8 -*-
import json
import os
import hashlib
from openai import OpenAI

client = OpenAI(base_url='https://api.deepseek.com', api_key='')

# Extract a unique identifier from three key values
def extract_changes_signature(func_sample):  # Generate a unique identifier based on commit_id and input to ensure sample stability and uniqueness.
    idx = func_sample.get("idx", "")
    input_content = func_sample.get("input", "")
    try:
        # Combine commit_id and input as the basis for the unique identifier
        combined_str = f"{idx}|{input_content}"
        return hashlib.sha256(combined_str.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"Error generating signature: {e}")
        return "error_signature"

def generate_format_changes(initial_changes):  # Refine the handling of each change in the initial_changes list, generate prompts by case, and concatenate them at the end
    format_changes = []
    for change in initial_changes:
        deletions = change.get("deletions", "").strip()
        additions = change.get("additions", "").strip()
        context_line_del = change.get("context_line_del", "").strip()
        context_line_add = change.get("context_line_add", "").strip()
        if deletions and additions:
            format_changes.append(f' "{deletions}" was modified to "{additions}"')
        elif not deletions and additions:
            if context_line_add.startswith('+'):
                format_changes.append(f' Additional code "{additions}" was added after the newly modified code "{context_line_add[1:]}"')
            else:
                format_changes.append(f' New code "{additions}" was added after "{context_line_add}"')
        elif deletions and not additions:
            if context_line_del:
                format_changes.append(f' Code "{deletions}" was deleted after "{context_line_del}"')
            else:
                format_changes.append(f' Code "{deletions}" was deleted"')
    return '; '.join(format_changes)


def prompt_unsafe_diff_eval(func_sample: dict):
    """
    Generate two Chinese repair prompts for the two unsafe analyses in func_sample
    """
    func_code = func_sample.get("input", "")
    unsafe1 = func_sample.get("Unsafe1_diff", "")
    unsafe2 = func_sample.get("Unsafe2_diff", "")
    changes = generate_format_changes(func_sample.get("changes", []))
    prompt = f"""Given this code:\n{func_code}\nwhich is unsafe and vulnerable, I have two repair proposals for how to fix the vulnerability in the current code:\nProposal 1: {unsafe1}\nProposal 2: {unsafe2}\nPlease score these two repair proposals and evaluate which one is better.
Additionally, I have a ground truth repair proposal as follows:\n{changes}\nPlease refer to the ground truth repair proposal (first compare if the repair starting points are the same as the ground truth; if one repair’s starting point matches the ground truth and the other does not, the one matching the ground truth is better; if both have the same starting point as the ground truth, then compare the semantic similarity of the code implementations).
Please evaluate these two repair proposals. The final output format should be:
[evaluation_start] 1>2 [evaluation_end] (meaning the first repair proposal is better)
or [evaluation_start] 2>1 [evaluation_end] (meaning the second repair proposal is better)
or [evaluation_start] 1=2 [evaluation_end] (meaning the two repair proposals are equal, only if they are exactly the same)
Note: Only output the evaluation result without any explanation or additional text.
"""
    return prompt.strip()

def prompt_safe_diff_eval(func_sample: dict):
    """
    Generate two Chinese prompts for security-irrelevant modifications for safe samples
    """
    func_code = func_sample.get("input", "")
    safe1 = func_sample.get("Safe1_diff", "")
    safe2 = func_sample.get("Safe2_diff", "")
    changes = generate_format_changes(func_sample.get("changes", []))
    prompt = f"""Given this code:\n{func_code}\nwhich is safe and has no vulnerabilities, although there are no security vulnerabilities, there exist security-irrelevant modifications (such as feature modifications, syntax changes, adding comments, etc.). Please score the following two modification proposals and evaluate which one is better.
The two modification proposals are:\nProposal 1: {safe1}\nProposal 2: {safe2}\nPlease score and evaluate which proposal is better.
Additionally, I have a ground truth modification proposal as follows:\n{changes}\nPlease refer to the ground truth modification proposal (first compare if the modification starting points are the same as the ground truth; if one modification’s starting point matches the ground truth and the other does not, the one matching the ground truth is better; if both have the same starting point as the ground truth, then compare the semantic similarity of the code implementations).
Please evaluate these two modification proposals. The final output format should be:
[evaluation_start] 1>2 [evaluation_end] (meaning the first modification proposal is better)
or [evaluation_start] 2>1 [evaluation_end] (meaning the second modification proposal is better)
or [evaluation_start] 1=2 [evaluation_end] (meaning the two modification proposals are equal, only if they are exactly the same)
Note: Only output the evaluation result without any explanation or additional text.
"""
    return prompt.strip()

# Call API to get analysis result
def get_analysis(prompt):
    response = client.chat.completions.create(
        model="deepseek-reasoner", # deepseek-reasoner -> DeepSeek-R1 ; deepseek-chat -> DeepSeek-V3
        messages=[
            {'role': 'system', 'content': 'Please act as a code editing assistant'}, # originally: '请你作为一个代码编辑助手'
            {"role": "user", "content": prompt}
        ]
    )
    reasoning_content = response.choices[0].message.reasoning_content
    content = response.choices[0].message.content
    #print(f"reasoning_content --> {reasoning_content}")
    print(f"content --> {content}")
    return reasoning_content, content

# Read processed sample hashes to support resuming from breakpoints
# Read processed sample function signatures to support resuming from breakpoints
def get_processed_samples(output_file):
    """
    Extract processed samples from the output file to support resuming.
    """
    processed_signatures = set()

    if not os.path.exists(output_file):
        return processed_signatures

    with open(output_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                sample = json.loads(line.strip())
                if "func_signature" in sample:
                    processed_signatures.add(sample["func_signature"])
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Warning: Failed to parse existing record: {e}")
                continue

    print(f"Loaded {len(processed_signatures)} processed samples.")
    return processed_signatures

def process_json(input_file, output_file, reasoning_content_file):
    """
    Process JSON file, generate analysis results and support resuming from breakpoints.
    """
    processed_signatures = get_processed_samples(output_file)
    num_call = 0
    with open(input_file, "r", encoding="utf-8") as f_in, \
         open(output_file, "a", encoding="utf-8") as f_out, \
         open(reasoning_content_file, "a", encoding="utf-8") as reason_out:
        for line in f_in:
            try:
                sample = json.loads(line.strip())
                output = sample["output"]
                idx = sample.get("idx", "")
                func_signature = extract_changes_signature(sample)  # Generate unique identifier
                # Skip already processed samples
                if func_signature in processed_signatures:
                    continue
                # Generate prompt and call analysis API
                if output == "1":
                    prompt = prompt_unsafe_diff_eval(sample)
                    # print(f"prompt --> {prompt}")
                else:
                    prompt = prompt_safe_diff_eval(sample)

                reasoning_content, analysis_result = get_analysis(prompt)

                if not analysis_result:
                    print(f"Warning: Empty analysis result for commit_id {idx}, skipping...")
                    continue

                print(f"idx {idx} analysis completed --> ", idx)
                print("=" * 20)
                # Update sample and write to output file
                sample["eval_result"] = analysis_result
                f_out.write(json.dumps(sample, ensure_ascii=False) + "\n")

                sample["eval_result_reasoning_content"] = reasoning_content
                reason_out.write(json.dumps(sample, ensure_ascii=False) + "\n")
                # Flush immediately to prevent data loss (optional, adjust based on data size)
                f_out.flush()
                reason_out.flush()
                # Record processed signature to avoid duplicates
                processed_signatures.add(func_signature)
                # num_call += 1 # Run 5 scripts each time
                # if(num_call > 2):
                #    break
                #break # Currently only process one sample

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Error processing sample: {e}")
                continue

    print("Processing completed.")

if __name__ == "__main__":

    input_file = "./evaluate_2646_2diff_part/train512_22837_3970_0x01_3r_2646diff_eval_split_part1.json"      # Input data file
    output_file = "./evaluate_2646_2diff_part/train512_22837_3970_0x01_3r_2646diff_eval_split_part1_result.json"    # Output file written in real-time
    reasoning_content_file = "./evaluate_2646_2diff_part/train512_22837_3970_0x01_3r_2646diff_eval_split_part1_ReasonINCoT.json"
    process_json(input_file, output_file, reasoning_content_file)
