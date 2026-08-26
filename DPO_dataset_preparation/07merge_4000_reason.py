import os
import json

# Set the base directory
base_dir = './01generate_3reaons_splited_after'
output_file = './train512_22837_randomSampled3970_0x01_3reasons.json'

# Used to store all JSON objects
all_data = []

# Traverse 24 subdirectories
for i in range(1, 25 + 1):  # train_512_22837_randomSampled3970_0x03_split_part6_result
    part_dir = f'randomSampled3970_0x03_part{i}'
    json_filename = f'train_512_22837_randomSampled3970_0x01_split_part{i}_result.json'
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

# Write to output file (as a JSON array)
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, indent=4, ensure_ascii=False)

print(f'✅ Merge completed, saved to {output_file}')
