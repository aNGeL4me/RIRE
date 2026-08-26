# -*- coding: utf-8 -*-
import json
import os
import hashlib
from openai import OpenAI

client = OpenAI(base_url='https://api.deepseek.com', api_key='')


def extract_changes_signature(func_sample):

    if isinstance(func_sample, str):
        func_sample = json.loads(func_sample)
    func_content = func_sample.get("input", "")
    idx = func_sample.get("idx", "")
    commit_id = func_sample.get("commit_id", "")
    try:
        combined_str = f"{idx}|{func_content}|{commit_id}"
        return hashlib.sha256(combined_str.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"Error generating signature: {e}")
        return "error_signature"

def generate_prompt(func_sample):
    func = func_sample.get("input", "")
    message = func_sample.get("message", "")
    label = func_sample.get("output", "")
    prompt1 = """Please modify the given code snippet and output the modified version. The output format should refer to the style of GitHub commit pages. Specific requirements will be described below. There are three types of code modifications: deletion only, addition only, and both deletion and addition. Note that when presenting the modified code, you must also include the context lines before and after the changes.

**Case 1: Deletion Only**  
If one or more lines of code are deleted, add a "-" at the beginning of each deleted line. Also include one line before and one line after the deleted section as context. Both the deleted lines and the context lines must preserve the exact indentation of the original source code.

**Case 2: Addition Only**  
If one or more lines of code are added, add a "+" at the beginning of each added line. To show where the addition occurs, you must include the line before and the line after the addition from the original code as context. The added lines and the surrounding context must retain the exact indentation as in the original source code.

**Case 3: Both Deletion and Addition**  
If lines are both deleted and added, prepend deleted lines with "-" and added lines with "+". If the deletion and addition represent a replacement (i.e., the added code is a revised version of the deleted code), include the line before and the line after the change as context, and present the diff with consistent indentation from the source code.  
If the deletion and addition are unrelated (i.e., not a replacement), present them separately:  
- The deleted section must include the deleted lines and their surrounding context, following Case 1.  
- The added section must include the added lines and their surrounding context, following Case 2.

The output for all three types of changes should consist of 5 parts:  
1. The header line: "@@ @@"  
2. The function definition line from the original code  
3. The context line before the modification  
4. The modified line(s)  
5. The context line after the modification

Below are examples for the three cases:

**Deletion Only Example:**  
"@@ -414,7 +414,6 @@ static int swf_write_trailer(AVFormatContext *s)\n        url_fseek(pb, swf->duration_pos, SEEK_SET);\n        put_le16(pb, video_enc->frame_number);\n    }\n-    av_free(swf);\n    return 0;\n}"

**Addition Only Example:**  
"@@ -36,6 +36,7 @@ static int raw_read_packet(AVFormatContext *s, AVPacket *pkt)\n\n    ret= av_get_packet(s->pb, pkt, size);\n\n+    pkt->flags &= ~AV_PKT_FLAG_CORRUPT;\n    pkt->stream_index = 0;\n    if (ret < 0)\n        return ret;"

**Replacement Example:**  
"@@ -242,15 +242,15 @@ static int v4l2_send_frame(AVCodecContext *avctx, const AVFrame *frame)\n{\n-    V4L2m2mContext *s = avctx->priv_data;\n+    V4L2m2mContext *s = ((V4L2m2mPriv*)avctx->priv_data)->context;\n    V4L2Context *const output = &s->output;"\n"""
    
    prompt2 = f"""Given the code: \"{func}\" {"This code is safe and does not contain any vulnerabilities. Please modify the code with security-irrelevant changes to ensure the modified version remains safe." if label == "0" else "This code is unsafe and contains vulnerabilities. Please apply security-related changes to ensure the modified code is secure."}"""
    
    prompt3 = f"""The message field is: \"{message} \"  
{"Since the original code is safe, if the commit message mentions crashes, integer overflows, buffer overflows (e.g., out-of-bounds access, stack overflow), out-of-bounds reads/writes, illegal memory access, memory leaks, command injection, use-after-free, improper input validation, resource leakage (e.g., sensitive data leaks), null pointer dereference, improper exception handling, resource management errors, or logical flaws, please ignore the content of the message and avoid applying security-related modifications. Only when the message does **not** involve any security issues may it be referenced to make functional or structural improvements." if label == "0" else "You may use the message as auxiliary reference for your modification. However, note that the content of the message may not be strongly aligned with the actual secure fix in the source code and could contain noise. Therefore, use your discretion: if the message is unrelated to the code, ignore it; if it is clearly relevant, use it as a basis for the fix."}"""

    prompt4 = """When modifying the code, you must not only add a comment line; you must ensure that the output includes actual executable code changes.  
When the original code has very few lines, avoid modifying **all** lines entirely, as such changes are too drastic.  
**Important:** The diff output must strictly reflect the actual code changes — do **not** delete and immediately re-add identical lines.  
When adding new code, only include the new lines prefixed with "+". Context lines should remain unchanged.  
When modifying code, make sure the "-" and "+" lines are actually different.  
Use reasonable assumptions for line numbers to construct the `@@ -x,y +x,y @@` diff header. If the actual line numbers are uncertain, you may use placeholder numbers.  
Use `\\n` to indicate line breaks explicitly to avoid formatting issues.  
If the source code contains `\\t` characters, retain them in the modified code; do not replace them with 4 spaces.  
Ensure that in the generated diff:  
- Lines starting with "+" are newly added (not part of original code).  
- Lines starting with "-" and lines without "+" or "-" must exactly match the original source code in content, indentation, and formatting.

Finally, wrap the generated diff strictly between the following markers:  
[DIFF_START]  
<diff content>  
[DIFF_END]  
Do **not** add any explanatory text or comments between [DIFF_START] and [DIFF_END]. Explanations, if any, should go outside of the diff block."""
    
    prompt = prompt1 + prompt2 + prompt3 + prompt4
    return prompt


# 调用 API 获取分析结果
def get_analysis(prompt):
    response = client.chat.completions.create(
        model="deepseek-reasoner", # deepseek-reasoner -> DeepSeek-R1 ; deepseek-chat -> DeepSeek-V3
        messages=[
            {'role': 'system', 'content': '请你作为一个代码编辑助手'}, # 'You are a security assistant.'
            {"role": "user", "content": prompt}
        ]
    )
    reasoning_content = response.choices[0].message.reasoning_content
    content = response.choices[0].message.content
    print(f"reasoning_content --> {reasoning_content}")
    print(f"content --> {content}")
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

def process_json(input_file, output_file, reasoning_content_file):

    processed_signatures = get_processed_samples(output_file)

    with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "a", encoding="utf-8") as f_out, open(reasoning_content_file, "a", encoding="utf-8") as reason_out:
        for line in f_in:
            try:
                func_sample = json.loads(line.strip())

                func_signature = extract_changes_signature(func_sample)

                if func_signature in processed_signatures:
                    continue

                prompt = generate_prompt(func_sample)
                reasoning_content, modified_result = get_analysis(prompt)
                print("analysis done --> ", modified_result)
                print("="*20)

                func_sample["prompt"] = prompt
                func_sample["modified_result"] = modified_result
                func_sample["func_signature"] = func_signature
                
                f_out.write(json.dumps(func_sample, ensure_ascii=False) + "\n")

                func_sample["reasoning_content"] = reasoning_content
                reason_out.write(json.dumps(func_sample, ensure_ascii=False) + "\n")

                f_out.flush()
                reason_out.flush()

                processed_signatures.add(func_signature)
                #break

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Error processing sample: {e}")
                continue

    print("Processing completed.")

if __name__ == "__main__":

    input_file = "train_512_InDiversevul_AddNewKeysCommitidProjectEtc_updateProjectKeyValue_updateMessage_updateChanges_ChangesNull_DelIndent.json" 
    output_file = "train_512_InDiversevul_AddNewKeysCommitidProjectEtc_updateProjectKeyValue_updateMessage_updateChanges_ChangesNull_DelIndent_GenerateDiff.json"
    reasoning_content_file = "train_512_InDiversevul_AddNewKeysCommitidProjectEtc_updateProjectKeyValue_updateMessage_updateChanges_ChangesNull_DelIndent_GenerateDiff_WithReason.json"
    process_json(input_file, output_file, reasoning_content_file)
