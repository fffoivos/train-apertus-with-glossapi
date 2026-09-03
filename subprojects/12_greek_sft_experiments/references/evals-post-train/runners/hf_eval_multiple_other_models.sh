#!/bin/bash

# Define MODEL:CKPT_PATH pairs using an associative array
declare -A MODEL_CHECKPOINTS=(
    # # EuroLLM models
    # ["EuroLLM-1.7B-Instruct"]="utter-project/EuroLLM-1.7B-Instruct"
    # ["EuroLLM-9B-Instruct"]="utter-project/EuroLLM-9B-Instruct"
    # ["EuroLLM-22B-Instruct-Preview"]="utter-project/EuroLLM-22B-Instruct-Preview"
    
    # # # Gemma models
    # ["gemma-3-4b-it"]="google/gemma-3-4b-it"
    # ["gemma-3-12b-it"]="google/gemma-3-12b-it"
    # ["gemma-3-27b-it"]="google/gemma-3-27b-it"
    
    # # K2 models
    # ["K2-Chat"]="K2-Chat"

    # # Llama models
    ["Llama-3.1-8B-Instruct"]="meta-llama/Llama-3.1-8B-Instruct"
    # ["Llama-3.3-70B-Instruct"]="meta-llama/Llama-3.3-70B-Instruct"
    
    # # # # # # OLMo models (fine-tuned variants)
    # ["OLMo-2-1124-7B-SFT"]="allenai/OLMo-2-1124-7B-SFT"
    # ["OLMo-2-1124-7B-DPO"]="allenai/OLMo-2-1124-7B-DPO"
    # ["OLMo-2-1124-7B-Instruct"]="allenai/OLMo-2-1124-7B-Instruct"
    
    # ["OLMo-2-0325-32B-SFT"]="allenai/OLMo-2-0325-32B-SFT"
    # ["OLMo-2-0325-32B-DPO"]="allenai/OLMo-2-0325-32B-DPO"
    # ["OLMo-2-0325-32B-Instruct"]="allenai/OLMo-2-0325-32B-Instruct"

    # ["OLMo-2-1124-13B-SFT"]="allenai/OLMo-2-1124-13B-SFT"
    # ["OLMo-2-1124-13B-DPO"]="allenai/OLMo-2-1124-13B-DPO"
    # ["OLMo-2-1124-13B-Instruct"]="allenai/OLMo-2-1124-13B-Instruct"
    
    # # # # Qwen 2.5 models
    # # ["Qwen2.5-7B"]="Qwen/Qwen2.5-7B"
    # # ["Qwen2.5-7B-Instruct"]="Qwen/Qwen2.5-7B-Instruct"
    # # ["Qwen2.5-14B-Instruct"]="Qwen/Qwen2.5-14B-Instruct"
    # # ["Qwen2.5-32B-Instruct"]="Qwen/Qwen2.5-32B-Instruct"
    # # ["Qwen2.5-72B-Instruct"]="Qwen/Qwen2.5-72B-Instruct"
    
    # # # Qwen 3 models
    # # ["Qwen3-1.7B"]="Qwen/Qwen3-1.7B"
    # # ["Qwen3-4B"]="Qwen/Qwen3-4B"
    # # ["Qwen3-8B"]="Qwen/Qwen3-8B"
    # # ["Qwen3-14B"]="Qwen/Qwen3-14B"
    # # ["Qwen3-32B"]="Qwen/Qwen3-32B"

    # # # SmolLM models
    # # ["SmolLM3-3B"]="HuggingFaceTB/SmolLM3-3B"

    # # # # Other open models
    # ["salamandra-7b-instruct"]="BSC-LT/salamandra-7b-instruct"
    # # # ["Minerva-7B-instruct-v1.0"]="sapienzanlp/Minerva-7B-instruct-v1.0"
    # # ["ALLaM-7B-Instruct-preview"]="ALLaM-AI/ALLaM-7B-Instruct-preview"
    # ["jais-13b-chat"]="inceptionai/jais-13b-chat"
    # ["jais-adapted-7b-chat"]="inceptionai/jais-adapted-7b-chat"
    # ["jais-adapted-13b-chat"]="inceptionai/jais-adapted-13b-chat"
    # # ["jais-adapted-70b-chat"]="inceptionai/jais-adapted-70b-chat"
    # ["Poro-34B-chat"]="LumiOpen/Poro-34B-chat"
    # # ["Teuken-7B-instruct-v0.6"]="openGPT-X/Teuken-7B-instruct-v0.6"
    

    # # # marin
    # ["marin-8b-instruct"]="marin-community/marin-8b-instruct"
)

export WANDB_ENTITY=${WANDB_ENTITY:-apertus}
export WANDB_PROJECT=${WANDB_PROJECT:-swissai-evals}

# SFT model configurations
export APPLY_CHAT_TEMPLATE=${APPLY_CHAT_TEMPLATE:-true}

# Call the common runner script
source runners/hf_base_runner.sh "SFT models"
