from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import types
import unittest
from unittest import mock


HERE = pathlib.Path(__file__).resolve().parent
RUNNER = HERE / "pod" / "run_stage.sh"


class PodRunnerTests(unittest.TestCase):
    def _write_executable(self, path: pathlib.Path, text: str) -> None:
        path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")
        path.chmod(0o755)

    def _environment(self, root: pathlib.Path, scenario: str) -> tuple[dict[str, str], pathlib.Path]:
        fake_bin = root / "bin"; fake_bin.mkdir()
        state = root / "state"; (state / "pod").mkdir(parents=True)
        events = root / "events.log"
        control = root / "prime.key"; control.write_text("PRIME_SECRET_SENTINEL\n", encoding="utf-8")
        token = root / "hf.token"; token.write_text("HF_SECRET_SENTINEL\n", encoding="utf-8")
        ssh_key = root / "ssh.key"; ssh_key.write_text("not-a-real-key\n", encoding="utf-8")
        forecast_text = json.dumps({
            "admission_status": "admitted", "admitted_size": 28,
            "sol_reservations": {"smoke": 6, "annotation": 74, "user_continuation": 28,
                                 "openings": 4, "candidate_review": 6,
                                 "adjudication": 1, "repairs": 1},
        })
        (state / "forecast.json").write_text(forecast_text, encoding="utf-8")
        if scenario != "missing_receipt":
            forecast_sha = hashlib.sha256(forecast_text.encode()).hexdigest()
            if scenario == "forecast_hash_mismatch":
                forecast_sha = "0" * 64
            (state / "receipt.json").write_text(json.dumps({
                "artifacts": {"forecast.json": {"sha256": forecast_sha, "frozen": True}},
            }), encoding="utf-8")

        self._write_executable(fake_bin / "python3", r'''
            #!/usr/bin/env bash
            set -u
            first="${1:-}"
            if [[ "$first" == *dqd_provision.py ]]; then
              action="$2"; state_path="$3"
              if [[ "$action" == provision ]]; then
                printf '{"pod_id":"fake-pod","ssh_host":"fake-host","ssh_user":"ubuntu","ssh_port":2222,"price_hr":1.5}\n' > "$state_path"
                echo provision >> "$FAKE_EVENTS"
                echo 'provision fake-pod'
                exit 0
              fi
              rm -f "$state_path"
              echo teardown >> "$FAKE_EVENTS"
              echo 'DELETE_CONFIRMED pod_id=fake-pod'
              exit 0
            fi
            if [[ "$first" == *dqd.py ]]; then
              args=" $* "
              if [[ "$args" == *' ledger gpu-start '* ]]; then
                printf '{"record":"gpu_start","pod_id":"fake-pod","shutdown_deadline_utc":"2099-01-01T00:00:00+00:00"}\n' >> "$DQD_STATE_DIR/ledger.jsonl"
                echo gpu-start >> "$FAKE_EVENTS"
                echo 'DQD_OK ledger action="gpu-start"'
                exit 0
              fi
              if [[ "$args" == *' ledger gpu-stop '* ]]; then
                echo gpu-stop >> "$FAKE_EVENTS"
                echo 'DQD_OK ledger action="gpu-stop"'
                exit 0
              fi
              if [[ "$args" == *' rollout measurement '* ]]; then
                echo rollout >> "$FAKE_EVENTS"
                [[ "$FAKE_POD_SCENARIO" == stage_failure ]] && { echo 'DQD_FAIL rollout injected'; exit 33; }
                echo 'DQD_OK rollout horizon=8'
                exit 0
              fi
              if [[ "$args" == *' candidates measurement '* ]]; then
                echo candidates >> "$FAKE_EVENTS"
                echo 'DQD_OK candidates selected=1'
                exit 0
              fi
              if [[ "$args" == *' resample measurement '* ]]; then
                echo resample >> "$FAKE_EVENTS"
                [[ "$args" == *' --max-fresh 32 '* ]] || exit 35
                [[ "$args" == *' --targets '*'/measurement/resample_targets.json '* ]] || exit 36
                echo 'DQD_OK resample targets=1'
                exit 0
              fi
            fi
            exec "$REAL_PYTHON" "$@"
        ''')
        self._write_executable(fake_bin / "ssh", r'''
            #!/usr/bin/env bash
            set -u
            args=" $* "
            if [[ "$args" == *' -N '* ]]; then exec sleep 300; fi
            if [[ "$args" == *'dqd_pod_setup.sh'* ]]; then
              case "$FAKE_POD_SCENARIO" in
                preflight_work)   echo 'DQP_SETUP_FAIL code=41 reason=work_directory_not_writable'; exit 41 ;;
                preflight_disk)   echo 'DQP_SETUP_FAIL code=42 reason=disk_free_below_40GB'; exit 42 ;;
                preflight_driver) echo 'DQP_SETUP_FAIL code=43 reason=driver_version_unreadable'; exit 43 ;;
                preflight_memory) echo 'DQP_SETUP_FAIL code=44 reason=gpu_memory_below_38000MB'; exit 44 ;;
                sha_mismatch)     echo 'DQP_PREFLIGHT_OK'; echo 'DQP_SETUP_FAIL code=46 reason=model_sha256_mismatch'; exit 46 ;;
                serve_death)      echo 'DQP_PREFLIGHT_OK'; echo 'DQP_MODEL_SHA_OK'; echo 'DQP_SETUP_FAIL code=48 reason=serve_process_died'; echo 'last server error'; exit 48 ;;
                *) echo 'DQP_PREFLIGHT_OK'; echo 'DQP_MODEL_SHA_OK'; echo 'DQP_MODEL_CONFIG_OK max_position_embeddings=4096'; echo 'DQP_SERVE_READY model=fffoivos/greek-apertus-8b-sft-r4-full'; exit 0 ;;
              esac
            fi
            exit 0
        ''')
        self._write_executable(fake_bin / "scp", "#!/usr/bin/env bash\nexit 0\n")
        self._write_executable(fake_bin / "curl", r'''
            #!/usr/bin/env bash
            printf '{"data":[{"id":"fffoivos/greek-apertus-8b-sft-r4-full"}]}\n'
        ''')
        env = dict(os.environ)
        env.update({
            "PATH": str(fake_bin) + os.pathsep + env.get("PATH", ""),
            "REAL_PYTHON": sys.executable,
            "FAKE_EVENTS": str(events),
            "FAKE_POD_SCENARIO": scenario,
            "DQD_STATE_DIR": str(state),
            "DQD_CONTROL_KEY_FILE": str(control),
            "DQD_HF_TOKEN_FILE": str(token),
            "DQD_SSH_KEY": str(ssh_key),
        })
        return env, events

    def _run(self, scenario: str, stage: str = "measurement") -> tuple[subprocess.CompletedProcess[str], str]:
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        root = pathlib.Path(td.name)
        env, events = self._environment(root, scenario)
        output_path = root / "runner.out"
        with output_path.open("w", encoding="utf-8") as output:
            result = subprocess.run(["bash", str(RUNNER), stage], cwd=HERE, env=env,
                                    text=True, stdout=output, stderr=subprocess.STDOUT, timeout=15)
        event_text = events.read_text(encoding="utf-8") if events.exists() else ""
        combined = output_path.read_text(encoding="utf-8")
        result.stdout = combined
        result.stderr = ""
        self.assertNotIn("PRIME_SECRET_SENTINEL", combined)
        self.assertNotIn("HF_SECRET_SENTINEL", combined)
        for log in (root / "state" / "pod").glob("*.log"):
            text = log.read_text(encoding="utf-8")
            self.assertNotIn("PRIME_SECRET_SENTINEL", text)
            self.assertNotIn("HF_SECRET_SENTINEL", text)
        return result, event_text

    def _real_setup_environment(
            self, root: pathlib.Path, scenario: str,
    ) -> tuple[dict[str, str], pathlib.Path, pathlib.Path]:
        fake_bin = root / "bin"
        fake_bin.mkdir()
        home = root / "home"
        home.mkdir()
        events = root / "setup-events.log"
        fallback = home / "work"
        if scenario == "preflight_work":
            fallback.write_text("not a directory", encoding="utf-8")
        else:
            venv_bin = fallback / "vllmenv" / "bin"
            venv_bin.mkdir(parents=True)
            self._write_executable(venv_bin / "python", r'''
                #!/usr/bin/env bash
                if [[ " $* " == *' import torch,vllm;'* ]]; then
                  echo 'DQP_VLLM_OK version=stub torch=stub cuda=stub'
                  exit 0
                fi
                exec "$REAL_PYTHON" "$@"
            ''')
            self._write_executable(venv_bin / "hf", r'''
                #!/usr/bin/env bash
                echo hf_download >> "$FAKE_EVENTS"
                model_dir="${@: -1}"
                mkdir -p "$model_dir"
                printf 'model bytes\n' > "$model_dir/model.safetensors"
                printf '{"max_position_embeddings":4096}\n' > "$model_dir/config.json"
            ''')
            self._write_executable(venv_bin / "vllm", "#!/usr/bin/env bash\nexit 99\n")

        uv_shim = r'''
            #!/usr/bin/env bash
            echo "uv $*" >> "$FAKE_EVENTS"
            if [[ "${1:-}" == venv ]]; then mkdir -p "$2/bin"; fi
            exit 0
        '''
        self._write_executable(fake_bin / "uv-template", uv_shim)
        if scenario not in {"uv_bootstrap", "uv_download_failure"}:
            self._write_executable(fake_bin / "uv", uv_shim)
        self._write_executable(fake_bin / "python3", r'''
            #!/usr/bin/env bash
            if [[ " $* " == *' -m pip install '*' uv '* ]]; then
              echo "python3 $*" >> "$FAKE_EVENTS"
              mkdir -p "$HOME/.local/bin"
              cp "$FAKE_UV_TEMPLATE" "$HOME/.local/bin/uv"
              chmod +x "$HOME/.local/bin/uv"
              exit 0
            fi
            exec "$REAL_PYTHON" "$@"
        ''')

        self._write_executable(fake_bin / "sudo", "#!/usr/bin/env bash\nexit 1\n")
        self._write_executable(fake_bin / "df", r'''
            #!/usr/bin/env bash
            echo df >> "$FAKE_EVENTS"
            echo 'Filesystem 1024-blocks Used Available Capacity Mounted on'
            if [[ "$FAKE_POD_SCENARIO" == preflight_disk ]]; then
              echo 'fake 60000000 1 1048576 1% /fake'
            else
              echo 'fake 60000000 1 52428800 1% /fake'
            fi
        ''')
        self._write_executable(fake_bin / "nvidia-smi", r'''
            #!/usr/bin/env bash
            if [[ " $* " == *'query-gpu=driver_version'* ]]; then
              echo nvidia_driver >> "$FAKE_EVENTS"
              [[ "$FAKE_POD_SCENARIO" == preflight_driver ]] && { echo unknown; exit 0; }
              [[ "$FAKE_POD_SCENARIO" == cuda12 ]] && { echo 570.148.08; exit 0; }
              echo 580.126.09
              exit 0
            fi
            echo nvidia_memory >> "$FAKE_EVENTS"
            [[ "$FAKE_POD_SCENARIO" == preflight_memory ]] && { echo 37000; exit 0; }
            echo 40960
        ''')
        self._write_executable(fake_bin / "curl", r'''
            #!/usr/bin/env bash
            echo "curl $*" >> "$FAKE_EVENTS"
            if [[ " $* " == *'astral.sh/uv/install.sh'* ]]; then
              [[ "$FAKE_POD_SCENARIO" == uv_download_failure ]] && exit 7
              output=''
              while (( $# )); do
                if [[ "$1" == -o ]]; then output="$2"; shift 2; else shift; fi
              done
              [[ -n "$output" ]] || exit 8
              cat > "$output" <<'INSTALL'
            #!/bin/sh
            mkdir -p "$HOME/.local/bin"
            cp "$FAKE_UV_TEMPLATE" "$HOME/.local/bin/uv"
            chmod +x "$HOME/.local/bin/uv"
            INSTALL
              exit 0
            fi
            [[ "$FAKE_POD_SCENARIO" == serve_death ]] && exit 7
            printf '{"data":[{"id":"fffoivos/greek-apertus-8b-sft-r4-full"}]}\n'
        ''')
        self._write_executable(fake_bin / "sha256sum", r'''
            #!/usr/bin/env bash
            echo sha256sum >> "$FAKE_EVENTS"
            if [[ "$FAKE_POD_SCENARIO" == sha_mismatch ]]; then
              printf '%064d  %s\n' 0 "$1"
            else
              printf '%s  %s\n' "$EXPECTED_MODEL_SHA" "$1"
            fi
        ''')
        self._write_executable(fake_bin / "nohup", r'''
            #!/usr/bin/env bash
            echo nohup >> "$FAKE_EVENTS"
            if [[ "$FAKE_POD_SCENARIO" == serve_death ]]; then
              echo 'last server error from real setup harness' >&2
              exit 9
            fi
            exec /bin/sleep 60
        ''')
        env = dict(os.environ)
        env.update({
            "PATH": str(fake_bin) + os.pathsep + env.get("PATH", ""),
            "HOME": str(home),
            "REAL_PYTHON": sys.executable,
            "FAKE_EVENTS": str(events),
            "FAKE_UV_TEMPLATE": str(fake_bin / "uv-template"),
            "FAKE_POD_SCENARIO": scenario,
            "EXPECTED_MODEL_SHA": "54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763",
            "DQD_POD_WORK_PRIMARY": str(root / "primary-work"),
            "DQD_POD_WORK_FALLBACK": str(fallback),
        })
        if scenario in {"uv_bootstrap", "uv_download_failure"}:
            # Exclude the host's real uv so the production bootstrap path is
            # exercised entirely by the controlled installer shim.
            env["PATH"] = os.pathsep.join((str(fake_bin), "/usr/bin", "/bin"))
        return env, events, fallback

    def _run_real_setup(
            self, scenario: str, *, token_trailing_newline: bool = True,
    ) -> tuple[subprocess.CompletedProcess[str], str]:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root = pathlib.Path(td.name)
        env, events, work = self._real_setup_environment(root, scenario)
        token_path = root / "token.input"
        token_text = "HF_SETUP_SECRET_SENTINEL" + ("\n" if token_trailing_newline else "")
        token_path.write_text(token_text, encoding="utf-8")
        output_path = root / "setup.out"
        with token_path.open("r", encoding="utf-8") as token, \
                output_path.open("w", encoding="utf-8") as output:
            result = subprocess.run(
                ["bash", str(HERE / "pod" / "dqd_pod_setup.sh")],
                cwd=HERE, env=env, text=True, stdin=token,
                stdout=output, stderr=subprocess.STDOUT, timeout=10,
            )
        pid_path = work / "serve.pid"
        if pid_path.is_file():
            try:
                os.kill(int(pid_path.read_text(encoding="utf-8").strip()), 9)
            except (ProcessLookupError, ValueError):
                pass
        result.stdout = output_path.read_text(encoding="utf-8")
        result.stderr = ""
        self.assertNotIn("HF_SETUP_SECRET_SENTINEL", result.stdout)
        event_text = events.read_text(encoding="utf-8") if events.exists() else ""
        return result, event_text

    def test_fake_pod_preflight_failures_always_teardown(self):
        for scenario, code in (("preflight_work", 41), ("preflight_disk", 42),
                               ("preflight_driver", 43), ("preflight_memory", 44)):
            with self.subTest(scenario=scenario):
                result, events = self._run(scenario)
                self.assertEqual(result.returncode, code, result.stdout)
                self.assertIn(f"code={code}", result.stdout + result.stderr)
                self.assertIn("gpu-stop", events)
                self.assertIn("teardown", events)

    def test_real_setup_preflight_failures_precede_all_downloads(self):
        for scenario, code in (("preflight_work", 41), ("preflight_disk", 42),
                               ("preflight_driver", 43), ("preflight_memory", 44)):
            with self.subTest(scenario=scenario):
                result, events = self._run_real_setup(scenario)
                self.assertEqual(result.returncode, code, result.stdout)
                self.assertIn(f"DQP_SETUP_FAIL code={code}", result.stdout)
                self.assertNotIn("curl ", events)
                self.assertNotIn("uv ", events)
                self.assertNotIn("hf_download", events)

    def test_real_setup_sha_and_server_process_failures(self):
        sha_result, sha_events = self._run_real_setup("sha_mismatch")
        self.assertEqual(sha_result.returncode, 46, sha_result.stdout)
        self.assertIn("DQP_SETUP_FAIL code=46", sha_result.stdout)
        self.assertIn("hf_download", sha_events)
        death_result, death_events = self._run_real_setup("serve_death")
        self.assertEqual(death_result.returncode, 48, death_result.stdout)
        self.assertIn("last server error from real setup harness", death_result.stdout)
        self.assertIn("nohup", death_events)

    def test_real_setup_happy_path_runs_real_script(self):
        for trailing_newline in (False, True):
            with self.subTest(trailing_newline=trailing_newline):
                result, events = self._run_real_setup(
                    "happy", token_trailing_newline=trailing_newline,
                )
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn("DQP_PREFLIGHT_OK", result.stdout)
                self.assertIn("DQP_MODEL_SHA_OK", result.stdout)
                self.assertIn("DQP_MODEL_CONFIG_OK max_position_embeddings=4096", result.stdout)
                self.assertIn("DQP_SERVE_READY model=fffoivos/greek-apertus-8b-sft-r4-full", result.stdout)
                self.assertIn("hf_download", events)
                self.assertLess(events.index("nvidia_memory"), events.index("curl "))

    def test_real_setup_cuda_tracks_use_exact_dependency_commands(self):
        cuda13, cuda13_events = self._run_real_setup("happy")
        self.assertEqual(cuda13.returncode, 0, cuda13.stdout)
        cuda13_install = next(line for line in cuda13_events.splitlines()
                              if line.startswith("uv pip install"))
        self.assertIn("vllm==0.29.0", cuda13_install)
        self.assertIn("huggingface_hub[cli]", cuda13_install)
        self.assertNotIn("--torch-backend", cuda13_install)
        self.assertNotIn("--override", cuda13_install)

        cuda12, cuda12_events = self._run_real_setup("cuda12")
        self.assertEqual(cuda12.returncode, 0, cuda12.stdout)
        cuda12_install = next(line for line in cuda12_events.splitlines()
                              if line.startswith("uv pip install"))
        self.assertIn("vllm==0.19.1", cuda12_install)
        self.assertIn("--torch-backend=cu128", cuda12_install)
        self.assertIn("--override /dev/fd/", cuda12_install)
        self.assertIn("huggingface_hub[cli]", cuda12_install)

    def test_real_setup_bootstraps_uv_only_when_missing(self):
        result, events = self._run_real_setup("uv_bootstrap")
        self.assertEqual(result.returncode, 0, result.stdout)
        installer = next(line for line in events.splitlines()
                         if "astral.sh/uv/install.sh" in line)
        self.assertIn("--retry 5", installer)
        self.assertIn("--retry-all-errors", installer)
        self.assertIn("vllm==0.29.0", events)

        fallback, fallback_events = self._run_real_setup("uv_download_failure")
        self.assertEqual(fallback.returncode, 0, fallback.stdout)
        self.assertIn("python3 -m pip install --user --disable-pip-version-check uv", fallback_events)
        self.assertIn("vllm==0.29.0", fallback_events)

    def test_fake_pod_sha_mismatch_aborts_and_tears_down(self):
        result, events = self._run("sha_mismatch")
        self.assertEqual(result.returncode, 46, result.stdout)
        self.assertIn("code=46", result.stdout + result.stderr)
        self.assertNotIn("rollout", events)
        self.assertIn("teardown", events)

    def test_fake_pod_serve_death_is_reported_and_tears_down(self):
        result, events = self._run("serve_death")
        self.assertEqual(result.returncode, 48, result.stdout)
        self.assertIn("code=48", result.stdout + result.stderr)
        self.assertIn("last server error", result.stdout + result.stderr)
        self.assertIn("teardown", events)

    def test_forecast_receipt_gate_precedes_provisioning(self):
        for scenario, message in (("missing_receipt", "missing frozen forecast receipt"),
                                  ("forecast_hash_mismatch", "SHA-256 does not match")):
            with self.subTest(scenario=scenario):
                result, events = self._run(scenario)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stdout)
                self.assertNotIn("provision", events)

    def test_provision_adapter_overrides_hostile_gpu_count_before_helper_import(self):
        module_path = HERE / "pod" / "dqd_provision.py"
        spec = importlib.util.spec_from_file_location("dqd_provision_under_test", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        observed: dict[str, str] = {}
        helper = types.ModuleType("prime_provision")

        def provision(_args):
            observed["gpu_count"] = os.environ.get("GREEK_GPU_COUNT", "")
            return 0

        offer = {"cloudId": "one", "dataCenter": "dc", "provider": "test",
                 "gpuType": "A100_40GB", "stockStatus": "Available",
                 "prices": {"onDemand": 1.0}}
        helper.ApiError = RuntimeError
        helper.get_availability = lambda: {"items": [offer]}
        helper._iter_offers = lambda payload: iter(payload["items"])
        helper._offer_price = lambda item: float(item["prices"]["onDemand"])
        helper.rank_pick = lambda payload: dict(payload["items"][0], _canonical_gpu="A100_40GB")
        helper.cmd_provision = provision
        helper.cmd_teardown = lambda _args: 0
        with tempfile.TemporaryDirectory() as td, \
                mock.patch.dict(sys.modules, {"prime_provision": helper}), \
                mock.patch.dict(os.environ, {
                    "GREEK_GPU_COUNT": "8",
                    "PRIME_INTELLECT_CONTROL_KEY": "test-only-key",
                }), contextlib.redirect_stdout(io.StringIO()):
            result = adapter.main(["provision", str(pathlib.Path(td) / "state.json")])
        self.assertEqual(result, 0)
        self.assertEqual(observed["gpu_count"], "1")

    def _fake_prime_for_retry(self, offers: list[dict], succeed_on: tuple[str, str] | None):
        helper = types.ModuleType("prime_provision")
        attempts: list[tuple[str, str]] = []

        class ApiError(RuntimeError):
            pass

        helper.ApiError = ApiError
        helper.get_availability = lambda: {"items": offers}
        helper._iter_offers = lambda payload: iter(payload["items"])
        helper._offer_price = lambda offer: float(offer["prices"]["onDemand"])

        def rank_pick(payload):
            items = payload.get("items", [])
            if not items:
                return None
            result = dict(items[0])
            result["_canonical_gpu"] = result["gpuType"]
            return result

        def provision(_args):
            pick = helper.rank_pick(helper.get_availability())
            identity = (pick["cloudId"], pick["dataCenter"])
            attempts.append(identity)
            if identity != succeed_on:
                raise ApiError("POST /pods/ -> HTTP 503: Insufficient Capacity")
            pathlib.Path(os.environ["GREEK_SWEEP_POD_STATE"]).write_text(
                json.dumps({"pod_id": "fake-success"}), encoding="utf-8",
            )
            return 0

        helper.rank_pick = rank_pick
        helper.cmd_provision = provision
        helper.cmd_teardown = lambda _args: 0
        return helper, attempts

    def test_provision_retries_next_offer_after_http_error_and_prefers_stock(self):
        module_path = HERE / "pod" / "dqd_provision.py"
        spec = importlib.util.spec_from_file_location("dqd_provision_retry_test", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        low = {"cloudId": "low-cloud", "dataCenter": "low-dc", "provider": "runpod",
               "gpuType": "A100_80GB", "stockStatus": "Low", "prices": {"onDemand": 1.0}}
        stocked = {"cloudId": "stocked-cloud", "dataCenter": "stocked-dc", "provider": "other",
                   "gpuType": "A100_40GB", "stockStatus": "Available", "prices": {"onDemand": 1.1}}
        helper, attempts = self._fake_prime_for_retry([low, stocked], ("low-cloud", "low-dc"))
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as td, \
                mock.patch.dict(sys.modules, {"prime_provision": helper}), \
                mock.patch.dict(os.environ, {
                    "PRIME_INTELLECT_CONTROL_KEY": "test-only-key",
                    "DQD_PROVISION_RETRY_WAIT_SECONDS": "0",
                }), contextlib.redirect_stdout(output):
            result = adapter.main(["provision", str(pathlib.Path(td) / "state.json")])
        self.assertEqual(result, 0)
        self.assertEqual(attempts, [("stocked-cloud", "stocked-dc"), ("low-cloud", "low-dc")])
        self.assertIn("DQP_PROVISION_ATTEMPT_FAILED attempt=1/2", output.getvalue())
        self.assertIn("DQP_PROVISION_ATTEMPT_OK attempt=2/2", output.getvalue())

    def test_provision_exhausts_all_distinct_offers_after_http_errors(self):
        module_path = HERE / "pod" / "dqd_provision.py"
        spec = importlib.util.spec_from_file_location("dqd_provision_exhaustion_test", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        offers = [
            {"cloudId": "first", "dataCenter": "dc-1", "provider": "runpod",
             "gpuType": "A100_80GB", "stockStatus": "Available", "prices": {"onDemand": 1.4}},
            {"cloudId": "first", "dataCenter": "dc-1", "provider": "runpod",
             "gpuType": "A100_80GB", "stockStatus": "Available", "prices": {"onDemand": 1.4}},
            {"cloudId": "second", "dataCenter": "dc-2", "provider": "other",
             "gpuType": "L40S_48GB", "stockStatus": "Available", "prices": {"onDemand": 1.5}},
        ]
        helper, attempts = self._fake_prime_for_retry(offers, None)
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as td, \
                mock.patch.dict(sys.modules, {"prime_provision": helper}), \
                mock.patch.dict(os.environ, {
                    "PRIME_INTELLECT_CONTROL_KEY": "test-only-key",
                    "DQD_PROVISION_RETRY_WAIT_SECONDS": "0",
                }), contextlib.redirect_stdout(output):
            state_path = pathlib.Path(td) / "state.json"
            result = adapter.main(["provision", str(state_path)])
            self.assertFalse(state_path.exists())
        self.assertEqual(result, 1)
        self.assertEqual(attempts, [("first", "dc-1"), ("second", "dc-2")])
        self.assertIn("provision: ABORT -- all 2 ranked offers failed.", output.getvalue())

    def test_fake_pod_happy_path_and_candidates_entry(self):
        result, events = self._run("happy")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("rollout", events)
        self.assertIn("gpu-stop", events)
        self.assertIn("teardown", events)
        self.assertIn("teardown=confirmed", result.stdout)
        candidate_result, candidate_events = self._run("happy", "candidates")
        self.assertEqual(candidate_result.returncode, 0, candidate_result.stdout + candidate_result.stderr)
        self.assertIn("candidates", candidate_events)
        resample_result, resample_events = self._run("happy", "resample")
        self.assertEqual(resample_result.returncode, 0, resample_result.stdout + resample_result.stderr)
        self.assertIn("resample", resample_events)

    def test_fake_pod_stage_failure_runs_exit_trap(self):
        result, events = self._run("stage_failure")
        self.assertEqual(result.returncode, 33, result.stdout + result.stderr)
        self.assertIn("rollout", events)
        self.assertIn("gpu-stop", events)
        self.assertIn("teardown", events)
        self.assertIn("exit=33", result.stdout)

    def test_all_pod_shell_scripts_parse_and_disable_trace(self):
        scripts = sorted((HERE / "pod").glob("*.sh"))
        self.assertGreaterEqual(len(scripts), 3)
        for script in scripts:
            with self.subTest(script=script.name):
                parsed = subprocess.run(["bash", "-n", str(script)], stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
                self.assertEqual(parsed.returncode, 0)
                self.assertNotIn("set -x", script.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
