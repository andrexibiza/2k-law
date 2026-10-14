# Authorship and provenance

**Code and architecture: Axl Ibiza, MBA.**

This repository contains my original code: the standalone enforcer, CLI, GitHub Action adapter, byte-window checks, Seam Identity checks and tests. It is not a fork or port of Hermes Agent and contains no copied or vendored Hermes Agent code. It has no Hermes Agent dependency.

## My earlier published work

These links document my authorship and the development of my work. They identify my earlier contributions, not third-party code imported into this package.

- [All Gods Must Die, August 2026](https://drive.google.com/file/d/1GYR9AikBP7B6teFMyNOyp-P606fMzfVS/view): the 2K Law (§5), blind method (§6), executable enforcement (§7), and refined byte-bounded claim (§24.3).
- [Campaign EPIC #78647](https://github.com/NousResearch/hermes-agent/issues/78647): historical work, credit, coordination and remaining debt.
- [My original enforcement commit](https://github.com/NousResearch/hermes-agent/commit/458473cc6c60770b1eccf3c56e90bba1e2043664).
- [My earlier 2K implementation](https://github.com/NousResearch/hermes-agent/blob/5daff1e2166b57fbf153eb26505b1b217d898161/tests/scripts/test_2k_law.py), contribution [#79779](https://github.com/NousResearch/hermes-agent/pull/79779).
- [My descriptor-aware Seam Identity tests](https://github.com/NousResearch/hermes-agent/blob/8d7ec76ccb345041e1717bf0ae15329980728d81/tests/gateway/test_telegram_config_mention_seam.py), contribution [#79010](https://github.com/NousResearch/hermes-agent/pull/79010).

At the October 14, 2026 observation, my contributions #79779 and #79010 were closed and unmerged. That is their integration status, not an ambiguity about authorship. My earlier checker had a five-line tolerance and an editable current manifest. This standalone implementation has a strict trusted-base ratchet. These are distinct implementations of my own work.

The standalone code implements a fixed source policy, strict JSON, raw-object base comparison, exact current ledger, CR/LF metric and an opt-in seam command. Its executable scope is distinct from the full architecture: the tool does not itself dispatch reviewers, audit GitHub interlocks, judge translation semantics, or supply release authority.

Hermes is a case study and a repository where I published earlier work. The teaching page separately credits other contributors for their work in that case study; those historical credits do not identify code incorporated into this package.

## Reproducibility

Tests and the smoke script are committed beside the implementation. CI records the exact tested commit and operating system. Local terminal output is not substituted for a hosted Action result; a source hash is not a test result. Public installation examples use this repository, not an unverified PyPI distribution.

The full teaching page explains why source size, byte preservation, namespace identity, patch effects, behavioral tests and independent review establish different claims:

https://axlibiza.com/learn/blind-witness-engine/
