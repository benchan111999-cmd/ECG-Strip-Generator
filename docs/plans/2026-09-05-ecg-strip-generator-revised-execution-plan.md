# ECG Strip Generator — Revised Execution Plan

**Date:** 2026-09-05
**Status:** Approved by the project owner on 2026-09-05
**Repository:** `C:\Projects\ECG Strip Generator`
**Replaces:** The proposed 27-phase execution plan
**Implementation authorization:** Owner approved Milestones 0–7 on 2026-09-05 and requested that work begin with Milestone 0. Remote push remains separately gated.

## 1. Purpose

Build a reproducible, teaching-only ECG strip generator that can prepare clinically reviewed examples for systematic ECG interpretation during lectures.

The completed tool must support:

- one-lead, two-lead, and twelve-lead presentation;
- normal rhythm;
- narrow-complex tachycardia;
- wide-complex tachycardia;
- bradyarrhythmias;
- heart blocks;
- atrial fibrillation, including separate onset and termination examples;
- atrial flutter;
- ventricular tachycardia;
- ventricular fibrillation;
- asystole;
- premature atrial complexes;
- premature ventricular complexes; and
- paced rhythms and selected pacing malfunctions.

The system is **real-data first**. Synthetic signals are a clearly labelled, human-reviewed fallback for teaching gaps. The tool does not diagnose patients and does not create clinical evidence.

## 2. Confirmed Owner Decisions

The following decisions are already approved:

1. This is a standalone tool-development subproject of ECG Course.
2. Current use is personal, non-commercial education only. It is not for patient care, clinical diagnosis, formal institutional operation, or a paid course.
3. The existing repository is used directly. Do not create a nested repository or run `git init` again.
4. Local commits may be created automatically after an approved milestone passes its checks.
5. Remote push always requires separate owner approval.
6. Deployment is out of scope.
7. English is primary for code and documentation; zh-HK may be added where it improves teaching use.
8. Onset and termination may be illustrated by separate strips. If they come from different episodes, the output must not imply continuity or shared case identity.
9. Core real-data sources are PTB-XL, INCART, MIT-BIH Arrhythmia, MIT-BIH Atrial Fibrillation, MIT-BIH Supraventricular Arrhythmia, MIT-BIH Malignant Ventricular Ectopy, and MIT-BIH Normal Sinus Rhythm.
10. CU Ventricular Tachyarrhythmia and Sudden Cardiac Death Holter are supplementary sources, not primary truth sources.
11. The primary renderer is an in-house deterministic Matplotlib/PDF renderer.
12. ECG-Image-Kit is optional and cosmetic only. It must not change waveforms, lead identity, timing, or calibration.
13. NeuroKit2 may support synthetic prototypes but does not establish clinical correctness.
14. Hindsight remains routed through `proj-ecg-course` with the `project:ecg-strip-generator` tag. No new bank is required now.

## 3. Non-Goals

This plan does not include:

- clinical decision support or automated diagnosis;
- patient-identifiable data;
- inference of missing leads from one- or two-lead recordings;
- diagnosis-grade claims for synthetic twelve-lead ECGs;
- a web application or deployment configuration;
- automatic GitHub push;
- AI-generated diagnosis labels;
- public redistribution of raw datasets;
- making every dataset a prerequisite for basic operation; or
- creating five overlapping repository-local skills before the workflow is stable.

## 4. Success Criteria

The project is successful when all of the following are true:

1. A clean installation can run the core CLI in a uv-managed Python 3.12 environment.
2. The renderer supports one-, two-, and twelve-lead layouts without inventing unavailable leads.
3. Print-ready PDF output is physically calibrated at the declared paper speed and gain when printed at 100% scale.
4. Digital PNG output carries time and voltage metadata but does not claim physical millimetre accuracy.
5. Every rendered strip has a machine-readable manifest with source, lead, timing, transformation, licence, and review information.
6. Raw source data remains immutable and outside Git.
7. Student and instructor packages are physically separated and pass answer-leak checks.
8. Every released teaching strip has passed technical validation, clinical review, and teaching-release approval as separate decisions.
9. Each requested rhythm category has at least one approved teaching example in an appropriate lead format, or is honestly reported as a coverage gap.
10. No test or report silently upgrades an uncertain source label into a precise clinical mechanism.

## 5. Clinical Authority Model

Four independent axes must be recorded for every case.

### 5.1 Source evidence

Allowed values:

- `real_manual_rhythm_annotation`
- `real_manual_beat_annotation`
- `real_dataset_diagnostic_statement`
- `real_dataset_metadata_only`
- `synthetic_didactic`

Source evidence states what the dataset or recipe actually provides. It does not represent project approval.

### 5.2 Technical validation

Allowed values:

- `not_run`
- `passed`
- `failed`

Technical validation covers file integrity, units, gain, sampling rate, lead identity, timing, rendering geometry, and output completeness.

### 5.3 Clinical review

Allowed values:

- `not_reviewed`
- `approved`
- `approved_with_limited_label`
- `rejected`

Only an explicitly assigned clinical reviewer may approve the clinical label and teaching interpretation. If the source supports only “supraventricular tachyarrhythmia,” the project must not publish “AVNRT” or “AVRT” without separate evidence and review.

### 5.4 Teaching release

Allowed values:

- `draft`
- `approved`
- `retired`

Teaching approval governs whether an example may enter a lecture pack. It does not increase clinical certainty.

The per-case manifest is the canonical approval record. SQLite and folder location are derived views and must not hold competing approval states.

## 6. Data-Source Portfolio

| Dataset | Role | Expected lead use | Primary teaching coverage | Important limits |
|---|---|---:|---|---|
| PTB-XL | Core | 12; may select 1 or 2 recorded leads | Normal, conduction findings, static twelve-lead interpretation | Ten-second records; multi-label statements; not a transition source |
| INCART | Core | 12; may select 1 or 2 recorded leads | Multi-lead ectopy and rhythm comparison | Beat annotations do not prove every rhythm mechanism |
| MIT-BIH Arrhythmia | Core | 1 or 2 recorded leads | PAC, PVC, ectopy, paced beats, rhythm-strip practice | Mainly beat-level reference annotations |
| MIT-BIH SVDB | Core | 1 or 2 recorded leads | Supraventricular ectopy and narrow-complex tachyarrhythmia | Do not assume AVNRT versus AVRT mechanism |
| MIT-BIH AFDB | Core | 1 or 2 recorded leads | AF and atrial-flutter onset, established rhythm, and termination examples | Prefer manual rhythm annotations; some beat annotations are automated |
| MIT-BIH VFDB | Core | 1 or 2 recorded leads | VT, VF, ventricular flutter, asystole, sinus bradycardia, first-degree block, escape and paced rhythm | Rhythm-change labels only; no beat labels |
| MIT-BIH NSRDB | Core | 1 or 2 recorded leads | Clean long-duration normal sinus rhythm | Normal-reference source, not twelve-lead |
| CUDB | Supplementary | Recorded leads only | Additional VT/VF candidates | Event labels are not definitive; VF onset can be approximate |
| SDDB | Supplementary | Recorded leads only | Additional malignant rhythm and pacing candidates | Audited annotations are incomplete |

Official references:

- https://physionet.org/content/ptb-xl/1.0.3/
- https://physionet.org/content/incartdb/1.0.0/
- https://physionet.org/content/mitdb/1.0.0/
- https://physionet.org/content/svdb/1.0.0/
- https://physionet.org/content/afdb/1.0.0/
- https://physionet.org/content/vfdb/1.0.0/
- https://physionet.org/content/nsrdb/1.0.0/
- https://physionet.org/content/cudb/1.0.0/
- https://physionet.org/content/sddb/1.0.0/

Datasets are registered first and downloaded only when required by the current approved milestone.

## 7. Rhythm Coverage Strategy

| Teaching category | Preferred real source | Synthetic fallback | Release rule |
|---|---|---|---|
| Normal sinus rhythm | NSRDB; PTB-XL for 12-lead | Optional variation only | Real source preferred |
| PAC | MIT-BIH Arrhythmia; SVDB; INCART | Controlled timing variation | Confirm beat annotation and surrounding rhythm |
| PVC | MIT-BIH Arrhythmia; INCART | Controlled timing and morphology variation | Confirm ventricular beat annotation |
| Narrow-complex tachycardia | SVDB; VFDB `SVTA`; AFDB where applicable | Didactic regular narrow tachycardia | Publish mechanism-neutral label unless mechanism is independently supported |
| AF | AFDB; PTB-XL for static 12-lead | Didactic fallback only | Use manual rhythm annotations for transition examples |
| Atrial flutter | AFDB; PTB-XL if label is suitable | Didactic fallback | Clinical review required for flutter-wave interpretation |
| Wide-complex tachycardia | VFDB; supplementary CUDB/SDDB | Didactic undifferentiated WCT | Do not label VT solely from QRS width |
| VT | VFDB; supplementary CUDB/SDDB | Didactic fallback | Prefer explicit VT rhythm annotation |
| VF | VFDB; supplementary CUDB/SDDB | Didactic fallback | Mark approximate boundaries when the source is approximate |
| Asystole | VFDB where available | Controlled didactic example | Real scarcity must be disclosed; synthetic source must be prominent |
| Sinus bradycardia | VFDB; selected real cases | Controlled-rate fallback | Verify sinus features during clinical review |
| First-degree AV block | VFDB; PTB-XL candidates | Didactic fallback | PR measurement and clinical review required |
| Mobitz I, Mobitz II, complete block | Reviewed real case if found | Planned didactic fallback | Never release solely from an unverified automated recipe |
| Paced rhythm | VFDB; MIT-BIH Arrhythmia; SDDB candidates | Didactic fallback | Confirm visible pacing evidence and capture relationship |
| Pacing failure modes | Reviewed real case if available | Planned didactic fallback | Clinical review required for each failure mechanism |

Coverage reporting must use `released`, `candidate`, `synthetic_review_required`, or `gap`. A category must never be marked complete merely because code can render a similarly shaped signal.

## 8. Lead and Time Rules

1. A renderer may show only leads present in the source header or explicitly produced by an approved synthetic recipe.
2. A twelve-lead source may be rendered as one or two selected leads without changing the underlying signal.
3. A one- or two-lead source must never be expanded into twelve leads by copying, scaling, or relabelling channels.
4. Missing Lead II is an error when Lead II is requested. There is no first-lead fallback.
5. Units must be converted to mV from source metadata. Unknown gain or units block release.
6. Twelve-lead output must declare whether columns are simultaneous or sequential time segments.
7. Separate onset and termination strips use independent case identifiers unless they are extracted from the same verified episode.
8. Separate strips may be linked by a teaching-set identifier, but the label must say `illustrative_pair` when they are not the same episode.

## 9. Rendering Contract

### 9.1 Primary renderer

Implement a deterministic Matplotlib-based renderer with:

- one-, two-, and twelve-lead layouts;
- configurable paper speed, default 25 mm/s;
- configurable gain, default 10 mm/mV;
- major and minor ECG grid;
- calibration pulse;
- explicit lead labels;
- optional title and neutral teaching prompt;
- deterministic colours, dimensions, fonts, and margins; and
- PDF and PNG output.

### 9.2 Physical calibration

Only PDF output may claim physical millimetre calibration. Validation must calculate expected page dimensions from duration, lead layout, paper speed, gain, margins, and calibration pulse. Documentation must instruct users to print at 100% with “fit to page” disabled.

PNG output is for screen display. It records pixel dimensions, DPI metadata, time scale, and voltage scale but does not claim that a screen displays physical millimetres.

### 9.3 Optional cosmetic renderer

ECG-Image-Kit is deferred until the core system is complete. If added later:

- run it in an isolated legacy environment;
- disable random waveform-affecting behaviour;
- do not accept modified WFDB files as source truth;
- compare its output against the canonical render manifest;
- prohibit automatic lead substitution; and
- treat paper damage, scanning, handwriting, and perspective effects as cosmetic derivatives only.

## 10. Synthetic Signal Contract

Synthetic output is allowed only as `synthetic_didactic`.

Every recipe must record:

- recipe name and version;
- random seed;
- target rhythm label;
- rate and timing parameters;
- morphology parameters;
- pacing parameters when applicable;
- source library and version;
- technical validation result;
- clinical review result; and
- known teaching limitations.

The first synthetic release supports one- and two-lead output only. Synthetic twelve-lead release is disabled until a separate, physiologically justified lead-vector model and clinical validation plan are approved.

NeuroKit2 may supply prototype waveforms but must not be cited as proof of diagnostic correctness.

## 11. Data Lifecycle and Provenance

### 11.1 Local data layout

Proposed local-only paths:

```text
data/
  staging/
  raw/
  derived/
  catalog/
```

All are ignored by Git except placeholder documentation where needed.

Downloads follow this sequence:

1. Download to `data/staging/<dataset>/<version>/`.
2. Record source URL, retrieval time, dataset version, and declared licence.
3. Verify an official checksum where supplied.
4. Otherwise record the checksum as `locally_observed`, not `official`.
5. Reject incomplete or mismatched files.
6. Promote verified files atomically into `data/raw/`.
7. Never modify files under `data/raw/`.

### 11.2 Public source registry

Track a small registry containing:

- dataset identifier and version;
- official landing page;
- licence and required attribution;
- citation;
- expected lead and annotation characteristics;
- download status as local runtime information, not committed state; and
- known limitations.

### 11.3 Per-case manifest

Each candidate and released case records:

- project case ID;
- source dataset and version;
- de-identified source record ID;
- source annotation file or metadata field;
- start and end sample/time;
- recorded lead names;
- displayed lead names;
- sampling rate and physical units;
- transformations performed;
- source checksum reference;
- renderer and version;
- layout and time-alignment mode;
- output checksums;
- attribution notice;
- the four independent review axes; and
- teaching-pair relationship, if any.

Do not store patient identifiers, source patient IDs, local absolute paths, usernames, or credentials in committed manifests.

## 12. Student and Instructor Packages

Student and instructor outputs must be generated into separate roots.

```text
output/
  student/
  instructor/
```

Student output may contain:

- ECG image or PDF;
- neutral, non-identifying context approved for teaching;
- systematic interpretation prompts; and
- case ID that cannot reveal the diagnosis.

Instructor output may additionally contain:

- approved rhythm label;
- source evidence and certainty;
- measurements and teaching points;
- answer key; and
- review and attribution summary.

Automated leak checks must search student filenames, image metadata, PDF metadata, visible text, manifest exports, QR codes, and package indexes for diagnosis labels and instructor-only fields.

## 13. Proposed Repository Structure

```text
docs/
  architecture.md
  clinical-safety.md
  data-sources.md
  rendering-and-calibration.md
  plans/
src/
  ecg_strip_generator/
    cli.py
    models.py
    datasets/
      registry.py
      wfdb_adapter.py
      ptbxl.py
      incart.py
      mitdb.py
      svdb.py
      afdb.py
      vfdb.py
      nsrdb.py
    catalog.py
    selection.py
    validation.py
    rendering/
      matplotlib_renderer.py
      geometry.py
    synthetic/
      recipes.py
    teaching_packages.py
    provenance.py
config/
  datasets.yaml
  rhythms.yaml
  render_presets.yaml
tests/
  unit/
  integration/
  dataset/
```

This structure is a target, not permission to create every file at once. Each milestone creates only the files it needs.

## 14. CLI Surface

Proposed command name: `ecg-strip`.

```text
ecg-strip doctor
ecg-strip datasets audit
ecg-strip datasets fetch <dataset>
ecg-strip catalog build <dataset>
ecg-strip coverage report
ecg-strip cases select ...
ecg-strip render <case-manifest>
ecg-strip package <teaching-set>
```

Commands must fail closed on unknown lead identity, units, gain, source version, checksum, or release status. They must never silently switch to synthetic data or a different lead.

## 15. Python Environments

### 15.1 Core environment

- uv-managed Python 3.12;
- WFDB;
- NumPy;
- SciPy;
- pandas;
- Matplotlib;
- Pydantic;
- PyYAML;
- Typer;
- Rich;
- Pillow;
- pytest; and
- Ruff.

Pin resolved versions in `uv.lock`. Do not modify the system Python installation.

### 15.2 Optional ECG-Image-Kit environment

Do not create this environment during core milestones. If later approved, isolate it from the core environment because its documented Python and NumPy requirements conflict with the current core stack and Python 3.10 is approaching end of support.

## 16. Test Strategy

### 16.1 Fast tests

Run without external datasets:

- schema validation;
- lead-name guardrails;
- unit conversion;
- deterministic rendering;
- geometry calculations;
- manifest generation;
- output separation; and
- answer-leak detection.

### 16.2 Dataset integration tests

Mark as dataset-dependent and run only when the named local dataset is available:

- WFDB header and signal loading;
- annotation parsing;
- source-window extraction;
- real lead identity;
- checksum verification; and
- candidate selection.

Public CI must not require downloading all datasets.

### 16.3 Visual and physical checks

- Verify PDF page size and plotted geometry numerically.
- Maintain a small, licence-compliant set of golden render fixtures.
- Compare deterministic PNG output within a documented tolerance.
- Perform manual 100% print measurement before claiming calibrated release.

### 16.4 Human review

Automated tests cannot approve clinical accuracy. Clinical review and teaching release remain explicit human gates.

## 17. Execution Milestones

### Milestone 0 — Governance and project skeleton

**Goal:** Make the repository rules consistent with the approved decisions and create the minimal Python project.

**Planned changes:**

- amend, do not replace, `AGENTS.md`;
- record automatic milestone commits and manual push approval;
- update `README.md` and `.gitignore`;
- confirm rather than invent the project code licence;
- add `pyproject.toml` and uv lockfile;
- add minimal package and test skeleton; and
- add core documentation headings.

**Verification:**

- repository remains the existing repository;
- no deployment files;
- no secrets or data files tracked;
- core import succeeds;
- tests and Ruff pass; and
- working tree diff contains only Milestone 0 scope.

**Automatic commit after pass:** `chore: establish ECG generator project contract`

### Milestone 1 — Domain model, lead guard, and deterministic renderer

**Goal:** Prove one-, two-, and twelve-lead layout using non-clinical test fixtures.

**Planned changes:**

- case-manifest models;
- lead and unit validation;
- deterministic Matplotlib renderer;
- PDF and PNG outputs;
- calibration and geometry calculations; and
- unit and visual tests.

**Verification:**

- identical input and preset produce identical output checksums;
- requested missing leads fail;
- no first-lead fallback;
- PDF geometry matches declared speed and gain; and
- PNG contains no physical-millimetre claim.

**Automatic commit after pass:** `feat: add deterministic ECG rendering core`

### Milestone 2 — Dataset registry and immutable data lifecycle

**Goal:** Establish reproducible, licence-aware source handling before clinical extraction.

**Planned changes:**

- dataset registry;
- staged download and checksum workflow;
- immutable raw-data policy;
- attribution templates;
- local derived SQLite catalog design; and
- dataset-audit command.

**Verification:**

- interrupted downloads never enter `data/raw/`;
- official and locally observed checksums are distinguished;
- data directories remain untracked;
- each registry entry has version, source, licence, citation, and limitations; and
- SQLite approval fields, if any, are derived from manifests.

**Automatic commit after pass:** `feat: add reproducible ECG source registry`

### Milestone 3 — Normal and twelve-lead vertical slice

**Goal:** Deliver the first real-data teaching candidates across the lead-range boundary.

**Sources:** NSRDB and PTB-XL first; INCART adapter foundation if needed.

**Planned outputs:**

- a real one- or two-lead normal rhythm candidate;
- a real twelve-lead normal or conduction candidate;
- student and instructor draft packages; and
- complete source manifests and attribution.

**Verification:**

- waveform values originate from verified raw data;
- selected leads match source headers;
- twelve-lead time alignment is explicit;
- no diagnosis appears in student output; and
- outputs remain `draft` until human review.

**Automatic commit after pass:** `feat: add real normal and twelve-lead source path`

### Milestone 4 — Ectopy and narrow-complex rhythm path

**Goal:** Support PAC, PVC, and mechanism-neutral narrow-complex tachycardia candidates.

**Sources:** MIT-BIH Arrhythmia, SVDB, and INCART.

**Verification:**

- beat annotations align with extracted windows;
- surrounding rhythm is retained for teaching context;
- PAC and PVC labels trace to source annotation plus review;
- narrow-complex cases remain mechanism-neutral unless separately supported; and
- coverage report distinguishes released cases from candidates.

**Automatic commit after pass:** `feat: add ectopy and supraventricular source paths`

### Milestone 5 — AF, flutter, malignant rhythms, and transitions

**Goal:** Support AF, atrial flutter, VT, VF, asystole, bradycardia, escape, and paced-rhythm candidates.

**Sources:** AFDB and VFDB; CUDB and SDDB only for supplementary candidates.

**Verification:**

- AFDB transition windows use manual rhythm annotations;
- onset and termination examples may be separate and are labelled accordingly;
- unrelated examples never share an episode identity;
- VT/VF/asystole labels trace to explicit rhythm annotations or limited clinical review;
- approximate event boundaries are disclosed; and
- supplementary datasets cannot automatically override a stronger source.

**Automatic commit after pass:** `feat: add atrial and malignant rhythm source paths`

### Milestone 6 — Synthetic teaching-gap engine

**Goal:** Fill only the remaining teaching gaps with deterministic, review-gated one- or two-lead recipes.

**Priority gaps:**

- Mobitz I;
- Mobitz II;
- complete heart block;
- selected pacing failure modes;
- controlled asystole when suitable real material is unavailable; and
- repeatable rate or ectopy variations for practice.

**Verification:**

- every output is visibly and structurally labelled synthetic;
- recipes are deterministic from recorded parameters and seed;
- no synthetic twelve-lead release;
- no recipe is released without clinical review; and
- coverage report does not merge synthetic and real evidence classes.

**Automatic commit after pass:** `feat: add review-gated synthetic teaching recipes`

### Milestone 7 — Teaching packs and release audit

**Goal:** Produce a clinically reviewed baseline lecture-practice pack.

**Verification:**

- one-, two-, and twelve-lead renderer support is demonstrated;
- each requested rhythm category is `released` or explicitly remains a `gap`;
- every released case has separate technical, clinical, and teaching approval;
- student packages pass visible-text, filename, metadata, and index leak checks;
- instructor packages contain source and attribution information;
- all fast tests pass;
- available dataset tests pass; and
- repository contains no raw datasets, patient identifiers, credentials, or local paths.

**Automatic commit after pass:** `feat: add reviewed ECG teaching pack workflow`

### Milestone 8 — Optional enhancements

This milestone is not part of core completion.

Possible later work:

- ECG-Image-Kit cosmetic rendering adapter;
- additional CUDB and SDDB candidates;
- extra real sources for heart block or pacing malfunctions;
- a user interface;
- a single orchestration skill after the workflow is stable; and
- deployment, only under a separately approved plan.

Each enhancement requires its own scope and approval. No automatic remote push is implied.

## 18. Commit and Push Policy

After this plan is approved:

1. Complete one milestone at a time.
2. Run the milestone checks.
3. Inspect the exact diff.
4. If checks pass and the diff is within the approved milestone, create the listed local commit automatically.
5. Report the commit hash, checks, known gaps, and next milestone.
6. Do not push unless the owner explicitly approves the push.
7. If a milestone changes scope, stop and request approval before committing the expanded scope.

## 19. Stop Conditions

Stop the affected operation rather than silently falling back when:

- source licence or attribution obligations are unresolved;
- checksum verification fails;
- source version cannot be established;
- lead name, unit, gain, or sampling rate is missing or contradictory;
- an annotation does not support the requested clinical label;
- a source window crosses missing or corrupted data without disclosure;
- synthetic output is not clearly identified;
- PDF geometry verification fails;
- student output leaks an answer;
- clinical review is absent for release;
- personal non-commercial use changes; or
- implementation requires deployment or remote push.

## 20. Project Records

Responsibilities remain separate:

- **Repository documents and manifests:** technical contract, source evidence, and reproducibility.
- **Git:** reviewed implementation history.
- **Obsidian dashboard:** canonical project progress and owner-facing status.
- **Hindsight:** compact decisions, blockers, failure modes, and next steps.

Do not automatically copy full repository documents into Hindsight. Do not treat Hindsight as the source of full clinical content.

## 21. Approval Gate

Approval of this document authorizes Milestones 0–7 in the stated order, including required dependency and dataset downloads and automatic local milestone commits, subject to the stop conditions above.

It does **not** authorize:

- remote push;
- deployment;
- commercial or institutional use;
- publication of unreviewed ECG teaching cases;
- new live skills; or
- work outside the stated milestones.

Implementation starts only after the owner explicitly approves this revised plan.
