#!/bin/bash

# 1. Define the array of models
MODELS=(
    "qwen3-coder-next:q8_0"
    "codellama:70b"
    "codegemma:7b"
    "starcoder2:15b"
)

for MODEL in "${MODELS[@]}"
do
  ollama pull "$MODEL"

# EXPERIMENTS FROM DEEPSEEK THAT I STILL NEED TO RUN
echo "Running Experiment 1..."
python3 experiment1_w_args.py --model deepseek-coder-v2:236b

# Experiment 2 - REGEX_AIDED
echo "Running Experiment 2 (REGEX_AIDED)..."
python3 experiment2_w_args.py --model deepseek-coder-v2:236b --mode REGEX_AIDED

# Experiment 2 - FULL_AI
echo "Running Experiment 2 (FULL_AI)..."
python3 experiment2_w_args.py --model deepseek-coder-v2:236b --mode FULL_AI


# 2. Loop through each model in the array
for MODEL in "${MODELS[@]}"
do
    echo "==========================================================="
    echo "STARTING EXPERIMENTS FOR MODEL: $MODEL"
    echo "==========================================================="

    # Experiment 1
    echo "Running Experiment 1..."
    python3 experiment1_w_args.py --model "$MODEL"

    # Experiment 2 - REGEX_AIDED
    echo "Running Experiment 2 (REGEX_AIDED)..."
    python3 experiment2_w_args.py --model "$MODEL" --mode REGEX_AIDED

    # Experiment 2 - FULL_AI
    echo "Running Experiment 2 (FULL_AI)..."
    python3 experiment2_w_args.py --model "$MODEL" --mode FULL_AI

    # Experiment 3
    echo "Running Experiment 3..."
    python3 experiment3_w_args.py --model "$MODEL"

    echo "Completed all experiments for $MODEL"
    echo "-----------------------------------------------------------"
done

echo "ALL MODELS PROCESSED."