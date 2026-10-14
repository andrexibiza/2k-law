# The 2K Law

**An architectural ratchet by Axl Ibiza, MBA.**

No repository-owned code file above 2,000 physical lines. Existing oversized files are explicit debt: they may shrink, never grow, and their allowances disappear when they reach the ceiling.

The 2K Law is one pillar of my graph-gated, adversarially verified transformation architecture. The other is independent verification: the actor that produces a change does not certify it. [Read the complete teaching page](https://axlibiza.com/learn/blind-witness-engine/) and [*All Gods Must Die*](https://axlibiza.com/writing/all-gods-must-die/).

This repository makes the **size ceiling, legacy ratchet, exact-byte comparison, and declared Python Seam Identity checks** reusable. It does not pretend that a line counter implements the entire witness protocol or proves runtime correctness.

## Install

Python 3.11 or newer and Git are required. Runtime dependencies: none.

```bash
git clone https://github.com/andrexibiza/2k-law.git
cd 2k-law
python -m pip install .
2k-law check --root /path/to/your/repository
```

A virtual environment is recommended. On Windows, repository paths such as `C:/projects/example` work. Use the environment's `python` and `2k-law` executables. For automation, install a reviewed immutable commit rather than a moving branch:

```text
python -m pip install "git+https://github.com/andrexibiza/2k-law.git@FULL_REVIEWED_COMMIT_SHA"
python -I -m two_k_law check --root /path/to/your/repository
```

`FULL_REVIEWED_COMMIT_SHA` is a placeholder to replace with the actual reviewed revision, not a published package identifier. This project is not advertised as available on PyPI.

## What the check means

- **`pass`**: complete inventory, no reported violations, and no remaining oversized source.
- **`pass_with_debt`**: complete inventory and a passing comparison to an explicitly supplied accepted base; some tracked source still exceeds 2,000 lines.
- **`fail`**: an evaluated violation. Exit **1**.
- **`error`**: invalid inputs, unavailable objects, or incomplete inventory. Exit **2**, never a pass.
- Successful checks exit **0**. Argument-parser usage errors also exit 2.

Output is JSON. It includes each measured source path, raw-byte SHA-256, physical line count, excluded paths/reasons, base identity, findings, remaining debt, and excess lines. `baseline` instead prints a proposed manifest; its successful execution is **not compliance**.

Normal `check`, `baseline`, and `bytes` commands do not import target Python modules, execute project build scripts, install its dependencies, or modify its source. Runtime `seam` checking is a separate, explicit code-execution operation.

## Adopt an existing repository

A baseline is an acknowledgement of debt, not permission for future growth.

```bash
2k-law baseline --root /path/to/project > proposed-2k-law.json
```

Review the inventory and place the accepted proposal at the target repository's root as `.2k-law.json`. Example shape:

```json
{"version": 1, "limit": 2000, "files": {"legacy.py": 4200}}
```

The example count is illustrative. The actual proposal is measured from the selected repository. The tool never installs the proposal automatically. The accepted baseline belongs in version control; record the full commit SHA that contains both the source and its exact manifest. That reviewed adoption commit is the initial trust root.

```text
2k-law check --root /path/to/project --base FULL_ACCEPTED_BASE_COMMIT_SHA
```

The base must be present locally and be a full lowercase commit SHA. No branch names or abbreviated identifiers are accepted. The engine reads the previous manifest and source directly from Git objects, with replacement refs and lazy fetch disabled. It compares each surviving oversized file against the **actual previous measurement**, not merely an old ceiling in the candidate manifest.

After extracting code, `baseline` can produce the new measured ledger. Updating it cannot legalize a growth or a new oversized file: `check --base ...` compares it against the independently accepted base. Current entries must match current measurements exactly. Deleted/compliant paths must leave the ledger. Oversized renames receive no automatic allowance transfer in this version.

A stale accepted ledger fails too. Each accepted change must therefore carry its updated measured debt. To prevent shrink-then-regrow, CI must compare to the current accepted base rather than continuing to use the original adoption commit forever.

**The tool cannot choose your authority.** A caller who supplies an old or attacker-selected base, replaces the checker, changes the workflow, or weakens repository-required checks can defeat that governance. Protect the workflow and choose the base outside the candidate's control. A full SHA identifies bytes; it does not grant those bytes authority.

## GitHub Action

For a repository with no legacy debt, a checked-out tree and Python 3.11+ are sufficient:

```yaml
name: 2K Law
on: [push, pull_request]
permissions:
  contents: read
jobs:
  size:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
        with:
          persist-credentials: false
      - uses: andrexibiza/2k-law@v0.1.0
```

For legacy ratcheting, supply a trusted base and fetch its objects. A pull-request-only job can use GitHub's PR-object base SHA:

```yaml
name: 2K Law ratchet
on: [pull_request]
permissions:
  contents: read
jobs:
  ratchet:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          fetch-depth: 0
          persist-credentials: false
      - uses: andrexibiza/2k-law@v0.1.0
        with:
          base: ${{ github.event.pull_request.base.sha }}
```

For strongest supply-chain pinning, replace the version tag with its reviewed full commit. This composite Action calls the same Python engine through a fixed adapter and passes user inputs as environment data, not shell code. It does **not** run runtime seam imports. Do not use a privileged `pull_request_target` workflow to execute untrusted target code. Required-check configuration and acceptance of the latest head/base remain repository-owner responsibilities; this tool does not make live GitHub freshness decisions.

## Exact-byte relocation evidence

Compare a 1-based, inclusive line window from an immutable Git commit with an equal-length window in a moved file:

```text
2k-law bytes --root /path/to/project --base FULL_SOURCE_COMMIT_SHA \
  --source original.py --start 20 --end 40 \
  --target extracted.py --target-start 5
```

The output includes both SHA-256 values. Whitespace and CRLF/LF differences are differences: this is raw-byte evidence, not AST normalization. The comparison reads the original from Git, not from a candidate-owned expected hash. Window selection is part of the reviewed contract. A matching window does not verify imports, initialization, patch routing, callers, or behavior.

## Python Seam Identity

A seam specification can assert a re-export and a method inherited through its original class:

```json
{
  "version": 1,
  "checks": [
    {"kind": "object", "original": "original:helper", "moved": "extracted:helper"},
    {"kind": "inherited", "original": "original:Adapter", "moved": "extracted:Mixin", "member": "send"}
  ]
}
```

```text
python -I -m two_k_law seam --root /path/to/project \
  --spec seams.json --allow-execution
```

**This executes target imports with the caller's privileges. It is not a sandbox.** Use only in an environment where that code is trusted to execute. It is disabled without the explicit command-line acknowledgement. Both endpoint modules must resolve inside the selected root. Install trusted project dependencies separately if needed.

Object checks require functions or classes, not interned strings or numbers. Inherited checks require the declared mixin to be the actual MRO owner, reject direct shadowing in the original class, and handle Python functions, staticmethods, classmethods and properties distinctly. Classmethods also retain the original class as receiver.

Identity does not prove that an old-namespace monkeypatch intercepts a real call, that `super()` means the same thing, or that initialization/serialization is unchanged. Application-owned behavioral regressions and independent witnesses still do that work.

## Inventory contract and limits

- The metric counts LF, CRLF and lone CR as physical line endings, plus a final unterminated line. Blank lines and comments count. Exactly 2,000 is allowed.
- The filesystem scan includes untracked and ignored source. At a Git root, missing tracked source is an error. A directory-only scan is supported when no `.git` is present.
- Known non-code documents/configuration and binary assets are excluded and reported. Unknown nonbinary text is conservatively counted. Known source containing NUL or UTF-16/32 encoding markers is rejected, not silently omitted.
- Root dependency/build/vendor directories and dependency/cache subtrees are excluded by the fixed versioned policy. An absolute ancestor named `build` does not exclude your project; first-party `src/build/` is scanned. Excluded root directories must actually be generated or third-party: the scanner cannot infer semantic ownership from a path. Keep first-party code outside those declared exclusions.
- Observed source symlinks, junctions/reparse points and unsupported Git modes are refused. A changing source file is an error. These checks assume a quiescent checkout: they are not an OS containment boundary against a hostile concurrent filesystem writer.
- Limits: 50,000 entries, 32 MiB per selected file, 256 MiB total selected bytes, 1 MiB manifest, and bounded Git reads. Exhaustion is an error. The tool does not silently narrow a scan to fit.
- Submodules, exotic encodings and custom descriptors are not silently treated as verified source. Use a separately defined integration if your repository requires them.
- No automatic rewrites, exemption widening, network calls, or model calls. Git and the Python installation are trusted dependencies.

## Verification

```bash
python -m pip install .
python -I -m unittest discover -s tests -v
python -I -m two_k_law check --root .
python scripts/smoke.py
```

The suite includes boundary and rejection cases, real temporary Git histories, exact-base ledger transitions, installed CLI subprocesses, Action-adapter parity, import opt-in and descriptor identity. Hosted CI runs on Linux and Windows. Passing cases establish their asserted properties—not universal runtime correctness or total language coverage. [Provenance and historical boundaries](docs/PROVENANCE.md).

## Authorship and license

The 2K Law, graph-gated engineering and adversarially verified transformation architecture were authored by **Axl Ibiza, MBA**. Hermes is the original documented case study, not the owner of the doctrine. This implementation is authored under that direction and retains links to the historical contributions and their actual integration status. Other contributors retain credit for their work.

MIT licensed. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
