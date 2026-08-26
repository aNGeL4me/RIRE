import json

def build_preference_dataset(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    preference_data = []

    for item in data:
        output = int(item.get("output", 0))

        # Common fields
        base_fields = {
            "instruction": item.get("instruction", ""),
            "input": item.get("input", ""),
            "output": item.get("output", ""),
            "idx": item.get("idx", 0)
        }

        if output == 0:
            # ✅ Case 1: output is 0, Safe is dominant
            # Preference sample 1: SafeW vs Unsafe
            if "AsSafeW" in item and "AsUnsafe" in item:
                sample1 = base_fields.copy()
                sample1["chosen"] = item["AsSafeW"]
                sample1["rejected"] = item["AsUnsafe"]
                preference_data.append(sample1)

            # Preference sample 2: SafeW vs SafeL
            if "AsSafeW" in item and "AsSafeL" in item:
                sample2 = base_fields.copy()
                sample2["chosen"] = item["AsSafeW"]
                sample2["rejected"] = item["AsSafeL"]
                preference_data.append(sample2)

        elif output == 1:
            # ✅ Case 2: output is 1, Unsafe is dominant
            # Preference sample 1: UnsafeW vs Safe
            if "AsUnsafeW" in item and "AsSafe" in item:
                sample1 = base_fields.copy()
                sample1["chosen"] = item["AsUnsafeW"]
                sample1["rejected"] = item["AsSafe"]
                preference_data.append(sample1)

            # Preference sample 2: UnsafeW vs UnsafeL
            if "AsUnsafeW" in item and "AsUnsafeL" in item:
                sample2 = base_fields.copy()
                sample2["chosen"] = item["AsUnsafeW"]
                sample2["rejected"] = item["AsUnsafeL"]
                preference_data.append(sample2)

    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(preference_data, f, indent=4, ensure_ascii=False)

# Example usage
input_file = "./03eval_2diff_after/train512_22837_randomSampled3970_0x01_2646_eval_preference_keys.json"
output_file = "./03eval_2diff_after/train512_22837_randomSampled3970_0x01_2646_preference.json"

build_preference_dataset(input_file, output_file)
