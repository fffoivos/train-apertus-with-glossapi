"""python -m rlhf.prompts <command> ...
  migrate  <legacy.sqlite> <bank.sqlite>     carry the legacy registry across, through the constraints
  audit    <bank.sqlite>                     every invariant, counted
  stats    <bank.sqlite>                     sources and prompts by kind and state
  supply   <bank.sqlite> [kind]              unused sources per cell
  coverage <bank.sqlite> <plan>              target / filled / claimed / remaining
  feasibility <bank.sqlite> <plan>           share quotas the unused supply cannot meet (empty = attainable)
  lineage  <bank.sqlite> <prompt id|alias>   the prompt, its source verbatim, earlier attempts
"""
import json, sys
from .bank import PromptBank

def main(argv):
    if len(argv) < 2: raise SystemExit(__doc__)
    cmd, args = argv[0], argv[1:]
    if cmd == "migrate":
        from .migrate import migrate
        out = migrate(args[0], args[1])
    else:
        b = PromptBank(args[0])
        if cmd == "audit": out = b.audit()
        elif cmd == "stats": out = {k: {"/".join(map(str, kk)): v for kk, v in d.items()} for k, d in b.stats().items()}
        elif cmd == "supply": out = b.supply(args[1] if len(args) > 1 else None)
        elif cmd == "coverage": out = b.coverage(args[1])
        elif cmd == "feasibility": out = b.feasibility(args[1])
        elif cmd == "lineage": out = b.lineage(args[1])
        else: raise SystemExit(__doc__)
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))

main(sys.argv[1:])
