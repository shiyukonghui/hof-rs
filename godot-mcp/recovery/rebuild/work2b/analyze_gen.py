import io, json, os, re

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
LC = os.path.join(R, "rebuild", "_low-confidence", "modules", "mcp_server", "scripts", "gen_renamed_contract.py")
txt = io.open(LC, encoding="utf-8").read()

def slice_block(name):
    i = txt.index(name + " = {")
    depth = 0
    j = txt.index("{", i)
    k = j
    while k < len(txt):
        if txt[k] == "{":
            depth += 1
        elif txt[k] == "}":
            depth -= 1
            if depth == 0:
                return txt[j:k + 1], txt[:i].count("\n") + 1
        k += 1
    return None, None

block, line = slice_block("DESCRIPTION_OVERRIDES")
keys = re.findall(r'^    "([^"]+)": \{', block, re.M)
print("DESCRIPTION_OVERRIDES declared names = %d (starts line %d)" % (len(keys), line))
for k in keys:
    print("   ", k)
sb, sl = slice_block("SCHEMA_OVERRIDES")
print("SCHEMA_OVERRIDES block line", sl, "len", len(sb))
sb2 = sb if sb else "{}"
keys2 = re.findall(r'^    "([^"]+)": \{', sb2, re.M)
print("SCHEMA_OVERRIDES names =", len(keys2), keys2)
# added tools
ab = txt[txt.index("ADDED_TOOLS = ["):]
names = re.findall(r'"name": "([^"]+)"', ab[:40000])
print("ADDED_TOOLS names =", len(names), names)
print("GENERATOR_VERSION line:", re.search(r'GENERATOR_VERSION = "([^"]+)"', txt).group(1))
