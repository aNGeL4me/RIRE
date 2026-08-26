import json

def generate_null_json(a_path, notnull_path, output_path):
    with open(a_path, 'r', encoding='utf-8') as f:
        a_data = json.load(f)

    with open(notnull_path, 'r', encoding='utf-8') as f:
        notnull_data = json.load(f)
    notnull_inputs = set(item['input'] for item in notnull_data)

    null_data = [item for item in a_data if item['input'] not in notnull_inputs]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(null_data, f, indent=4, ensure_ascii=False)


generate_null_json('train_512_InDevign_AddNewKeysCommitidProject_updated_target1target0.json', \
                   'train_512_InDevign_AddNewKeysCommitidProject_updated_target1target0_ChangesNotNull.json', \
                    'train_512_InDevign_AddNewKeysCommitidProject_updated_target1target0_ChangesNull.json')
