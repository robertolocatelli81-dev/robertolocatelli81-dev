#!/usr/bin/env python3
"""Profile README (robertolocatelli81-dev): the version column of the project table must equal each repository's
newest release tag. Run by .github/workflows/versions.yml on every change and every Monday (`python3 check_versions.py
README.md`, with `gh` logged in or GH_TOKEN set); exit 1 on any mismatch. Found on 2026-10-05: ap2-evidence-pack 1.2.2 in the table,
v1.3.0 released. A table row that links a repository of this account and whose version this script cannot read is a
mismatch too, and so is a table with no row at all: before 2026-11-16 such a row was skipped in silence and the run
said `mismatches: 0` (measured: test_check_profile.py, class CheckVersions). Read-only, unless `--write` is given
(update(), below): then the version column of the file is rewritten."""
import json
import re
import subprocess
import sys

OWNER = "robertolocatelli81-dev"
LINKED = re.compile(r"^\| \[[^\]]+\]\(https://github\.com/" + re.escape(OWNER) + r"/")
ROW = re.compile(r"^\| \[(?P<repo>[A-Za-z0-9_.-]+)\]\(https://github\.com/" + OWNER + r"/(?P=repo)\) \|.*\| (?P<ver>\d+\.\d+\.\d+)( ·|\s*\|)")


def latest_tag(repo: str) -> str:
    out = subprocess.run(["gh", "api", f"repos/{OWNER}/{repo}/releases/latest", "-q", ".tag_name"],
                         capture_output=True, text=True, check=True).stdout.strip()
    return out[1:] if out.startswith("v") else out


def main(path: str) -> int:
    bad = rows = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = ROW.match(line)
            if not m:
                if LINKED.match(line):
                    bad += 1
                    print(json.dumps({"row": line.strip()[:120], "ok": False, "why": "version not readable in this row"}))
                continue
            rows += 1
            repo, ver = m.group("repo"), m.group("ver")
            tag = latest_tag(repo)
            ok = tag == ver
            bad += 0 if ok else 1
            print(json.dumps({"repo": repo, "table": ver, "latest_release": tag, "ok": ok}))
    if not rows:
        bad += 1
        print(json.dumps({"ok": False, "why": "no table row read: nothing was checked"}))
    print("rows:", rows)
    print("mismatches:", bad)
    return 1 if bad else 0


SEMVER = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")   # ASCII digits only: \d also matches ١, １


def update(path: str) -> int:
    """--write (2026-11-23): sets the version column of each table row to the newest release, and nothing else (the
    descriptions are claims and stay with a person). Exit 0 with or without a change; exit 1, file untouched, when a
    row cannot be read or a release tag is not X.Y.Z."""
    with open(path, encoding="utf-8", newline="") as fh:   # newline="": line endings are kept as they are
        lines = fh.readlines()
    out, changed, rows = [], [], 0
    for line in lines:
        m = ROW.match(line)
        if not m:
            if LINKED.match(line):
                print(json.dumps({"row": line.strip()[:120], "ok": False, "why": "version not readable in this row"}))
                return 1
            out.append(line)
            continue
        rows += 1
        tag = latest_tag(m.group("repo"))
        if not SEMVER.match(tag):
            print(json.dumps({"repo": m.group("repo"), "ok": False, "why": f"release tag {tag!r} is not X.Y.Z"}))
            return 1
        if tag != m.group("ver"):
            line = line[:m.start("ver")] + tag + line[m.end("ver"):]
            changed.append(f"{m.group('repo')} {m.group('ver')} -> {tag}")
        out.append(line)
    if not rows:
        print(json.dumps({"ok": False, "why": "no table row read: nothing was updated"}))
        return 1
    if changed:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.writelines(out)
    print("rows:", rows)
    print("changed:", "; ".join(changed) if changed else "none")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    write = args[:1] == ["--write"]
    rest = args[1:] if write else args
    if len(rest) > 1 or any(a.startswith("-") for a in rest):   # an argument that is not understood is an error
        sys.exit("usage: check_versions.py [--write] [README.md]")
    sys.exit((update if write else main)(rest[0] if rest else "README.md"))
