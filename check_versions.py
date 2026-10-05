#!/usr/bin/env python3
"""Profile README (robertolocatelli81-dev): the version column of the project table must equal each repository's
newest release tag. Run by .github/workflows/versions.yml on every change and every Monday (`python3 check_versions.py
README.md`, with `gh` logged in or GH_TOKEN set); exit 1 on any mismatch. Found on 2026-10-05: ap2-evidence-pack 1.2.2 in the table,
v1.3.0 released. Read-only; no write anywhere."""
import json
import re
import subprocess
import sys

OWNER = "robertolocatelli81-dev"
ROW = re.compile(r"^\| \[(?P<repo>[A-Za-z0-9_.-]+)\]\(https://github\.com/" + OWNER + r"/(?P=repo)\) \|.*\| (?P<ver>\d+\.\d+\.\d+)( ·|\s*\|)")


def latest_tag(repo: str) -> str:
    out = subprocess.run(["gh", "api", f"repos/{OWNER}/{repo}/releases/latest", "-q", ".tag_name"],
                         capture_output=True, text=True, check=True).stdout.strip()
    return out[1:] if out.startswith("v") else out


def main(path: str) -> int:
    bad = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = ROW.match(line)
            if not m:
                continue
            repo, ver = m.group("repo"), m.group("ver")
            tag = latest_tag(repo)
            ok = tag == ver
            bad += 0 if ok else 1
            print(json.dumps({"repo": repo, "table": ver, "latest_release": tag, "ok": ok}))
    print("mismatches:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "README.md"))
