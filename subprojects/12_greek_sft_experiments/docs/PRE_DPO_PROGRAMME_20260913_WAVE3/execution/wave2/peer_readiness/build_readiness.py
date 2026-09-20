#!/usr/bin/env python3
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "bundle"

def digest(path):
    h=hashlib.sha256(); b=path.read_bytes(); h.update(b); return len(b),h.hexdigest()

files=sorted(p for p in BUNDLE.rglob("*") if p.is_file() and p.name != "peer_eval_science_manifest.json")
payload=hashlib.sha256()
for p in files:
    n,h=digest(p); payload.update(str(p.relative_to(BUNDLE)).encode()+b"\0"+str(n).encode()+b"\0"+h.encode()+b"\n")
payload_sha=payload.hexdigest()
remote_root=f"/iopsstor/scratch/cscs/fffoivos/sft_round1/wave2_peer_eval/bundle_{payload_sha[:16]}"
inputs=[]
for p in files:
    n,h=digest(p)
    inputs.append({"path":f"{remote_root}/{p.relative_to(BUNDLE)}","bytes":n,"sha256":h})
model_root="/iopsstor/scratch/cscs/fffoivos/sft_round1/hf_home/hub/models--ilsp--Llama-Krikri-8B-Instruct-v1.5/snapshots/326e2c0ea90d771c19fcf06225fe87dc922b51b2"
weight_rows=[
 ("model-00001-of-00004.safetensors",4913767264,"ca278ed6f262c1993c3bc9cee433a93fff6ffebb217cb767cc9a5ec5cc9e5464"),
 ("model-00002-of-00004.safetensors",4915916160,"cf1c87f848dec168d63b5d0742a3d79b0dbc521b3de5c68e8c70f23d082364e6"),
 ("model-00003-of-00004.safetensors",4999819336,"7728f1f441f5a51b5292b4b790eb65cce0d3964e6734a5d244bdf2fbc33b9cc8"),
 ("model-00004-of-00004.safetensors",1574986528,"e1576939e0f64e6d1d029d52f8de042a9045e4ac9e36054c4a6b197beb18631d"),
]
control_rows=[
 ("config.json",869,"22ce76d0064ea51c20458ff58326c5e42433f2f3a87ce9eb47b27acd432c37d0"),
 ("generation_config.json",184,"fb6f007ef838d8fca7d11f2f97a8fdfe97be7e08210f33eb1348e833abf2f642"),
 ("tokenizer.json",19508014,"1b12728a215cde26d96f3add66a7a10f0e47147afbf2e677cc0a70ba49228ada"),
 ("tokenizer_config.json",50639,"1b56d3abd51a1e1609e04027d709852a0b14d059471d6cccc30ba1d1dcc7acab"),
 ("special_tokens_map.json",752,"e8e2824903f20c7a7e8b676181b9ae8e9631653823210ef914e5e0db990a9cfc"),
 ("chat_template.jinja",4614,"e10ca381b1ccc5cf9db52e371f3b6651576caee0a630b452e2816b2d404d4b65"),
 ("model.safetensors.index.json",23986,"12329d543e4402298270d49949d388d32ea8cb3e1fe16cf462aeeadbe31b151a"),
]
manifest={
 "schema_version":"krikri_v15_peer_eval_science_v1",
 "status":"not_launched_readiness_pending",
 "payload_sha256":payload_sha,
 "deployment_root":remote_root,
 "model":{
  "repo_id":"ilsp/Llama-Krikri-8B-Instruct-v1.5",
  "revision":"326e2c0ea90d771c19fcf06225fe87dc922b51b2",
  "snapshot_path":model_root,
  "served_name":"krikri-v1.5",
  "license":"llama3.1",
  "chat_template_sha256":"e10ca381b1ccc5cf9db52e371f3b6651576caee0a630b452e2816b2d404d4b65",
  "tokenizer_json_sha256":"1b12728a215cde26d96f3add66a7a10f0e47147afbf2e677cc0a70ba49228ada",
  "tokenizer_config_sha256":"1b56d3abd51a1e1609e04027d709852a0b14d059471d6cccc30ba1d1dcc7acab",
  "model_index_sha256":"12329d543e4402298270d49949d388d32ea8cb3e1fe16cf462aeeadbe31b151a",
  "files":[{"path":f"{model_root}/{name}","bytes":n,"sha256":h} for name,n,h in weight_rows],
  "control_files":[{"path":f"{model_root}/{name}","bytes":n,"sha256":h} for name,n,h in control_rows],
 },
 "runtime":{
  "uenv":"pytorch/v2.9.1:v2","uenv_view":"default","python":"/user-environment/env/default/bin/python3",
  "vllm_executable":"/iopsstor/scratch/cscs/fffoivos/venvs/vllm/bin/vllm","vllm_version":"0.28.0",
  "lm_eval_pythonpath":"/iopsstor/scratch/cscs/fffoivos/python_envs/lm_eval",
  "lm_eval_version":"0.4.11","transformers_version":"4.57.0","datasets_version":"4.0.0","accelerate_version":"1.13.0","torch_version":"2.9.1",
  "hf_home":"/iopsstor/scratch/cscs/fffoivos/sft_round1/hf_home","offline":True,
 },
 "generation":{"system_prompt":None,"apply_native_chat_template":True,"temperature":0,"top_p":1,"max_tokens":{"math500":2048,"other_fixed":1024},"max_model_len":4096},
 "tasks":{
  "fixed":{"math500_el":500,"math500_en":500,"ifbench_el":300,"ifbench_en":300,"xstest_el":450,"xstest_en":450,"multichallenge_el":213,"multichallenge_en":213},
  "fixed_source_counts":{"multichallenge_el":262,"multichallenge_en":262},
  "context_exclusions":{"file":"multichallenge_context_exclusions.json","union_ids":49,"rule":"retain only IDs whose native-template input plus requested output fits 4096 in both languages; apply identical IDs to original and v1.5"},
  "ilsp":{"ifeval_greek":541,"mgsm_greek":250},"total_generations":3717,
  "judging_deferred":["xstest_el","xstest_en","multichallenge_el","multichallenge_en"],
  "not_in_batch":["mt_bench_greek","mt_bench_english","belebele_ell_Grek"],
 },
 "allocation":{"partition":"debug","account":"a0140","nodes":1,"gpus_per_node":4,"cpus_per_task":288,"memory":"640G","time":"01:25:00","node_hours_requested":1.4167,"measurement_envelope_node_hours":4.0,"placement":{"gpu0":"vLLM fixed suite","gpu1":"lm-eval IFEval+MGSM","gpu2":"reserve","gpu3":"reserve"}},
 "budget":{"cap_chf":230.0,"rate_chf_per_node_hour":2.69,"current_node_hours":60.602,"current_chf":163.02,"prior_conservative_chf":164.54,"reconciliation_chf":-1.52,"remaining_chf":66.98,"remaining_node_hours":24.9007,"one_attempt_projected_chf":3.81,"four_node_hour_envelope_chf":10.76,"ledger_source":"experiment execution_state.json; immutable deployed copy is included in inputs"},
 "canonical":{"repo":"fffoivos/apertus-cscs-efficiency","origin_main":"22c4561050cba36f34b8480e1373788e139aaf3c","preflight_sha256":"bc24ae97314f7f48893aafc2bd6c5aa451b5f42c07fcef2270f2f4d1f54f6ee9","standalone_external_checkpoint_supported":False},
 "inputs":inputs,
 "output_root":"/iopsstor/scratch/cscs/fffoivos/sft_round1/evals/wave2_krikri_v15",
}
(BUNDLE/"peer_eval_science_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
(ROOT/"deployment_identity.json").write_text(json.dumps({"payload_sha256":payload_sha,"remote_root":remote_root,"file_count":len(files)},indent=2)+"\n")
print(remote_root)
