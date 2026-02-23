#!/bin/bash

# 1. Define the array of models
MODELS=(
    "deepseek-coder-v2:236b"
    "qwen3-coder:480b"
    "codellama:70b"
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
    python3 experiments/experiment1/main.py --model "$MODEL"

    # Experiment 2 - REGEX_AIDED
    echo "Running Experiment 2..."
    python3 experiments/experiment2/main.py --model "$MODEL"

    # Experiment 3
    echo "Running Experiment 3..."
    python3 experiments/experiment3/main.py --model "$MODEL"

    echo "Completed all experiments for $MODEL"
    echo "-----------------------------------------------------------"

    ollama rm "$MODEL"
done

echo "ALL MODELS PROCESSED."
