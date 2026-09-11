# ECG Strip Generator — Handoff

Last updated: 2026-09-11

## Latest closeout — PVC/NCT teaching selection

- Owner requested recording and a local commit of this session; no new push authorized.
- Selected MITDB119 target42126 as the beginner PVC example.
- Approved pedagogical sequence: cleaner MITDB209 case-4b9e906f0b6e6ea7,
  artifact MITDB209 case-25717c7e542ef962, then SVDB840 case-cd7f2bf3bac107f3.
  These are not one chronological recording or one continuous patient event.
- Read docs/reviews/2026-09-11-approved-pvc-nct-teaching-sequence.md first.
  Teach suspected hidden P waves/P-T separation and uncertainty; do not require
  confirmed ST conversion. Adenosine discussion is conditional, not a universal
  test for irregular NCT/MAT or a guarantee of diagnosis. Draft release fields unchanged.
- 840 dual-channel 70-second context and independent sample comparison are in
  docs/reviews/2026-09-11-svdb840-transition-review.md and ignored output artifacts.
- This is candidate review, not full M5 AFDB/VFDB implementation. Resume that
  approved scope separately; no need to repeat the search for the accepted examples.
- Fresh closeout tests: 264 passed, 6 source-dependent skips without explicit
  dataset environment variables; six review scripts pass Ruff lint and format.
  Earlier 270-pass configured-data run remains historical, not this run's result.
- Verify Git and canonical Obsidian dashboard for commit/sync status on resume.
  All sections below are historical checkpoints, not current pending instructions.

## Latest owner-reviewed checkpoint

- M4 implementation commit: 3d38f3a. Owner authorized commit and push of review
  documentation and pending M4 work on 2026-09-11; verify Git state on resume.
- SVDB 800 sample 61322: possible aberrantly conducted PAC; source V preserved.
  See docs/reviews/2026-09-11-svdb-800-possible-aberrant-pac.md for facts and limits.
  Advanced discussion only; excluded from beginner typical-PVC examples.
- MITDB 100 targets 66792/74986 accepted as PAC demonstration/practice.
  Clarity accepted; physical dimensions unverified and not required to continue review.
- Next: select a clearer typical PVC and a real narrow-complex candidate.
  Teaching release remains pending. The recovery checklist below is historical.

## Current position

- Milestone 4 implementation and technical verification are complete.
- Expected local commit subject: `feat: add ectopy and supraventricular source paths`.
  Read Git history and status for its SHA and current working-tree state.
- The 2026-09-11 push is explicitly authorized; future pushes need separate approval.
- The earlier usage-limit interruption was recovered using scoped approved commands.

## Completed so far

- Added ECG1/ECG2 channel metadata and profile handling.
- Added WFDB source/profile support for SVDB, MITDB, and INCARTDB.
- Added annotated-source discovery and teaching-case support.
- Added coverage/reporting support and unit tests.
- Added `docs/milestone-4-checkpoint.md`.
- Generated preview material is under ignored `output/`; do not commit it.

## Evidence and decisions

- SVDB officially labels signals only as ECG1 and ECG2.
- Available background supports the hypothesis that ECG1 is commonly modified Lead II and ECG2 commonly a chest lead near V1.
- This remains a provenance-qualified hypothesis, not a universal record-level fact.
- Do not silently claim exact lead identity when the source header does not provide it.
- Preserve the no-silent-default calibration policy.

## Verification status

- Resume verification on 2026-09-10: 270 tests passed, no skips, using explicit
  local PTB-XL/MITDB/SVDB/INCART bundles.
- Added tests/dataset/test_annotated_local.py for independent raw ADC decoding,
  WFDB comparison, annotation alignment and draft audit.
- Coverage E501 fixed; Ruff lint/format, uv lock and diff checks passed.
- Both historical Hindsight operations completed with extracted facts; project recall
  confirms the M4 scope and owner approval.
- Obsidian dashboard updated using the official adapter with matching readback hashes.

SVDB visual review and coverage smoke check passed. The checklist below is retained
as historical recovery procedure. Next: verify the local milestone commit, obtain
separate push approval, then follow owner direction for Milestone 5. Clinical review,
teaching release, physical printing and a real narrow-complex example remain pending.

## Resume checklist

1. Read current project instructions and relevant Hindsight pages.
2. Run fresh `rtk git status`, `rtk git diff --stat`, and `rtk git diff`.
3. Fix the unresolved Ruff E501 issue.
4. Run:
   - `python -m pytest tests/unit/test_annotated_sources.py`
   - `python -m pytest`
5. Rerun Ruff and independently confirm the result.
6. Review scope, privacy, provenance, generated files, and secrets.
7. Update the canonical Obsidian dashboard through the official CLI adapter with pre-image/readback checks.
8. Verify Hindsight retains at fact level.
9. If all checks pass, create the approved local Milestone 4 commit.
10. Ask separately before any remote push.

## Do not do

- Do not commit downloaded source bundles, generated previews, caches, secrets, or patient-identifiable data.
- Do not treat previews as proof of record-level lead identity.
- Do not push without explicit approval.
- Do not write to the Obsidian Vault directly.
