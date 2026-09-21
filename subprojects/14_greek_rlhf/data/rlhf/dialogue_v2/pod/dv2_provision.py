#!/usr/bin/env python3
"""Prime Intellect adapter for the dialogue v2 development runner.

Copied from data/rlhf/dialogue_quality_depth/pod/dqd_provision.py (reviewed CK3/CK5: ranked offers, HTTP-error
fallback, Low-stock de-prioritisation) and extended with read-only listing, a pre-provision "no active pod" gate
and a GET-confirmed deletion. The shared helper prime_provision.py is imported read-only and never edited.
The control key is read from ~/.config/prime/key into this process only; it is never printed.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time

PRIME_HELPER_DIR = pathlib.Path("/Users/foivoskarounos-zamparloukos/Projects/greek-page-ocr/scripts")
ALLOWED_GPUS = ("A100_40GB", "A100_80GB", "L40S_48GB")
POD_NAME = "greek-rlhf-dialogue-v2-dev"
TERMINAL_STATUSES = {"TERMINATED", "DELETED", "STOPPED", "ERROR"}


def _configure(state_path: str, max_price: float) -> None:
    os.environ["GREEK_SWEEP_POD_STATE"] = state_path
    os.environ["GREEK_GPU_COUNT"] = "1"
    os.environ["GREEK_SWEEP_GPU_WHITELIST"] = ",".join(ALLOWED_GPUS)
    os.environ["PRIME_MAX_PRICE_HR"] = f"{max_price:.2f}"
    os.environ["PRIME_MAX_HOURS"] = "2"
    os.environ["GREEK_SWEEP_IMAGE"] = "ubuntu_22_cuda_12"
    if not os.environ.get("PRIME_INTELLECT_CONTROL_KEY"):
        key_path = pathlib.Path(os.environ.get("DV2_CONTROL_KEY_FILE", "~/.config/prime/key")).expanduser()
        os.environ["PRIME_INTELLECT_CONTROL_KEY"] = key_path.read_text(encoding="utf-8").strip()


def _helper(state_path: str, max_price: float):
    _configure(state_path, max_price)
    sys.path.insert(0, str(PRIME_HELPER_DIR))
    import prime_provision as prime  # read-only import after env configuration
    prime.POD_NAME = POD_NAME
    return prime


def _offer_identity(offer: dict) -> tuple[str, str]:
    return (str(offer.get("cloudId") or ""), str(offer.get("dataCenter") or offer.get("dataCenterId") or ""))


def ranked_offers(prime, payload) -> list[dict]:
    candidates: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for raw_offer in prime._iter_offers(payload):
        offer = prime.rank_pick({"items": [dict(raw_offer)]})
        if offer is None:
            continue
        identity = _offer_identity(offer)
        if identity in seen:
            continue
        seen.add(identity)
        candidates.append(offer)

    def order(offer: dict):
        price = prime._offer_price(offer)
        price = float("inf") if price is None else price
        low_stock = str(offer.get("stockStatus") or "").strip().lower() == "low"
        cloud_id, data_center = _offer_identity(offer)
        return price * (1.2 if low_stock else 1.0), low_stock, price, cloud_id, data_center

    return sorted(candidates, key=order)


def active_pods(prime) -> list[dict]:
    payload = prime._api("GET", "/pods/")
    items = payload.get("data") if isinstance(payload, dict) else payload
    if items is None and isinstance(payload, dict):
        items = payload.get("items") or payload.get("pods") or []
    out = []
    for pod in items or []:
        status = str(pod.get("status") or "").upper()
        if status not in TERMINAL_STATUSES:
            out.append({"id": pod.get("id"), "name": pod.get("name"), "status": status,
                        "priceHr": pod.get("priceHr"), "createdAt": pod.get("createdAt")})
    return out


def pod_record(prime, pod_id: str) -> dict:
    info = prime._api("GET", f"/pods/{pod_id}")
    keep = ("id", "name", "status", "createdAt", "terminatedAt", "priceHr", "gpuName", "gpuCount", "providerType")
    return {key: info.get(key) for key in keep if key in info}


def cmd_provision(prime, state_path: pathlib.Path) -> int:
    active = active_pods(prime)
    if active:
        print(f"DV2_PROVISION_ABORT active_pods={len(active)} ids={[p['id'] for p in active]}")
        return 3
    payload = prime.get_availability()
    offers = ranked_offers(prime, payload)
    if not offers:
        print("DV2_PROVISION_ABORT no ranked GPU available under the price cap")
        return 1
    provision_args = argparse.Namespace(image="ubuntu_22_cuda_12", disk_gb=100, network_volume=None,
                                        timeout=1500, poll_interval=15, force=False)
    original_get, original_rank = prime.get_availability, prime.rank_pick
    original_write = prime.write_pod_state
    created: list[dict] = []

    def capture(state: dict) -> None:
        if state.get("pod_id") and not any(c["pod_id"] == state["pod_id"] for c in created):
            created.append({"pod_id": state["pod_id"], "price_hr": state.get("price_hr"), "created_at": state.get("created_at")})
        original_write(state)
    prime.write_pod_state = capture
    total = len(offers)
    for attempt, offer in enumerate(offers, start=1):
        cloud_id, data_center = _offer_identity(offer)
        print(f"DV2_PROVISION_ATTEMPT attempt={attempt}/{total} gpu={offer.get('_canonical_gpu') or offer.get('gpuType')} "
              f"provider={offer.get('provider')} cloudId={cloud_id} dataCenter={data_center} "
              f"stock={offer.get('stockStatus')} price_usd_hr={prime._offer_price(offer)}")
        prime.get_availability = lambda selected=offer: {"items": [selected]}
        prime.rank_pick = lambda _payload, selected=offer: dict(selected)
        post_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        try:
            result = int(prime.cmd_provision(provision_args))
        except prime.ApiError as exc:
            if "POST /pods/ -> HTTP " not in str(exc):
                raise
            result = 1
            print(f"DV2_PROVISION_ATTEMPT_FAILED attempt={attempt}/{total} error={str(exc)[:300]}")
        finally:
            prime.get_availability, prime.rank_pick = original_get, original_rank
        if result == 0:
            state = json.loads(state_path.read_text())
            state["post_utc_local"] = post_utc
            state_path.write_text(json.dumps(state, indent=2) + "\n")
            print(f"DV2_PROVISION_ATTEMPT_OK attempt={attempt}/{total}")
            return 0
        if state_path.exists():
            print("DV2_PROVISION_ABORT failed attempt left pod state behind; refusing a second billing pod")
            return result or 1
        for pod in [c for c in created if not c.get("charged")]:
            _charge_failed_attempt(prime, pod)
            pod["charged"] = True
        if attempt < total:
            time.sleep(5)
    print(f"DV2_PROVISION_ABORT all {total} ranked offers failed")
    return 1


def _charge_failed_attempt(prime, pod: dict) -> None:
    """A pod created by a failed provisioning attempt is billed too: confirm its deletion and charge the ledger."""
    import datetime as dt
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    import ledger  # dialogue_v2/ledger.py
    record: dict = {}
    for _ in range(24):
        try:
            record = pod_record(prime, pod["pod_id"])
            if str(record.get("status") or "").upper() in TERMINAL_STATUSES:
                break
            prime._api("DELETE", f"/pods/{pod['pod_id']}")
        except prime.ApiError as exc:
            if "HTTP 404" in str(exc):
                record = {"status": "NOT_FOUND"}
                break
        time.sleep(5)
    post = dt.datetime.fromtimestamp(pod["created_at"], dt.timezone.utc).isoformat()
    stage = os.environ.get("DV2_STAGE", "unknown")
    ledger.gpu_start(pod["pod_id"], stage, float(pod["price_hr"] or 2.0), post, 1.0)
    ledger.gpu_stop(pod["pod_id"], record.get("createdAt"), record.get("terminatedAt"))
    print(f"DV2_FAILED_ATTEMPT_CHARGED pod_id={pod['pod_id']} status={record.get('status')}")


def cmd_teardown(prime, state_path: pathlib.Path, pod_id: str | None, record_path: pathlib.Path | None) -> int:
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    pod_id = pod_id or state.get("pod_id")
    if not pod_id:
        print("DV2_TEARDOWN nothing recorded")
        return 0
    delete_ok = False
    for attempt in range(1, 4):
        try:
            prime._api("DELETE", f"/pods/{pod_id}")
            delete_ok = True
            print(f"DV2_DELETE_SENT pod_id={pod_id} attempt={attempt}")
            break
        except prime.ApiError as exc:
            text = str(exc)
            if "HTTP 404" in text:
                delete_ok = True
                print(f"DV2_DELETE_404 pod_id={pod_id}")
                break
            print(f"DV2_DELETE_FAILED pod_id={pod_id} attempt={attempt} error={text[:200]}")
            time.sleep(10)
    record: dict = {}
    confirmed = False
    for _ in range(24):
        try:
            record = pod_record(prime, pod_id)
            if str(record.get("status") or "").upper() in TERMINAL_STATUSES:
                confirmed = True
                break
        except prime.ApiError as exc:
            if "HTTP 404" in str(exc):
                confirmed = True
                record = {"id": pod_id, "status": "NOT_FOUND"}
                break
        time.sleep(5)
    if record_path is not None:
        record_path.parent.mkdir(parents=True, exist_ok=True)
        with record_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"pod_id": pod_id, "delete_sent": delete_ok, "get_confirmed": confirmed,
                                     "record": record, "checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
                         + "\n")
    if confirmed:
        if state_path.exists():
            state_path.unlink()
        print(f"DELETE_CONFIRMED pod_id={pod_id} status={record.get('status')} createdAt={record.get('createdAt')} "
              f"terminatedAt={record.get('terminatedAt')}")
        return 0
    print(f"DELETE_UNCONFIRMED pod_id={pod_id} last_status={record.get('status')}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("pods", "get", "availability", "provision", "teardown"))
    parser.add_argument("state_path", nargs="?", default="/dev/null")
    parser.add_argument("--pod-id")
    parser.add_argument("--max-price", type=float, default=float(os.environ.get("DV2_MAX_PRICE_HR", "2.0")))
    parser.add_argument("--record")
    args = parser.parse_args(argv)
    prime = _helper(args.state_path if args.action in {"provision", "teardown"} else "/tmp/dv2_unused_state.json",
                    args.max_price)
    if args.action == "pods":
        pods = active_pods(prime)
        print(json.dumps({"active_pods": pods, "count": len(pods)}))
        return 0
    if args.action == "get":
        print(json.dumps(pod_record(prime, args.pod_id)))
        return 0
    if args.action == "availability":
        offers = ranked_offers(prime, prime.get_availability())
        print(json.dumps([{"gpu": o.get("_canonical_gpu") or o.get("gpuType"), "provider": o.get("provider"),
                           "dataCenter": _offer_identity(o)[1], "stock": o.get("stockStatus"),
                           "price_usd_hr": prime._offer_price(o)} for o in offers]))
        return 0
    if args.action == "provision":
        return cmd_provision(prime, pathlib.Path(args.state_path))
    return cmd_teardown(prime, pathlib.Path(args.state_path), args.pod_id,
                        pathlib.Path(args.record) if args.record else None)


if __name__ == "__main__":
    raise SystemExit(main())
