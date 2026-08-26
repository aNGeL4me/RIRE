# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed according to the terms of the Llama 2 Community License Agreement.

from dataclasses import dataclass


@dataclass
class train_config:
    model_name: str=""
    enable_fsdp: bool=False
    low_cpu_fsdp: bool=False
    run_validation: bool=True
    batch_size_training: int=64
    batching_strategy: str="packing" #alternative: padding
    context_length: int=512
    gradient_accumulation_steps: int=1
    num_epochs: int=5
    num_workers_dataloader: int=1
    lr: float= 1e-6#1e-5#5e-5#1e-6#1e-4#2e-6#2e-5#3e-5#2e-5#3e-5#2e-5#6e-6#3e-6#4e-6#6e-6#1e-6#5e-6#6e-5#1e-4#8e-6#3e-5#1e-5#5e-5#4e-5#1e-4#6e-5#8e-5#1e-4#3e-4#1e-4#5e-5#1e-4#5e-5#1e-4#1.4e-4#5e-5#51e-4#5e-4#1e-4#8e-5#1e-5#5e-4#1e-4
    weight_decay: float=0.01#0.01#0.0#0.01#0.0#0.01#0.0#0.01#0.01#0.0#0.01#0.005#0.01#0.0#0.01#0.0#0.01#0.0#0.01#0.0#0.01#0.0#0.01#0.0#0.01#0.0
    gamma: float= 0.85#0.95#0.85#0.9#0.85
    seed: int=42
    use_fp16: bool=False
    mixed_precision: bool=True
    val_batch_size: int=32
    dataset = "alpaca_dataset"
    peft_method: str = "lora" # None , llama_adapter, prefix
    use_peft: bool=False
    output_dir: str = "PATH/to/save/PEFT/model"
    freeze_layers: bool = False
    num_freeze_layers: int = 1
    quantization: bool = False
    one_gpu: bool = False
    save_model: bool = True
    dist_checkpoint_root_folder: str="PATH/to/save/FSDP/model" # will be used if using FSDP
    dist_checkpoint_folder: str="fine-tuned" # will be used if using FSDP
    save_optimizer: bool=False # will be used if using FSDP
    use_fast_kernels: bool = False # Enable using SDPA from PyTroch Accelerated Transformers, make use Flash Attention and Xformer memory-efficient kernels
