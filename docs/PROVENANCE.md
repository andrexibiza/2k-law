# Provenance and evidence boundaries

**Architecture: Axl Ibiza, MBA.**

- [All Gods Must Die, August 2026](https://drive.google.com/file/d/1GYR9AikBP7B6teFMyNOyp-P606fMzfVS/view): the 2K Law (§5), blind method (§6), executable enforcement (§7), and refined byte-bounded claim (§24.3).
- [Campaign EPIC #78647](https://github.com/NousResearch/hermes-agent/issues/78647): historical work, credit, coordination and remaining debt.
- [Original enforcement commit](https://github.com/NousResearch/hermes-agent/commit/458473cc6c60770b1eccf3c56e90bba1e2043664).
- [Historical 2K implementation](https://github.com/NousResearch/hermes-agent/blob/5daff1e2166b57fbf153eb26505b1b217d898161/tests/scripts/test_2k_law.py), contribution [#79779](https://github.com/NousResearch/hermes-agent/pull/79779).
- [Descriptor-aware Seam Identity tests](https://github.com/NousResearch/hermes-agent/blob/8d7ec76ccb345041e1717bf0ae15329980728d81/tests/gateway/test_telegram_config_mention_seam.py), contribution [#79010](https://github.com/NousResearch/hermes-agent/pull/79010).

At the October 14, 2026 source observation, #79779 and #79010 were closed and unmerged. The historical checker permitted `recorded + 5`, trusted an editable current manifest, and skipped absent entries. Those bytes do not implement a strict zero-growth protected-base ratchet. This tool deliberately implements a narrower, explicit standalone contract rather than claiming a byte-verbatim port.

The new code was written separately from the historical implementation. Its fixed source policy, strict JSON, raw-object base comparison, exact current ledger, CR/LF metric and opt-in seam command are explicit product decisions. They do not amend the original paper. The tool does not implement campaign dispatch, reviewer independence, GitHub interlock auditing, native-language semantic review, or release authority.

The associated teaching page preserves iacker's French seed authorship, Teknium's later simplification and other collaborators' credit. Axl's architectural authorship does not turn every subsequent repository change into his individually authored implementation.

## Reproducibility

Tests and the smoke script are committed beside the implementation. CI records the exact tested commit and operating system. Local terminal output is not substituted for a hosted Action result; a source hash is not a test result. Public installation examples use this repository, not an unverified PyPI distribution.

The full teaching page explains why source size, byte preservation, namespace identity, patch effects, behavioral tests and independent review establish different claims:

https://axlibiza.com/learn/blind-witness-engine/
