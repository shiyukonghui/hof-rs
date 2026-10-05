"""A faithful Python transcription of `src/runtime/secrets.rs`'s shape rule, used
to decide whether a candidate evidence file may be added to the tracked tree.
NEVER prints a value: only a fingerprint (first 8 hex of sha256) and the length."""
import hashlib
import os
import sys

KEY_PREFIXES = ["sk-", "sk_", "pk-", "pk_", "ghp_", "gho_", "xoxb-", "xoxp-", "AKIA", "AIza"]
KEY_BODY_MINIMUM = 16
KEY_ASSIGNMENT_NAMES = [
    "api_key", "apikey", "api-key", "secret", "access_token", "auth_token", "password",
]
KEY_VALUE_MINIMUM = 32
ALLOWED = ["test-key-not-a-secret", "sk-late-occurrence"]


def is_token_byte(c):
    return c.isascii() and (c.isalnum() or c in "-_")


def is_token_character(c):
    return c.isascii() and (c.isalnum() or c == "_")


def key_shaped_tokens(text):
    found = set()
    n = len(text)
    for prefix in KEY_PREFIXES:
        start = 0
        while True:
            pos = text.find(prefix, start)
            if pos < 0:
                break
            starts_a_token = pos == 0 or not is_token_character(text[pos - 1])
            body_start = pos + len(prefix)
            i = body_start
            while i < n and is_token_byte(text[i]):
                i += 1
            body = i - body_start
            if starts_a_token and body >= KEY_BODY_MINIMUM:
                found.add(text[pos:body_start + body])
            start = pos + len(prefix)
    return found


def looks_key_shaped(text):
    if key_shaped_tokens(text):
        return True
    lowered = text.lower()
    for name in KEY_ASSIGNMENT_NAMES:
        start = 0
        while True:
            pos = lowered.find(name, start)
            if pos < 0:
                break
            rest = text[pos + len(name):]
            rest = rest.lstrip()
            if rest.startswith('"') or rest.startswith("'"):
                rest = rest[1:]
            rest = rest.lstrip()
            if not rest.startswith(":") and not rest.startswith("="):
                start = pos + len(name)
                continue
            rest = rest[1:].lstrip()
            if rest.startswith('"') or rest.startswith("'"):
                rest = rest[1:]
            i = 0
            while i < len(rest) and (rest[i].isascii() and (rest[i].isalnum() or rest[i] in "-_")):
                i += 1
            if i >= KEY_VALUE_MINIMUM:
                return True
            start = pos + len(name)
    return False


def fp(value):
    return hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()[:8]


def scan(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    text = raw.decode("utf-8", "replace")
    findings = []
    for value in key_shaped_tokens(text):
        if any(a in value for a in ALLOWED):
            continue
        findings.append((fp(value), len(value), "token"))
    for line in text.splitlines():
        if looks_key_shaped(line) and not key_shaped_tokens(line):
            if any(a in line for a in ALLOWED):
                continue
            findings.append((fp(line.strip()), len(line.strip()), "assignment"))
    return len(raw), findings


def main():
    for path in sys.argv[1:]:
        if not os.path.isfile(path):
            print("MISSING", path)
            continue
        size, findings = scan(path)
        status = "CLEAN" if not findings else "KEY-SHAPED"
        print("%-9s %10d %s %s" % (status, size, path, findings if findings else ""))


if __name__ == "__main__":
    main()
