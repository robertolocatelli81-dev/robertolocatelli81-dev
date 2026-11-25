#!/usr/bin/env python3
"""Profile README (robertolocatelli81-dev): the version column of the project table must equal each repository's
newest release tag. Run by .github/workflows/versions.yml on every change and every Monday (`python3 check_versions.py
README.md`, with `gh` logged in or GH_TOKEN set); exit 1 on any mismatch. Found on 2026-10-05: ap2-evidence-pack 1.2.2 in the table,
v1.3.0 released. A table row that links a repository of this account and whose version this script cannot read is a
mismatch too, and so is a table with no row at all: before 2026-11-16 such a row was skipped in silence and the run
said `mismatches: 0` (measured: test_check_profile.py, class CheckVersions). Read-only, unless `--write` is given
(update(), below): then the version column of the file is rewritten. `--missing` (missing(), below) checks the other
direction: every public repository of this account with a release is a row of the table or is in EXCLUDED."""
import json
import re
import subprocess
import sys

OWNER = "robertolocatelli81-dev"
LINKED = re.compile(r"^\| \[[^\]]+\]\(https://github\.com/" + re.escape(OWNER) + r"/")
ROW = re.compile(r"^\| \[(?P<repo>[A-Za-z0-9_.-]+)\]\(https://github\.com/" + OWNER + r"/(?P=repo)\) \|.*\| (?P<ver>\d+\.\d+\.\d+)( ·|\s*\|)")


# Public repositories of this account that have a release and are, on purpose, not rows of the table: name -> reason.
# A repository that is in neither the table nor this list makes `--missing` fail with its name (2026-11-25: three
# projects with public releases, agent-payment-chain, pq-scitt and work-acceptance-check-omega, had never been added).
EXCLUDED = {
    "aee-verifier": "row added with 0.3.0, which follows the agent-evidence-vectors 0.38.0 verdict contract "
                    "(measured 2026-11-25: 0.2.0 reads 0/288 as is)",
    "omega-rwawatch": "a monitor of public data, not a verifier package; listed in TRACK_RECORD if others use it",
}


def public_repos():
    """[(name, is_fork)] of the public repositories of this account (the users/ endpoint lists public ones only)."""
    out = subprocess.run(["gh", "api", "--paginate", f"users/{OWNER}/repos?type=owner&per_page=100", "-q",
                          ".[] | [.name, .fork] | @tsv"], capture_output=True, text=True, check=True).stdout
    return [(n, f == "true") for n, f in (l.split("\t") for l in out.splitlines())]


def has_release(repo: str) -> bool:
    """True if the repository has a published release that is not a pre-release; any error other than 404 is raised."""
    r = subprocess.run(["gh", "api", f"repos/{OWNER}/{repo}/releases/latest", "-q", ".tag_name"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        return True
    if "HTTP 404" in r.stderr:
        return False
    raise RuntimeError(f"{repo}: {r.stderr.strip()}")


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


def missing(path: str) -> int:
    """--missing (2026-11-25): exit 1, with the name, for a public repository of this account that has a release and is
    neither a table row nor in EXCLUDED; also for an EXCLUDED name that is a row too, or that no longer is a public
    repository with a release (a stale exclusion). Forks are skipped: they are other people's projects."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    table = {m.group("repo") for m in map(ROW.match, lines) if m}
    bad = 0
    if not table or any(LINKED.match(l) and not ROW.match(l) for l in lines):
        print(json.dumps({"ok": False, "why": "the table cannot be read in full: nothing was checked"}))
        return 1
    released = {n for n, fork in public_repos() if not fork and has_release(n)}
    for name in sorted(released - table):
        ok = name in EXCLUDED
        bad += 0 if ok else 1
        print(json.dumps({"repo": name, "ok": ok, "why": "excluded: " + EXCLUDED[name] if ok else
                          "public repository with a release, neither a row of the table nor in EXCLUDED"}))
    for name in sorted(EXCLUDED):
        if name in table or name not in released:
            bad += 1
            print(json.dumps({"repo": name, "ok": False, "why": "in EXCLUDED but " + (
                "also a row of the table" if name in table else "not a public repository with a release")}))
    print("rows:", len(table), "public repositories with a release:", len(released))
    print("missing:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    mode = args[0] if args[:1] in (["--write"], ["--missing"]) else None
    rest = args[1:] if mode else args
    if len(rest) > 1 or any(a.startswith("-") for a in rest):   # an argument that is not understood is an error
        sys.exit("usage: check_versions.py [--write | --missing] [README.md]")
    sys.exit({"--write": update, "--missing": missing, None: main}[mode](rest[0] if rest else "README.md"))
