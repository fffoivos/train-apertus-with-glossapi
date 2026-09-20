"""Restrict a task to the frozen screen IDs (DPO01). Scorers, few-shot, decoding and chat
template are inherited unchanged from the sibling production task; this only drops documents
that are not named in screen_manifest.json, and refuses to run if the match is incomplete."""
import json, os, functools

@functools.lru_cache(maxsize=1)
def _manifest():
    p = os.environ.get("SCREEN_MANIFEST")
    if not p:
        raise RuntimeError("SCREEN_MANIFEST is not set: refusing to run an unscoped screen")
    return json.load(open(p, encoding="utf-8"))

def _keep(dataset, component, key_field):
    c = _manifest()["components"][component]
    if "error" in c:
        raise RuntimeError(f"screen component {component} failed to freeze: {c['error']}")
    want = set(map(str, c["selected"]))
    out = dataset.filter(lambda d, i: str(d.get(key_field, i)) in want, with_indices=True)
    if len(out) != len(want):
        raise RuntimeError(f"{component}: matched {len(out)} of {len(want)} frozen ids "
                           f"(key field {key_field!r}); refusing to score a partial screen")
    return out

def ifeval_screen(dataset):
    return _keep(dataset, "ifeval_greek", "key")

def mgsm_screen(dataset):
    return _keep(dataset, "mgsm_greek", "id")
