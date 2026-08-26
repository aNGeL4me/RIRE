import json
import re

# Replace with your actual path
input_path = "train512_22837_randomSampled3970_0x01_3reasons_processed.json"
output_path = "train512_22837_randomSampled3970_0x01_3reasons_cleaned.json"

def remove_analysis_titles(text):
    """
    Remove all redundant header content before 'Vulnerable line:', 
    such as '**Result: 1**', '**Output 1:**', '**First Analysis:**', etc.
    """
    # Keep content starting from "Vulnerable line:" and delete everything before it
    return re.sub(
        r"^.*?(?=Vulnerable line\s*:)",  # Non-greedy match until 'Vulnerable line:'
        "", 
        text,
        flags=re.IGNORECASE | re.DOTALL
    )


def normalize_reason_fields(text):
    """
    Normalize reasoning field format: remove bold symbols and unify the format after field names.
    """
    # Match field names and remove surrounding ** for **Vulnerable line**, **Vulnerable line:**, **Vulnerable line: **, etc.
    text = re.sub(
        r"\*\*\s*(Vulnerable line|Cause|Summary|Result)\s*:?\s*\*\*",  # Remove ** around field names
        r"\1", 
        text
    )
    # Normalize line breaks and extra spaces after field names into ": "
    text = re.sub(
        r"(Vulnerable line|Cause|Summary|Result)\s*[:：]?\s*[\r\n]+\s*", 
        r"\1: ", 
        text
    )
    # Ensure there is a colon and a space after the field names
    text = re.sub(
        r"(Vulnerable line|Cause|Summary|Result)\s*[:：]?\s*", 
        r"\1: ", 
        text
    )

    return text.strip()


def clean_reason_text(text):
    text = remove_analysis_titles(text)
    text = normalize_reason_fields(text)
    return text


with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data:
    output = item.get("output", "")
    if output == "1":
        for key in ["AsUnsafe1", "AsUnsafe2", "AsSafe"]:
            if key in item:
                item[key] = clean_reason_text(item[key])
    elif output == "0":
        for key in ["AsSafe1", "AsSafe2", "AsUnsafe"]:
            if key in item:
                item[key] = clean_reason_text(item[key])

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Cleaning complete, saved to:", output_path)
