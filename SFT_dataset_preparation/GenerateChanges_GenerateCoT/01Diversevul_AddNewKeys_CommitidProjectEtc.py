import json

vulllm_path = "./train_512.json_InDiversevul.json"
diversevul_path = "./VulLLMDataset_DevignDataset_DiversevulDataset/diversevul_20230702.json"
output_path = "train_512_InDiversevul_AddNewKeysCommitidProjectEtc.json"

with open(vulllm_path, 'r', encoding='utf-8') as f:
    vulllm_data = json.load(f)


diversevul_func_map = {}
with open(diversevul_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            func_code = item["func"].strip()
            diversevul_func_map[func_code] = item
        except json.JSONDecodeError as e:
            print("JSON decode error：", line)
            raise e


updated_data = []
for item in vulllm_data:
    input_code = item["input"].strip()
    match = diversevul_func_map.get(input_code)
    if match:
        item["project"] = match.get("project", "")
        item["commit_id"] = match.get("commit_id", "")
        item["cwe"] = match.get("cwe", [])
        item["message"] = match.get("message", "")
    updated_data.append(item)


with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(updated_data, f, ensure_ascii=False, indent=4)

print(f"✅ new file saved: {output_path}")
