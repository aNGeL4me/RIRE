import os
import shutil

# Parameter settings train512_22837_3970_0x03_3r_2646diff_eval_split_part2
num_parts = 14
json_prefix = 'train512_22837_3970_0x01_3r_2646diff_eval_split_part'
folder_prefix = 'evaluate_2646_2diff_part'
splited_dir = './03eval_2diff_pre'
api_script = '51deepseek_evaluate_2_diff.py'

# Absolute path
current_dir = os.getcwd()
api_script_path = os.path.join(current_dir, api_script)

# Check if API script exists
if not os.path.exists(api_script_path):
    raise FileNotFoundError(f"File not found: {api_script_path}")

# Create folders and move files
for i in range(1, num_parts + 1):
    part_str = f'{i}'
    json_filename = f'{json_prefix}{part_str}.json'
    folder_name = f'{folder_prefix}{part_str}'

    src_json_path = os.path.join(splited_dir, json_filename)
    dst_folder_path = os.path.join(splited_dir, folder_name)
    dst_json_path = os.path.join(dst_folder_path, json_filename)
    dst_api_path = os.path.join(dst_folder_path, api_script)

    # Create subfolder
    os.makedirs(dst_folder_path, exist_ok=True)

    # Move JSON file
    if os.path.exists(src_json_path):
        shutil.move(src_json_path, dst_json_path)
        print(f'Moved {json_filename} to {folder_name}/')
    else:
        print(f'Warning: {json_filename} not found, skipping')

    # Copy API file
    shutil.copy(api_script_path, dst_api_path)
    print(f'Copied {api_script} to {folder_name}/')

print("Operation completed!")
