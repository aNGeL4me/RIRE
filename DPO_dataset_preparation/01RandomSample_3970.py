import json
import random

random.seed(42)

with open('train_512_14837.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

output_1_samples = [sample for sample in data if sample.get("output") == "1"]
output_0_samples = [sample for sample in data if sample.get("output") == "0"]

n1 = 1985
n0 = 1985


if len(output_1_samples) < n1 or len(output_0_samples) < n0:
    raise ValueError(f"Insufficient number of samples: output=1 has {len(output_1_samples)} samples, output=0 has {len(output_0_samples)} samples")

sampled_output_1 = random.sample(output_1_samples, n1)
sampled_output_0 = random.sample(output_0_samples, n0)
sampled_data = sampled_output_1 + sampled_output_0
random.shuffle(sampled_data)

with open('train_512_22837_randomSampled3970_0x01.json', 'w', encoding='utf-8') as f:
    json.dump(sampled_data, f, indent=4, ensure_ascii=False)

print(f"Sampling completed. Number of samples with output 1: {len(sampled_output_1)}, number of samples with output 0: {len(sampled_output_0)}")
print(f"Total number of samples: {len(sampled_data)}, saved to randomSampled_fixed_counts.json")
