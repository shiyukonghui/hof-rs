import sys, re

p = r'F:\moonbit-hof-rs\runs\smoke-t10\iter-1\traj\developer.attempt2.json'
raw = open(p, encoding='utf-8', errors='replace').read()
start = 0
n = 0
while True:
    pos = raw.find('<redacted>', start)
    if pos < 0:
        break
    n += 1
    print(f"--- attempt2 occurrence {n} ---")
    print(repr(raw[pos - 200:pos + 120]))
    start = pos + 1
print("total:", n)

print()
print("=== SIMULATION of src/runtime/secrets.rs redact_secret_assignments on JSON-escaped text ===")
SECRET_ENV_VARS = ["HOH_MODEL_API_KEY", "OPENAI_API_KEY"]
REDACTED = "<redacted>"

def redact_secret_assignments(text):
    out = text
    for name in SECRET_ENV_VARS:
        needle = name + "="
        search_from = 0
        while True:
            found = out.find(needle, search_from)
            if found < 0:
                break
            start = found
            value_start = start + len(needle)
            if value_start < len(out) and out[value_start] == '"':
                rel = out.find('"', value_start + 1)
                value_end = len(out) if rel < 0 else value_start + 1 + rel + 1
            else:
                idxs = [i for i in (out.find(c, value_start) for c in (';', '\n', '\r')) if i >= 0]
                value_end = min(idxs) if idxs else len(out)
            out = out[:start] + needle + REDACTED + out[value_end:]
            search_from = start + len(needle) + len(REDACTED)
    return out

sample = '      "content": "<returncode>0</returncode>\\n<output>\\nHOH_MODEL_API_KEY=sk-REALSECRET51CHARS\\n</output>",\n      "extra": {'
step1 = sample.replace('sk-REALSECRET51CHARS', REDACTED)
print("after value substitution:", repr(step1))
print("after assignment redaction:", repr(redact_secret_assignments(step1)))
