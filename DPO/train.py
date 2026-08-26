# -*- coding: utf-8 -*-

import os
import json
from dataclasses import dataclass, field
from typing import Optional, Dict
from transformers import (HfArgumentParser, AutoTokenizer, AutoModelForCausalLM, AutoConfig, BitsAndBytesConfig)
from datasets import load_dataset
from loguru import logger
from trl import DPOTrainer, DPOConfig
from peft import LoraConfig, TaskType
import torch
from copy import deepcopy


@dataclass
class ScriptArguments:
    model_name_or_path: str = field(metadata={"help": "Path to the SFT model or base model"})
    tokenizer_name_or_path: Optional[str] = field(default=None)
    ref_model_path: Optional[str] = field(default=None)
    train_file: Optional[str] = field(default=None)
    validation_file: Optional[str] = field(default=None)
    output_dir: str = field(default="outputs-dpo")
    use_peft: bool = field(default=True)
    qlora: bool = field(default=False)
    target_modules: Optional[str] = field(default=None)
    lora_rank: int = field(default=8)
    lora_alpha: float = field(default=16.0)
    lora_dropout: float = field(default=0.05)
    per_device_train_batch_size: int = field(default=2)
    per_device_eval_batch_size: int = field(default=1)
    learning_rate: float = field(default=5e-5)
    max_steps: int = field(default=1000)
    logging_steps: int = field(default=10)
    save_steps: int = field(default=100)
    eval_steps: int = field(default=100)
    warmup_steps: int = field(default=50)
    max_length: int = field(default=1024)
    gradient_checkpointing: bool = field(default=True)
    gradient_accumulation_steps: int = field(default=4)
    torch_dtype: Optional[str] = field(default="float16")
    fp16: bool = field(default=True)
    bf16: bool = field(default=False)
    report_to: Optional[str] = field(default="tensorboard")


def print_trainable_parameters(model):
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    logger.info(f"Trainable params: {trainable} / {total} ({100 * trainable / total:.2f}%)")


# def tokenize_dpo_example(example, tokenizer, max_length):
#     prompt = example["prompt"]
#     chosen = example["chosen"]
#     rejected = example["rejected"]
#     prompt_chosen = tokenizer(prompt + chosen, truncation=True, max_length=max_length)
#     prompt_rejected = tokenizer(prompt + rejected, truncation=True, max_length=max_length)
#     return (len(prompt_chosen["input_ids"]) <= max_length and
#             len(prompt_rejected["input_ids"]) <= max_length)

def main():
    parser = HfArgumentParser(ScriptArguments)
    args = parser.parse_args_into_dataclasses()[0]
    os.makedirs(args.output_dir, exist_ok=True)

    # Save config
    with open(os.path.join(args.output_dir, "dpo_config.json"), "w") as f:
        json.dump(vars(args), f, indent=2)

    # Tokenizer
    tokenizer_path = args.tokenizer_name_or_path or args.model_name_or_path
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, use_fast=False, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token or tokenizer.unk_token

    # Load model
    dtype = getattr(torch, args.torch_dtype)
    quant_cfg = None
    if args.qlora:
        quant_cfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=dtype,
        )

    model = AutoModelForCausalLM.from_pretrained(
        args.model_name_or_path,
        torch_dtype=dtype,
        device_map="auto",
        trust_remote_code=True,
        quantization_config=quant_cfg
    )

    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        model.config.use_cache = False

    # PEFT
    peft_config = None
    if args.use_peft:
        target_modules = args.target_modules.split(",") if args.target_modules else ["q_proj", "v_proj", "k_proj", "o_proj"]
        peft_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            target_modules=target_modules,
            inference_mode=False,
            r=args.lora_rank,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
        )

    # Dataset
    data_files = {}
    if args.train_file: data_files["train"] = args.train_file
    if args.validation_file: data_files["validation"] = args.validation_file
    dataset = load_dataset("json", data_files=data_files)

    def preprocess(example):
        return {
            "prompt": example["prompt"],
            "chosen": example["chosen"],
            "rejected": example["rejected"]
        }

    dataset = dataset.map(preprocess, remove_columns=dataset["train"].column_names)

    # def tokenize_dpo_example(...)...
    def tokenize_function(example):
        prompt = example["prompt"]
        chosen = example["chosen"]
        rejected = example["rejected"]
        prompt_chosen = tokenizer(prompt + chosen, truncation=True, padding="max_length", max_length=args.max_length, return_tensors="pt")
        prompt_rejected = tokenizer(prompt + rejected, truncation=True, padding="max_length", max_length=args.max_length, return_tensors="pt")
        return {
            "input_ids_chosen": prompt_chosen["input_ids"].squeeze(),
            "attention_mask_chosen": prompt_chosen["attention_mask"].squeeze(),
            "input_ids_rejected": prompt_rejected["input_ids"].squeeze(),
            "attention_mask_rejected": prompt_rejected["attention_mask"].squeeze(),
        }

    tokenized_dataset = {}
    tokenized_dataset["train"] = dataset["train"].map(tokenize_function)

    # Ref model
    ref_model = None
    if args.ref_model_path:
        ref_model = AutoModelForCausalLM.from_pretrained(args.ref_model_path, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True)
    else:
        # Fallback: if reference model is not specified, deep copy the policy model (not recommended but usable)
        # ref_model = deepcopy(model)
        ref_model = None

    # Trainer
    train_config = DPOConfig(
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_eval_batch_size,
        max_steps=args.max_steps,
        learning_rate=args.learning_rate,
        save_steps=args.save_steps,
        # eval_steps=args.eval_steps,
        logging_steps=args.logging_steps,
        warmup_steps=args.warmup_steps,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        gradient_checkpointing=args.gradient_checkpointing,
        report_to=args.report_to,
        fp16=args.fp16,
        bf16=args.bf16,
        output_dir=args.output_dir,
    )

    trainer = DPOTrainer(
        model=model,
        ref_model=None,  # DPO will automatically clone ref_model from model. If using full-parameter fine-tuning, you must explicitly provide ref_model (initialized same as policy model)
        args=train_config,
        train_dataset=dataset["train"],
        # eval_dataset=dataset.get("validation", None),
        tokenizer=tokenizer,
        peft_config=peft_config,
    )

    print_trainable_parameters(trainer.model)

    trainer.train()
    trainer.save_model()  # Default behavior: save to TrainingArguments.output_dir
    tokenizer.save_pretrained(args.output_dir)


if __name__ == "__main__":
    main()
