# Atomic AI Security Unit (AASU)

**AASU = (P, M, R, T, K)**  
Prompt package, Model instance & parameters, Retrieval configuration, Tool/MCP configuration, Runtime constraints.

This repository provides:
- The AASU white paper (Markdown + HTML/PDF)
- A Git-native CMDB-as-code protocol for asset mapping and audit-ready governance
- A reference registry + CLI tooling for GitHub PR workflows

## Quick links
- Protocol: `docs/protocol.md`
- Registry & tooling: `docs/registry.md`
- GitHub Pages site entry: `docs/index.md`
- TODOs / roadmap: `TODO.md`

## Repository structure
```
docs/            GitHub Pages content
registry/        CMDB-as-code registry (manifests + schemas)
tools/           Registry CLI and utilities
arxiv_paper/     LaTeX source for submission-style paper
```

## Local usage (registry)
```bash
python3 tools/aasu_registry.py validate
python3 tools/aasu_registry.py fingerprint --all --write
```

## Contributing
See `CONTRIBUTING.md` for branch, PR, and validation requirements.

## Security
See `SECURITY.md` for reporting guidelines.

## License
Apache-2.0. See `LICENSE`.

