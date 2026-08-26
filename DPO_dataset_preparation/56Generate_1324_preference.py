import json

# Input and output file paths
input_file = "train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_3970-2646_1324.json"
output_file = "train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_3970-2646_1324_preference.json"

# Load the original data
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

preference_data = []

for sample in data:
    output = sample.get("output")
    new_sample = {
        "instruction": sample.get("instruction"),
        "input": sample.get("input"),
        "output": output,
        "idx": sample.get("idx"),
    }

    # Select candidate content
    if output == "0":
        # Safe sample: AsSafe1 as chosen, AsUnsafe as rejected
        new_sample["chosen"] = sample.get("AsSafe1")
        new_sample["rejected"] = sample.get("AsUnsafe")
    elif output == "1":
        # Unsafe sample: AsUnsafe1 as chosen, AsSafe as rejected
        new_sample["chosen"] = sample.get("AsUnsafe1")
        new_sample["rejected"] = sample.get("AsSafe")
    else:
        # Skip the sample if output is not "0" or "1"
        continue

    preference_data.append(new_sample)

# Save the new preference format data
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(preference_data, f, indent=4, ensure_ascii=False)

print(f"Successfully generated {len(preference_data)} preference samples, saved to {output_file}")
