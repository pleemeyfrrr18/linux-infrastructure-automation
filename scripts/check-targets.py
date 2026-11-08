#!/usr/bin/env python3
"""Read-only check through an SSH tunnel to Prometheus."""
import json
import sys
import urllib.request
base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:9090").rstrip("/")
with urllib.request.urlopen(base + "/api/v1/targets", timeout=10) as response:
    targets = json.load(response)["data"]["activeTargets"]
expected = {("node", "app01"), ("node", "mon01"), ("application", "app01"),
            ("prometheus", "127.0.0.1:9090")}
actual = {(t["labels"]["job"], t["labels"]["instance"]) for t in targets}
for target in targets:
    print(target["labels"], target["health"], target.get("lastError", ""))
if actual != expected or any(t["health"] != "up" for t in targets):
    sys.exit("FAIL: expected four healthy lab targets")
print("PASS: all four expected targets are up")
