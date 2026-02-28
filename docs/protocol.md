---
layout: default
title: AASU Git-CMDB Version Control Protocol (AGCVCP)
---

<!--
NOTE: This is a GitHub Pages-friendly copy of `AASU_Git_CMDB_Version_Control_Protocol_v1.md`.
Keep both in sync if you update the protocol.
-->

# AASU Git-CMDB Version Control Protocol (AGCVCP) v1

**Goal:** Use Git (GitHub-first, but Git-native) as a **CMDB-as-code** system for AASU implementations—so organizations can do **asset mapping**, **configuration management**, and **audit-ready governance** for AI systems (prompts, models, retrieval, tools/MCP, runtime constraints) using PR-based change control.

This protocol is designed to be:
- **Git-compatible**: plain-text manifests, diffable, reviewable, taggable, revertible.
- **GitHub-operable**: PR workflows, CODEOWNERS, branch protections, Actions.
- **Hugging Face-compatible**: the same manifests can live in or reference Hugging Face Hub repos (Git + LFS).
- **ServiceNow-aligned**: assets are modeled as **Configuration Items (CIs)** and relationships mirror CMDB relationship tables.

---

## 1) Analysis (what you need for AASU governance)

### 1.1 Why AASU needs “configuration CMDB”, not “app CMDB”
The AASU model formalizes that an AI capability is a **configuration-bound unit**:

**AASU = (P, M, R, T, K)**  
Prompt package, Model instance, Retrieval configuration, Tool/MCP configuration, Runtime constraints.

Security and assurance therefore require:
- A **versioned manifest** per deployed configuration snapshot
- A **stable, computable configuration ID** (hash/fingerprint)
- A clear record of **ownership**, **approvals**, and **evidence** tied to that snapshot

### 1.2 What breaks in classic CMDB patterns (ServiceNow included)
Traditional CMDBs are valuable for operational discovery, but are frequently weak as a governance backbone for AI:
- **Fast drift**: prompts and orchestration change faster than CMDB updates
- **Distributed ownership**: changes are done by multiple teams via code, not a single CMDB operator
- **Evidence mismatch**: approvals and test results often don’t bind to an exact configuration snapshot
- **Topology blindness**: multi-AASU graphs and tool privileges are hard to represent without “CMDB-as-graph”

### 1.3 Requirements for an AASU-grade asset map
Minimum requirements for a practical AASU asset registry:

**Inventory & ownership**
- Every AI-relevant asset is a CI: prompt packages, models, retrieval indices, tools/MCP servers, runtime policies, and AASU snapshots.
- Every CI has explicit **owners** (primary + security/ops as applicable).

**Relationship graph**
- First-class relationships: *depends_on*, *calls_tool*, *retrieves_from*, *deployed_on*, etc.
- Relationships must be queryable and reviewable like code.

**Snapshot binding**
- AASU snapshots MUST be representable as an immutable tuple `(P,M,R,T,K)` with explicit version references (commit SHA, image digest, provider snapshot ID).
- Each snapshot MUST compute a deterministic **fingerprint** (e.g., `sha256:`) and treat that as the canonical identity for certification.

**Change control**
- CI/relationship changes happen through PRs with required checks and required reviewers.
- Emergency change path exists but still produces an auditable trail.

**Interoperability**
- Export/import mapping to ServiceNow (or other CMDBs) is possible without losing IDs.
- Hugging Face repos (models/datasets) can be referenced or can contain manifests directly.

---

## 2) Protocol overview (what AGCVCP standardizes)

AGCVCP standardizes:
1. **A manifest format** for CIs and relationships (YAML)
2. **A directory layout** for a registry repo (`registry/…`)
3. **A fingerprinting rule** for AASU snapshots
4. **A Git/GitHub workflow** for ownership, review, and validation
5. **A ServiceNow-compatible mapping strategy**
6. **A Hugging Face-compatible reference strategy**

---

## 3) Registry repository layout (Git-native)

Recommended structure:

```
registry/
  assets/
  relationships/
  schemas/
tools/
  aasu_registry.py
```

---

## 4) Data model

### 4.1 Configuration Item (CI) manifest
Each CI is a YAML file with:
- `apiVersion`: `aasu.ai/v1alpha1`
- `kind`: `ConfigurationItem`
- `metadata`: stable identity + ownership
- `spec`: typed details

Required minimum fields:
- `metadata.id` (stable, globally unique within your org)
- `metadata.name`
- `metadata.owners[]`
- `spec.type`
- `spec.lifecycle`

Recommended CI classes for regulated agentic systems:
- Core runtime: `aasu`, `model`, `prompt_package`, `retrieval`, `tool`, `policy`
- Governance extensions: `skill_package`, `memory_short_term_profile`, `memory_long_term_profile`
- Graph context: `knowledge_graph`, `context_graph_profile`
- Supply chain and evidence: `aibom_document`, `attestation_bundle`

### 4.2 Relationship manifest
Each relationship is a YAML file with:
- `kind`: `Relationship`
- `metadata.id` (unique relationship ID)
- `spec.type`: relationship type
- `spec.from`: source CI ID
- `spec.to`: destination CI ID

Recommended relationship types for governance extensions:
- `uses_skill`
- `uses_short_term_memory`
- `uses_long_term_memory`
- `uses_knowledge_graph`
- `uses_context_graph_profile`
- `context_graph_derived_from`
- `stores_memory_in`
- `indexes_from_corpus`
- `attests`

### 4.3 AASU snapshot & fingerprint (the core AASU binding)
For CIs where `spec.type: aasu`, the manifest MUST include:
- `spec.aasu.snapshot`: the exact `(P,M,R,T,K)` tuple using **versioned references**
- `spec.aasu.fingerprint`: deterministic hash of `spec.aasu.snapshot`

**Fingerprint rule (v1):**
- Canonicalize `spec.aasu.snapshot` to JSON with sorted keys
- Compute `sha256` and store as `sha256:<64-hex>`

Validation invariants for regulated profiles:
- AASUs MAY omit memory relationships.
- If an AASU references long-term memory, it MUST also reference short-term memory.
- If an AASU enables memory in production, it MUST reference exactly one long-term memory profile.
- If an AASU references a context graph profile, it MUST also reference a knowledge graph.

---

## 5) Version control workflow (GitHub-first, Git-native)

### 5.1 Branching & PR workflow
- Use protected `main` (or `trunk`) branch.
- All registry updates happen via PRs.

### 5.2 Required checks (automated)
At minimum:
- Schema validation
- Graph integrity
- AASU fingerprint verification

---

## 6) ServiceNow interoperability (CMDB alignment)

Recommended mapping:
- `metadata.id` → `u_ci_id` (custom stable ID in ServiceNow CI table)
- `metadata.name` → `name`
- `spec.type` → class mapping
- Relationship manifests → CMDB relationship table rows (type/from/to)

---

## 7) Hugging Face compatibility (models, datasets, prompts)

Two supported patterns:
- Reference HF artifacts from the central registry (pin by commit SHA or tag).
- Embed manifests inside HF repos and validate externally.

---

## 8) Reference implementation

See:
- Registry + example manifests in `registry/`
- CLI: `python3 tools/aasu_registry.py validate`
- GitHub PR validation + impact comments: `.github/workflows/registry-validate.yml`
