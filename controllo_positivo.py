#!/usr/bin/env python3
"""Positive control of the tests themselves: each mutant below is one of the scripts with one rule switched off; the
unit tests must then fail. A mutant that survives is a rule no test protects. Offline, standard library; works on
temporary copies, writes nothing here.

    python3 controllo_positivo.py        # prints `mutanti=46 uccisi=46 sopravvissuti=0`, exit 0; exit 1 if one survives

The unmutated copy is run first: if the tests do not pass on it, «killed» would mean nothing, and the run stops (exit 2)."""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_FILES = ("check_profile.py", "check_versions.py", "test_check_profile.py", "README.md", "TRACK_RECORD.md",
              os.path.join("testdata", "README.md"), os.path.join("testdata", "TRACK_RECORD.md"))

PROFILO = [
 ("check_profile.py", 'state = "verified" if said == counted else "contradicted"', 'state = "verified"'),
 ("check_profile.py", 'state = "not_evaluated"\n        else:\n            state = "verified" if', 'state = "verified"\n        else:\n            state = "verified" if'),
 ("check_profile.py", 'return 1 if bad else (2 if lost else 0)', 'return 1 if bad else 0'),
 ("check_profile.py", 'return 1 if bad else (2 if lost else 0)', 'return 2 if lost else (1 if bad else 0)'),
 ("check_profile.py", 'p in by_repo and ("`pip install %s`" % p) in by_repo[p]["latest"]', 'p in by_repo'),
 ("check_profile.py", 'if p in by_repo and', 'if'),
 ("check_profile.py", 'int(m.group(2)) + int(m.group(3)) if m else None', 'int(m.group(1)) if m else None'),
 ("check_profile.py", 'if t.startswith("IETF Internet-Draft")]', 'if "Internet-Draft" in t]'),
 ("check_profile.py", 'prs = set(re.findall(', 'prs = list(re.findall('),
 ("check_profile.py", 'add("conformance-suite entries in TRACK_RECORD all named in the README", len(titles), len(named))', 'add("conformance-suite entries in TRACK_RECORD all named in the README", len(named), len(named))'),
 ("check_profile.py", 'found = [x for x in named if any(t.startswith(x) for t in titles)]\n        add("named upstream', 'found = named\n        add("named upstream'),
 ("check_profile.py", 'elif len(have) > said or len(have) + len(absent) < said:', 'elif len(have) + len(absent) < said:'),
 ("check_profile.py", 'elif not absent and len(have) == said:', 'elif len(have) == said:'),
 ("check_profile.py", 'and any(f.startswith("differential") for f in os.listdir(v)) \\\n', '\\\n'),
 ("check_profile.py", '(r["repo"],) + ALIASES.get(r["repo"], ())', '(r["repo"],)'),
 ("check_profile.py", 'number(t.group(1)) if t else None)', 'number(m.group(1)) if m else None)'),
 ("check_versions.py", '                if LINKED.match(line):\n                    bad += 1', '                if LINKED.match(line):\n                    bad += 0'),
 ("check_versions.py", '    if not rows:\n        bad += 1', '    if not rows:\n        bad += 0'),
 ("check_versions.py", 'bad += 0 if ok else 1', 'bad += 0'),
 ("check_profile.py", 'start = [pip_name(a) for a in re.findall(r"^pip install (.*)$", readme, re.M)]', 'start = re.findall(r"^pip install ([A-Za-z0-9_.-]+)", readme, re.M)'),
 ("check_profile.py", 'start = [pip_name(a) for a in re.findall(r"^pip install (.*)$", readme, re.M)]', 'start = [p for p in map(pip_name, re.findall(r"^pip install (.*)$", readme, re.M)) if p]'),
 ("check_profile.py", 'm = PIP.fullmatch(arg.rstrip())', 'm = PIP.match(arg.rstrip())'),
 ("check_profile.py", 'return (m.group("q") or m.group("n")) if m else None', 'return m.group("n") if m else None'),
 ("check_profile.py", ' @ [^"\\s]+"|', ' @ [^"]*"|'),
 ("check_profile.py", 'return int(word) if word.isdigit() else WORDS.get(word)', 'return WORDS.get(word)'),
 ("check_profile.py", 'elif out[name]["bullets"] and line.strip():', 'elif False:'),
 ("check_profile.py", r'\[DOI\]\(https://doi\.org/10\.\d+/zenodo\.\d+\)', r'\[DOI\]'),
 ("check_profile.py", 'and any(os.path.isdir(os.path.join(v, f)) for f in os.listdir(v))', ''),
 ("check_profile.py", 'if said is None:\n            d["state"] = "not_evaluated"\n        elif', 'if False:\n            pass\n        elif'),
 ("check_profile.py", 'os.path.join(os.path.dirname(readme_path), "TRACK_RECORD.md")', '"TRACK_RECORD.md"'),
 ("check_profile.py", '" ".join(track.split()))', 'track)'),
 ("check_profile.py", '"`pip install %s`" % p', '"pip install %s" % p'),
 ("check_profile.py", 'number(m2.group("all") or m2.group("k"))', 'number(m2.group("all") or m2.group("m"))'),
 ("check_profile.py", 'number(m2.group("all") or m2.group("m"))', 'number(m2.group("all") or m2.group("k"))'),
 ("check_versions.py", 'ok = name in EXCLUDED', 'ok = True'),
 ("check_versions.py", 'if not fork and has_release(n)', 'if has_release(n)'),
 ("check_versions.py", 'if name in table or name not in released:', 'if name in table:'),
 ("check_versions.py", 'if name in table or name not in released:', 'if name not in released:'),
 ("check_versions.py", 'if not table or any(', 'if any('),
 ("check_versions.py", 'any(LINKED.match(l) and not ROW.match(l) for l in lines)', 'False'),
 ("check_versions.py", 'if "HTTP 404" in r.stderr:', 'if True:'),
 ("check_versions.py", 'return [(n, f == "true") for n, f in', 'return [(n, f == "True") for n, f in'),
 ("check_versions.py", '["gh", "api", "--paginate", f"users', '["gh", "api", f"users'),
 ("check_versions.py", 'capture_output=True, text=True, check=True).stdout\n    return [(n, f', 'capture_output=True, text=True).stdout\n    return [(n, f'),
 ("check_versions.py", 'return 1 if bad else 0\n\n\nif __name__', 'return 0\n\n\nif __name__'),
 ("check_versions.py", '"--missing": missing,', '"--missing": main,'),
]

def run(files, src, module, target=None, old=None, new=None):
    d = tempfile.mkdtemp()
    try:
        for n in files:
            os.makedirs(os.path.dirname(os.path.join(d, n)), exist_ok=True)
            shutil.copy(os.path.join(src, n), os.path.join(d, n))
        if target:
            p = os.path.join(d, target)
            with open(p, encoding="utf-8") as fh:
                s = fh.read()
            if old not in s:
                return None                      # the mutant no longer applies: counted as a failure of this script
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(s.replace(old, new, 1))
        r = subprocess.run([sys.executable, "-B", "-m", "unittest", module], cwd=d, capture_output=True, text=True)
        return r.returncode != 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    if run(ROOT_FILES, HERE, "test_check_profile"):
        print("the tests fail on the unmutated scripts: nothing measured")
        return 2
    total = killed = 0
    bad = []
    for target, old, new in PROFILO:
        total += 1
        k = run(ROOT_FILES, HERE, "test_check_profile", target, old, new)
        killed += 1 if k else 0
        if not k:
            bad.append((target, new[:70], "not applicable" if k is None else "survived"))
    for b in bad:
        print("NOT KILLED:", b)
    print("mutanti=%d uccisi=%d sopravvissuti=%d" % (total, killed, total - killed))
    return 0 if killed == total else 1


if __name__ == "__main__":
    sys.exit(main())
