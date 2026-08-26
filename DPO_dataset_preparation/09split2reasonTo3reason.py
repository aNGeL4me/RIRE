import os
import json
import re

# File paths (please adjust according to your actual paths)
input_file = "train512_22837_randomSampled3970_0x01_3reasons.json"
output_file = "train512_22837_randomSampled3970_0x01_3reasons_processed.json"

# Load data
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

def robust_split_reason_sections(text):
    """
    General reasoning structure splitter to extract two reasoning parts:
    1. Supports splitting by headings like "### Analysis X" or "### First Analysis"
    2. Supports no headings, splitting by multiple structures of "Vulnerable line: ... Cause: ... Summary: ... Result: [...]"
    """
    # Normalize newline characters
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Try splitting by headings (e.g., ### Analysis 1, ### First Analysis)
    parts = re.split(r'### .*?Analysis.*?\n', text)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) >= 2:
        return parts[:2]

    # If splitting by headings fails, try splitting based on two "Result:" structures
    result_matches = list(re.finditer(r'Result:\s*\[[^\]]+\]', text))

    if len(result_matches) >= 2:
        split_index = result_matches[0].end()
        first = text[:split_index].strip()
        second = text[split_index:].strip()
        return [first, second]

    # If only one reasoning structure or cannot split, return original text as single item
    return [text.strip()]

# Process data
for item in data:
    output = item.get("output", "")
    
    if output == "1":
        as_unsafe = item.get("AsUnsafe", "")
        parts = robust_split_reason_sections(as_unsafe)
        if len(parts) == 2:
            item["AsUnsafe1"] = parts[0]
            item["AsUnsafe2"] = parts[1]
        item.pop("AsUnsafe", None)

    elif output == "0":
        as_safe = item.get("AsSafe", "")
        parts = robust_split_reason_sections(as_safe)
        if len(parts) == 2:
            item["AsSafe1"] = parts[0]
            item["AsSafe2"] = parts[1]
        item.pop("AsSafe", None)

# Save results
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
