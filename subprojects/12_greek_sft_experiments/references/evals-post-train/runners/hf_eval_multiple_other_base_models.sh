#!/bin/bash

# Define MODEL:CKPT_PATH pairs using an associative array
declare -A MODEL_CHECKPOINTS=(
    # EuroLLM models
    # ["EuroLLM-1.7B"]="utter-project/EuroLLM-1.7B"
    # ["EuroLLM-9B"]="utter-project/EuroLLM-9B"
    # ["EuroLLM-22B-Preview"]="utter-project/EuroLLM-22B-Preview"
    
    # # # # OLMo models (base)
    # ["OLMo-2-1124-7B"]="allenai/OLMo-2-1124-7B"
    # ["OLMo-2-1124-13B"]="allenai/OLMo-2-1124-13B"
    # ["OLMo-2-0325-32B"]="allenai/OLMo-2-0325-32B"
    
    # # # # Qwen 2.5 models
    # ["Qwen2.5-7B"]="Qwen/Qwen2.5-7B"

    # # LLama
    ["Llama-3.1-8B"]="meta-llama/Llama-3.1-8B"

    # # marin
    # ["marin-8b-base"]="marin-community/marin-8b-base"


    # # # Other open models
    # ["ALIA-40b"]="BSC-LT/ALIA-40b"
    # ["jais-13b"]="inceptionai/jais-13b"
    # ["jais-adapted-7b"]="inceptionai/jais-adapted-7b"
    # ["jais-adapted-13b"]="inceptionai/jais-adapted-13b"
    # ["jais-adapted-70b"]="inceptionai/jais-adapted-70b"
    # ["sabia-7b"]="maritaca-ai/sabia-7b"
    # ["Viking-7B"]="LumiOpen/Viking-7B"
    # ["Viking-13B"]="LumiOpen/Viking-13B"
    # ["Viking-33B"]="LumiOpen/Viking-33B"
    # ["Poro-34B"]="LumiOpen/Poro-34B"

)

export WANDB_ENTITY=${WANDB_ENTITY:-apertus}
export WANDB_PROJECT=${WANDB_PROJECT:-swissai-evals}

# Base model configurations
export APPLY_CHAT_TEMPLATE=${APPLY_CHAT_TEMPLATE:-false}

# Call the common runner script
source runners/hf_base_runner.sh "Base models"
