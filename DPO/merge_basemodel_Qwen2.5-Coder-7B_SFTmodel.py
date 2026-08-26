from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

base_model_path = "/home/user/USER_NAME/.cache/modelscope/hub/Qwen/Qwen2___5-Coder-7B/"
lora_model_path = "../SFT/CodeLlama/Qwen2.5-Coder-7B_SFT-CoT_Refinement_length1024/epoch-7/"
merged_model_path = "./merged_Qwen2.5-Coder-7B_SFT-CoT_Refinement_length1024/"

print("Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_path,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True,
)

print("Loading LoRA adapter...")
model = PeftModel.from_pretrained(base_model, lora_model_path)

print("Merging LoRA weights into base model...")
merged_model = model.merge_and_unload()

print(f"Saving merged model to {merged_model_path} ...")
merged_model.save_pretrained(merged_model_path)

print("Saving tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(base_model_path, use_fast=False)
tokenizer.save_pretrained(merged_model_path)

print("Done.")
