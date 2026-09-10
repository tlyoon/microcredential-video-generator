# Repository Rename Migration

## Recommended name

The preferred GitHub repository slug is:

```text
microcredential-video-generator
```

The earlier slug `physics-lab-microcredential-video-generator` was appropriate for the first reference implementation but became misleading once the engine was generalized for arbitrary structured teaching DOCX sources and configurable course profiles.

## Why this name

`microcredential-video-generator` is preferred because it:

- matches the Python distribution name;
- describes the software's purpose rather than one sample course;
- does not lock the project to Physics;
- leaves room for future source formats beyond DOCX;
- keeps the CLI/package identity concise and stable.

## Rename on GitHub

Repository owner action:

1. Open the repository on GitHub.
2. Open **Settings**.
3. Under **General**, locate **Repository name**.
4. Change it to `microcredential-video-generator`.
5. Confirm the rename.

Alternatively, from an authenticated GitHub CLI session:

```powershell
gh repo rename microcredential-video-generator --yes
```

Run that command from a local clone of the repository.

## Existing local clones

GitHub normally redirects many requests from the old repository URL, but explicitly updating `origin` is clearer:

```powershell
git remote set-url origin https://github.com/tlyoon/microcredential-video-generator.git
git remote -v
```

No package reinstall is required solely because the GitHub repository was renamed.

## What does not change

The following remain unchanged:

```text
Python distribution: microcredential-video-generator
Python import package: microvid
CLI command: microvid
course profiles: unchanged
workspace structure: unchanged
sample DOCX location: unchanged
Gemini configuration: unchanged
Chirp TTS configuration: unchanged
```

## Repository-name independence

Runtime code does not derive paths, profiles, model configuration, TTS settings, or source-document behavior from the GitHub repository slug. Documentation uses relative links wherever possible. The rename is therefore a discovery/identity improvement, not a functional migration.
