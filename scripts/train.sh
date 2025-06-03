   #!/bin/bash

python3 src/train.py \
  --stage sft \
  --model_name_or_path microsoft/Phi-4-mini-instruct \
  --do_train \
  --dataset magic1 \
  --template default \
  --finetuning_type lora \
  --lora_target all \
  --lora_r 128 \
  --lora_alpha 256 \
  --lora_dropout 0.01 \
  --output_dir ./lora-phi4-magic1 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 16 \
  --lr_scheduler_type constant \
  --learning_rate 5e-4 \
  --num_train_epochs 20 \
  --warmup_steps 10 \
  --logging_steps 5 \
  --save_steps 20 \
  --cutoff_len 2048 \
  --fp16 \
  --gradient_checkpointing \
  --dataloader_pin_memory False \
  --plot_loss \
  --save_only_model

