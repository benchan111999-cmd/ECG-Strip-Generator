# Milestone 4 execution checkpoint

Parent: [approved execution plan](plans/2026-09-05-ecg-strip-generator-revised-execution-plan.md),
Milestone 4 and owner clarification dated 2026-09-10.

## Baseline and boundary

- Start: main at 96c902af1e86a3f44979a30587357679bffbb5f8; upstream divergence 0/0,
  clean staged/unstaged/untracked state, one worktree, no active Git operation.
- User-visible need: reproducible beat/context evidence for PAC, PVC and
  mechanism-neutral narrow-complex candidates, with honest coverage.
- Change necessity: the existing adapter handles only PTB-XL statements;
  documentation or one-off plots cannot provide aligned annotation selection.
- Owner fit: expand the existing WFDB decoding owner with pinned source profiles;
  one annotation owner and one coverage projection. Reuse the draft packager.
- Complexity budget: source files below 400 lines, no duplicate renderer,
  no registry snapshot rewrite, no catalog/release engine or M5 sources.
- TDD route: mode off / skipped; no strict authority. Behavioral tests accompany
  implementation, including malformed source refusal and PTB-XL regressions.
- Architecture review: bounded source-profile and evidence interfaces only;
  no new persistence, deployment or clinical approval authority.
- Required baseline read: plan, AGENTS, WFDB reader, PTB-XL selection,
  package builder, CLI, source/package tests, official WFDB and source docs.

## Work slices

1. Implemented: source profiles, preserved annotation coordinates and context.
2. Implemented: shared draft packaging, CLI selection, coverage projection.
3. Verified: fixtures, real-source tests, SVDB visual check and draft coverage smoke check.

## Resume verification, 2026-09-10

- Baseline HEAD remains 96c902af1e86a3f44979a30587357679bffbb5f8 on main.
- Fixed coverage.py E501 without changing the emitted string.
- Added opt-in real MITDB/SVDB/INCART tests with independent raw ADC decoding,
  WFDB physical comparison, exact annotation windows and draft audit.
- Full suite with explicit local PTB-XL/MITDB/SVDB/INCART bundles: 270 passed,
  no skips (32.19 seconds). Ruff check, format check (43 files), uv lock check,
  and git diff --check passed before documentation-only updates.
- No additional source downloads or remote push. Clinical review remains pending.
- Obsidian dashboard updated through official adapter with matching CLI/filesystem
  SHA-256 readback. Historical Hindsight operations both completed with extracted facts.
- Final scope is M4 source/profile/annotation/coverage code, tests and documentation.
  Generated data/output remain ignored. Approved commit subject:
  `feat: add ectopy and supraventricular source paths`; see Git history for its SHA.
- Confidence: B. Automated source-path obligations passed; clinical/teaching review,
  physical printing and a real narrow-complex example remain outside this verification.

## Verification obligations

Compare extracted samples with independent raw-byte decoding and WFDB; check
half-open annotation boundaries, required surrounding beats, no S-to-PAC or
SVTA-to-AVNRT/AVRT relabelling, no ECG1/2 standard-lead substitution, no student
answer leakage, and no candidate-to-release escalation. Preserve original data.
Run full available-source tests, Ruff, lock and exact diff checks before commit.

No clinical review, teaching release, physical print approval or remote push
is authorized by automated verification.
