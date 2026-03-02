# Atomic AI Security Unit (AASU)
[![Validate registry manifests](https://github.com/SAISec/AASU/actions/workflows/registry-validate.yml/badge.svg)](https://github.com/SAISec/AASU/actions/workflows/registry-validate.yml)
[![License: Apache-2.0](https://img.shields.io/github/license/SAISec/AASU)](LICENSE)

**AASU core = (P, M, R, T, K)**  
Prompt package, Model instance & parameters, Retrieval configuration, Tool/MCP configuration, Runtime constraints.

**AASU extension = (Mem, S)**  
Memory configuration, Skill configuration.

This repository provides:
- The AASU white paper (Markdown + HTML/PDF) — **primary deliverable**
- A Git-native CMDB-as-code protocol for asset mapping and audit-ready governance
- A reference registry + CLI tooling for GitHub PR workflows (add-on)

## Quick links
- Protocol: `docs/protocol.md`
- Registry & tooling: `docs/registry.md`
- GitHub Pages site entry: `docs/index.md`
- TODOs / roadmap: `TODO.md`
- Roadmap: `ROADMAP.md`

## AASU unit decomposition
An Atomic AI Security Unit is a **configuration-bound** unit:

**AASU core = (P, M, R, T, K)**
- **P**: Prompt package
- **M**: Model instance & parameters
- **R**: Retrieval configuration (RAG)
- **T**: Tool/MCP configuration
- **K**: Runtime constraints
- **Mem**: Memory configuration (optional extension)
- **S**: Skill configuration (optional extension)

Any change to **P/M/R/T/K/Mem/S** creates a new AASU and requires re-validation.

## Architecture patterns (chains and graphs)
Modern AI systems are composed of multiple AASUs, typically in these patterns:

- **Single AASU**: User → AASU → Output  
  Risks: prompt injection, tool misuse, retrieval leakage

```mermaid
flowchart LR
  User --> AASU["AASU<br/>(P,M,R,T,K + Mem,S)"]
  AASU --> Output
```

- **Sequential chain**: User → AASU‑1 → AASU‑2 → AASU‑3 → Output  
  Risks: cascading failure, injection amplification, context contamination, privilege escalation chains
```mermaid
flowchart LR
  User --> A1["AASU-1<br/>(core + Mem/S)"]
  A1 --> A2["AASU-2<br/>(core + Mem/S)"]
  A2 --> A3["AASU-3<br/>(core + Mem/S)"]
  A3 --> Output
```

- **Parallel agent fabric**: User → Router → {AASU‑A, AASU‑B, AASU‑C}  
  Risks: routing manipulation, policy inconsistency, surface area expansion
```mermaid
flowchart LR
  User --> Router
  Router --> A1["AASU-A<br/>(core + Mem/S)"]
  Router --> A2["AASU-B<br/>(core + Mem/S)"]
  Router --> A3["AASU-C<br/>(core + Mem/S)"]
  A1 --> Output
  A2 --> Output
  A3 --> Output
```

- **Hybrid directed graph**: Nodes = AASUs, Edges = data flow  
  Risks: emergent behavior, cross‑branch contamination, recursive tool abuse

## Validation layers (overview)
1. **AASU‑level testing**: prompt injection, tool misuse, retrieval leakage
2. **Orchestration testing**: cross‑unit contamination, state poisoning
3. **Attack‑graph testing**: multi‑agent escalation, cross‑AASU exfiltration

## How AASU differs from typical AI and agentic AI applications
- **Unit of analysis**: AASU treats the *configuration snapshot* (P/M/R/T/K, optionally Mem/S) as the unit of risk, not the model or the app.
- **Topology‑aware**: Typical AI app reviews are per‑app; AASU models chains, routers, and graphs as a security surface.
- **Certification‑bound**: Validation ties evidence to a specific configuration hash; any change creates a new AASU.
- **Agentic clarity**: Agentic systems often blur boundaries; AASU makes each agent an explicit, testable unit with clear edges and privileges.
- **Governance‑first**: AASU is designed for auditability, approval workflows, and CMDB‑aligned change control.

## FAQ
**Is AASU just a model card?**  
No. AASU covers the full configuration snapshot (P/M/R/T/K, optionally Mem/S), including retrieval, tooling, runtime guardrails, memory, and skill behavior.

**Do I need AASU if I only use one model?**  
Yes—prompt, tools, and runtime constraints can materially change risk even when the model stays the same.

**How does AASU relate to agentic systems?**  
Each agent is an AASU; the overall system is a directed graph of AASUs with explicit edges and privilege flows.

**Are the validation scripts required?**  
They are add‑ons. The core deliverable is the AASU concept and white paper; tooling exists to operationalize it in Git workflows.

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
