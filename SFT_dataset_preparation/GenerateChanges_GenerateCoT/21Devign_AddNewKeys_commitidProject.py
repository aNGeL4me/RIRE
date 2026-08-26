import json

with open('train_512.json_InDevign.json', 'r', encoding='utf-8') as f:
    a_data = json.load(f)

with open('../VulLLMDataset_DevignDataset_DiversevulDataset/formatted_function.json', 'r', encoding='utf-8') as f:
    formatted_data = json.load(f)

func_map = {
    item['func']: {
        'project': item['project'],
        'commit_id': item['commit_id']
    }
    for item in formatted_data
}

matched_data = []
for elem in a_data:
    input_code = elem.get("input")
    if input_code in func_map:
        elem.update(func_map[input_code])
    matched_data.append(elem)

with open('train_512_InDevign_AddNewKeysCommitidProject.json', 'w', encoding='utf-8') as f:
    json.dump(matched_data, f, indent=4, ensure_ascii=False)
