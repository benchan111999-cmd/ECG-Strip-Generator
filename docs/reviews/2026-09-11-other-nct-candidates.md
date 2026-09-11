# Additional NCT comparison candidates

Owner requested other examples after two MITDB 209 windows. No replacement approved in this review.

Reviewed new MITDB 234 and SVDB 802–804, 806–808, 820–822, 840–842 using checksum-verified official subsets and source annotations. This is a bounded search, not an exhaustive database review. Original sources and previous student packages remain unchanged.

## Exported alternatives

- MITDB 234: MLII, [309554,313154), 859.872–869.872 s, target J311518. 22 J beats, median-RR rate approximately 136/min. Entire window inside source SVTA interval [304425,313772); official directory describes junctional tachycardia. Narrow-looking QRS, but baseline ripple and a central baseline shift persist. Below the approximately 150/min teaching target; not claimed superior to 209. Existing selector excludes J from its rapid-run category, so exported truthfully as a supraventricular-ectopy candidate without changing that rule.
- SVDB 840: ECG1, [83598,84878), 653.109–663.109 s, target S84302. 22 S beats, median-RR rate approximately 137/min. Narrow-looking QRS, variable RR and residual artifact. Not a preferred regular-NCT introductory example and no mechanism inferred from S annotations.

Both packages are under `output/candidate-review-2026-09-11/`, named `mitdb234-alternative-package` and `svdb840-alternative-package`. Standard 25 mm/s, 10 mm/mV; original consecutive source samples without filtering or resampling. Source/attribution evidence is retained in the packages. Both audit-draft checks passed output checksums; both remain clinically not_reviewed.

SVDB 806 appeared visually cleaner but its examined middle window contained only N beats around 105/min; it was not presented as the requested specific tachyarrhythmia example. Other screened candidates were too brief, insufficiently fast, or visually unsuitable. Source flags are screening aids, not QRS-width adjudication.

Sources: https://physionet.org/physiobank/database/html/mitdbdir/records.htm#234 and https://physionet.org/content/svdb/1.0.0/. Internal source-preserving review only; no external publication or clinical release.
