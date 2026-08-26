import json

def process_json(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f_in:
        data = json.load(f_in)

    processed_signatures = set()

    with open(output_file, "a", encoding="utf-8") as f_out:
        for sample in data:
            json.dump(sample, f_out, ensure_ascii=False)
            f_out.write("\n")

    print(f"处理完成")

process_json(
    "train_512_InDiversevul_AddNewKeysCommitidProjectEtc_updateProjectKeyValue_updateMessage_updateChanges.json",\
        "train_512_InDiversevul_updateChanges_DelIndent.json")
