import json

def merge_changes_by_input(first_file, second_file, output_file):
    # Read the first file
    with open(first_file, "r", encoding="utf-8") as f1:
        data1 = json.load(f1)

    # Build a mapping: input → changes
    input_to_changes = {item["input"]: item.get("changes", []) for item in data1}

    # Read the second file
    with open(second_file, "r", encoding="utf-8") as f2:
        data2 = json.load(f2)

    # Iterate over each element in the second file, attempt to add changes from the first file
    for item in data2:
        input_key = item["input"]
        if input_key in input_to_changes:
            item["changes"] = input_to_changes[input_key]

    # Write to output file
    with open(output_file, "w", encoding="utf-8") as fout:
        json.dump(data2, fout, indent=4, ensure_ascii=False)

# Example file paths (adjust according to your actual paths)
first_file = "./train_512_22837_cot_Refinement.json"
second_file = "./train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_randomSampled2646_diff.json"
output_file = "./train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_randomSampled2646_diff_changes.json"

# Execute the merge
merge_changes_by_input(first_file, second_file, output_file)
