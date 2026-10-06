## Roberto Locatelli — verifiable compliance evidence, in the open

Independent developer (fintech / regtech). Everything here is measured before it is claimed: every release
runs its checks in CI and lists its assets in a `SHA256SUMS`; five of the six projects add independent verifiers in
other languages checked by a differential oracle and KMS-signed release assets; four carry a Zenodo DOI (the
concept DOI below always resolves to the latest version). Public interventions by my AI agent (Noûs) are signed as
such; I review them and I am accountable for them.

| Project | What it is | Latest |
|---|---|---|
| [cryptovalid-opencore](https://github.com/robertolocatelli81-dev/cryptovalid-opencore) | Hash-chained ledgers, signed chain tip, hybrid Ed25519 + ML-DSA-65, C2SP checkpoints and tlog-witness (split-view evidence, ML-DSA-44 cosignatures, real Rekor checkpoints verified), SCITT RFC 9943; verifiers in Python, JS, Go, Rust, Java + differential oracle, plus a reduced-scope Swift verifier | 0.18.1 · [DOI](https://doi.org/10.5281/zenodo.22539578) · `pip install --extra-index-url https://robertolocatelli81-dev.github.io/pypi/ cryptovalid-opencore` |
| [omega-evidence](https://github.com/robertolocatelli81-dev/omega-evidence) | Apache-2.0 toolkit for long-term, offline-verifiable evidence: packs with graduated authenticity, trust registry, RFC 3161, hybrid post-quantum packs, Agent Audit Trail interop; verifiers in Go, Java, Node | 0.11.1 · [DOI](https://doi.org/10.5281/zenodo.22539633) |
| [omega-health-companion](https://github.com/robertolocatelli81-dev/omega-health-companion) | Pre-hospital pre-alert as evidence: FHIR R4 / CH EMS documents with a detached JWS `Bundle.signature`, hash-chained provenance, conformance measured with validator_cli and Matchbox. Not a medical device | 0.8.0 · [DOI](https://doi.org/10.5281/zenodo.22539173) |
| [cra-evidence](https://github.com/robertolocatelli81-dev/cra-evidence) | Firm-side evidence for the EU Cyber Resilience Act: SBOM record (SPDX), Art. 14 clock, crypto-agile seal, cryptovalid-compatible ledger | 0.4.0 |
| [ap2-evidence-pack](https://github.com/robertolocatelli81-dev/ap2-evidence-pack) | Offline-verifiable dispute evidence for AP2 SD-JWT mandates, conformance vectors | 1.3.0 · [DOI](https://doi.org/10.5281/zenodo.22539659) |
| [x402-signature-vectors](https://github.com/robertolocatelli81-dev/x402-signature-vectors) | Conformance vectors for the x402 signature layer (EIP-712, secp256k1 recovery), cross-validated against libsecp256k1 and eth-account; 81 vectors (31 accept, 50 reject) | 1.4.0 |

Where others name this work — an IETF Internet-Draft, the Tersign, Verax, APS and ScopeBlind conformance suites, fixes
merged upstream at Microsoft and Google from my reports — each with a link and the quote: [TRACK_RECORD.md](TRACK_RECORD.md).

Package index (PEP 503, sha256-pinned to GitHub release assets): https://robertolocatelli81-dev.github.io/pypi/

Contact: roberto.locatelli.81@gmail.com — pilots and interoperability reports welcome; the answer says what is measured and what is not.
