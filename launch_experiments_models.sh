#!/bin/bash

# 1. Define the array of models
MODELS=(
  "qwen2.5-coder:7b"
  "qwen2.5-coder:14b"
  "qwen2.5-coder:32b"
  "qwen3-coder:30b"
  "codegemma:7b"
  "deepseek-coder-v2:16b"
  "deepseek-coder:33b"
  "yi-coder:9b"
)

# 2. Loop through each model in the array
for MODEL in "${MODELS[@]}"
do
    echo "Pulling model $MODEL"

    ollama pull "$MODEL"

    echo "==========================================================="
    echo "STARTING EXPERIMENTS FOR MODEL: $MODEL"
    echo "==========================================================="

    echo "Running Experiment 1..."
    python3 experiments/experiment_prompt/main.py --model "$MODEL" --experiment 1

    echo "Running Experiment 2..."
    python3 experiments/experiment_prompt/main.py --model "$MODEL" --experiment 2

    echo "Running Experiment 3..."
    python3 experiments/experiment_tgts/main.py --model "$MODEL"

    echo "Completed all experiments for $MODEL"
    echo "-----------------------------------------------------------"

    ollama rm "$MODEL"
done

echo "ALL MODELS PROCESSED."