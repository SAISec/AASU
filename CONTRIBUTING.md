# Contributing to AASU

Thank you for your interest in contributing.

## Branching and PRs
- Development happens on `dev` or feature branches off `dev`.
- Open PRs targeting `dev` (never `main`).
- Use clear commit messages and link to the relevant issue/ADR when applicable.

## Local checks
At minimum:
```bash
python3 tools/aasu_registry.py validate
```
If you modify AASU snapshots, update fingerprints:
```bash
python3 tools/aasu_registry.py fingerprint --all --write
python3 tools/aasu_registry.py validate
```

## Documentation
- Keep `docs/` and top-level docs in sync where appropriate.
- Update `CHANGELOG.md` for user-facing changes.

## Security
If you discover a security issue, see `SECURITY.md`.

