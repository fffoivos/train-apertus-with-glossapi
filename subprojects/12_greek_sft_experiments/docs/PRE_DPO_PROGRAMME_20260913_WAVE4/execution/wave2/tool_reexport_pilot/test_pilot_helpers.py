#!/usr/bin/env python3
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pilot_run", HERE / "pilot_run.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

schemas = '[{"type":"function","function":{"name":"weather.lookup","parameters":{"type":"object","properties":{"city":{"type":"string"},"days":{"type":"integer"},"metric":{"type":"boolean"}},"required":["city","days"]}}}]'
declared = module.declared_functions(schemas)
assert set(declared) == {"weather.lookup"}
calls = module.parse_calls('weather.lookup(city="Athens", days=3, metric=true)')
assert calls == [{"name": "weather.lookup", "arguments": {"city": "Athens", "days": 3, "metric": True}, "grammar": "python_call"}]
module.validate_instance(calls[0]["arguments"], declared[calls[0]["name"]])
multi = module.parse_calls('first(a=1)\nsecond(b=null)')
assert [x["name"] for x in multi] == ["first", "second"] and multi[1]["arguments"]["b"] is None
jcall = module.parse_calls('[{"name":"weather.lookup","arguments":{"city":"Athens","days":2}}]')
assert jcall[0]["grammar"] == "json" and jcall[0]["arguments"]["days"] == 2
try:
    module.parse_calls('bad(1)')
except ValueError:
    pass
else:
    raise AssertionError("positional arguments did not fail closed")
print("PASS pilot call/schema parsers")
