import os
import json

# Set base directory
base_dir = './03eval_2diff_after'
output_file = './03eval_2diff_after/train512_22837_randomSampled3970_0x01_3r_2646diff_eval2diff.json'

# Used to store all JSON objects
all_data = []
total_files = 0
total_elements = 0

print("Starting to merge files and count the number of elements in each file...")

# Traverse 14 subdirectories train512_22837_3970_0x03_3r_2646diff_eval_split_part5_result
for i in range(1, 14 + 1):
    part_dir = f'evaluate_2646_2diff_part{i}'
    json_filename = f'train512_22837_3970_0x01_3r_2646diff_eval_split_part{i}_result.json'
    json_path = os.path.join(base_dir, part_dir, json_filename)
    
    if not os.path.exists(json_path):
        print(f'⚠️ File not found: {json_path}, skipping')
        continue

    total_files += 1
    file_elements = 0
    print(f"\nProcessing file: {json_filename}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                all_data.append(obj)
                file_elements += 1
            except json.JSONDecodeError:
                print(f'  ⚠️ Parse error: line {line_num}, skipping this line')
    
    total_elements += file_elements
    print(f"  Number of elements in file: {file_elements} (Current total: {total_elements})")

print(f'\nTotal processed files: {total_files}')
print(f'Total JSON objects extracted from files: {total_elements}')

# Check the actual number of elements in the merged list
merged_count = len(all_data)
if merged_count != total_elements:
    print(f"⚠️ Warning: Total elements counted from files ({total_elements}) does not match merged result ({merged_count})")
    print(f"⚠️ Possible data duplication or parsing errors, difference: {abs(total_elements - merged_count)}")
else:
    print(f"✅ Data consistency check passed")

print(f'Writing merged data to target file {output_file}...')

# Write result file (as a JSON array)
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, indent=4, ensure_ascii=False)

# Verify the actual number of elements in the output file
print(f'✅ Merge completed, saved to {output_file}')
print(f'Final number of elements in merged file: {len(all_data)}')
