import json

def is_empty_change(change):
    return all(change.get(key, "") == "" for key in ["context_line_del", "context_line_add", "deletions", "additions"])

with open('train_512_InDiversevul_AddNewKeysCommitidProjectEtc_updateProjectKeyValue_updateMessage_updateChanges.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

filtered_data = []

for item in data:
    changes = item.get("changes", [])
    cleaned_changes = [change for change in changes if not is_empty_change(change)]
    
    item["changes"] = cleaned_changes

    if cleaned_changes:
        filtered_data.append(item)

with open('train_512_InDiversevul_AddNewKeysCommitidProjectEtc_updateProjectKeyValue_updateMessage_updateChanges_ChangesNotNull.json', 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f, indent=4, ensure_ascii=False)

print(f"Extracted {len(filtered_data)} ")
