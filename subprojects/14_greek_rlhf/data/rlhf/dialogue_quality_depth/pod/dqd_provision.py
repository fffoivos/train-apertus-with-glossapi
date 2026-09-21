#!/usr/bin/env python3
"""Narrow Prime Intellect adapter for the dialogue-quality pod runner."""
from __future__ import annotations

import argparse
import os
import pathlib
import sys
import time

PRIME_HELPER_DIR = pathlib.Path(
    "/Users/foivoskarounos-zamparloukos/Projects/greek-page-ocr/scripts"
)
ALLOWED_GPUS = ("A100_40GB", "A100_80GB", "L40S_48GB")


def _configure(state_path: str) -> None:
    os.environ["GREEK_SWEEP_POD_STATE"] = state_path
    # The shared helper reads this at import time. Never allow an inherited
    # shell value to widen this single-GPU experiment.
    os.environ["GREEK_GPU_COUNT"] = "1"
    os.environ["GREEK_SWEEP_GPU_WHITELIST"] = ",".join(ALLOWED_GPUS)
    os.environ["PRIME_MAX_PRICE_HR"] = "2.5"
    os.environ["PRIME_MAX_HOURS"] = "2"
    os.environ["GREEK_SWEEP_IMAGE"] = "ubuntu_22_cuda_12"
    if not os.environ.get("PRIME_INTELLECT_CONTROL_KEY"):
        key_path = pathlib.Path("~/.config/prime/key").expanduser()
        os.environ["PRIME_INTELLECT_CONTROL_KEY"] = key_path.read_text(encoding="utf-8").strip()


def _offer_identity(offer: dict) -> tuple[str, str]:
    """Return the provider-capacity identity required for retry exclusion."""
    return (
        str(offer.get("cloudId") or ""),
        str(offer.get("dataCenter") or offer.get("dataCenterId") or ""),
    )


def _ranked_offers(prime, payload) -> list[dict]:
    """Apply the shared helper's policy, then de-prioritize Low stock by 20%."""
    candidates: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for raw_offer in prime._iter_offers(payload):
        # A singleton call reuses every policy constraint in the read-only
        # helper: GPU whitelist, security, count, price cap and no-spot rule.
        offer = prime.rank_pick({"items": [dict(raw_offer)]})
        if offer is None:
            continue
        identity = _offer_identity(offer)
        if identity in seen:
            continue
        seen.add(identity)
        candidates.append(offer)

    def order(offer: dict) -> tuple[float, bool, float, str, str]:
        price = prime._offer_price(offer)
        if price is None:
            price = float("inf")
        low_stock = str(offer.get("stockStatus") or "").strip().lower() == "low"
        # A non-Low offer costing at most 20% more sorts ahead of a Low offer.
        effective_price = price * (1.2 if low_stock else 1.0)
        cloud_id, data_center = _offer_identity(offer)
        return effective_price, low_stock, price, cloud_id, data_center

    return sorted(candidates, key=order)


def _provision_with_fallback(prime, provision_args, state_path: pathlib.Path) -> int:
    payload = prime.get_availability()
    offers = _ranked_offers(prime, payload)
    if not offers:
        print("provision: ABORT -- no ranked GPU available right now.")
        return 1

    original_get_availability = prime.get_availability
    original_rank_pick = prime.rank_pick
    wait_seconds = max(0.0, float(os.environ.get("DQD_PROVISION_RETRY_WAIT_SECONDS", "5")))
    total = len(offers)
    for attempt, offer in enumerate(offers, start=1):
        cloud_id, data_center = _offer_identity(offer)
        price = prime._offer_price(offer)
        print(
            f"DQP_PROVISION_ATTEMPT attempt={attempt}/{total} "
            f"gpu={offer.get('_canonical_gpu') or offer.get('gpuType')} "
            f"provider={offer.get('provider')} cloudId={cloud_id} "
            f"dataCenter={data_center} stock={offer.get('stockStatus')} price_usd_hr={price}"
        )
        # cmd_provision retains its polling, immediate state persistence and
        # anti-orphan teardown. Pin only its selection to this ranked attempt.
        prime.get_availability = lambda selected=offer: {"items": [selected]}
        prime.rank_pick = lambda _payload, selected=offer: dict(selected)
        try:
            result = int(prime.cmd_provision(provision_args))
        except prime.ApiError as exc:
            if "POST /pods/ -> HTTP " not in str(exc):
                raise
            result = 1
            print(f"DQP_PROVISION_ATTEMPT_FAILED attempt={attempt}/{total} error={exc}")
        finally:
            prime.get_availability = original_get_availability
            prime.rank_pick = original_rank_pick
        if result == 0:
            print(f"DQP_PROVISION_ATTEMPT_OK attempt={attempt}/{total}")
            return 0
        if state_path.exists():
            print(
                "provision: ABORT -- failed attempt left pod state behind; "
                "refusing to risk provisioning a second billing pod."
            )
            return result or 1
        print(
            f"DQP_PROVISION_EXCLUDED cloudId={cloud_id} dataCenter={data_center} "
            f"remaining={total - attempt}"
        )
        if attempt < total and wait_seconds:
            print(f"DQP_PROVISION_RETRY_WAIT seconds={wait_seconds:g}")
            time.sleep(wait_seconds)
    print(f"provision: ABORT -- all {total} ranked offers failed.")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("provision", "teardown"))
    parser.add_argument("state_path")
    parser.add_argument("--pod-id")
    args = parser.parse_args(argv)
    _configure(args.state_path)
    sys.path.insert(0, str(PRIME_HELPER_DIR))
    import prime_provision as prime  # imported read-only after env configuration

    prime.POD_NAME = "greek-rlhf-dialogue"
    if args.action == "provision":
        provision_args = argparse.Namespace(
            image="ubuntu_22_cuda_12", disk_gb=100, network_volume=None,
            timeout=1500, poll_interval=15, force=False,
        )
        return _provision_with_fallback(prime, provision_args, pathlib.Path(args.state_path))

    pod_id = args.pod_id
    teardown_args = argparse.Namespace(pod_id=pod_id, no_save=True, force=False)
    result = int(prime.cmd_teardown(teardown_args))
    if result == 0 and not pathlib.Path(args.state_path).exists():
        print(f"DELETE_CONFIRMED pod_id={pod_id or 'state-record'}")
        return 0
    print(f"DELETE_UNCONFIRMED pod_id={pod_id or 'state-record'}", file=sys.stderr)
    return result or 1


if __name__ == "__main__":
    raise SystemExit(main())
