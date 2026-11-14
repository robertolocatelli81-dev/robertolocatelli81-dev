# Track record — where others name this work

Each entry in the sections below links to text written by someone else, in their own repository or document, and quotes it;
the exception is «Pull requests merged in others' repositories», which lists my own pull requests that their maintainers
merged. Checked against
the source on 2026-11-14 (every quote below re-read in its source that day). Most of the work below was done by my AI agent (Noûs) under my revocable mandate; I review it
and I am accountable for it.

## Named in specifications

- **IETF Internet-Draft `draft-krausz-verification-state-03`** (an individual draft, not a standard), x402 evidence-record
  work: «The split between keys a relying party happens to hold and a list it declares complete is Roberto Locatelli's
  (x402 TSC issue #4, 2026-09-24).» The draft also records my review inputs and my reproduction of the first
  from-scratch cold build. [datatracker](https://datatracker.ietf.org/doc/draft-krausz-verification-state/)
- **IETF Internet-Draft `draft-dogru-cedulon-decision-profile-04`** (individual draft): «Tymofii Pidlisnyi (Agent
  Passport System) and Roberto Locatelli (cryptovalid-opencore) ran the second implementation's test vectors with
  verifiers of their own; the first three changes of -04 are their findings.»
  [draft](https://www.ietf.org/archive/id/draft-dogru-cedulon-decision-profile-04.txt)
- **IETF Internet-Draft `draft-sansone-axes-evidence-envelope-00`** (individual draft), implementation experience:
  «robertolocatelli81-dev: from the specification text only, with an independent canonicaliser and no AXES code.»; and
  in the acknowledgments, «robertolocatelli81-dev (Noûs) for specification-only reproduction of the corpus of record.»
  [draft](https://www.ietf.org/archive/id/draft-sansone-axes-evidence-envelope-00.txt)
- **Elara protocol specification**, Appendix D «Independent implementations»: an independent reader of their vector set
  by Noûs for @robertolocatelli81-dev, «written from this spec's text with the reference implementations unopened»,
  «21 of 25 vectors byte-agreed».
  [docs/PROTOCOL-SPEC.md](https://github.com/navigatorbuilds/elara-mesh/blob/main/docs/PROTOCOL-SPEC.md)

## Credited in conformance suites

- **Tersign evidence-record conformance**, `CONTRIBUTORS.md`, crypto profile: «Roberto Locatelli, via his agent Noûs. A
  third runner written from…»; and, from the clean-room run in issue #9, «Unpinned classes, listed», the three classes
  v0.5.4 then pinned with vectors.
  [CONTRIBUTORS.md](https://github.com/tersignhq/evidence-record-conformance/blob/main/CONTRIBUTORS.md)
- **Verax test vectors**, «Independent runs»: «Roberto Locatelli (cryptovalid-opencore), with clean-room checkers
  written from the drafts…»: «with the checkpoint verified under the witness key, 16 of 16 verdicts and 15 of 16 first
  failing stages at `vectors-v1`»; the same entry records that one match «came from a rule added after reading the vector».
  [test-vectors/README.md](https://github.com/verax-ai/verax/blob/main/test-vectors/README.md)
- **APS conformance suite** (Agent Authority Conformance): my run record of cryptovalid-opencore 0.17.0 (written on my
  side, [PR #149](https://github.com/Agent-Authority-Conformance/aps-conformance-suite/pull/149)), reviewed and merged by
  the maintainer: «Thanks, this is a clean record.» and, after the Ed25519 layer was relabelled author-produced at his
  request, «The relabel matches, and every other recorded file hash is unchanged. Merged.»
  [review](https://github.com/Agent-Authority-Conformance/aps-conformance-suite/pull/149#issuecomment-5984344055),
  [merge](https://github.com/Agent-Authority-Conformance/aps-conformance-suite/pull/149#issuecomment-5987752842),
  [interop/cryptovalid-opencore-aps-da95834](https://github.com/Agent-Authority-Conformance/aps-conformance-suite/tree/main/interop/cryptovalid-opencore-aps-da95834)
- **ScopeBlind agent-governance test vectors**: the key-window cases «follow a measurement by @giskard09 and
  @robertolocatelli81-dev». [verifier-vectors/README.md](https://github.com/ScopeBlind/agent-governance-testvectors/blob/main/verifier-vectors/README.md)
  The repository README counts cryptovalid-opencore among the «three independent Python implementations» of the four
  that «pass every check here in CI» (the driver under `implementations/` is mine, merged as PR #25); its status table
  (22 October 2026 run) marks cryptovalid-opencore «Conformant», one of four implementations so marked. [README.md](https://github.com/ScopeBlind/agent-governance-testvectors/blob/main/README.md)

## Fixes made upstream from my reports

- **Microsoft agent-governance-toolkit**: [PR #4201](https://github.com/microsoft/agent-governance-toolkit/pull/4201),
  merged, closes my issue #4165: «Credit to @robertolocatelli81-dev for #4165's reproductions and proposed
  missing-signature and explicit-empty-list corrections.»
- **Google cybernetic-agent-governance-engine**: [issue #286](https://github.com/google/cybernetic-agent-governance-engine/issues/286),
  fixed in [PR #394](https://github.com/google/cybernetic-agent-governance-engine/pull/394): «The diagnosis and
  reproduction were exactly right.» ([comment](https://github.com/google/cybernetic-agent-governance-engine/issues/286#issuecomment-5983037241))
- **Cloudflare web-bot-auth**: [issue #153](https://github.com/cloudflare/web-bot-auth/issues/153) (the Rust verifier
  accepted a signature whose `alg` did not match the key), fixed in [PR #157](https://github.com/cloudflare/web-bot-auth/pull/157),
  merged: «RFC 9421 Section 3.2, step 6: when `alg` is present it must name a registered algorithm and agree with the
  algorithm of the resolved key. Fixes #153.»
- **DCMTK (OFFIS)**: commit [d23d76b](https://github.com/DCMTK/dcmtk/commit/d23d76b34493) «Correctly print cert
  validity dates after 2049»: «Thanks to Roberto Locatelli for the bug report and fix.»
- **giskard09/argentum-core**, `CHANGELOG.md` (2026-09-23): the `"tool"` / `tool_name` defect in the
  `farley-receipt-signature` vectors, «Reported by robertolocatelli81-dev (Noûs) in #96», fixed the same day.
  [CHANGELOG.md](https://github.com/giskard09/argentum-core/blob/main/CHANGELOG.md)
- **FINOS AI governance framework**: [issue #337](https://github.com/finos/ai-governance-framework/issues/337), the
  author of the companion proposal #359 withdrew the request for a forward reference in the decision receipt after
  giskard09 and I answered it: «you're right, and thank you both. […] I withdraw the request for a forward reference in
  the decision receipt.» ([comment](https://github.com/finos/ai-governance-framework/issues/337#issuecomment-5867876375))

## Pull requests merged in others' repositories

[x402-foundation/x402#3965](https://github.com/x402-foundation/x402/pull/3965) (specification),
[SynapseKit/SynapseKit#1077](https://github.com/SynapseKit/SynapseKit/pull/1077) (EU AI Act record-keeping mode),
[TKCollective/tanilo-receipt-spec#11](https://github.com/TKCollective/tanilo-receipt-spec/pull/11),
[babyblueviper1/preaction-governance-conformance#11](https://github.com/babyblueviper1/preaction-governance-conformance/pull/11) and
[#14](https://github.com/babyblueviper1/preaction-governance-conformance/pull/14),
[Agent-Authority-Conformance/aps-conformance-suite#149](https://github.com/Agent-Authority-Conformance/aps-conformance-suite/pull/149),
[ScopeBlind/agent-governance-testvectors#25](https://github.com/ScopeBlind/agent-governance-testvectors/pull/25).

## Used by others

- **MarkovianProtocol** ran the independent witness-gauntlet suite against cryptovalid-opencore
  v0.14.0 and again against v0.23.0 on 2026-11-14: «14 cases, 0 spec failures, 0 stricter-than-reference misses, the
  same as 0.14.0. The non-canonical base64 root is now a spec case (C2SP #370) and 0.23.0 refuses it.»
  ([comment](https://github.com/robertolocatelli81-dev/cryptovalid-opencore/issues/2#issuecomment-6869426976))
- **Matawaka/uu-aap** runs a C2SP witness qualification workflow on cryptovalid-opencore v0.14.0.
  [scripts/cryptovalid-c2sp-witness-qualification](https://github.com/Matawaka/uu-aap/tree/main/scripts/cryptovalid-c2sp-witness-qualification)
- **Elara** carries the ap2-evidence-pack specification and vectors byte for byte, with their licence, as the input of
  their reader. [tools/ap2-evidence-reader](https://github.com/navigatorbuilds/elara-mesh/tree/main/tools/ap2-evidence-reader)

What this is not: these are credits for verification and review inside a few working groups, not adoption at scale and
not a certification.
