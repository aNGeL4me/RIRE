import json
import re

input_file = "train_512_InDevign_AddNewKeysCommitidProject_updated_target1target0_ChangesNull_DelIndent_GenerateDiff.json"
output_file = "train_512_InDevign_AddNewKeysCommitidProject_updated_target1target0_ChangesNull_DelIndent_GenerateDiff_patch.json"

extracted_elements = []

with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        try:
            element = json.loads(line)
        except json.JSONDecodeError:
            print("Invalid JSON line, skipping.")
            continue

        new_element = {
            "input": element.get("input", ""),
            "output": element.get("output", ""),
            "idx": element.get("idx", ""),
            "project": element.get("project", ""),
            "commit_id": element.get("commit_id", ""),
            "func_signature": element.get("func_signature", "")
        }


        modified = element.get("modified_result", "")
        diff_block_match = re.search(r'\[DIFF_START\]\n(.*?)\n\[DIFF_END\]', modified, re.DOTALL)
        if diff_block_match:
            new_element["modified_result"] = diff_block_match.group(1).strip()
        else:
            new_element["modified_result"] = ""

        extracted_elements.append(new_element)

with open(output_file, 'w', encoding='utf-8') as f:
    for item in extracted_elements:
        json.dump(item, f, ensure_ascii=False)
        f.write('\n')
