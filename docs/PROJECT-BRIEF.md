# 2K Law — public implementation brief

Author of the 2K Law and the graph-gated, adversarially verified transformation architecture: **Axl Ibiza, MBA**.

## Requested deliverables

Create the distinct public repository `andrexibiza/2k-law` suggested in the supplied feedback, alongside the teaching page at `https://axlibiza.com/learn/blind-witness-engine/`.

The repository must provide a working standalone CLI and drop-in GitHub Action for the 2,000-line architectural ratchet, an enumerable legacy-exemption burndown ledger, a Seam Identity verification surface, and a CI gate. Documentation must distinguish structural compliance, byte preservation, runtime identity, and behavior exercised by tests. None is a universal guarantee of runtime correctness.

## Primary authority

*All Gods Must Die: Adversarially Verified Transformation*, August 2026, by Axl Ibiza, MBA:

https://drive.google.com/file/d/1GYR9AikBP7B6teFMyNOyp-P606fMzfVS/view

The complete paper controls the methodology. Its Section 5.2 defines the source-code ceiling and exclusions; Section 6 defines the blind role geometry, source pins, golden window hashes, identity-preserving seams and independent review; Section 7 specifies executable ratchets; Sections 23–26 assign authority and bound the claims. The public teaching edition must not present private operating extensions as words from the paper.

## Five analysis regions

These are responsibility boundaries for independent design, not implementation prescriptions or expected answers:

1. **Source inventory and counting:** exact scope of repository-owned source, counting semantics, exclusion transparency, path safety, deterministic results, failures that must not silently disappear.
2. **Legacy manifest and monotonic ratchet:** explicit measured debt, first adoption, shrink-only progression, trusted comparison, removed/stale entries, attempted baseline inflation, reproducible machine receipts.
3. **Seam Identity and relocation evidence:** original and moved namespaces, object identity, byte-window proof, initialization and patch-target risks, explicit execution trust boundary, limits of static versus runtime checks.
4. **CLI, package and GitHub Action:** installation, invocation, input/output contracts, failure exit codes, portable paths, GitHub runner integration, untrusted pull-request boundary, reproducible distribution.
5. **Verification, documentation and provenance:** tests that expose failures, positive and negative controls, real CLI and Action smoke execution, source attribution/license preservation, reproducibility, tutorial and adoption examples, platform coverage.

## Acceptance obligations

- Ordinary checks are read-only and do not rewrite user source or silently regenerate exemptions.
- Every supported source path is included or explicitly accounted for; no silent successful partial inventory.
- An untracked over-limit source file fails. A legacy debt allowance cannot quietly expand through the proposed change.
- Burndown state is explicit and machine-readable. An adoption baseline is debt, not a claim of compliance.
- The seam facility reports exactly what it verifies and what it executes. Normal size checking must not import arbitrary target code.
- CLI and Action share one implementation rather than divergent checks. README commands must be exercised against the built package.
- The tool checks itself. Production code, tests and scripts remain below the 2,000-line ceiling.
- Tests cover rejection paths, including malformed input and attempted exemptions that defeat the rule. Windows and Linux behavior are distinguished by real runtime evidence.
- Public examples contain no secrets, local personal paths, private operating documents, or invented execution outputs.
- Authorship remains attached to the law, package, documentation and historical sources. Existing contributors retain credit for any copied code.
- Publication must use exact commit identities and live CI evidence. No remote history rewrite, PR merge, maintainer pings, or unsupported release claim.

## Evidence and scope

The August paper is a dated case study, not a current repository census. Historical PR totals, release-marketing statements, runtime measurements and lane counts need their own source and denominator. Pure relocation does not by itself establish a reduction in total repository lines.

This brief does not authorize changes to agent governance, runtime configuration, other profiles, credentials, unrelated repositories, or restricted storage. Work is confined to this project and the separately assigned website page. Independent analysis produces proposals; adjudication must resolve the graph before implementation.
