#!/usr/bin/env python3
"""Tests of check_profile.py and check_versions.py: offline, standard library only (`python3 -m unittest -v`).
Every check has its positive control: the same page with one thing changed must come out `contradicted` (or, when the
sentence itself is gone, `not_evaluated` with exit 2). A check that cannot fail is not a check.

The positive controls run on a frozen copy of the page (testdata/), so that editing the live README (a new version in
the table, a reworded sentence) cannot break them; only ThePageAsItIs reads the live README.md and TRACK_RECORD.md."""
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest

import check_profile
import check_versions

HERE = os.path.dirname(os.path.abspath(__file__))


def read(*name):
    with open(os.path.join(HERE, *name), encoding="utf-8") as fh:
        return fh.read()


README, TRACK = read("testdata", "README.md"), read("testdata", "TRACK_RECORD.md")
LIVE_README, LIVE_TRACK = read("README.md"), read("TRACK_RECORD.md")


def states(readme=README, track=TRACK, corpus=None):
    return {d["claim"]: d["state"] for d in check_profile.claims(readme, track, corpus)}


def swap(text, old, new, count=1):
    assert old in text, "the mutant no longer applies: %r is not in the page" % old
    return text.replace(old, new, count)


def drop_line(text, starts):
    lines = text.splitlines(keepends=True)
    kept = [l for l in lines if not l.startswith(starts)]
    assert len(kept) == len(lines) - 1, "the mutant must remove exactly one line starting with %r" % starts
    return "".join(kept)


class ThePageAsItIs(unittest.TestCase):
    def test_every_required_claim_is_verified(self):
        res = check_profile.claims(LIVE_README, LIVE_TRACK)
        self.assertEqual([d for d in res if d["required"] and d["state"] != "verified"], [])
        self.assertGreaterEqual(sum(1 for d in res if d["required"]), 11)

    def test_exit_code_zero_on_the_real_files(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_profile.main([os.path.join(HERE, "README.md")]), 0)

    def test_without_corpus_the_verifier_count_is_not_evaluated_never_verified(self):
        res = [d for d in check_profile.claims(LIVE_README, LIVE_TRACK) if not d["required"]]
        self.assertEqual([d["state"] for d in res], ["not_evaluated"])

    def test_the_frozen_copy_is_verified_too(self):
        res = check_profile.claims(README, TRACK)
        self.assertEqual([d for d in res if d["required"] and d["state"] != "verified"], [])


class PositiveControls(unittest.TestCase):
    """One change each; the named claim must turn `contradicted` and every other required claim must stay verified
    unless listed in `also`."""

    def only(self, st, claim, also=()):
        self.assertEqual(st[claim], "contradicted", claim)
        for k, v in st.items():
            if k != claim and k not in also and "needs --corpus" not in k:
                self.assertEqual(v, "verified", k)

    def test_a_row_removed(self):
        st = states(drop_line(README, "| [omega-evidence]"))
        self.assertEqual(st["of-the-M-projects equals table rows"], "contradicted")
        self.assertEqual(st["DOI sentence: M equals table rows"], "contradicted")
        self.assertEqual(st["rows with a Zenodo DOI link"], "contradicted")

    def test_a_doi_removed_from_one_row(self):
        st = states(swap(README, " · [DOI](https://doi.org/10.5281/zenodo.22539633)", ""))
        self.only(st, "rows with a Zenodo DOI link")

    def test_prose_says_eight_projects(self):
        st = states(swap(README, "all seven carry", "all eight carry"))
        self.only(st, "DOI sentence: M equals table rows", also=("rows with a Zenodo DOI link",))
        self.assertEqual(st["rows with a Zenodo DOI link"], "contradicted")

    def test_the_k_of_m_form_of_the_doi_sentence(self):
        # «K of the M carry a Zenodo DOI» (2026-11-25, when three rows without a DOI came in): M against the rows,
        # K against the rows with a DOI link; the frozen page has seven rows, all with a DOI
        self.assertEqual(states(swap(README, "all seven carry", "seven of the seven carry"))["rows with a Zenodo DOI link"],
                         "verified")
        self.only(states(swap(README, "all seven carry", "six of the seven carry")), "rows with a Zenodo DOI link")
        self.only(states(swap(README, "all seven carry", "seven of the eight carry")), "DOI sentence: M equals table rows")
        st = states(swap(swap(README, "all seven carry", "six of the seven carry"),
                         " · [DOI](https://doi.org/10.5281/zenodo.22539633)", ""))
        self.assertEqual(st["rows with a Zenodo DOI link"], "verified")

    def test_start_here_names_a_package_that_is_not_a_row(self):
        st = states(swap(README, "pip install rigorous-levels        #", "pip install rigorous-level         #"))
        self.only(st, "Start-here packages that are table rows marked pip-installable")

    def test_start_here_line_that_cannot_be_read_is_not_skipped(self):
        # two packages on one line: neither is read, so the line is not matched (before 2026-11-16 it was skipped)
        st = states(swap(README, "pip install rigorous-levels        #", "pip install rigorous-levels numpy  #"))
        self.only(st, "Start-here packages that are table rows marked pip-installable")

    def test_start_here_pinned_url_form_is_read(self):
        url = '"rigorous-levels @ https://example.org/rigorous_levels-0.3.0-py3-none-any.whl#sha256=00"'
        self.assertEqual(states(swap(README, "pip install rigorous-levels        #", "pip install %s   #" % url))[
            "Start-here packages that are table rows marked pip-installable"], "verified")
        st = states(swap(README, "pip install rigorous-levels        #", "pip install %s   #" % url.replace("rigorous-levels @", "rigorous-level @")))
        self.only(st, "Start-here packages that are table rows marked pip-installable")

    def test_pip_lines_that_are_not_read(self):
        for arg in ('"x @ "', '"x @ a b"', "x y", "x[e]", "x==1", "-r req.txt", "  x", '"x@https://a"'):
            self.assertIsNone(check_profile.pip_name(arg), arg)
        for arg, name in (("x", "x"), ("x   # c", "x"), ('"x @ https://a/b.whl#sha256=00"  # c', "x")):
            self.assertEqual(check_profile.pip_name(arg), name, arg)

    def test_numbers_written_as_digits_are_read(self):
        self.assertEqual(check_profile.number("7"), 7)
        st = states(swap(README, "all seven carry", "all 7 carry"))
        self.assertEqual(st["DOI sentence: M equals table rows"], "verified")

    def test_a_doi_link_that_is_not_zenodo_does_not_count(self):
        st = states(swap(README, "https://doi.org/10.5281/zenodo.22539633", "https://example.org/doi"))
        self.only(st, "rows with a Zenodo DOI link")

    def test_a_pip_marker_without_backticks_does_not_count(self):
        st = states(swap(README, " · `pip install rigorous-levels` |", " · pip install rigorous-levels |"))
        self.only(st, "Start-here packages that are table rows marked pip-installable")

    def test_wrapped_lines_in_the_track_record_are_read(self):
        # the ScopeBlind sentence and a bold draft title broken across two lines are still found
        track = swap(TRACK, "one of four implementations so marked", "one of four\n  implementations so marked")
        track = swap(track, "- **IETF Internet-Draft `draft-sansone", "- **IETF Internet-Draft\n  `draft-sansone")
        st = states(track=track)
        self.assertEqual(st["ScopeBlind conformant implementations, README equals TRACK_RECORD"], "verified")
        self.assertEqual(st["IETF Internet-Drafts in TRACK_RECORD"], "verified")

    def test_start_here_names_a_row_without_the_pip_marker(self):
        # the page as it was at a0b2a03 (found by this check on 2026-11-16): rigorous-levels in «Start here», no
        # `pip install` in its row
        st = states(swap(README, " · `pip install rigorous-levels` |", " |"))
        self.only(st, "Start-here packages that are table rows marked pip-installable")

    def test_vector_counts_do_not_add_up(self):
        st = states(swap(README, "84 vectors (34 accept", "84 vectors (35 accept"))
        self.only(st, "vector total equals accept + reject")

    def test_a_fourth_draft_claimed(self):
        st = states(swap(README, "three IETF Internet-Drafts", "four IETF Internet-Drafts"))
        self.only(st, "IETF Internet-Drafts in TRACK_RECORD")

    def test_a_draft_removed_from_the_track_record(self):
        st = states(track=swap(TRACK, "- **IETF Internet-Draft `draft-sansone", "- **Internet-Draft `draft-sansone"))
        self.only(st, "IETF Internet-Drafts in TRACK_RECORD")

    def test_a_suite_named_that_the_track_record_does_not_have(self):
        st = states(swap(README, "the Tersign, Verax, APS and ScopeBlind", "the Tersign, Verax, APS and Sigstore"))
        self.only(st, "named conformance suites present in TRACK_RECORD")

    def test_a_suite_in_the_track_record_not_named_in_the_readme(self):
        st = states(swap(README, "the Tersign, Verax, APS and ScopeBlind", "the Tersign, Verax and ScopeBlind"))
        self.only(st, "conformance-suite entries in TRACK_RECORD all named in the README")

    def test_an_upstream_fix_named_that_the_track_record_does_not_have(self):
        st = states(swap(README, "Microsoft, Google, Cloudflare and DCMTK", "Microsoft, Google, Cloudflare and Mozilla"))
        self.only(st, "named upstream fixes present in TRACK_RECORD")

    def test_a_pull_request_removed(self):
        st = states(track=drop_line(TRACK, "[SynapseKit/SynapseKit#1077]"))
        self.only(st, "merged pull requests listed in TRACK_RECORD")

    def test_a_pull_request_listed_twice_counts_once(self):
        line = "[x402-foundation/x402#3965](https://github.com/x402-foundation/x402/pull/3965) (specification),\n"
        st = states(track=swap(TRACK, line, line + line))
        self.assertEqual(st["merged pull requests listed in TRACK_RECORD"], "verified")

    def test_eight_pull_requests_claimed(self):
        st = states(swap(README, "plus seven pull", "plus eight pull"))
        self.only(st, "merged pull requests listed in TRACK_RECORD")

    def test_scopeblind_counts_differ(self):
        st = states(swap(README, "one of the four implementations", "one of the five implementations"))
        self.only(st, "ScopeBlind conformant implementations, README equals TRACK_RECORD")


class ASentenceThatDisappears(unittest.TestCase):
    def test_reworded_sentence_is_not_evaluated_and_the_run_exits_2(self):
        readme = swap(README, "all seven carry a Zenodo DOI", "each one has a Zenodo DOI")
        self.assertEqual(states(readme)["DOI sentence: M equals table rows"], "not_evaluated")
        with tempfile.TemporaryDirectory() as d:
            for name, text in (("README.md", readme), ("TRACK_RECORD.md", TRACK)):
                with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                    fh.write(text)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(check_profile.main([os.path.join(d, "README.md")]), 2)

    def test_the_track_record_next_to_the_readme_is_read_not_the_one_in_the_working_directory(self):
        track = drop_line(TRACK, "[SynapseKit/SynapseKit#1077]")
        with tempfile.TemporaryDirectory() as d:
            for name, text in (("README.md", README), ("TRACK_RECORD.md", track)):
                with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                    fh.write(text)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(check_profile.main([os.path.join(d, "README.md")]), 1)

    def test_contradiction_wins_over_a_lost_sentence(self):
        readme = swap(swap(README, "all seven carry a Zenodo DOI", "each one has a Zenodo DOI"), "(34 accept", "(35 accept")
        with tempfile.TemporaryDirectory() as d:
            for name, text in (("README.md", readme), ("TRACK_RECORD.md", TRACK)):
                with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                    fh.write(text)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(check_profile.main([os.path.join(d, "README.md")]), 1)


class UsageErrors(unittest.TestCase):
    def test_usage_errors_exit_3_not_1(self):
        with tempfile.TemporaryDirectory() as d:
            bad = os.path.join(d, "bad.md")
            with open(bad, "wb") as fh:
                fh.write(b"\xff\xfe")
            for argv in (["--corpus"], ["--corpus", os.path.join(d, "absent")], ["--corpus", d, "--corpus", d],
                         [os.path.join(d, "absent.md")], ["-x"], [bad, bad], ["a", "b", "c"]):
                with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(check_profile.main(argv), 3, argv)


class WithLocalCheckouts(unittest.TestCase):
    def corpus(self, d, with_verifiers, plain):
        for name in with_verifiers:
            os.makedirs(os.path.join(d, name, "verifiers", "go"))
            open(os.path.join(d, name, "verifiers", "differential_oracle.py"), "w").close()
        for name in plain:
            os.makedirs(os.path.join(d, name))

    def claim(self, d):
        return [x for x in check_profile.claims(README, TRACK, d) if not x["required"]][0]

    FIVE = ["cryptovalid-opencore", "omega-evidence", "omega-health-companion", "cra-evidence", "ap2-evidence-pack"]

    def test_five_with_all_seven_present_is_verified_and_the_old_name_is_followed(self):
        with tempfile.TemporaryDirectory() as d:
            self.corpus(d, self.FIVE, ["x402-signature-vectors", "rigorous-levels"])
            c = self.claim(d)
            self.assertEqual((c["state"], c["counted"], c["checkout_absent"]), ("verified", 5, []))
            self.assertIn("omega-cra-evol", c["have"])

    def test_an_absent_checkout_keeps_it_not_evaluated(self):
        with tempfile.TemporaryDirectory() as d:
            self.corpus(d, self.FIVE, ["x402-signature-vectors"])
            self.assertEqual(self.claim(d)["state"], "not_evaluated")

    def test_four_with_all_present_is_contradicted(self):
        with tempfile.TemporaryDirectory() as d:
            self.corpus(d, self.FIVE[:4], ["ap2-evidence-pack", "x402-signature-vectors", "rigorous-levels"])
            self.assertEqual(self.claim(d)["state"], "contradicted")

    def test_six_is_contradicted(self):
        with tempfile.TemporaryDirectory() as d:
            self.corpus(d, self.FIVE + ["x402-signature-vectors"], ["rigorous-levels"])
            self.assertEqual(self.claim(d)["state"], "contradicted")

    def test_an_oracle_without_any_verifier_directory_does_not_count(self):
        with tempfile.TemporaryDirectory() as d:
            self.corpus(d, self.FIVE[:4], ["x402-signature-vectors", "rigorous-levels"])
            os.makedirs(os.path.join(d, "ap2-evidence-pack", "verifiers"))
            open(os.path.join(d, "ap2-evidence-pack", "verifiers", "differential_oracle.py"), "w").close()
            self.assertEqual(self.claim(d)["counted"], 4)

    def test_with_a_corpus_and_the_sentence_gone_it_is_not_evaluated(self):
        readme = swap(README, "five of the seven projects add independent verifiers", "most projects add independent verifiers")
        with tempfile.TemporaryDirectory() as d:
            self.corpus(d, self.FIVE, ["x402-signature-vectors", "rigorous-levels"])
            c = [x for x in check_profile.claims(readme, TRACK, d) if not x["required"]][0]
            self.assertEqual(c["state"], "not_evaluated")

    def test_a_verifiers_directory_without_an_oracle_does_not_count(self):
        with tempfile.TemporaryDirectory() as d:
            self.corpus(d, self.FIVE[:4], ["x402-signature-vectors", "rigorous-levels"])
            os.makedirs(os.path.join(d, "ap2-evidence-pack", "verifiers", "js"))
            self.assertEqual(self.claim(d)["counted"], 4)


class CheckVersions(unittest.TestCase):
    """check_versions.py with the network call replaced: the table's own versions are «the latest release»."""

    def run_on(self, readme, latest=None):
        table = {r["repo"]: check_versions.ROW.match(l).group("ver") for l in README.splitlines()
                 for r in [check_profile.ROW.match(l)] if r for r in [r.groupdict()]}
        table.update(latest or {})
        old = check_versions.latest_tag
        check_versions.latest_tag = lambda repo: table[repo]
        try:
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, "README.md")
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(readme)
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    return check_versions.main(p), out.getvalue()
        finally:
            check_versions.latest_tag = old

    def test_both_scripts_read_the_same_seven_rows(self):
        a = [l for l in README.splitlines() if check_versions.ROW.match(l)]
        b = [l for l in README.splitlines() if check_profile.ROW.match(l)]
        self.assertEqual(a, b)
        self.assertEqual(len(a), 7)

    def test_all_equal_is_zero(self):
        code, out = self.run_on(README)
        self.assertEqual(code, 0)
        self.assertIn("rows: 7", out)

    def test_a_newer_release_is_a_mismatch(self):
        code, out = self.run_on(README, {"cryptovalid-opencore": "0.26.0"})
        self.assertEqual(code, 1)
        self.assertIn("mismatches: 1", out)

    def write_on(self, readme, latest=None):
        table = {r["repo"]: check_versions.ROW.match(l).group("ver") for l in README.splitlines()
                 for r in [check_profile.ROW.match(l)] if r for r in [r.groupdict()]}
        table.update(latest or {})
        old = check_versions.latest_tag
        check_versions.latest_tag = lambda repo: table[repo]
        try:
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, "README.md")
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(readme)
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = check_versions.update(p)
                with open(p, encoding="utf-8") as fh:
                    return code, out.getvalue(), fh.read()
        finally:
            check_versions.latest_tag = old

    def test_write_sets_only_the_version_of_the_row_behind(self):
        code, out, after = self.write_on(README, {"cryptovalid-opencore": "0.99.0"})
        self.assertEqual(code, 0)
        self.assertIn("cryptovalid-opencore 0.25.0 -> 0.99.0", out)
        diff = [(x, y) for x, y in zip(README.splitlines(), after.splitlines()) if x != y]
        self.assertEqual(len(diff), 1)                                   # one line, and in it only the version
        self.assertEqual(diff[0][0].replace("| 0.25.0 ·", "| 0.99.0 ·"), diff[0][1])
        self.assertEqual(len(README.splitlines()), len(after.splitlines()))

    def test_write_with_nothing_behind_changes_nothing(self):
        code, out, after = self.write_on(README)
        self.assertEqual((code, after), (0, README))
        self.assertIn("changed: none", out)

    def test_write_refuses_a_tag_that_is_not_semver_and_leaves_the_file(self):
        code, out, after = self.write_on(README, {"cryptovalid-opencore": "0.26.0-rc1"})
        self.assertEqual((code, after), (1, README))
        self.assertIn("is not X.Y.Z", out)

    def test_write_on_a_page_without_table_rows_is_an_error(self):
        code, out, after = self.write_on("# no table here\n")
        self.assertEqual((code, after), (1, "# no table here\n"))
        self.assertIn("nothing was updated", out)

    def test_write_refuses_tags_that_only_look_like_semver(self):
        for tag in ("\u0661.\u0662.\u0663", "\uff11.\uff12.\uff13", "1.2.3.4", "x1.2.3", "1.2.3\n| x", "1.2.3 ", ""):
            code, out, after = self.write_on(README, {"cryptovalid-opencore": tag})
            self.assertEqual((code, after), (1, README), repr(tag))
        self.assertEqual(self.write_on(README, {"cryptovalid-opencore": "10.20.30"})[0], 0)      # positive control

    def test_write_keeps_crlf_line_endings(self):
        crlf = README.replace("\n", "\r\n")
        check_versions_latest = check_versions.latest_tag
        check_versions.latest_tag = lambda repo: "0.99.0" if repo == "cryptovalid-opencore" else check_versions.ROW.match(
            [l for l in README.splitlines() if "/%s)" % repo in l][0]).group("ver")
        try:
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, "README.md")
                with open(p, "wb") as fh:
                    fh.write(crlf.encode("utf-8"))
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(check_versions.update(p), 0)
                with open(p, "rb") as fh:
                    after = fh.read().decode("utf-8")
        finally:
            check_versions.latest_tag = check_versions_latest
        self.assertEqual(after, crlf.replace("| 0.25.0 ·", "| 0.99.0 ·"))
        self.assertNotEqual(after, crlf)

    def test_command_line_write_is_reached_and_unknown_arguments_are_refused(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "README.md")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("# no table here\n")
            run = lambda *a: subprocess.run([sys.executable, os.path.join(here, "check_versions.py"), *a],
                                            capture_output=True, text=True)
            r = run("--write", p)
            self.assertEqual(r.returncode, 1)
            self.assertIn("nothing was updated", r.stdout)                 # update() ran, not main()
            self.assertIn("nothing was checked", run(p).stdout)            # and without --write it is main()
            for bad in ((p, "--write"), ("--write", p, p), ("--wrte", p), ("--write", "--write")):
                r = run(*bad)
                self.assertEqual(r.returncode, 1, bad)
                self.assertIn("usage:", r.stderr, bad)

    def test_write_refuses_an_unreadable_row_and_leaves_the_file(self):
        bad = swap(README, "| 0.25.0 · [DOI]", "| v0.25.0 · [DOI]")
        code, out, after = self.write_on(bad, {"cryptovalid-opencore": "0.26.0"})
        self.assertEqual((code, after), (1, bad))
        self.assertIn("version not readable", out)

    def test_a_row_whose_version_cannot_be_read_is_a_mismatch(self):
        # «v0.25.0» instead of «0.25.0»: the old script skipped the row and said `mismatches: 0`
        code, out = self.run_on(swap(README, "| 0.25.0 · [DOI]", "| v0.25.0 · [DOI]"), {"cryptovalid-opencore": "0.26.0"})
        self.assertEqual(code, 1)
        self.assertIn("version not readable", out)
        self.assertIn("rows: 6", out)

    def test_no_table_at_all_is_a_mismatch(self):
        code, out = self.run_on("## A page without the table\n")
        self.assertEqual(code, 1)
        self.assertIn("nothing was checked", out)



class MissingRows(unittest.TestCase):
    """check_versions.py --missing with the network calls replaced: every public repository of the account with a
    release is a row or in EXCLUDED (2026-11-25: three released projects had never been added, and nothing said so)."""

    ROWS = [r["repo"] for r in check_profile.rows(README)]

    def run_on(self, repos, released, excluded=None, readme=README):
        saved = check_versions.public_repos, check_versions.has_release, check_versions.EXCLUDED
        check_versions.public_repos = lambda: list(repos)
        check_versions.has_release = lambda repo: repo in released
        check_versions.EXCLUDED = dict(excluded or {})
        try:
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, "README.md")
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(readme)
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    return check_versions.missing(p), out.getvalue()
        finally:
            check_versions.public_repos, check_versions.has_release, check_versions.EXCLUDED = saved

    def repos(self, *extra, fork=()):
        return [(n, False) for n in self.ROWS + list(extra)] + [(n, True) for n in fork]

    def test_every_released_repository_a_row_is_zero(self):
        code, out = self.run_on(self.repos("profile-page"), set(self.ROWS))
        self.assertEqual(code, 0, out)
        self.assertIn("missing: 0", out)

    def test_a_released_repository_not_in_the_table_fails_with_its_name(self):
        code, out = self.run_on(self.repos("pq-scitt"), set(self.ROWS) | {"pq-scitt"})
        self.assertEqual(code, 1)
        self.assertIn('"repo": "pq-scitt", "ok": false', out)
        self.assertIn("missing: 1", out)

    def test_an_excluded_repository_passes_and_says_why(self):
        code, out = self.run_on(self.repos("pq-scitt"), set(self.ROWS) | {"pq-scitt"}, {"pq-scitt": "a reason"})
        self.assertEqual(code, 0, out)
        self.assertIn("excluded: a reason", out)

    def test_an_excluded_name_that_is_also_a_row_fails(self):
        code, out = self.run_on(self.repos(), set(self.ROWS), {"omega-evidence": "a reason"})
        self.assertEqual(code, 1)
        self.assertIn("also a row of the table", out)

    def test_a_stale_exclusion_fails(self):
        for repos in (self.repos("old-project"), self.repos()):        # no release any more, or no public repository
            code, out = self.run_on(repos, set(self.ROWS), {"old-project": "a reason"})
            self.assertEqual(code, 1)
            self.assertIn("not a public repository with a release", out)

    def test_forks_and_repositories_without_a_release_are_not_asked_for(self):
        code, out = self.run_on(self.repos("no-release-yet", fork=("someone-elses",)),
                                set(self.ROWS) | {"someone-elses"})
        self.assertEqual(code, 0, out)
        self.assertEqual(self.run_on(self.repos("someone-elses"), set(self.ROWS) | {"someone-elses"})[0], 1)  # control

    def test_a_table_that_cannot_be_read_in_full_checks_nothing(self):
        for readme in ("# no table here\n", swap(README, "| 0.25.0 · [DOI]", "| v0.25.0 · [DOI]")):
            code, out = self.run_on(self.repos(), set(self.ROWS), readme=readme)
            self.assertEqual(code, 1)
            self.assertIn("nothing was checked", out)

    def test_has_release_reads_404_as_no_release_and_raises_on_any_other_error(self):
        saved = check_versions.subprocess.run
        try:
            for rc, err, want in ((0, "", True), (1, "gh: Not Found (HTTP 404)", False), (1, "HTTP 403: rate limit", None)):
                check_versions.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, rc, "v1.0.0\n", err)
                if want is None:
                    self.assertRaises(RuntimeError, check_versions.has_release, "x")
                else:
                    self.assertIs(check_versions.has_release("x"), want)
        finally:
            check_versions.subprocess.run = saved

    def test_public_repos_reads_the_fork_flag_asks_for_every_page_and_raises_when_gh_fails(self):
        # the list of repositories is the other half of --missing: a fork flag read wrong, a first page only, or a
        # failed call read as a shorter list would each let a released project go unseen
        saved = check_versions.subprocess.run
        seen = []
        try:
            def fake(cmd, **k):
                seen.append((cmd, k))
                return subprocess.CompletedProcess(cmd, 0, "mine\tfalse\ntheirs\ttrue\n", "")
            check_versions.subprocess.run = fake
            self.assertEqual(check_versions.public_repos(), [("mine", False), ("theirs", True)])
            cmd, k = seen[0]
            self.assertIn("--paginate", cmd)
            self.assertTrue(k.get("check"))
        finally:
            check_versions.subprocess.run = saved

    def test_command_line_missing_is_reached_and_mixed_modes_are_refused(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "README.md")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("# no table here\n")
            run = lambda *a: subprocess.run([sys.executable, os.path.join(here, "check_versions.py"), *a],
                                            capture_output=True, text=True)
            r = run("--missing", p)
            self.assertEqual(r.returncode, 1)
            self.assertIn("the table cannot be read in full", r.stdout)     # missing() ran, before any network call
            for bad in (("--missing", "--write", p), ("--write", "--missing"), (p, "--missing")):
                r = run(*bad)
                self.assertEqual(r.returncode, 1, bad)
                self.assertIn("usage:", r.stderr, bad)

if __name__ == "__main__":
    unittest.main()
