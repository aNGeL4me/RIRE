import json
import os
import hashlib
from openai import OpenAI

client = OpenAI(base_url='https://api.deepseek.com', api_key='')

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
    
def prompt_unsafe_unsafe(func_sample):
    func = func_sample.get("input", "")
    label = func_sample.get("output", "")  # Assume output field stores the label
    prompt = f"""Given that this code {func} is unsafe and contains vulnerabilities (you don't need to judge whether the code is safe; even if you think it is safe, treat it as unsafe),
    please explain why the code is unsafe. The analysis can consider the following aspects: integer overflow, buffer overflow (out-of-bounds access, stack overflow), out-of-bounds read/write, illegal memory access, memory leak, command injection, use-after-free,
    improper input validation, resource leak (sensitive information leakage), null pointer dereference, input validation and error handling (exception conditions not properly checked or handled), resource management errors, logical defects, etc.
    These aspects almost cover all security concerns. You only need to focus on one or two aspects, and explain why the code is unsafe based on related code.
    Organize your output as follows: first output the vulnerable code line, then the cause of the vulnerability (i.e., what security issue exists in this line), then a summary of the cause, and finally the result.
    Keep the cause and summary each within 60-80 words. The final output must follow this format:
Vulnerable line: xxx
Cause: xxx
Summary: xxx
Result: [Vulnerable]
I need you to generate two different analysis results (in English), analyzing different security issues. The Vulnerable line field should be wrapped with a backtick ` (do not use Markdown bold syntax like **)."""
    return prompt.strip()

def prompt_unsafe_safe(func_sample):
    func = func_sample.get("input", "")
    label = func_sample.get("output", "")  # Assume output field stores the label
    prompt = f"""Given that this code {func} is safe and has no vulnerabilities (you don't need to judge whether the code is safe; even if you think it is unsafe, treat it as safe), please identify the security mechanisms in the original code,
    and explain why the code does not contain security issues. The analysis should consider aspects such as: integer overflow, buffer overflow (out-of-bounds access, stack overflow), out-of-bounds read/write, illegal memory access, memory leak, command injection, use-after-free,
    improper input validation, resource leak (sensitive information leakage), null pointer dereference, input validation and error handling (exception conditions not properly checked or handled), resource management errors, logical defects.
    These aspects almost cover all security concerns. You only need to focus on 1–2 secure coding patterns, explain why the code is safe, provide reasonable explanations, and cite relevant code as evidence (the related code should follow the explanation without a line break).
    For example: If a function contains pointer operations but performs null pointer checks before use to effectively avoid null pointer dereference, explicitly point this out and mention the corresponding code location. The final output must follow this format (do not use Markdown bold syntax like **):
Vulnerable line: None
Cause: None
Summary: xxx
Result: [Secure]
The summary should analyze only one or two aspects and be controlled within 70-90 words. Only one analysis result is needed (in English)."""
    return prompt.strip()

def prompt_safe_safe(func_sample):
    func = func_sample.get("input", "")
    prompt = f"""Given that this code {func} is safe and has no vulnerabilities (you don't need to judge whether the code is safe; even if you think it is unsafe, treat it as safe), please identify the security mechanisms in the original code,
    and explain why the code does not contain security issues. The analysis should consider aspects such as: integer overflow, buffer overflow (out-of-bounds access, stack overflow), out-of-bounds read/write, illegal memory access, memory leak, command injection, use-after-free,
    improper input validation, resource leak (sensitive information leakage), null pointer dereference, input validation and error handling (exception conditions not properly checked or handled), resource management errors, logical defects.
    These aspects almost cover all security concerns. You only need to focus on 1–2 secure coding patterns, explain why the code is safe, provide reasonable explanations, and cite relevant code as evidence (the related code should follow the explanation without a line break).
    For example: If a function contains pointer operations but performs null pointer checks before use to effectively avoid null pointer dereference, explicitly point this out and mention the corresponding code location. The final output must follow this format (do not use Markdown bold syntax like **):
Vulnerable line: None
Cause: None
Summary: xxx
Result: [Secure]
I need you to generate two different analysis results (in English), i.e., the summary parts differ, analyzing different security aspects (each summary should analyze two secure coding patterns, kept within 70-90 words, and the content should remain coherent)."""
    return prompt.strip()

def prompt_safe_unsafe(func_sample):
    func = func_sample.get("input", "")
    prompt = f"""Given that this code {func} is unsafe and contains vulnerabilities (you don't need to judge whether the code is safe; even if you think it is safe, treat it as unsafe), please explain why the code is unsafe.
    The analysis can consider the following aspects: integer overflow, buffer overflow (out-of-bounds access, stack overflow), out-of-bounds read/write, illegal memory access, memory leak, command injection, use-after-free, improper input validation,
    resource leak (sensitive information leakage), null pointer dereference, input validation and error handling (exception conditions not properly checked or handled), resource management errors, logical defects, etc.
    These aspects almost cover all security concerns. You only need to focus on one or two aspects, and explain why the code is unsafe based on related code. Organize your output as follows: first output the vulnerable code line,
    then the cause of the vulnerability (i.e., what security issue exists in this line), then a summary of the cause, and finally the result. Keep the cause and summary each within 60-80 words. The final output must follow this format:
Vulnerable line: xxx
Cause: xxx
Summary: xxx
Result: [Vulnerable]
Only one analysis result is needed (in English). The Vulnerable line field should be wrapped with a backtick ` (do not use Markdown bold syntax like **)."""
    return prompt.strip()

def get_analysis(prompt):  # Call API to get analysis results
    response = client.chat.completions.create(
        model="deepseek-reasoner",  # deepseek-reasoner -> DeepSeek-R1 ; deepseek-chat -> DeepSeek-V3
        messages=[
            {'role': 'system', 'content': 'You are a security assistant.'},
            {"role": "user", "content": prompt}
        ]
    )
    reasoning_content = response.choices[0].message.reasoning_content
    content = response.choices[0].message.content
    #print(f"reasoning_content --> {reasoning_content}")
    #print(f"content --> {content}")
    return reasoning_content, content

def get_processed_samples(output_file):  # Read processed sample hashes, support resuming from breakpoint... Read function signatures of processed samples from output file, support resuming
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
    # Read processed samples, support resuming from breakpoint
    processed_signatures = set(get_processed_samples(output_file))  # Ensure it is a set

    num_call = 0
    with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "a", encoding="utf-8") as f_out, open(reasoning_content_file, "a", encoding="utf-8") as reason_out:
        counter = 0  # Flush counter
        for line in f_in:
            try:
                sample = json.loads(line.strip())
                output = sample["output"]
                idx = sample.get("idx", "")
                func_signature = extract_changes_signature(sample)  # Generate unique identifier
                if func_signature in processed_signatures:
                    continue  # Skip already processed samples

                if output == "1":
                    prompt_1 = prompt_unsafe_unsafe(sample)
                    prompt_0 = prompt_unsafe_safe(sample)
                    # print(f"prompt --> {prompt}")
                else:
                    prompt_0 = prompt_safe_safe(sample)
                    prompt_1 = prompt_safe_unsafe(sample)
                # Get analysis results
                reasoning_content_1, analysis_result_1 = get_analysis(prompt_1)
                reasoning_content_0, analysis_result_0 = get_analysis(prompt_0)
                # Handle empty results
                if not analysis_result_1 or not analysis_result_0:
                    print(f"Warning: Empty analysis result for commit_id {idx}, skipping...")
                    continue
                print(f"idx {idx} analysis completed --> ", idx)
                print("=" * 20)
                # Update sample and write to output file

                sample["AsUnsafe"] = analysis_result_1
                sample["AsSafe"] = analysis_result_0
                sample["func_signature"] = func_signature
                f_out.write(json.dumps(sample, ensure_ascii=False) + "\n")
                # Only write CoT content
                #reason_out.write(json.dumps({"func_signature": func_signature, "reasoning_content": reasoning_content}, ensure_ascii=False) + "\n")
                sample["prompt_AsUnsafe"] = prompt_1
                sample["reasoning_AsUnsafe"] = reasoning_content_1
                sample["prompt_AsSafe"] = prompt_0
                sample["reasoning_AsSafe"] = reasoning_content_0
                reason_out.write(json.dumps(sample, ensure_ascii=False) + "\n")
                counter += 1
                # if counter % 10 == 0:  # Flush every 10 times to avoid frequent I/O
                #     f_out.flush()
                #     reason_out.flush()
                f_out.flush()
                reason_out.flush()
                processed_signatures.add(func_signature)  # Record processed signature to avoid duplicate processing
                
                #num_call += 1 # Run 5 scripts each time
                #if(num_call > 2):
                #    break
                # break # Currently run only one sample
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Error processing sample: {e}")
                continue
    print("Processing completed.")

if __name__ == "__main__":

    input_file = "./randomSampled3970_0x01_part1/train_512_22837_randomSampled3970_0x01_split_part1.json"      # Input data file
    output_file = "./randomSampled3970_0x01_part1/train_512_22837_randomSampled3970_0x01_split_part1_result.json"    # Real-time output file
    reasoning_content_file = "./randomSampled3970_0x01_part1/train_512_22837_randomSampled3970_0x01_split_part1_ReasonINCoT.json"
    process_json(input_file, output_file, reasoning_content_file)
