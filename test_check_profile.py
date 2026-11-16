#!/usr/bin/env python3
"""Tests of check_profile.py and check_versions.py: offline, standard library only (`python3 -m unittest -v`).
Every check has its positive control: the same page with one thing changed must come out `contradicted` (or, when the
sentence itself is gone, `not_evaluated` with exit 2). A check that cannot fail is not a check.

The positive controls run on a frozen copy of the page (testdata/), so that editing the live README (a new version in
the table, a reworded sentence) cannot break them; only ThePageAsItIs reads the live README.md and TRACK_RECORD.md."""
import contextlib
import io
import os
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
        self.assertEqual(st["all-M-carry-a-DOI equals table rows"], "contradicted")
        self.assertEqual(st["rows with a Zenodo DOI link"], "contradicted")

    def test_a_doi_removed_from_one_row(self):
        st = states(swap(README, " · [DOI](https://doi.org/10.5281/zenodo.22539633)", ""))
        self.only(st, "rows with a Zenodo DOI link")

    def test_prose_says_eight_projects(self):
        st = states(swap(README, "all seven carry", "all eight carry"))
        self.only(st, "all-M-carry-a-DOI equals table rows", also=("rows with a Zenodo DOI link",))
        self.assertEqual(st["rows with a Zenodo DOI link"], "contradicted")

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
        self.assertEqual(st["all-M-carry-a-DOI equals table rows"], "verified")

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
        self.assertEqual(states(readme)["all-M-carry-a-DOI equals table rows"], "not_evaluated")
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


if __name__ == "__main__":
    unittest.main()
