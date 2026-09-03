#!/bin/bash

# Define MODEL:CKPT_PATH pairs using an associative array
declare -A MODEL_CHECKPOINTS=(
    # RLVR models
 

    # # # from Slack Canvas
    # ["Apertus8B-tokens15T-it2627139-apertus-sft-mixture-7-ln-v2-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens15T-it2627139-apertus-sft-mixture-7-ln-v2-ademamix/checkpoints/2087d36b7ab2cef8/checkpoint-8926"
    # ["Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-7-ln-v2-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-7-ln-v2-ademamix/checkpoints/e59e65229aa13246/checkpoint-8925"
    # # ["Apertus8B-tokens10.2T-it2059810-newcooldown-apertus-sft-mixture-7-ln-v2-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens10.2T-it2059810-newcooldown-apertus-sft-mixture-7-ln-v2-ademamix/checkpoints/7fea1f8c44336360/checkpoint-8925"
    # # ["Apertus8B-tokens10.2T-it2059810-newcooldown-apertus-sft-mixture-7-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens10.2T-it2059810-newcooldown-apertus-sft-mixture-7-ademamix-tulu/checkpoints/d15daeeaa7199732/checkpoint-8925"
    # # ["Apertus-8B-10.2T-newcooldown-mixture1-fast-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens10.2T-it2059810-newcooldown-apertus-sft-mixture-1-ademamix/checkpoints/ee969b526b1995f7/checkpoint-1622"
    # # ["Apertus-8B-10.2T-newcooldown-mixture2-fast-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens10.2T-it2059810-newcooldown-apertus-sft-mixture-2-ademamix/checkpoints/53e2ead7db07314d/checkpoint-3914"
    # # ["Apertus-8B-10.2T-newcooldown-mixture4-fast-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens10.2T-it2059810-newcooldown-apertus-sft-mixture-4-ademamix/checkpoints/1ce7109f7dde7ed2/checkpoint-4792"
    # # ["Apertus8B-tokens10.2T-it2059810-newcooldown-apertus-sft-mixture-4-ln-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens10.2T-it2059810-newcooldown-apertus-sft-mixture-4-ln-ademamix/checkpoints/0584e1255fd1c050/checkpoint-4792"
    # # ["Apertus8B-tokens10.2T-it2059810-newcooldown-apertus-sft-mixture-5-ln-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens10.2T-it2059810-newcooldown-apertus-sft-mixture-5-ln-ademamix/checkpoints/25be975e6fb49231/checkpoint-3452"
    # # ["Apertus8B-tokens10.2T-it2059810-newcooldown-apertus-sft-mixture-6-ln-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens10.2T-it2059810-newcooldown-apertus-sft-mixture-6-ln-ademamix/checkpoints/f3c01f37d68b4655/checkpoint-3934"
    # # ["Apertus8B-tokens10.2T-it2059810-newcooldown-tulu3-sft-mixture-licenseFiltered-ln"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens10.2T-it2059810-newcooldown-tulu3-sft-mixture-licenseFiltered-ln/checkpoints/a33f200010b779b8/checkpoint-1590"
    # # ["Apertus8B-tokens10.2T-it2059810-newcooldown-tulu3-sft-mixture-ln"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens10.2T-it2059810-newcooldown-tulu3-sft-mixture-ln/checkpoints/3d1fadf422dd2b23/checkpoint-1781"
    # # ["Apertus8B-tokens10.2T-it2059810-newcooldown-tulu3-sft-mixture-original-ln"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens10.2T-it2059810-newcooldown-tulu3-sft-mixture-original-ln/checkpoints/219fbc9f7c06528a/checkpoint-1826"



    # ["Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8-ln-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8-ln-ademamix/checkpoints/c44611dc45683423/checkpoint-7797"
    # ["Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8b-ln-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8b-ln-ademamix/checkpoints/8b5faba76be27c18/checkpoint-7798"
    # ["Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8b-ln-plw0.5-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/plw-ablations/Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8b-ln-plw0.5-ademamix/checkpoints/452fb3f74d71b8f2/checkpoint-7798"
    # ["Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8c-ln-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8c-ln-ademamix/checkpoints/f09edf4e61a075e2/checkpoint-7798"
    # ["Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8d-ln-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8d-ln-ademamix/checkpoints/e0d5e69aed15046b/checkpoint-7799"
    # ["Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8e-ln-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8e-ln-ademamix/checkpoints/2b3cc4db8d388204/checkpoint-7681"
    # ["Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8d-ln-plw0.05-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/plw-ablations/Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8d-ln-plw0.05-ademamix/checkpoints/38584b9a7425f641/checkpoint-7799"
    # ["Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8e-ln-plw0.05-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/plw-ablations/Apertus8B-tokens15T-longcontext64k-apertus-sft-mixture-8e-ln-plw0.05-ademamix/checkpoints/95b00381ce1ad7d0/checkpoint-7681"
    

    # # # # 70B slack canvas
    # ["Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-7-ln-v2-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-7-ln-v2-ademamix/checkpoints/d0012600a8854237/checkpoint-4462"
    # # ["Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-6-ln-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-6-ln-ademamix/checkpoints/221d3f43ba5bd31d/checkpoint-3934"
    # # ["Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-5-ln-ademamix"]=["/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-5-ln-ademamix/checkpoints/6772117863c6be50/checkpoint-3452"]
    # # ["Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-4-ademamix"]=["/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-4-ademamix/checkpoints/f5389cd828c653a4/checkpoint-4792"]
    # # ["Apertus-70B-15T-mixture1-fast-ademamix-fixed"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/apertus-sft-mixture-1-fast-ademamix/Apertus70B-tokens15T-it1155828-apertus-sft-mixture-1-bs512-lr2e-06-maxgnorm1-epochs1-ademamix/checkpoints/4fc579918b550aac/checkpoint-1622"
    # #["Apertus-70B-15T-mixture4-fast-ademamix-fixed"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/fix-ademamix-fast-noquote/Apertus70B-tokens15T-it1155828-apertus-sft-mixture-4-bs512-lr2e-06-maxgnorm1-epochs1-ademamix/checkpoints/0bc386f8352f3273/checkpoint-4792"
    
    # ["Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-8-ln-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-8-ln-ademamix/checkpoints/2a75ff8ae2766daa/checkpoint-3898"
    # ["Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-8b-ln-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-8b-ln-ademamix/checkpoints/269b44fdd21ec150/checkpoint-3899"
    # ["Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-8d-ln-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-8d-ln-ademamix/checkpoints/1f20ee760c1e2161/checkpoint-3899"
    # ["Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-8e-ln-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/final-run/Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-8e-ln-ademamix/checkpoints/6b9bf7de3db26256/checkpoint-3840"
    # ["Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-8e-ln-plw0.05-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/plw-ablations/Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-8e-ln-plw0.05-ademamix/checkpoints/77cda2547d7c1ec5/checkpoint-3840"

    # # Bettina 
    # ["Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-8b-honesty"]="/iopsstor/scratch/cscs/bmessmer/projects/swiss-alignment/artifacts/private/outputs/train_sft/sft4honesty/Apertus70B-tokens15T-longcontext64k-apertus-sft-mixture-8b-ln-ademamix-apertus_70b_3899_0.2_0.75_majority_correct_sft-bs1024-lr2e-06-epochs1-adam-apertus/checkpoints/9bbf90fc740aff86/checkpoint-7"

    # # # # Alignment models
    # # # # 8B sft mixture 7 only-reward-model QRPO AdamW checkpoint-719
    # #["Apertus-8B-sft-mixture-7-qrpo"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_preference/apertus-first-sweep/swissai-olmo2-32b-preference-apertus-8b-sft-10T-mixture-7-7fea1f8c44336360-maxlen4096-Nref30-logprobs-skywork-llama3-8b-Npairs1-qrpo-adamw_torch-r5e-07-beta5.0/checkpoints/eda1dcdb866189ef/checkpoint-719"
    # ["Apertus-8B-sft-mixture-7-qrpo"]="/iopsstor/scratch/cscs/flubeck/models/apertus-7b-qrpo"

    
    # # old
    # ["Apertus-70B-15T-swissai-tulu-3-ademamix"]="/iopsstor/scratch/cscs/smoalla/projects/swiss-alignment/artifacts/shared/outputs/train_sft/apertus-70b-sweep/token-count/Apertus70B-tokens15T-it1155828-ademamix-swissai-tulu-3-sft-0225/checkpoints/c9b2910640c220b1/checkpoint-13446"

    # final aligned
    # ["Apertus-70B-aligned"]="/capstor/store/cscs/swissai/infra01/swiss-alignment/checkpoints/Apertus-70B-aligned"
    # ["Apertus-70B-aligned-branded"]="/capstor/store/cscs/swissai/infra01/swiss-alignment/checkpoints/Apertus-70B-aligned-branded"
    # ["Apertus-8B-aligned"]="/capstor/store/cscs/swissai/infra01/swiss-alignment/checkpoints/Apertus-8B-aligned"
    # ["Apertus-8B-aligned-branded"]="/capstor/store/cscs/swissai/infra01/swiss-alignment/checkpoints/Apertus-8B-aligned-branded"

    # aligned
    ["Apertus-8B-sft-mixture-8e-aligned"]="/capstor/store/cscs/swissai/infra01/swiss-alignment/checkpoints/Apertus-8B-sft-mixture-8e-aligned"
    ["Apertus-70B-sft-mixture-8e-aligned"]="/capstor/store/cscs/swissai/infra01/swiss-alignment/checkpoints/Apertus-70B-sft-mixture-8e-aligned"

    # ["Apertus-8B-sft-mixture-8e-pwl-aligned"]="/capstor/store/cscs/swissai/infra01/swiss-alignment/checkpoints/Apertus-8B-sft-mixture-8e-pwl-aligned"
    # ["Apertus-70B-sft-mixture-8e-pwl-aligned"]="/capstor/store/cscs/swissai/infra01/swiss-alignment/checkpoints/Apertus-70B-sft-mixture-8e-pwl-aligned"
)

export WANDB_ENTITY=${WANDB_ENTITY:-apertus}
export WANDB_PROJECT=${WANDB_PROJECT:-swissai-evals}

# SFT model configurations
export APPLY_CHAT_TEMPLATE=${APPLY_CHAT_TEMPLATE:-true}

# Call the common runner script
source runners/hf_base_runner.sh "Apertus SFT models"


