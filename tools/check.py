#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# THE GATE: the bands are sound and the texts are whole. Run from the repository's root:
#   python3 tools/check.py             check bands.toml, languages.toml and every text/<lang>.toml
#   python3 tools/check.py --controls  also prove the gate refuses each kind of damage (each control must FAIL)
import copy, re, sys, tomllib
from pathlib import Path

TYPES = {"tilt": False, "lowShelf": True, "highShelf": True, "bell": True}   # type -> takes a q
KEY = re.compile(r"^[a-z][a-z0-9]*$")
NAME_MAX, SHORT_MAX = 24, 40
# Familiar address, refused in every language that has it (the site's rule: polite or impersonal, never familiar).
# A language's list lands with the language.
FAMILIAR = {
    "ru": r"\b(ты|тебя|тебе|тобой|твой|твоя|твоё|твое|твои|твоих|твоим)\b",
    "uk": r"\b(ти|тебе|тобі|тобою|твій|твоя|твоє|твої)\b",
    "de": r"\b(du|dich|dir|dein|deine|deinen|deinem|deiner)\b",
}

def problems(bands, languages, texts):
    out = []
    keys = list(bands.get("bands", {}))
    if not keys: out.append("bands.toml: no [bands.*]")
    for k, b in bands.get("bands", {}).items():
        if not KEY.match(k): out.append(f"band key {k!r}: lowercase letters and digits only")
        t = b.get("type")
        if t not in TYPES: out.append(f"{k}: type {t!r} is not one of {sorted(TYPES)}"); continue
        hz = b.get("hz")
        if not isinstance(hz, (int, float)) or not 10 <= hz <= 24000: out.append(f"{k}: hz {hz!r} outside 10…24000")
        if TYPES[t]:
            q = b.get("q")
            if not isinstance(q, (int, float)) or not 0.1 <= q <= 10: out.append(f"{k}: q {q!r} outside 0.1…10")
        elif "q" in b: out.append(f"{k}: a {t} takes no q")
        extra = set(b) - {"type", "hz", "q"}
        if extra: out.append(f"{k}: unknown fields {sorted(extra)}")
    langs = languages.get("languages", [])
    if not langs or langs[0] != "ru": out.append("languages.toml: ru must be listed first (the canon)")
    for lang in langs:
        text = texts.get(lang)
        if text is None: out.append(f"text/{lang}.toml: listed but missing"); continue
        missing, extra = set(keys) - set(text), set(text) - set(keys)
        if missing: out.append(f"text/{lang}.toml: no entry for {sorted(missing)}")
        if extra: out.append(f"text/{lang}.toml: entries for unknown bands {sorted(extra)}")
        for k in keys:
            e = text.get(k)
            if not isinstance(e, dict): continue
            if set(e) != {"name", "short"}: out.append(f"text/{lang}.toml [{k}]: exactly name and short, got {sorted(e)}")
            for field, limit in (("name", NAME_MAX), ("short", SHORT_MAX)):
                v = e.get(field)
                if not isinstance(v, str) or not v.strip(): out.append(f"text/{lang}.toml [{k}].{field}: empty"); continue
                if len(v) > limit: out.append(f"text/{lang}.toml [{k}].{field}: {len(v)} characters, at most {limit}")
                if v != v.strip() or v.endswith("."): out.append(f"text/{lang}.toml [{k}].{field}: no outer spaces, no final period")
                if lang in FAMILIAR and re.search(FAMILIAR[lang], v, re.IGNORECASE):
                    out.append(f"text/{lang}.toml [{k}].{field}: familiar address — polite or impersonal only")
    for lang in texts:
        if lang not in langs: out.append(f"text/{lang}.toml: not listed in languages.toml")
    return out

def load(root):
    read = lambda p: tomllib.loads(p.read_text(encoding="utf-8"))
    return (read(root / "bands.toml"), read(root / "languages.toml"),
            {p.stem: read(p) for p in sorted((root / "text").glob("*.toml"))})

def controls(bands, languages, texts):
    def broken(name, mutate):
        b, l, t = copy.deepcopy(bands), copy.deepcopy(languages), copy.deepcopy(texts)
        mutate(b, l, t)
        return name, bool(problems(b, l, t))
    first = next(iter(bands["bands"]))
    cases = [
        broken("a band without a type", lambda b, l, t: b["bands"][first].pop("type")),
        broken("a frequency out of range", lambda b, l, t: b["bands"][first].update(hz=5)),
        broken("a band missing in a language", lambda b, l, t: t["en"].pop(first)),
        broken("a short line too long", lambda b, l, t: t["en"][first].update(short="x" * (SHORT_MAX + 1))),
        broken("a final period", lambda b, l, t: t["en"][first].update(short="Ends with a period.")),
        broken("familiar address in ru", lambda b, l, t: t["ru"][first].update(short="Сделай как тебе нравится")),
        broken("an unlisted language file", lambda b, l, t: t.update(xx=copy.deepcopy(t["en"]))),
        broken("ru not first", lambda b, l, t: l.update(languages=["en", "ru"])),
    ]
    failed = [n for n, refused in cases if not refused]
    for n, refused in cases: print(f"  control {'ok' if refused else 'NOT REFUSED'}: {n}")
    return failed

def main():
    root = Path(__file__).resolve().parent.parent
    bands, languages, texts = load(root)
    found = problems(bands, languages, texts)
    for p in found: print(f"FAIL {p}")
    if found: return 1
    print(f"bands: {len(bands['bands'])}, languages: {', '.join(languages['languages'])} — whole")
    if "--controls" in sys.argv and controls(bands, languages, texts): print("FAIL a control was not refused"); return 1
    return 0

sys.exit(main())
