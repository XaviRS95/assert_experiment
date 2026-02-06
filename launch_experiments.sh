#!/bin/bash

# 1. Define the array of models
MODELS=(
    "deepseek-coder-v2:16b"
    "deepseek-coder-v2:236b"
    "qwen3-coder:30b"
    "qwen3-coder:480b"
    "qwen2.5-coder:32b"
    "codellama:70b"
    "codegemma:7b"
    "starcoder2:15b"
)


# 2. Loop through each model in the array
for MODEL in "${MODELS[@]}"
do
    echo "Pulling model $MODEL"

    ollama pull "$MODEL"

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

    ollama rm "$MODEL"
done

echo "ALL MODELS PROCESSED."
