#!/usr/bin/env python3
"""Profile README (robertolocatelli81-dev): the numbers and names the prose states must agree with the project table
and with TRACK_RECORD.md. Offline, standard library only, read-only.

    python3 check_profile.py [README.md [TRACK_RECORD.md]] [--corpus DIR]

One JSON line per claim, state in a closed vocabulary:
  verified       the text and the count agree
  contradicted   they do not (exit 1)
  not_evaluated  the sentence the check looks for is not there any more (exit 2: the check no longer covers the page,
                 which is a failure of the check, not a pass), or the claim needs --corpus and none was given (exit
                 unchanged: it is listed, never counted as verified)
Exit 3: a usage error (missing or unreadable file, --corpus without an existing directory): nothing was checked.

What it does NOT check: that a version is the newest release (check_versions.py, needs the network), that a quote in
TRACK_RECORD.md is still in its source, that a DOI resolves. --corpus DIR (local checkouts, one directory per
repository) adds the count of projects that carry a `verifiers/` directory with a differential oracle."""
import json
import os
import re
import sys

OWNER = "robertolocatelli81-dev"
WORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve".split())}
ROW = re.compile(r"^\| \[(?P<repo>[A-Za-z0-9_.-]+)\]\(https://github\.com/" + OWNER + r"/(?P=repo)\) \|(?P<what>.*)\|(?P<latest>[^|]*)\|\s*$")
# a repository renamed after the local checkout was taken: table name -> older directory name
ALIASES = {"omega-cra-evol": ("cra-evidence",)}


def number(word):
    word = word.lower()
    return int(word) if word.isdigit() else WORDS.get(word)


PIP = re.compile(r'(?:"(?P<q>[A-Za-z0-9_.-]+) @ [^"\s]+"|(?P<n>[A-Za-z0-9_.-]+))(?:\s+#.*)?')


def pip_name(arg):
    """'X   # comment' or '"X @ URL"   # comment' -> 'X'; anything else (two packages, extras, a version) -> None"""
    m = PIP.fullmatch(arg.rstrip())
    return (m.group("q") or m.group("n")) if m else None


def rows(readme):
    out = []
    for line in readme.splitlines():
        m = ROW.match(line)
        if m:
            out.append({"repo": m.group("repo"), "what": m.group("what"), "latest": m.group("latest")})
    return out


def sections(track):
    """{'Named in specifications': [bullet, ...], ...}; a bullet is the text from '- ' to the next bullet or heading."""
    out, name = {}, None
    for line in track.splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            out[name] = {"bullets": [], "text": ""}
        elif name is not None:
            out[name]["text"] += line + "\n"
            if line.startswith("- "):
                out[name]["bullets"].append(line[2:])
            elif out[name]["bullets"] and line.strip():
                out[name]["bullets"][-1] += " " + line.strip()
    return out


def bold_titles(bullets):
    return [m.group(1) for b in bullets for m in [re.match(r"\*\*(.+?)\*\*", b)] if m]


def names_list(text):
    """'Tersign, Verax, APS and ScopeBlind' -> ['Tersign', 'Verax', 'APS', 'ScopeBlind']"""
    return [n.strip() for n in re.split(r",| and ", text) if n.strip()]


def claims(readme, track, corpus=None):
    """List of dicts {claim, state, said, counted, required}. `required` False only for the corpus claim."""
    flat = " ".join(readme.split())
    table = rows(readme)
    n = len(table)
    sec = sections(track)
    out = []

    def add(claim, said, counted, required=True, note=None):
        if said is None:
            state = "not_evaluated"
        else:
            state = "verified" if said == counted else "contradicted"
        d = {"claim": claim, "state": state, "said": said, "counted": counted, "required": required}
        if note:
            d["note"] = note
        out.append(d)

    # 1. «N of the M projects», «all M carry a Zenodo DOI» or «K of the M carry a Zenodo DOI»: M is the number of table
    # rows, and K (M after «all») the number of rows with a Zenodo DOI link
    m = re.search(r"(\w+) of the (\w+) projects add independent verifiers", flat)
    add("of-the-M-projects equals table rows", number(m.group(2)) if m else None, n)
    m2 = re.search(r"(?:all (?P<all>\w+)|(?P<k>\w+) of the (?P<m>\w+)) carry a Zenodo DOI", flat)
    add("DOI sentence: M equals table rows", number(m2.group("all") or m2.group("m")) if m2 else None, n)
    with_doi = sum(1 for r in table if re.search(r"\[DOI\]\(https://doi\.org/10\.\d+/zenodo\.\d+\)", r["latest"]))
    add("rows with a Zenodo DOI link", number(m2.group("all") or m2.group("k")) if m2 else None, with_doi)

    # 2. «Start here»: every `pip install …` line names a table row whose Latest cell says `pip install X`. Two forms
    # are read, `pip install X` and `pip install "X @ URL"`; any other line is counted and never matched (not skipped)
    start = [pip_name(a) for a in re.findall(r"^pip install (.*)$", readme, re.M)]
    by_repo = {r["repo"]: r for r in table}
    ok = [p for p in start if p in by_repo and ("`pip install %s`" % p) in by_repo[p]["latest"]]
    add("Start-here packages that are table rows marked pip-installable", len(start) if start else None, len(ok),
        note=None if len(ok) == len(start) else "not matched: %s" % sorted(set(p or "<line not read>" for p in start) - set(ok)))

    # 3. x402 row: «T vectors (A accept, R reject)»
    m = re.search(r"(\d+) vectors \((\d+) accept, (\d+) reject\)", flat)
    add("vector total equals accept + reject", int(m.group(1)) if m else None, int(m.group(2)) + int(m.group(3)) if m else None)

    # 4. «N IETF Internet-Drafts» = bullets titled IETF Internet-Draft under «Named in specifications»
    m = re.search(r"(\w+) IETF Internet-Drafts", flat)
    drafts = [t for t in bold_titles(sec.get("Named in specifications", {}).get("bullets", [])) if t.startswith("IETF Internet-Draft")]
    add("IETF Internet-Drafts in TRACK_RECORD", number(m.group(1)) if m else None, len(drafts))

    # 5. named conformance suites: each is the title of a bullet under «Credited in conformance suites»
    m = re.search(r"the ([A-Za-z, ]+?) conformance suites", flat)
    titles = bold_titles(sec.get("Credited in conformance suites", {}).get("bullets", []))
    if m:
        named = names_list(m.group(1))
        found = [x for x in named if any(t.startswith(x) for t in titles)]
        add("named conformance suites present in TRACK_RECORD", len(named), len(found),
            note=None if len(found) == len(named) else "missing: %s" % sorted(set(named) - set(found)))
        add("conformance-suite entries in TRACK_RECORD all named in the README", len(titles), len(named))
    else:
        add("named conformance suites present in TRACK_RECORD", None, len(titles))

    # 6. «fixes made upstream at A, B, C and D»: each is the title of a bullet under «Fixes made upstream…»
    m = re.search(r"fixes made upstream at ([A-Za-z, ]+?) from my reports", flat)
    key = next((k for k in sec if k.startswith("Fixes made upstream")), None)
    titles = bold_titles(sec[key]["bullets"]) if key else []
    if m:
        named = names_list(m.group(1))
        found = [x for x in named if any(t.startswith(x) for t in titles)]
        add("named upstream fixes present in TRACK_RECORD", len(named), len(found),
            note=None if len(found) == len(named) else "missing: %s" % sorted(set(named) - set(found)))
    else:
        add("named upstream fixes present in TRACK_RECORD", None, len(titles))

    # 7. «N pull requests of mine merged» = distinct pull-request URLs under «Pull requests merged…»
    m = re.search(r"(\w+) pull requests of mine merged", flat)
    key = next((k for k in sec if k.startswith("Pull requests merged")), None)
    prs = set(re.findall(r"https://github\.com/[^/\s)]+/[^/\s)]+/pull/\d+", sec[key]["text"])) if key else set()
    add("merged pull requests listed in TRACK_RECORD", number(m.group(1)) if m else None, len(prs))

    # 8. «one of the N implementations ScopeBlind lists as conformant» = «one of N implementations so marked»
    m = re.search(r"one of the (\w+) implementations ScopeBlind lists as conformant", flat)
    t = re.search(r"one of (\w+) implementations so marked", " ".join(track.split()))
    add("ScopeBlind conformant implementations, README equals TRACK_RECORD", number(m.group(1)) if m else None,
        number(t.group(1)) if t else None)

    # 9. needs local checkouts: «N of the M projects add independent verifiers … checked by a differential oracle»
    m = re.search(r"(\w+) of the (\w+) projects add independent verifiers", flat)
    if corpus is None:
        out.append({"claim": "projects with verifiers/ and a differential oracle (needs --corpus)", "state": "not_evaluated",
                    "said": number(m.group(1)) if m else None, "counted": None, "required": False})
    else:
        have, absent = [], []
        for r in table:
            d = next((os.path.join(corpus, x) for x in (r["repo"],) + ALIASES.get(r["repo"], ()) if os.path.isdir(os.path.join(corpus, x))), None)
            if d is None:
                absent.append(r["repo"])
                continue
            v = os.path.join(d, "verifiers")
            if os.path.isdir(v) and any(f.startswith("differential") for f in os.listdir(v)) \
                    and any(os.path.isdir(os.path.join(v, f)) for f in os.listdir(v)):
                have.append(r["repo"])
        said = number(m.group(1)) if m else None
        d = {"claim": "projects with verifiers/ and a differential oracle (local checkouts)", "said": said,
             "counted": len(have), "required": False, "have": have, "checkout_absent": absent}
        # an absent checkout could add to the count: only «counted == said with nothing absent» is verified, and
        # only «counted + absent < said» or «counted > said» is contradicted
        if said is None:
            d["state"] = "not_evaluated"
        elif len(have) > said or len(have) + len(absent) < said:
            d["state"] = "contradicted"
        elif not absent and len(have) == said:
            d["state"] = "verified"
        else:
            d["state"] = "not_evaluated"
        out.append(d)
    return out


def usage(why):
    print("usage error (exit 3, nothing was checked): %s" % why, file=sys.stderr)
    return 3


def main(argv):
    corpus = None
    if argv.count("--corpus") > 1:
        return usage("--corpus given more than once")
    if "--corpus" in argv:
        i = argv.index("--corpus")
        if i + 1 >= len(argv) or not os.path.isdir(argv[i + 1]):
            return usage("--corpus needs an existing directory")
        corpus = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if len(argv) > 2 or any(a.startswith("-") for a in argv):
        return usage("unexpected arguments: %s" % argv)
    readme_path = argv[0] if argv else "README.md"
    track_path = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(readme_path), "TRACK_RECORD.md")
    try:
        with open(readme_path, encoding="utf-8") as fh:
            readme = fh.read()
        with open(track_path, encoding="utf-8") as fh:
            track = fh.read()
    except (OSError, UnicodeDecodeError) as e:
        return usage("%s: %s" % (type(e).__name__, e))
    res = claims(readme, track, corpus)
    for d in res:
        print(json.dumps(d, ensure_ascii=False))
    bad = sum(1 for d in res if d["state"] == "contradicted")
    lost = sum(1 for d in res if d["state"] == "not_evaluated" and d["required"])
    print("verified: %d  contradicted: %d  not_evaluated: %d (of which the check lost its sentence: %d)" % (
        sum(1 for d in res if d["state"] == "verified"), bad, sum(1 for d in res if d["state"] == "not_evaluated"), lost))
    return 1 if bad else (2 if lost else 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
