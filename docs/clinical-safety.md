# Clinical safety

## Intended use

Personal, non-commercial education only. Milestone 1 creates unreviewed draft
renders; it does not diagnose patients, generate clinical evidence, or approve
teaching cases. Included triangle/ramp fixtures are non-clinical tests, including
the twelve-channel example. They are not synthetic diagnostic ECG recipes.

## Independent review gates

Source evidence, technical validation, clinical review, and teaching release
are distinct axes. The renderer accepts only initially unreviewed drafts.
A render-specific pass does not approve overall technical validation: original
dataset files/checksums have not been verified. It never approves clinical or
teaching status. See the approved plan, section 5.

## Lead and source integrity

Exact recorded leads and physical units are required. No first-lead fallback,
MLII-to-II alias, missing-channel inference, filtering or automatic gain
adjustment exists. Invalid samples, checksum mismatches, and clipping fail.

Source licence/version/attribution must be explicitly declared; this is not
verification of those declarations against the original dataset. Milestone 2
will establish source audit. Separate onset/termination pairs are not implemented;
no output implies shared episode identity.

## Privacy and answer separation

Do not include patient identifiers, student names, secrets or answer keys in
requests, titles/prompts, sources or Git. Generated drafts include source
provenance and have not passed student answer-leak checks. They are not student
packages. Student/instructor separation and human review remain required before
teaching release. Synthetic twelve-lead teaching release remains disabled.
