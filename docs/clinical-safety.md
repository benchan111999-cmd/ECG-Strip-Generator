# Clinical safety

## Intended use

Personal, non-commercial education only. This development skeleton does not
diagnose patients, generate clinical evidence, or produce reviewed teaching cases.

## Independent review gates

Future cases must separately record source evidence, technical validation,
clinical review, and teaching release. A passing automated test approves neither
a clinical label nor teaching release. See the approved plan, section 5.

## Lead and source integrity

Future commands must fail on absent requested leads or uncertain units/gain;
they must not substitute leads or synthesize missing channels. Synthetic output
must be labelled and human-reviewed. Different onset/termination episodes must
not imply shared identity or continuity.

## Privacy and answer separation

No patient identifiers, student names, secrets, raw datasets, or private answer
keys belong in Git. Student/instructor package separation and leak checks are
required before teaching release; they are not implemented in Milestone 0.
