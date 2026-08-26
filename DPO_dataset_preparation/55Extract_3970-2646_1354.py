import json

# File paths
large_file = 'train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_3rd.json'
subset_file = 'train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_randomSampled2646_diff_changes.json'
output_file = 'train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_3970-2646_1324.json'

print("Loading files...")

# Load the large file (4000 elements)
with open(large_file, 'r', encoding='utf-8') as f:
    large_data = json.load(f)
    print(f"Large file loaded, total {len(large_data)} elements")

# Load the subset file (2646 elements)
with open(subset_file, 'r', encoding='utf-8') as f:
    subset_data = json.load(f)
    print(f"Subset file loaded, total {len(subset_data)} elements")

# Create a set of all 'input' values from the subset file for quick lookup
subset_inputs = {item['input'] for item in subset_data if 'input' in item}
print("Built index of 'input' values from subset file")

# Find elements in the large file but not in the subset (complement)
complement = []
for item in large_data:
    if 'input' in item and item['input'] not in subset_inputs:
        complement.append(item)

# Output statistics
print("\nStatistics:")
print(f"Total elements in large file: {len(large_data)}")
print(f"Total elements in subset file: {len(subset_data)}")
print(f"Number of complement elements found: {len(complement)}")
expected_diff = len(large_data) - len(subset_data)
print(f"Expected difference count: {expected_diff}")

# Verify results
if len(complement) != expected_diff:
    print(f"Warning: Found complement count ({len(complement)}) does not match expected difference ({expected_diff})")
else:
    print("Complement count verification passed")

# Save results to file
if complement:
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(complement, f, indent=4, ensure_ascii=False)
    print(f"\nSaved {len(complement)} complement elements to: {output_file}")
else:
    print("\nNo complement elements found")

print("Operation completed")
