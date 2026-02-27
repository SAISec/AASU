---
layout: default
title: Atomic AI Security Unit (AASU)
---

# Atomic AI Security Unit (AASU)

**AASU = (P, M, R, T, K)**  
Prompt package, Model instance & parameters, Retrieval configuration, Tool/MCP configuration, Runtime constraints.

This repository includes:
- The AASU white paper (HTML/PDF)
- A Git-native CMDB-as-code protocol for asset mapping and audit-ready governance
- A reference registry + CLI tooling for GitHub PR workflows

## Quick links
- White paper (HTML): [`paper/main.html`](paper/main.html)
- White paper (PDF): [`paper/main.pdf`](paper/main.pdf)
- Git-CMDB protocol (AGCVCP): [`protocol.md`](protocol.md)
- Registry + tooling: [`registry.md`](registry.md)

## What “CMDB-as-code” means for AASU
For AASU implementations, “the system” is its configuration snapshot:
- AASU snapshot manifests record the exact `(P,M,R,T,K)` tuple.
- A deterministic `sha256` fingerprint binds security tests, approvals, and risk acceptance to an immutable configuration identity.
- GitHub PRs become the change-control mechanism (review, evidence, audit trail).

