import json
import random

# Set random seed for reproducibility (optional)
random.seed(42)

# Load data
with open('train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Categorize by output field
output_1_samples = [sample for sample in data if sample.get("output") == "1"]
output_0_samples = [sample for sample in data if sample.get("output") == "0"]

# Fixed number sampling
n1 = 1323  # Sample 1323 from output=1
n0 = 1323  # Sample 1323 from output=0

# Check if there are enough samples
if len(output_1_samples) < n1 or len(output_0_samples) < n0:
    raise ValueError(f"Not enough samples: output=1 has {len(output_1_samples)}, output=0 has {len(output_0_samples)}")

sampled_output_1 = random.sample(output_1_samples, n1)
sampled_output_0 = random.sample(output_0_samples, n0)

# Combine the two sampling results
sampled_data = sampled_output_1 + sampled_output_0

# (Optional) Shuffle the final order
random.shuffle(sampled_data)

# Save to a new file
with open('train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_randomSampled2646.json', 'w', encoding='utf-8') as f:
    json.dump(sampled_data, f, indent=4, ensure_ascii=False)

print(f"Sampling completed, number of output=1 samples: {len(sampled_output_1)}, number of output=0 samples: {len(sampled_output_0)}")
print(f"Total samples: {len(sampled_data)}, saved to randomSampled_fixed_counts.json")
