# Data sources

## Registry authority

Milestone 2 implements a packaged registry at
`src/ecg_strip_generator/datasets/sources.json`. It ships with the installed
package and works outside the checkout; there is no second editable registry
under `config/`. Entries contain version, role, licence, source citation,
expected lead/annotation characteristics, limitations and review date.
Landing, file and licence URLs are constructed from the fixed PhysioNet
identifier and version. Local availability is computed from bytes, never
written into the public registry.

Official source review: **2026-09-06**. All nine pinned releases list
`SHA256SUMS.txt`. Registration is an assessment for the approved personal,
non-commercial educational workflow, not clinical approval or a grant of
project code rights.

| Source | Version | File licence | Official source / citation |
| --- | --- | --- | --- |
| PTB-XL | 1.0.3 | CC BY 4.0 | [Source](https://physionet.org/content/ptb-xl/1.0.3/), [DOI](https://doi.org/10.13026/kfzx-aw45) |
| INCART | 1.0.0 | ODC-By 1.0 | [Source](https://physionet.org/content/incartdb/1.0.0/), [DOI](https://doi.org/10.13026/C2V88N) |
| MIT-BIH Arrhythmia | 1.0.0 | ODC-By 1.0 | [Source](https://physionet.org/content/mitdb/1.0.0/), [DOI](https://doi.org/10.13026/C2F305) |
| MIT-BIH SVDB | 1.0.0 | ODC-By 1.0 | [Source](https://physionet.org/content/svdb/1.0.0/), [DOI](https://doi.org/10.13026/C2V30W) |
| MIT-BIH AFDB | 1.0.0 | ODC-By 1.0 | [Source](https://physionet.org/content/afdb/1.0.0/), [DOI](https://doi.org/10.13026/C2MW2D) |
| MIT-BIH VFDB | 1.0.0 | ODC-By 1.0 | [Source](https://physionet.org/content/vfdb/1.0.0/), [DOI](https://doi.org/10.13026/C22P44) |
| MIT-BIH NSRDB | 1.0.0 | ODC-By 1.0 | [Source](https://physionet.org/content/nsrdb/1.0.0/), [DOI](https://doi.org/10.13026/C2NK5R) |
| CUDB (supplementary) | 1.0.0 | ODC-By 1.0 | [Source](https://physionet.org/content/cudb/1.0.0/), [DOI](https://doi.org/10.13026/C2X59M) |
| SDDB (supplementary) | 1.0.0 | ODC-By 1.0 | [Source](https://physionet.org/content/sddb/1.0.0/), [DOI](https://doi.org/10.13026/C2W306) |

The registry retains source-specific limits: no invented leads, no automatic
mechanism inference, manual versus automated annotation distinctions, and
approximate or missing data. Header interpretation and annotation extraction
are later adapter work; byte integrity alone never validates an ECG window.

## Attribution

`ecg-strip datasets attribution <id> --changes "<actual modifications>"`
prints a reusable notice including source name/version, source and licence
links, resource citation, additional source publication where specified,
PhysioNet citation and supplied-notice retention reminder.

For [CC BY 4.0](https://physionet.org/content/ptb-xl/view-license/1.0.3/),
retain supplied creator, copyright, licence and disclaimer notices; link to
the licence and indicate modifications. For
[ODC-By 1.0](https://physionet.org/content/incartdb/view-license/1.0.0/),
retain relevant database notices and provide attribution accessible to users
of publicly used produced works. Include these notices with future teaching
derivatives. Preserve upstream notices; the generated notice does not replace
them. The registry includes the current PhysioNet citation requested on the
landing pages, [Pollard et al. (2026)](https://doi.org/10.1038/s44360-026-00096-z).

The data licences and the project's personal-use boundary are separate.
Institutional or commercial use requires a separate review under the plan.
No project code licence has been selected.

## Acquisition and immutable storage

```text
data/
  staging/<dataset>/<version>/attempt-<random>/
  raw/<dataset>/<version>/<selection-sha256>/
    files/<original-relative-path>
    official-sha256sums.txt
    receipt.json
  derived/
  catalog/
```

Each invocation selects 1–1000 exact, case-unique relative paths. No recursive
download or archive extraction occurs. Only HTTPS PhysioNet files are accepted;
redirects, HTML, encoded or partial responses and absent/invalid Content-Length
fail. Per-file limit is 256 MB, checksum list 16 MB, socket timeout 30 seconds,
and transfer budget 300 seconds checked between reads. These limits intentionally
exclude bulk archives. Keep the default ignored data root or use a dedicated
external local directory; never place a custom data root in tracked source paths.

1. An exclusively created lock serializes cooperating writers for the version.
2. Download and preserve the official checksum list in a new staging attempt.
3. Require every requested filename to have a unique official SHA-256 entry.
4. Download original bytes, check length and SHA-256, and fsync the files.
5. Write a typed receipt with exact selection, source metadata, UTC retrieval
   time, per-file URL, size, digest and checksum kind; re-read and verify it.
6. Rename the complete staging directory onto a previously absent raw bundle
   on the same filesystem. Data and receipt become visible together.

Raw bundles are append-only through this API. Repeating the same selection
verifies and returns the existing bundle without downloading or overwriting.
Different selections produce separate bundles; overlapping files may therefore
have multiple copies. A version string alone does not establish byte identity:
some upstream releases received corrections without changing version numbers.
Existing corrupted or source-mismatched bundles fail rather than being repaired.

Failed attempts remain in staging for inspection and never count as raw data.
Handled failures release only their own lock. Abrupt process termination may
leave a lock; inspect the owning process and attempt before manually removing
it. The program does not clear stale locks or delete partial source files.

Immutability is an application policy with subsequent byte auditing, not an
OS permission barrier or protection against a malicious local writer. Existing
symlinks and Windows junctions are rejected; the dedicated root must not be
concurrently modified by unrelated software. Rename provides atomic visibility,
not a guarantee against filesystem/hardware power-loss damage.

## Checksum meanings and offline audit

All currently registered sources require official checksums. Their retrieval
failure, malformed evidence, missing requested entry or mismatch **never**
falls back. Future sources without published checksums require an explicit
reviewed absence reason in the registry; their receipt uses `locally_observed`.
This means transport length was checked and local bytes hashed, not that the
publisher independently vouched for them.

An official receipt preserves the fetched checksum list and its local SHA-256.
This evidence is anchored to HTTPS retrieval, not a publisher signature.
`datasets audit` rehashes raw files and official evidence offline, checks
typed receipts and registry identity, and rejects extra or missing files.
It does not detect a coordinated malicious rewrite of all local evidence.

Statuses: `not_downloaded` (no verified raw bundle), `verified_subset`
(all local bundles checked), or `failed` (nonzero command exit).
File counts count copies across bundles, not distinct source records. Metadata
files such as RECORDS alone are still only a subset. No status implies an entire
dataset is present, waveforms are usable, or a case is reviewed.

## Derived SQLite catalog design

The catalog is **design only** in Milestone 2; record extraction starts in
Milestone 3. Proposed local path: `data/catalog/sources.sqlite3`.
It is disposable, rebuildable and ignored by Git.

| Table | Key and contents | Authoritative input |
| --- | --- | --- |
| acquisitions | dataset, version, selection; receipt relative path and SHA-256 | Verified acquisition receipts |
| files | acquisition + source relative path; bytes, digest, checksum kind | Verified file receipts and raw bytes |
| records | dataset, version, source record ID; leads, units, rate | Later validated WFDB adapters |
| cases | project case ID; manifest relative path, manifest SHA-256, source window | Per-case manifests |

First design stores **no approval columns**. Case technical, clinical and teaching
states are read from the canonical per-case manifest. If later added for queries,
they must be disposable projections keyed by manifest checksum and refreshed
transactionally; a catalog command may never approve a case. Rebuild into a new
temporary SQLite database, validate foreign keys and source hashes, then atomically
replace the derived catalog only. Raw bundles and case manifests remain untouched.
Do not import source patient IDs, personal metadata, secrets or absolute paths
into public exports.

## Real-data slice

Milestone 3 uses PTB-XL for both rhythm strips and twelve-lead drafts under the
owner-approved 2026-09-06 amendment. NSRDB's 18 verified headers declare gain zero;
it is deferred pending source-grounded calibration evidence. No default gain is
applied. See [real-data drafts](real-data-drafts.md) for the explicit acquisition,
calibration, source-name mapping, metadata filtering and draft-only contracts.
