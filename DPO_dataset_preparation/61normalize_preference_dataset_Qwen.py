import json

# Input and output file paths
input_file = "./train512_22837_Sampled3970_0x01_3970Cross2646InCategory_preference_shuffle_resultStartV4.json"
output_file = "./train512_22837_Sampled3970_0x01_3970Cross2646InCategory_preference_prompt_Qwen.json"

# Read the original data
with open(input_file, "r", encoding='utf-8') as f:
    data = json.load(f)

# Prompt template
prompt_template = (
    "<|im_start|>user\n"
        "Below is an instruction that describes a task, paired with an input that provides further context. "
        "Write a response that appropriately completes the request.\n\n"
        "Instruction: {instruction}\n\n"
        "Input: {input}\n"
        "<|im_end|>\n"
        "<|im_start|>assistant\n"
)

# Iterate over each sample, construct the prompt, and delete the original instruction and input
for example in data:
    example["prompt"] = prompt_template.format(
        instruction=example["instruction"],
        input=example["input"]
    )
    # Remove keys that are no longer needed
    del example["instruction"]
    del example["input"]

# Save the processed data
with open(output_file, "w", encoding='utf-8') as f:
    json.dump(data, f, indent=4)
