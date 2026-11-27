## Roberto Locatelli — verifiable compliance evidence, in the open

Independent developer (fintech / regtech). Everything here is measured before it is claimed: the newest release of every project
runs its checks in CI and lists its assets in a `SHA256SUMS`; four of the nine projects add independent verifiers in
other languages checked by a differential oracle, and a KMS-signed evidence pack in that release; seven of the nine carry a Zenodo DOI (the
concept DOI below always resolves to the latest version). Public interventions by my AI agent (Noûs) are signed as
such; I review them and I am accountable for them.

**Start here** (each line installs a released package and runs offline):

```
pip install cryptovalid-opencore   # cryptovalid-verify {auto,pack,archive,ledger,ap2,cldma} PATH: one verifier for ledgers, evidence packs and archives
pip install omega-cra-evol         # cra sbom / pack / verify: EU Cyber Resilience Act evidence, firm side
pip install "rigorous-levels @ https://github.com/robertolocatelli81-dev/rigorous-levels/releases/download/v0.3.0/rigorous_levels-0.3.0-py3-none-any.whl#sha256=b8b28d759340d6c654bb090fdc8ca9ca585464a1b8bcc257eb6942f9853f7e16"   # guaranteed eigenvalue intervals; the release wheel, sha256-checked by pip
```

| Project | What it is | Latest |
|---|---|---|
| [cryptovalid-opencore](https://github.com/robertolocatelli81-dev/cryptovalid-opencore) | Hash-chained ledgers, signed chain tip, hybrid Ed25519 + ML-DSA-65, C2SP checkpoints and tlog-witness (split-view evidence, ML-DSA-44 cosignatures, real Rekor checkpoints verified), SCITT RFC 9943; verifiers in Python, JS, Go, Rust, Java + differential oracle, plus a reduced-scope Swift verifier | 0.29.1 · [DOI](https://doi.org/10.5281/zenodo.22539578) · `pip install cryptovalid-opencore` |
| [omega-evidence](https://github.com/robertolocatelli81-dev/omega-evidence) | Apache-2.0 toolkit for long-term, offline-verifiable evidence: packs with graduated authenticity, trust registry, RFC 3161, hybrid post-quantum packs, Agent Audit Trail interop; verifiers in Go, Java, Node | 0.14.0 · [DOI](https://doi.org/10.5281/zenodo.22539633) |
| [omega-cra-evol](https://github.com/robertolocatelli81-dev/omega-cra-evol) | Firm-side, offline-verifiable evidence for the EU Cyber Resilience Act: SBOM record, Art. 14 clock, ENISA SRP field schema, crypto-agile seal, cryptovalid-compatible ledger. Formerly `cra-evidence`, renamed on purpose in 0.10.0 so that it is not mistaken for other products with a similar name | 0.13.1 · [DOI](https://doi.org/10.5281/zenodo.24172960) · `pip install omega-cra-evol` |
| [ap2-evidence-pack](https://github.com/robertolocatelli81-dev/ap2-evidence-pack) | Offline-verifiable dispute evidence for AP2 SD-JWT mandates, conformance vectors | 1.11.2 · [DOI](https://doi.org/10.5281/zenodo.22539659) · `pip install ap2-evidence-pack` |
| [x402-signature-vectors](https://github.com/robertolocatelli81-dev/x402-signature-vectors) | Conformance vectors for the x402 signature layer (EIP-712, secp256k1 recovery), cross-validated against libsecp256k1 and eth-account; 84 vectors (34 accept, 50 reject), three from real x402 payments | 1.6.0 · [DOI](https://doi.org/10.5281/zenodo.24172853) |
| [rigorous-levels](https://github.com/robertolocatelli81-dev/rigorous-levels) | Guaranteed eigenvalue intervals, truncation included, for charge-basis rotors (transmon), the fluxonium, Mathieu characteristic values, the spherical rotor and the 1Σ molecule; a sandboxed multiport checks other solvers against them | 0.3.1 · [DOI](https://doi.org/10.5281/zenodo.24172688) · `pip install rigorous-levels` |
| [agent-payment-chain](https://github.com/robertolocatelli81-dev/agent-payment-chain) | Offline verifier of payments made by AI agents, one bundle in and one verdict out: the AP2 mandate, the x402 payment (EIP-3009, Permit2, ERC-7710, auth-capture, Solana, XRPL, Stellar), the acceptance record and the links between them, checked against the chain data the bundle carries. Python standard library and two files of x402-signature-vectors pinned by SHA-256; the mandate checks also need ap2-evidence-pack and `cryptography`, the ML-DSA signatures `cryptography` | 0.21.8 |
| [pq-scitt](https://github.com/robertolocatelli81-dev/pq-scitt) | Checks hash-chained evidence logs offline and exports them as IETF SCITT Transparent Statements (COSE_Sign1, RFC 9943, with RFC 9162 inclusion proofs in the receipts, RFC 9942), verified by a closed verifier; Ed25519 or ML-DSA-65 signatures, SLH-DSA (FIPS 205) anchors, signing keys kept in a PKCS#11 HSM, AWS KMS, HashiCorp Vault Transit or a NetHSM | 0.1.2 · [DOI](https://doi.org/10.5281/zenodo.24172832) |
| [work-acceptance-check-omega](https://github.com/robertolocatelli81-dev/work-acceptance-check-omega) | war-verify: an independent verifier of work-acceptance records (Trilatic draft profile 1.4.12, vectors 01-128), written from the profile README, the published test vectors and the RFCs it names (the parts of the reference code that were read are listed in its README); a member it does not understand is refused, or listed in its notes in the cases its README names; none is ignored in silence. Its new vectors are CC0; third-party inputs are fetched by pinned SHA-256, not included | 0.12.1 |

Where others name this work — three IETF Internet-Drafts (individual submissions), the Tersign, Verax, APS and ScopeBlind
conformance suites (cryptovalid-opencore is one of the four implementations ScopeBlind lists as conformant), fixes made
upstream at Microsoft, Google, Cloudflare and DCMTK from my reports — each with a link and the quote, plus seven pull
requests of mine merged in others' repositories: [TRACK_RECORD.md](TRACK_RECORD.md).

Package index (PEP 503, sha256-pinned to GitHub release assets): https://robertolocatelli81-dev.github.io/pypi/

Contact: roberto.locatelli.81@gmail.com — interoperability reports welcome; the answer says what is measured and what is not.
