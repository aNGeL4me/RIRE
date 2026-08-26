import json

input_file = "train_512_InDiversevul_AddNewKeysCommitidProjectEtc.json"
owner_repo_file = "./OwnerRepo_corrected2nd.json"
output_file = "train_512_InDiversevul_AddNewKeysCommitidProjectEtc_updateProjectKeyValue.json"

project_to_owner_repo = {}
with open(owner_repo_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            project = data.get("project")
            owner_repo = data.get("OwnerRepo", "")
            if project and owner_repo:
                formatted_owner_repo = owner_repo.replace("/", "_")
                project_to_owner_repo[project] = formatted_owner_repo
        except json.JSONDecodeError as e:
            print("process OwnerRepo error: ", e)

with open(input_file, 'r', encoding='utf-8') as f:
    main_data = json.load(f)

updated_data = []
for item in main_data:
    project = item.get("project")
    new_project = project_to_owner_repo.get(project)
    if new_project:
        item["project"] = new_project
    updated_data.append(item)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(updated_data, f, ensure_ascii=False, indent=4)

print(f"✅ new file saved: {output_file}")
