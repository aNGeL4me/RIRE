import json

# Source file paths
file1_path = './train512_22837_randomSampled3970_0x01_2646_preference.json'
file2_path = './train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_3970-2646_1324_preference.json'

# Target output file path
output_path = './train512_22837_randomSampled3970_0x01_3970CrossCategory_2646IntraCategory_preference.json'

# Load contents of both files
with open(file1_path, 'r', encoding='utf-8') as f1:
    data1 = json.load(f1)

with open(file2_path, 'r', encoding='utf-8') as f2:
    data2 = json.load(f2)

# Combine the two lists
combined_data = data1 + data2

# Write to new file
with open(output_path, 'w', encoding='utf-8') as out_file:
    json.dump(combined_data, out_file, indent=4, ensure_ascii=False)

print(f"✅ Merge complete, output file saved as: {output_path}")
