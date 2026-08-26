import json


input_path = "train_512_InDevign_updated_target1_0_ChangesNull_UpdatedChanges_1.json"
output_path = "train_512_InDevign_updated_target1_0_ChangesNull_UpdatedChanges_1_ChangesNull.json"

with open(input_path, 'r', encoding='utf-8') as fin, open(output_path, 'w', encoding='utf-8') as fout:
    
    for line in fin:
        try:
            element = json.loads(line)
            if not element.get("changes"): 
                json.dump(element, fout, ensure_ascii=False)
                fout.write('\n')
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse line: {e}")
