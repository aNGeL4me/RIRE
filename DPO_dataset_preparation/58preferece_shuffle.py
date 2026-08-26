import json
import random

# Input file path
input_file = './train512_22837_randomSampled3970_0x01_3970CrossCategory_2646IntraCategory_preference.json'

# Output file path (you can also overwrite the original file)
output_file = './train512_22837_randomSampled3970_0x01_3970CrossCategory_2646IntraCategory_preference_shuffled.json'

# Load JSON data
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Shuffle the order of elements
random.shuffle(data)

# Save to new file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"✅ Data has been shuffled and saved to {output_file}")
