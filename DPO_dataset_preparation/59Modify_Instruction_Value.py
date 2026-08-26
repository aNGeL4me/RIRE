import json

# Input and output file paths
input_file = "./train512_22837_randomSampled3970_0x01_3970CrossCategory_2646IntraCategory_preference_shuffled.json"
output_file = "./train512_22837_Sampled3970_0x01_3970Cross2646InCategory_preference_shuffle_resultStartV4.json"

# New instruction content
new_instruction = (
    "Act as a security analyst and determine whether the following code is [Vulnerable] or [Secure]. "
    "Start your response by immediately outputting the detection result as either [Vulnerable] or [Secure], "
    "using the following strict format:\n\n"
    "Result: [Vulnerable] or [Secure]\n"
    "Vulnerable line: <the specific line that is vulnerable, or 'None' if secure>\n"
    "Cause: <brief explanation of the cause if vulnerable, or 'None' if secure>\n"
    "Summary: <concise summary>\n"
    "Result: [Vulnerable] or [Secure]"
)

# Read the original file
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Modify the instruction field of each sample
for item in data:
    item["instruction"] = new_instruction

# Save the modified file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"The instruction field has been updated and saved as: {output_file}")
