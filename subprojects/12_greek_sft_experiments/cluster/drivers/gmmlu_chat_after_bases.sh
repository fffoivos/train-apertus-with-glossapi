set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments
echo "[$(date '+%m-%d %H:%M')] queued: instruct-adapted GreekMMLU (chat_instructed) for krikri, krikri15, armB, G3F2P1 after the base-comparison run ends"
while pgrep -f "greekmmlu_official.sh G1F0P0_02" >/dev/null; do sleep 60; done
echo "[$(date '+%m-%d %H:%M')] LAUNCH: GreekMMLU chat_instructed, 4 models, one normal workbench <= 2 h (<= 2 nh)"
PROTOCOLS=chat_instructed SUFFIX=_chat bash cluster/greekmmlu_official.sh "krikri=/iopsstor/scratch/cscs/fffoivos/sft_round1/hf_home/hub/models--ilsp--Llama-Krikri-8B-Instruct/snapshots/06d813157ba5f19deb17d70c3862ce64035431ec" "krikri15=/iopsstor/scratch/cscs/fffoivos/sft_round1/hf_home/hub/models--ilsp--Llama-Krikri-8B-Instruct-v1.5/snapshots/326e2c0ea90d771c19fcf06225fe87dc922b51b2" "armB=/iopsstor/scratch/cscs/fffoivos/sft_round1/eval_copies/R2_idB_ep2" "G3F2P1=/iopsstor/scratch/cscs/fffoivos/sft_round1/eval_copies/R3_single_ep1"
echo "[$(date '+%m-%d %H:%M')] chat run wrapper exit $?"
