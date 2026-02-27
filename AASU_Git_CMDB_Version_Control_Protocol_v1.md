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

Recommended structure (implemented in this repo):

```
registry/
  assets/
    aasu/
    model/
    prompt_package/
    retrieval/
    tool/
    policy/
    ...
  relationships/
  schemas/
tools/
  aasu_registry.py
  validate_registry.py
```

**Why this works with Git and Hugging Face**
- Everything is **plain text** (YAML/JSON Schema), so diffs are meaningful.
- Large artifacts (model weights, embedding dumps) stay out of the registry and are referenced by **immutable digests** or HF/Git SHAs.
- Hugging Face Hub repos are Git repos; the same folder layout and files can live there if desired.

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

### 4.2 Relationship manifest
Each relationship is a YAML file with:
- `kind`: `Relationship`
- `metadata.id` (unique relationship ID)
- `spec.type`: relationship type
- `spec.from`: source CI ID
- `spec.to`: destination CI ID

### 4.3 AASU snapshot & fingerprint (the core AASU binding)
For CIs where `spec.type: aasu`, the manifest MUST include:
- `spec.aasu.snapshot`: the exact `(P,M,R,T,K)` tuple using **versioned references**
- `spec.aasu.fingerprint`: deterministic hash of `spec.aasu.snapshot`

**Fingerprint rule (v1):**
- Canonicalize `spec.aasu.snapshot` to JSON with sorted keys
- Compute `sha256` and store as `sha256:<64-hex>`

This makes “any change in P/M/R/T/K creates a new AASU” mechanically enforceable in code review and CI.

---

## 5) Version control workflow (GitHub-first, Git-native)

### 5.1 Branching & PR workflow
- Use protected `main` (or `trunk`) branch.
- All registry updates happen via PRs:
  - new CI onboarding
  - CI updates (lifecycle, ownership, environment changes)
  - relationship changes
  - AASU snapshot changes (P/M/R/T/K)

### 5.2 Required checks (automated)
At minimum:
- **Schema validation** (CI + relationship JSON Schemas)
- **Graph integrity** (relationship endpoints exist)
- **AASU fingerprint verification** (fingerprint matches snapshot)

### 5.3 Required approvals (governance)
Use **CODEOWNERS** and GitHub branch protection rules so that:
- CI owners approve CI changes
- Security owners approve AASU snapshot and tool privilege changes
- Platform owners approve runtime environment changes

### 5.4 Releases & audit references
Two common patterns:
- **Git commit SHA as the snapshot reference** (simple, Git-native)
- **Signed tags/releases for certified baselines** (e.g., `certified/2026-02-21`)

In both cases, the AASU fingerprint provides a cross-system ID that can be stored in ServiceNow and in audit evidence.

---

## 6) ServiceNow interoperability (CMDB alignment)

AGCVCP does not replace ServiceNow discovery; it complements it by making Git the **change-controlled, reviewable source** for AI configuration and relationships.

Recommended mapping:
- `metadata.id` → `u_ci_id` (custom stable ID in ServiceNow CI table)
- `metadata.name` → `name`
- `spec.type` → `sys_class_name` (or a custom CI class mapping)
- `spec.lifecycle` → `install_status` / `operational_status` mapping
- `spec.identifiers.servicenow_sys_id` ↔ `sys_id` (optional; generated by ServiceNow)
- Relationship manifests → CMDB relationship table rows (type/from/to)

**Source-of-truth guidance**
- Use Git as SoT for: AASU snapshots, tool allowlists, retrieval sources, model/prompt references, evidence references.
- Use ServiceNow as SoT for: runtime-discovered infra items if you already have discovery pipelines.

---

## 7) Hugging Face compatibility (models, datasets, prompts)

Hugging Face repos are Git repos with LFS for large artifacts.
AGCVCP supports Hugging Face in two ways:

**Option A — Reference HF from the central registry (recommended)**
- Keep the CMDB-as-code in one registry repo.
- In CI manifests, use `spec.artifacts[]` with `kind: huggingface` and pin to `repo_id` + `revision` (commit SHA or tag).

**Option B — Embed manifests inside HF repos**
- Add `registry/assets/...` manifests directly to the HF repo.
- Use an external CI (or local validation) to run `python3 tools/aasu_registry.py validate`.

Key rule for auditability: **do not reference moving revisions**. Use commit SHAs, immutable tags, or digests.

---

## 8) Reference implementation in this repo

This repo includes:
- `registry/` scaffolding and example manifests
- JSON Schemas in `registry/schemas/`
- CLI + validator in `tools/aasu_registry.py` (uses `tools/validate_registry.py`)
- GitHub Action workflow in `.github/workflows/registry-validate.yml`
- PR impact reporting via `python3 tools/aasu_registry.py impact` (optional PR comment)
- PR template in `.github/pull_request_template.md`

---

## 9) Suggested rollout plan for an organization

1. **Bootstrap**
   - Create the registry repo
   - Define CI ID conventions and owner mapping to GitHub teams
2. **Onboard assets**
   - Start with AASU snapshots and tool/MCP endpoints (highest governance value)
   - Add retrieval indices and datasets next
3. **Bind evidence**
   - Store or reference test results, approvals, and risk acceptances per AASU fingerprint
4. **Integrate CMDB**
   - Export/import to ServiceNow, preserving `metadata.id` and AASU fingerprints
5. **Operationalize**
   - Use the registry graph for threat modeling, access reviews, and audit reporting

---

## 10) Appendix: example objects

See `registry/assets/` and `registry/relationships/` for working examples.
