import json

def process_json(input_file, output_file):

    with open(input_file, "r", encoding="utf-8") as f_in:
        data = json.load(f_in)

    processed_signatures = set()


    with open(output_file, "a", encoding="utf-8") as f_out:
        for sample in data:
            json.dump(sample, f_out, ensure_ascii=False)
            f_out.write("\n")

    print(f"done")


process_json("train_512_22837_randomSampled3970_0x01.json", "train_512_22837_randomSampled3970_0x01_DelIndent.json")
