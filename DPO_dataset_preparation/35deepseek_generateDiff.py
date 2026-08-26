# -*- coding: utf-8 -*-
import json
import os
import hashlib
from openai import OpenAI

client = OpenAI(base_url='https://api.deepseek.com', api_key='')

# Extract a unique identifier from three parts
def extract_changes_signature(func_sample):  # Generate a unique identifier based on commit_id and input to ensure sample stability and uniqueness.
    idx = func_sample.get("idx", "")
    input_content = func_sample.get("input", "")
    try:
        # Combine commit_id and input as the base for the unique identifier
        combined_str = f"{idx}|{input_content}"
        return hashlib.sha256(combined_str.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"Error generating signature: {e}")
        return "error_signature"

def build_single_patch_prompt(func_code: str, explnation: str) -> str:
    """
    Construct a Chinese repair prompt corresponding to a single vulnerability analysis
    """
    prompt = f"""Given the following code:\n{func_code}\nIt is insecure and contains a vulnerability. The vulnerability analysis consists of four parts: vulnerable line, cause, summary, and result, detailed as follows:
{explnation}

Please fix the code based on the "vulnerable line", "cause", and "summary" sections from the vulnerability analysis above, ensuring that the given function-level code segment is secure after the fix.

Note:
- The final output does not need to provide the complete modified code segment (final output in English);
- Only provide the modified code and necessary context, for example:
    Delete `int temp_flag = 0;` after the line `else if (action == BUS_NOTIFY_ADD_DEVICE)`; (if the modification is deletion)
    Or add `host_features |= (1 << VIRTIO_NET_F_MAC);` after the line `int i, config_size = 0;`; (if the modification is addition)
    Or change `switch (open_flags)` to `switch (fmode)`; (if the modification is replacement)
- No explanations are required;
- Do not use Markdown bold syntax (like **);
"""
    return prompt.strip()

def prompt_unsafe_generate_diff(func_sample: dict):
    """
    Generate two Chinese repair prompts for the two unsafe analyses in func_sample
    """
    func_code = func_sample.get("input", "")
    unsafe1 = func_sample.get("AsUnsafe1", "")
    unsafe2 = func_sample.get("AsUnsafe2", "")
    prompt1 = build_single_patch_prompt(func_code, unsafe1)
    prompt2 = build_single_patch_prompt(func_code, unsafe2)

    return prompt1, prompt2

def build_safe_patch_prompt(func_code: str, analysis: str) -> str:
    """
    Construct a harmless modification prompt for safe code
    """
    prompt = f"""Given the following code:\n{func_code}\nIt is secure and contains no vulnerabilities. The analysis explaining why this function-level code is safe consists of four parts ("vulnerable line", "cause", "summary", "result"):
{analysis}

Please focus on the "Summary" section and make non-security-impacting modifications to the code, ensuring the modified code remains secure.

Note:
- The final output does not need to provide the complete modified code segment (final output in English);
- Only provide the modified code and its context, for example:
    Delete `int temp_flag = 0;` after `else if (action == BUS_NOTIFY_ADD_DEVICE)`; (if the modification is deletion)
    Or add `host_features |= (1 << VIRTIO_NET_F_MAC);` after `int i, config_size = 0;`; (if the modification is addition)
    Or change `switch (open_flags)` to `switch (fmode)`; (if the modification is replacement)
- No explanations are required;
- Do not use Markdown bold syntax (like **);
"""
    return prompt.strip()

def prompt_safe_generate_diff(func_sample: dict):
    """
    Generate two Chinese prompts for harmless modifications for safe samples
    """
    func_code = func_sample.get("input", "")
    safe1 = func_sample.get("AsSafe1", "")
    safe2 = func_sample.get("AsSafe2", "")  # Fix bugs in original code
    prompt1 = build_safe_patch_prompt(func_code, safe1)
    prompt2 = build_safe_patch_prompt(func_code, safe2)
    return prompt1, prompt2

# Call API to get analysis results
def get_analysis(prompt):
    response = client.chat.completions.create(
        model="deepseek-reasoner", # deepseek-reasoner -> DeepSeek-R1 ; deepseek-chat -> DeepSeek-V3
        messages=[
            {'role': 'system', 'content': 'Please act as a code editing assistant'}, # 'You are a security assistant.'
            {"role": "user", "content": prompt}
        ]
    )
    reasoning_content = response.choices[0].message.reasoning_content
    content = response.choices[0].message.content
    #print(f"reasoning_content --> {reasoning_content}")
    print(f"content --> {content}")
    return reasoning_content, content

# Read processed sample hashes, support breakpoint resume
# Read processed sample function signatures, support breakpoint resume
def get_processed_samples(output_file):
    """
    Extract processed samples from the output file to support breakpoint resume.
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
    Process JSON file, generate analysis results and support breakpoint resume.
    """
    processed_signatures = get_processed_samples(output_file)
    num_call = 0
    with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "a", encoding="utf-8") as f_out, open(reasoning_content_file, "a", encoding="utf-8") as reason_out:
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
                    prompt0, prompt1 = prompt_unsafe_generate_diff(sample)
                    print("prompt0 type:", type(prompt0))
                    # prompt1 = prompt_unsafe_generate_diff(sample)
                    # print(f"prompt --> {prompt}")
                else:
                    prompt0, prompt1 = prompt_safe_generate_diff(sample)
                    # prompt1 = prompt_safe_generate_diff(sample)

                reasoning_content0, analysis_result0 = get_analysis(prompt0)
                reasoning_content1, analysis_result1 = get_analysis(prompt1)

                if not analysis_result0 or not analysis_result1:
                    print(f"Warning: Empty analysis result for commit_id {idx}, skipping...")
                    continue

                print(f"idx {idx} analysis completed --> ", idx)
                print("=" * 20)
                # Update sample and write to output file
                if output == "1":
                    sample["Unsafe1_diff"] = analysis_result0
                    sample["Unsafe2_diff"] = analysis_result1
                else:
                    sample["Safe1_diff"] = analysis_result0
                    sample["Safe2_diff"] = analysis_result1
                f_out.write(json.dumps(sample, ensure_ascii=False) + "\n")

                if output == "1":
                    sample["Unsafe1_diff_reasoning_content"] = reasoning_content0
                    sample["Unsafe2_diff_reasoning_content"] = reasoning_content1
                else:
                    sample["Safe1_diff_reasoning_content"] = reasoning_content0
                    sample["Safe2_diff_reasoning_content"] = reasoning_content1

                reason_out.write(json.dumps(sample, ensure_ascii=False) + "\n")
                # Flush in real-time to prevent data loss in case of interruption (optional, adjust depending on data volume)
                f_out.flush()
                reason_out.flush()
                # Record processed signature to avoid duplicates
                processed_signatures.add(func_signature)
                # num_call += 1 # run 5 scripts at a time
                # if(num_call > 1):
                #    break
                # break # currently only process one sample

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Error processing sample: {e}")
                continue

    print("Processing completed.")

if __name__ == "__main__":

    input_file = "./3r2646_part1/train512_22837_randomSampled3970_0x01_3r_2646_split_part1.json"      # Input data file
    output_file = ".3r2646_part1/train512_22837_randomSampled3970_0x01_3r_2646_split_part1_result.json"    # Output file written in real-time
    reasoning_content_file = "./3r2646_part1/train512_22837_randomSampled3970_0x01_3r_2646_split_part1_ReasonINCoT.json"
    process_json(input_file, output_file, reasoning_content_file)
