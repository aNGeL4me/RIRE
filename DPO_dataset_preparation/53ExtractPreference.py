import json
import re

def rename_keys_based_on_eval_result(data):
    for item in data:
        output = int(item.get("output", 0))
        eval_result = item.get("eval_result", "")
        match = re.search(r"\[\s*evaluation_start\s*\]\s*(\d[>=<]\d)\s*\[\s*evaluation_end\s*\]", eval_result)
        if not match:
            continue

        eval_comp = match.group(1).strip()  # Extract '1>2', '2>1', or '1=2'
        
        # Decide which set of keys to use
        if output == 0:
            key1, key2 = "AsSafe1", "AsSafe2"
            winner_key, loser_key = "AsSafeW", "AsSafeL"
        else:
            key1, key2 = "AsUnsafe1", "AsUnsafe2"
            winner_key, loser_key = "AsUnsafeW", "AsUnsafeL"

        val1 = item.pop(key1, None)
        val2 = item.pop(key2, None)

        if val1 is None or val2 is None:
            continue  # Skip if any key is missing

        if eval_comp in ("1>2", "1=2"):
            item[winner_key] = val1
            item[loser_key] = val2
        elif eval_comp == "2>1":
            item[winner_key] = val2
            item[loser_key] = val1
        else:
            # Unknown format, leave keys unchanged
            item[key1] = val1
            item[key2] = val2

    return data

# Example usage
input_path = "./03eval_2diff_after/train512_22837_randomSampled3970_0x01_3r_2646diff_eval2diff.json"
output_path = "./03eval_2diff_after/train512_22837_randomSampled3970_0x01_2646_eval_preference_keys.json"

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

updated_data = rename_keys_based_on_eval_result(data)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(updated_data, f, indent=4, ensure_ascii=False)
