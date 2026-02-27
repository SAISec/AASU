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
## AASU unit decomposition
An Atomic AI Security Unit is a **configuration-bound** unit:

**AASU = (P, M, R, T, K)**
- **P**: Prompt package
- **M**: Model instance & parameters
- **R**: Retrieval configuration (RAG)
- **T**: Tool/MCP configuration
- **K**: Runtime constraints

Any change to **P/M/R/T/K** creates a new AASU and requires re‑validation.

## Architecture patterns (chains and graphs)
Modern AI systems are composed of multiple AASUs, typically in these patterns:

- **Single AASU**: User → AASU → Output  
  Risks: prompt injection, tool misuse, retrieval leakage

- **Sequential chain**: User → AASU‑1 → AASU‑2 → AASU‑3 → Output  
  Risks: cascading failure, injection amplification, context contamination, privilege escalation chains

- **Parallel agent fabric**: User → Router → {AASU‑A, AASU‑B, AASU‑C}  
  Risks: routing manipulation, policy inconsistency, surface area expansion

- **Hybrid directed graph**: Nodes = AASUs, Edges = data flow  
  Risks: emergent behavior, cross‑branch contamination, recursive tool abuse

## Validation layers (overview)
1. **AASU‑level testing**: prompt injection, tool misuse, retrieval leakage
2. **Orchestration testing**: cross‑unit contamination, state poisoning
3. **Attack‑graph testing**: multi‑agent escalation, cross‑AASU exfiltration

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

