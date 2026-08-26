import json
import re


def clean_commit_message(message):
    signature_patterns = [
        r'Author', r'Date',
        r'Signed-off-by', r'Reviewed-by', r'Acked-by', r'Co-authored-by',
        r'Tested-by', r'Reported-by', r'Cc', r'Suggested-by',
        r'Previous version reviewed-by', r'Previous version reviewed by', r'Inspired-by',
        r'Patchwork-ID', r'Link', r'References', r'Found-by',
        r'Authorship / merged commits', r'Message-id', r'Review-by', r'Reviewed by', 
        r'Suggested by', r'Signed-off by', r'Idea-by', r'Reported by'
    ]
    commit_pattern = r'^\s*commit [0-9a-f]{7,40}\s*$'
    other_patterns = rf'^\s*(?:{"|".join(signature_patterns)})[:\s].*'
    combined_pattern = rf'({other_patterns})|({commit_pattern})'
    compiled_pattern = re.compile(combined_pattern, flags=re.IGNORECASE)

    cleaned_lines = []
    for line in message.splitlines():
        if not compiled_pattern.match(line):
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines).rstrip()

input_file = "train_512_InDiversevul_AddNewKeysCommitidProjectEtc_updateProjectKeyValue.json"
output_file = "train_512_InDiversevul_AddNewKeysCommitidProjectEtc_updateProjectKeyValue_updateMessage.json"

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    original_message = item.get("message", "")
    cleaned_message = clean_commit_message(original_message)
    item["message"] = cleaned_message


with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"✅ save file: {output_file}")
