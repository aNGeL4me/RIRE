import json
import os
import hashlib
from openai import OpenAI

client = OpenAI(base_url='https://api.deepseek.com', api_key='')

def extract_changes_signature(func_sample):
    commit_id = func_sample.get("commit_id", "")
    input_content = func_sample.get("input", "")
    try:

        combined_str = f"{commit_id}|{input_content}"
        return hashlib.sha256(combined_str.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"Error generating signature: {e}")
        return "error_signature"

def generate_format_changes(initial_changes):
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

def unified_prompt(func_sample):
    func = func_sample.get("input", "")
    changes = generate_format_changes(func_sample.get("changes", []))
    message = func_sample.get("message", "")
    label = func_sample.get("output", "")

    prompt = f"""
Analyze the security of this function (label={label}):
{func}
Code modification context:
1. Changes: {changes or 'No changes'}
2. Commit message: {message}

Task requirements:
{"Explain why the code CONTAINS vulnerabilities" if label == "1" else "Explain why this code is SECURE"} by:
{"Analyze the cause of the vulnerability based on the vulnerability-fix(if changes exist) and the description (by comparing with the fixed code, focusing on the issues present in the original code). "
"Check whether the code lines mentioned in the commit message exist in the function. If the message refers to code that does not appear in the function, ignore those parts. If the message describes a vulnerability pattern that is semantically related to the current code logic, you may use the message as supporting information. Do not label code lines as vulnerable if they are mentioned in the message but not present in the function. "
"Required elements:"
"   - Describe vulnerable line: if there are multiple vulnerable lines(from the vulnerability function), select a representative line as the 'vulnerable line' rather than listing all lines"
"   - Describe the vulnerability cause, which should focus on describing the issues in the vulnerable code, not on how the fix resolves them"
"   - Summarize the cause of the vulnerability"
if label =="1" else 
"Code analysis (STRICTLY follow these rules):"
"   - If modification context is security-related (e.g., fixes vulnerabilities):"
"       * IGNORE modification context completely(Do NOT discuss modification context, removed/added lines, or commit messages when explaining security properties.)"
"       * Analyze original code's security mechanisms ONLY"
"   - If modification is non-security:"
"       * Use modification context to confirm original code's security properties" 
"       * DO NOT mention modification details in analysis"
"       * Cite original code's specific lines/structures as security evidence"
"   - Identify security mechanisms in the ORIGINAL code, analyze why the code does not contain security issues, consider the following aspects: integer overflow, buffer overflow (out-of-bounds access, stack overflow), out-of-bounds read/write, illegal memory access, memory leak, command injection, use-after-free, improper input validation, resource leakage (sensitive information disclosure), null pointer dereference, input validation and error handling (improper checks or handling of exceptional conditions), resource management errors, and logical defects."
"Required elements:"
"   - Highlight 1-2 secure code patterns: Explain why the code is safe, providing reasoning and referencing relevant parts of the code. For instance, if the function involves pointer operations but performs null checks before usage, ensuring null pointer dereference is avoided, mention this explicitly and refer to the relevant code section."}
Output format (MUST follow):
Vulnerable line: [vulnerable line / None]
Cause: [vulnerability cause / None]
Summary: [vulnerability cause summary / secure code patterns]
Result: {"[Vulnerable]" if label == "1" else "[Secure]"}

Examples:
Label=1 Example:
Vulnerable line: xxx
Cause: xxx
Summary: xxx
Result: [Vulnerable]

Label=0 Example:
Vulnerable line: None
Cause: None
Summary: xxx
Result: [Secure]
"""
    return prompt.strip()

def get_analysis(prompt):
    response = client.chat.completions.create(
        model="deepseek-reasoner", # deepseek-reasoner -> DeepSeek-R1 ; deepseek-chat -> DeepSeek-V3
        messages=[
            {'role': 'system', 'content': 'You are a security assistant.'},
            {"role": "user", "content": prompt}
        ]
    )
    reasoning_content = response.choices[0].message.reasoning_content
    content = response.choices[0].message.content
    #print(f"reasoning_content --> {reasoning_content}")
    #print(f"content --> {content}")
    return reasoning_content,content

def get_processed_samples(output_file):
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


def process_json(input_file, changesmessages_file, output_file, reasoning_content_file):

    processed_signatures = set(get_processed_samples(output_file))


    commit_index = {}
    with open(changesmessages_file, "r", encoding="utf-8") as f_target:
        for line in f_target:
            try:
                sampleB = json.loads(line.strip())
                commit_id = sampleB.get("commit_id", "")
                if commit_id:
                    if commit_id not in commit_index:
                        commit_index[commit_id] = []
                    commit_index[commit_id].append(sampleB)
            except json.JSONDecodeError:
                continue
    num_call = 0
    with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "a", encoding="utf-8") as f_out, open(reasoning_content_file, "a", encoding="utf-8") as reason_out:
        counter = 0
        for line in f_in:
            try:
                sampleA = json.loads(line.strip())
                target = sampleA["output"]
                commit_id = sampleA.get("commit_id", None)
                if not commit_id:
                    print("Warning: Missing commit_id in sampleA, skipping...")
                    continue

                func_signature = extract_changes_signature(sampleA)
                if func_signature in processed_signatures:
                    continue

                matched_sampleB = None
                if commit_id in commit_index:
                    for sampleB in commit_index[commit_id]:
                        if sampleA["input"] == sampleB["input"]:
                            matched_sampleB = sampleB
                            break
                if matched_sampleB:
                    prompt = unified_prompt(matched_sampleB)
                    # print(f"prompt --> {prompt}")
                else:
                    print(f"Warning: No matching entry found for commit_id {commit_id}")
                    continue

                reasoning_content, analysis_result = get_analysis(prompt)

                if not reasoning_content or not analysis_result:
                    print(f"Warning: Empty analysis result for commit_id {commit_id}, skipping...")
                    continue
                print(f"Target {target} analysis done --> ", analysis_result)
                print("=" * 20)

                sampleA["changes"] = sampleB["changes"]
                sampleA["message"] = sampleB["message"]
                sampleA["analysis_result"] = analysis_result
                sampleA["func_signature"] = func_signature
                f_out.write(json.dumps(sampleA, ensure_ascii=False) + "\n")

                #reason_out.write(json.dumps({"func_signature": func_signature, "reasoning_content": reasoning_content}, ensure_ascii=False) + "\n")
                sampleA["reasoning_content"] = reasoning_content
                reason_out.write(json.dumps(sampleA, ensure_ascii=False) + "\n")
                counter += 1

                #     f_out.flush()
                #     reason_out.flush()
                f_out.flush()
                reason_out.flush()
                processed_signatures.add(func_signature)
                

                # if(num_call > 4):
                #     break

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Error processing sample: {e}")
                continue
    print("Processing completed.")

if __name__ == "__main__":

    input_file = "train_512_InDevign_updated_target1_0_DelIndent_GeneratedChanges_merged.json"
    changesmessages_file = "train_512_InDevign_updated_target1_0_DelIndent_GeneratedChanges_merged.json"
    output_file = "train_512_InDevign_updated_target1_0_DelIndent_GeneratedChanges_merged_result.json"
    reasoning_content_file = "train_512_InDevign_updated_target1_0_DelIndent_GeneratedChanges_merged_ReasonINCoT.json"
    process_json(input_file, changesmessages_file, output_file, reasoning_content_file)
