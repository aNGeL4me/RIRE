# Dataset of Reasoning-Enhanced Fine-Tuning 

Run the Python scripts in the “SFT_dataset_preparation” directory sequentially to generate the dataset for “Reasoning-Enhanced Fine-Tuning.”

# Dataset of Refinement-Oriented Hierarchical Preference Optimization

Run the Python scripts in the “DPO_dataset_preparation” directory sequentially to generate the preference dataset for “Refinement-Oriented Hierarchical Preference Optimization.”

# Main Expriment

## CodeLlama-7b

### SFT

***Fine-tuning CodeLlama-7b***

```
pip install -r requirements.txt
conda activate RIRE_sft
cd ./RIRE/SFT/CodeLlama/
python finetuning.py \
    --use_peft \
    --model_name /home/user/USER_NAME/.cache/modelscope/hub/AI-ModelScope/CodeLlama-7b-hf/ \
    --peft_method lora \
    --batch_size_training 16 \
    --gradient_accumulation_steps 1 \
    --lr 1e-6 \
    --lora_rank 16 \
    --lora_alpha 32 \
    --val_batch_size 16 \
    --weight_decay 0.01 \
    --context_length 512 \
    --quantization \
    --num_epochs 3 \
    --alpaca_dataset.train_data_path "../../dataset/MixVul/llm/train_512_22837.json" \
    --alpaca_dataset.valid_data_path "../../dataset/MixVul/llm/valid_512.json" \
    --output_dir "./CodeLlama-7b_SFT_length512" > ./finetuning_CodeLlama-7b_SFT_length512.log
```

***Inference***

```
python inference_batch.py \
   --base_model /home/user/USER_NAME/.cache/modelscope/hub/AI-ModelScope/CodeLlama-7b-hf/ \
   --tuned_model ./codellama-7b_SFT_length512/epoch-2 \
   --data_file ../../dataset/DiverseVul/test_512.json \
  --batch_size 10 \
  --csv_path ./CodeLlama-7b_SFT_length512/CodeLlama-7b_SFT_DiverseVul.csv > ./CodeLlama-7b_SFT_length512/CodeLlama-7b_SFT_DiverseVul.log
```

### SFT-CoT

***Fine-tuning CodeLlama 7b***

```
python finetuning.py \
    --use_peft \
    --model_name /home/user/USER_NAME/.cache/modelscope/hub/AI-ModelScope/CodeLlama-7b-hf/ \
    --peft_method lora \
    --batch_size_training 32 \
    --gradient_accumulation_steps 1 \
    --lr 1e-4 \
    --lora_rank 80 \
    --lora_alpha 160 \
    --val_batch_size 32 \
    --weight_decay 0.01 \
    --context_length 1024 \
    --quantization \
    --num_epochs 10 \
    --alpaca_dataset.train_data_path "../../dataset/MixVul/cot/train_512_22837_cot_noRefinement.json" \
    --alpaca_dataset.valid_data_path "../../dataset/MixVul/cot/valid_512_modified.json" \
    --output_dir "./CodeLlama-7b_SFT-CoT_length1024" > finetuning_CodeLlama-7b_SFT-CoT_length1024.log
```

***Inference***

```
python inference_cot_batch_resume.py \
   --base_model /home/user/USER_NAME/.cache/modelscope/hub/AI-ModelScope/CodeLlama-7b-hf/ \
   --tuned_model ./codellama-7b-SFT-CoT_length1024/epoch-8 \
   --data_file ../../dataset/DiverseVul/test_512_newInstruction.json \
  --batch_size 10 \
  --csv_path ./CodeLlama-7b_SFT-CoT_length1024/CodeLlama-7b_SFT-CoT_noRefinement_DiverseVul.csv > ./CodeLlama-7b_SFT-CoT_length1024/CodeLlama-7b_SFT-CoT_noRefinement.log
```

### RIRE

#### Reasoning-Enhanced Fine-Tuning

```
python finetuning.py \
    --use_peft \
    --model_name /home/user/USER_NAME/.cache/modelscope/hub/AI-ModelScope/CodeLlama-7b-hf/ \
    --peft_method lora \
    --batch_size_training 32 \
    --gradient_accumulation_steps 1 \
    --lr 1e-4 \
    --lora_rank 80 \
    --lora_alpha 160 \
    --val_batch_size 32 \
    --weight_decay 0.01 \
    --context_length 1024 \
    --quantization \
    --num_epochs 10 \
    --alpaca_dataset.train_data_path "../../dataset/MixVul/cot/train_512_22837_cot_Refinement.json" \
    --alpaca_dataset.valid_data_path "../../dataset/MixVul/cot/valid_512_modified.json" \
    --output_dir "CodeLlama-7b_SFT-CoT_Refinement_length1024" > finetuing_CodeLlama-7b_SFT-CoT_Refinement_length1024.log
```

#### Refinement-Oriented Hierarchical Preference Optimization

***merge Fine-tuned model***

```
pip install -r dpo_requirements.txt
conda activate dpo
cd ./RIRE/DPO/
python merge_basemodel_CodeLlama-7B_SFTmodel.py
```

***DPO training***

```
python train.py \
    --model_name_or_path ./merged_CodeLlama-7b_SFT-CoT_Refinement_length1024/ \
    --ref_model_path ./merged_CodeLlama-7b_SFT-CoT_Refinement_length1024/ \
    --train_file ./train512_22837_7940_13232_preference_prompt.json \
    --use_peft True \
    --lora_rank 80 \
    --lora_alpha 160 \
    --lora_dropout 0.05 \
    --per_device_train_batch_size 16 \
    --gradient_accumulation_steps 2 \
    --learning_rate 2e-6 \
    --max_length 1024 \
    --max_steps 513 \
    --save_steps 171 \
    --output_dir CodeLlama-7b_dpo_7940_13232_length1024 > CodeLlama-7b_dpo_7940_13232_length1024.log
```

***Inference***

```
python inference_cot_batch_resume.py \
    --base_model ./merged_CodeLlama-7b_SFT-CoT_Refinement_length1024/ \
    --tuned_model ./CodeLlama-7b_dpo_7940_13232_length1024/checkpoint-513 \
    --data_file ../dataset/DiverseVul/test_512_newInstruction.json \
    --batch_size 5 \
    --csv_path ./CodeLlama-7b_dpo_7940_13232_length1024/CodeLlama-7b_dpo_DiverseVul.csv > ./CodeLlama-7b_dpo_7940_13232_length1024/CodeLlama-7b_dpo_DiverseVul.log
```

## Qwen2.5-Coder-7B

### SFT

***Fine-tuning Qwen2.5-Coder 7B***

```
pip install -r requirements.txt
conda activate RIRE_sft
cd ./RIRE/SFT/Qwen/
python finetuning_Qwen.py \
    --use_peft \
    --model_name /home/user/USER_NAME/.cache/modelscope/hub/Qwen/Qwen2___5-Coder-7B/ \
    --peft_method lora \
    --batch_size_training 16 \
    --gradient_accumulation_steps 1 \
    --lr 1e-5 \
    --lora_rank 16 \
    --lora_alpha 32 \
    --val_batch_size 16 \
    --weight_decay 0.01 \
    --context_length 512 \
    --quantization \
    --num_epochs 3 \
    --alpaca_dataset.train_data_path "../../dataset/MixVul/llm/train_512_22837.json" \
    --alpaca_dataset.valid_data_path "../../dataset/MixVul/llm/valid_512.json" \
    --output_dir "Qwen2.5-Coder-7B_SFT_length512" > finetuning_Qwen2.5-Coder-7B_SFT_length512.log
```

***Inference***

```
python inference_batch_Qwen.py \
    --base_model /home/user/USER_NAME/.cache/modelscope/hub/Qwen/Qwen2___5-Coder-7B/ \
    --tuned_model ./Qwen2.5-Coder-7B_SFT_length512/epoch-2 \
    --data_file ../../dataset/DiverseVul/test_512.json \
    --batch_size 10 \
    --csv_path ./Qwen2.5-Coder-7B_SFT_length512/Qwen2.5-Coder-7B_SFT_DiverseVul.csv > ./Qwen2.5-Coder-7B_SFT_length512/Qwen2.5-Coder-7B_SFT_DiverseVul.log
```

### SFT-CoT

```
python finetuning_Qwen.py \
    --use_peft \
    --model_name /home/user/USER_NAME/.cache/modelscope/hub/Qwen/Qwen2___5-Coder-7B/ \
    --peft_method lora \
    --batch_size_training 32 \
    --gradient_accumulation_steps 1 \
    --lr 1e-4 \
    --lora_rank 80 \
    --lora_alpha 160 \
    --val_batch_size 32 \
    --weight_decay 0.01 \
    --context_length 1024 \
    --quantization \
    --num_epochs 10 \
    --alpaca_dataset.train_data_path "../../dataset/MixVul/cot/train_512_22837_cot_noRefinement.json" \
    --alpaca_dataset.valid_data_path "../../dataset/MixVul/cot/valid_512_modified.json" \
    --output_dir "Qwen2.5-Coder-7B_SFT-CoT_length1024" > finetuing_Qwen2.5-Coder-7B_SFT-CoT_length1024.log
```

***Inference***

```
python inference_cot_batch_resume_Qwen.py \
   --base_model /home/user/USER_NAME/.cache/modelscope/hub/AI-ModelScope/CodeLlama-7b-hf/ \
   --tuned_model ./Qwen2.5-Coder-7B_SFT-CoT_length1024/epoch-5 \
   --data_file ../../dataset/DiverseVul/test_512_newInstruction.json \
  --batch_size 10 \
  --csv_path ./Qwen2.5-Coder-7B_SFT-CoT_length1024/Qwen2.5-Coder-7B_SFT-CoT_noRefinement_DiverseVul.csv > ./Qwen2.5-Coder-7B_SFT-CoT_length1024/Qwen2.5-Coder-7B_SFT-CoT_noRefinement_DiverseVul.log
```



### VulLLM

```
python finetuning_Qwen.py \
    --use_peft \
    --model_name /home/user/USER_NAME/.cache/modelscope/hub/Qwen/Qwen2___5-Coder-7B/ \
    --peft_method lora \
    --batch_size_training 32 \
    --gradient_accumulation_steps 1 \
    --lr 1e-4 \
    --lora_rank 16 \
    --lora_alpha 32 \
    --val_batch_size 32 \
    --weight_decay 0.01 \
    --context_length 512 \
    --quantization \
    --num_epochs 3 \
    --alpaca_dataset.train_data_path "../../dataset/MixVul/multi_task/multi_train_512_augmentation.json" \
    --alpaca_dataset.valid_data_path "../../dataset/MixVul/llm/valid_512.json" \
    --output_dir "Qwen2.5-Coder-7B_VulLLM_2clssification_length512" > finetuning_Qwen2.5-Coder-7B_VulLLM_2clssification_length512.log
```

***Inference***

```
python inference_batch_Qwen.py \
    --base_model /home/user/USER_NAME/.cache/modelscope/hub/Qwen/Qwen2___5-Coder-7B/ \
    --tuned_model ./Qwen2.5-Coder-7B_VulLLM_2clssification_length512/epoch-2 \
    --data_file ../../dataset/DiverseVul/test_512.json \
    --batch_size 10 \
    --csv_path ./Qwen2.5-Coder-7B_VulLLM_2clssification_length512/Qwen2.5-Coder-7B_VulLLM_DiverseVul.csv > ./Qwen2.5-Coder-7B_VulLLM_2clssification_length512/Qwen2.5-Coder-7B_VulLLM_DiverseVul.log
```

### RIRE

#### Reasoning-Enhanced Fine-Tuning

```
python finetuning_Qwen.py \
    --use_peft \
    --model_name /home/user/USER_NAME/.cache/modelscope/hub/Qwen/Qwen2___5-Coder-7B/ \
    --peft_method lora \
    --batch_size_training 32 \
    --gradient_accumulation_steps 1 \
    --lr 1e-4 \
    --lora_rank 80 \
    --lora_alpha 160 \
    --val_batch_size 32 \
    --weight_decay 0.01 \
    --context_length 1024 \
    --quantization \
    --num_epochs 10 \
    --alpaca_dataset.train_data_path "../dataset/MixVul/cot/train_512_22837_cot_Refinement.json" \
    --alpaca_dataset.valid_data_path "../dataset/MixVul/cot/valid_512_modifiedv4.json" \
    --output_dir "Qwen2.5-Coder-7B_SFT-CoT_Refinement_length1024" > finetuing_Qwen2.5-Coder-7B_SFT-CoT_Refinement_length1024.log
```

#### Refinement-Oriented Hierarchical Preference Optimization

```
conda activate dpo
cd ./RIRE/DPO/
python train.py \
    --model_name_or_path ./merged_Qwen2.5-Coder-7B_SFT-CoT_Refinement_length1024/ \
    --ref_model_path ./merged_Qwen2.5-Coder-7B_SFT-CoT_Refinement_length1024/ \
    --train_file ./train512_22837_7940_13232_preference_prompt_Qwen.json \
    --use_peft True \
    --lora_rank 80 \
    --lora_alpha 160 \
    --lora_dropout 0.05 \
    --per_device_train_batch_size 8 \
    --gradient_accumulation_steps 4 \
    --learning_rate 2e-6 \
    --max_length 1024 \
    --max_steps 10260 \
    --save_steps 513 \
    --output_dir Qwen2.5Coder-7B_dpo_7940_13232_length1024 > Qwen2.5Coder-7B_dpo_7940_13232_length1024.log
```

***Inference***

```
python inference_cot_batch_resume_Qwen.py \
    --base_model ./merged_Qwen2.5-Coder-7B_SFT-CoT_Refinement_length1024/ \
    --tuned_model ./Qwen2.5Coder-7B_dpo_7940_13232_length1024/checkpoint-573 \
    --data_file ../../dataset/DiverseVul/test_512_newInstruction.json \
    --batch_size 5 \
    --csv_path ./Qwen2.5Coder-7B_dpo_7940_13232_length1024/Qwen2.5-Coder-7B_dpo_DiverseVul.csv > ./Qwen2.5Coder-7B_dpo_7940_13232_length1024/Qwen2.5-Coder-7B_dpo_DiverseVul.log
```

# Ablation Study

## ① 

We use the same model (**CodeLlama-7b SFT**) as described in the main experiment section to analyze the impact of individual components.

## ② 

We use the same model (**CodeLlama-7b SFT-CoT**) as described in the main experiment section to analyze the impact of individual components.

## ③ 

***Fine-tuning CodeLlama-7b***

```
python finetuning.py \
    --use_peft \
    --model_name /home/user/USER_NAME/.cache/modelscope/hub/AI-ModelScope/CodeLlama-7b-hf/ \
    --peft_method lora \
    --batch_size_training 32 \
    --gradient_accumulation_steps 1 \
    --lr 1e-4 \
    --lora_rank 80 \
    --lora_alpha 160 \
    --val_batch_size 32 \
    --weight_decay 0.01 \
    --context_length 1024 \
    --quantization \
    --num_epochs 10 \
    --alpaca_dataset.train_data_path "../../dataset/MixVul/cot/train_512_22837_cot_Refinement.json" \
    --alpaca_dataset.valid_data_path "../../dataset/MixVul/cot/valid_512_modified.json" \
    --output_dir "CodeLlama-7b_SFT-CoT_Refinement_length1024" > finetuing_CodeLlama-7b_SFT-CoT_Refinement_length1024.log
```

***Inference***

```
python inference_cot_batch_resume.py \
    --base_model /home/user/USER_NAME/.cache/modelscope/CodeLlama-7b-hf/ \
    --tuned_model ./CodeLlama-7b_SFT-CoT_Refinement_length1024/epoch-5 \
    --data_file ../dataset/DiverseVul/test_512_newInstruction.json \
    --batch_size 8 \
    --csv_path ./CodeLlama-7b_SFT-CoT_Refinement_length1024/CodeLlama-7b_SFT-CoT_Refinement_DiverseVul.csv > ./CodeLlama-7b_SFT-CoT_Refinement_length1024/CodeLlama-7b_SFT-CoT_Refinement_DiverseVul.log
```

## ④ 

We use the model obtained from **RIRE Reasoning-Enhanced Fine-Tuning** on **CodeLlama-7b** as the **reference model for DPO**.

***Fine-tuning CodeLlama-7b***

```
python train.py \
    --model_name_or_path ./merged_CodeLlama-7b_SFT-CoT_Refinement_length1024/ \
    --ref_model_path ./merged_CodeLlama-7b_SFT-CoT_Refinement_length1024/ \
    --train_file ./train512_22837_7940_13232_preference_NoRefinement_prompt.json \
    --use_peft True \
    --lora_rank 80 \
    --lora_alpha 160 \
    --lora_dropout 0.05 \
    --per_device_train_batch_size 16 \
    --gradient_accumulation_steps 2 \
    --learning_rate 2e-6 \
    --max_length 1024 \
    --max_steps 573 \
    --save_steps 171 \
    --output_dir CodeLlama-7b_dpo_NoRefine_length1024 > CodeLlama-7b_dpo_NoRefine_length1024.log
```

***Inference***

```
python inference_cot_batch_resume.py \
    --base_model ./merged_CodeLlama-7b_SFT-CoT_Refinement_length1024/ \
    --tuned_model ./CodeLlama-7b_dpo_NoRefine_length1024/checkpoint-573 \
    --data_file ../dataset/DiverseVul/test_512_newInstruction.json \
    --batch_size 5 \
    --csv_path ./CodeLlama-7b_dpo_NoRefine_length1024/CodeLlama-7b_dpo_NoRefine_DiverseVul.csv > ./CodeLlama-7b_dpo_NoRefine_length1024/CodeLlama-7b_dpo_NoRefine_DiverseVul.log
```

## ⑤ 

We use the same model (**CodeLlama-7b RIRE**) as described in the main experiment section to analyze the impact of individual components.
