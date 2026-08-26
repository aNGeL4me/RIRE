import json
import os
import json

def update_changes_if_empty(src_file_1, src_file_2, output_file):

    input_to_changes = {}
    with open(src_file_2, "r", encoding="utf-8") as f2:
        for line in f2:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                input_val = obj.get("input")
                changes = obj.get("changes", [])
                if input_val is not None:
                    input_to_changes[input_val] = changes
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON decode error in file2: {e}")

    updated_count = 0

    with open(src_file_1, "r", encoding="utf-8") as f1, open(output_file, "w", encoding="utf-8") as fout:
        for line in f1:
            if not line.strip():
                continue
            try:
                element = json.loads(line)
                changes = element.get("changes", [])
                if not changes:
                    input_val = element.get("input")
                    if input_val in input_to_changes and input_to_changes[input_val]:
                        element["changes"] = input_to_changes[input_val]
                        updated_count += 1

                fout.write(json.dumps(element, ensure_ascii=False) + "\n")
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON decode error in file1: {e}")


    print(f"[INFO] update changes null elements numbers: {updated_count}")

update_changes_if_empty(\
    "train_512_InDevign_AddNewKeysCommitidProject_updated_target1target0_DelIndent.json", \
        "train_512_InDevign_updated_target1_0_ChangesNull_UpdatedChanges_1st_2nd_merged.json", \
            "train_512_InDevign_updated_target1_0_DelIndent_GeneratedChanges_merged.json")
