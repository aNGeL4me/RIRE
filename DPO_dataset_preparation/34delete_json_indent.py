import json

def process_json(input_file, output_file):  # The entire content of input_file needs to be an array []
    # Read the JSON file
    with open(input_file, "r", encoding="utf-8") as f_in:
        data = json.load(f_in)  # Parse the entire JSON array

    processed_signatures = set()  # Used to record processed function signatures to avoid duplication

    # Iterate over each sample
    with open(output_file, "a", encoding="utf-8") as f_out:
        for sample in data:
            json.dump(sample, f_out, ensure_ascii=False)
            f_out.write("\n")  # Append newline for easier multi-line records

    print("Processing completed")

# Call the function
process_json("train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated.json", 
             "train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_DelIndent.json")
