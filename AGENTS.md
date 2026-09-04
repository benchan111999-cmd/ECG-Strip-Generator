# ECG Strip Generator — Agent Instructions

## Project identity

- This is a standalone tool-development subproject of ECG Course.
- Preserve the boundary between this repository and the parent ECG Course repository.
- Do not copy parent-project files or rules into this repository unless the project owner asks for it.

## Output language

- English is the primary language for code, documentation, and user-facing output.
- Add zh-HK wording when it improves local usability or is explicitly requested.

## Privacy and safety

- Do not store patient-identifiable information, student names, exam answers, secrets, API keys, tokens, or credentials.
- Treat generated ECG strips as teaching or tool output; do not make clinical claims without source review and human approval.
- A public repository must contain only material that is safe to publish.

## Source material

- Preserve original source files and their provenance.
- Do not rename, move, or delete original source files without explicit approval.
- Keep source, generated output, and derived notes clearly separated.

## Development workflow

- Use the `main` branch for the current single-developer workflow.
- Keep changes small and directly related to the requested work.
- Run the relevant checks before proposing a commit.
- Do not create a commit or push changes without asking the project owner first; the initial commit is the only currently approved exception.
- Do not add deployment configuration yet.

## GitHub

- Public repository: https://github.com/benchan111999-cmd/ECG-Strip-Generator
- Keep the local `main` branch aligned with the public `origin` after an approved push.

## Obsidian project dashboard

- Canonical Vault name: `2ndBrain`
- Canonical Vault root: `C:\Users\User\iCloudDrive\iCloud~md~obsidian\2ndBrain`
- Dashboard note: `C:\Users\User\iCloudDrive\iCloud~md~obsidian\2ndBrain\Projects\ECG Strip Generator.md`
- The dashboard is the canonical project progress record. Vault mutations must use the official Obsidian CLI adapter and its pre-image/readback checks; do not write to the Vault through direct filesystem commands.

## Commit scope

- Ask before every commit and confirm the intended scope.
- When approved, include project source, documentation, tests, and required configuration only.
- Exclude secrets, local caches, generated output, and original source material unless the owner explicitly approves them.
