import os
import json

# Set base directory
base_dir = './02generate_diff_split_after'
output_file = './train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_randomSampled2646_diff.json'

# Used to store all JSON objects
all_data = []

# Iterate over 49 subdirectories train512_22837_randomSampled3970_0x03_3r_2646_split_part2_result
for i in range(1, 49 + 1):  # Total number may need modification
    part_dir = f'3r2646_part{i}'
    json_filename = f'train512_22837_randomSampled3970_0x01_3r_2646_split_part{i}_result.json'
    json_path = os.path.join(base_dir, part_dir, json_filename)
    
    if not os.path.exists(json_path):
        print(f'File not found: {json_path}, skipping')
        continue

    with open(json_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                all_data.append(obj)
            except json.JSONDecodeError:
                print(f'Parse error: {json_path} line {line_num}, skipping this line')

print(f'Total collected {len(all_data)} JSON objects, writing to target file...')

# Write result file (as a JSON array)
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, indent=4, ensure_ascii=False)

print(f'✅ Merge completed and saved to {output_file}')
