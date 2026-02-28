# Defining the Atomic AI Security Unit (AASU)

## Enterprise-Grade AI Security Architecture & Validation Framework

### Consolidated White Paper (v2.2)

**Document ID:** AASU-WP-2.2-CONSOLIDATED  
**Version:** 2.2 (Consolidated from v1.0, v1.2, and v2.2)  
**Date:** 2026-02-23  
**Implementation Revision Note:** 2026-02-28 (v1alpha2 registry/governance extensions)  
**Intended Audience:** CISO \| AI Security Engineering \| Red Team \| AppSec \| ML Platform \| Risk & GRC \| Enterprise Architecture \| Audit/Regulators  
**Classification:** Public / External Distribution Ready

**Sources consolidated:**
- `Atomic_AI_Security_Unit_AASU_White_Paper.md` (v1.0)
- `AASU_White_Paper_Publish_Ready_v1_2.md` (v1.2)
- `AASU_White_Paper_Extended_v2_2_Enriched.md` (v2.2)

---

## Executive Summary

Modern enterprise GenAI systems are not single-model deployments. They are configuration-bound, tool-enabled, retrieval-augmented, orchestrated computational graphs.

Security failures in these systems are rarely “model-only” issues. They are configuration, orchestration, and topology issues. Two applications using the same model can exhibit materially different risk profiles depending on prompts, tool access, retrieval configuration, and runtime parameters.

This paper formalizes a security abstraction for repeatable testing and governance:

> **Atomic AI Security Unit (AASU)** — the smallest configuration-bound AI system instance that must be treated as a single unit for security testing, red teaming, and audit validation.

It further defines architecture-aware testing patterns, a three-layer validation methodology (unit → orchestration → attack-graph), mappings to common AI security taxonomies (OWASP and MITRE ATLAS), and implementation extensions for skills, memory, graph context, AIBOM, and attestations.

---

## 1. The Core Problem: Model-Only Security Is Structurally Incomplete

Traditional application security assumes deterministic software behavior. Modern GenAI systems are configuration-driven and behaviorally emergent.

**The model is not the unit of risk. The configuration is the unit of risk.**

Security posture is best expressed as:

**Security posture = f(configuration, topology, privilege graph, routing/orchestration logic)**

Not:

**Security posture = f(model)**

---

## 2. The Atomic AI Security Unit (AASU)

### 2.1 Formal Definition

An AASU is a tightly bound, versioned configuration:

**AASU = (P, M, R, T, K)**

Where:
- **P = Prompt Package** (system prompts, templates, policy prompts, routing prompts, prompt hierarchy, prompt chaining)
- **M = Model Instance & Parameters** (model identity/version/provider plus decoding/runtime parameters that shape behavior)
- **R = Retrieval Configuration** (RAG settings, corpus selection, embedding model, chunking, filters, top-k, thresholds)
- **T = Tool/MCP Configuration** (tool schemas, connectors/plugins, permissions, execution environment, Model Context Protocol if present)
- **K = Runtime Constraints / Guardrails** (policy enforcement, timeouts, rate limits, context limits, safety filters, sandbox constraints)

```mermaid
flowchart TB
  A["AASU<br/>(versioned configuration snapshot)"]:::aasu
  ID["Configuration ID<br/>(hash / manifest version)"]:::id

  P["P — Prompt package"]:::comp
  M["M — Model & parameters"]:::comp
  R["R — Retrieval (RAG) config"]:::comp
  T["T — Tools / MCP config"]:::comp
  K["K — Runtime constraints"]:::comp

  A --> P
  A --> M
  A --> R
  A --> T
  A --> K
  A -->|certify against| ID

  subgraph G["Governance Extension Assets (v1alpha2)"]
    S["Skill package"]:::ext
    STM["Short-term memory profile"]:::ext
    LTM["Long-term memory profile"]:::ext
    KG["Knowledge graph"]:::ext
    CG["Context graph profile"]:::ext
    BOM["AIBOM document"]:::ext
    ATT["Attestation bundle"]:::ext
  end

  A -->|uses_skill| S
  A -->|uses_short_term_memory| STM
  A -->|uses_long_term_memory| LTM
  A -->|uses_knowledge_graph| KG
  A -->|uses_context_graph_profile| CG
  CG -->|context_graph_derived_from| KG
  BOM -->|attests| M
  ATT -->|attests| A
  ATT -->|attests| BOM

  classDef aasu fill:#0b7285,stroke:#083344,color:#ffffff;
  classDef id fill:#fff3bf,stroke:#f08c00,color:#7c2d12;
  classDef comp fill:#e6fcf5,stroke:#0b7285,color:#083344;
  classDef ext fill:#f1f3f5,stroke:#495057,color:#212529;
```

Illustrative runtime flow for a single user request through an AASU:

```mermaid
flowchart TB
  IN["User input"] --> PRE["K: Pre-guardrails<br/>(policy checks, limits, allow/deny)"]
  PRE --> CG["Context graph assembly<br/>(R + KG + STM/LTM + policy filters)"]
  CG --> SK{"Skill required?"}

  SK -->|yes| SKILL["Skill package invocation<br/>(procedural memory)"]
  SK -->|no| ASSEMBLE["P: Prompt assembly<br/>(system + developer + user + context graph)"]
  SKILL --> ASSEMBLE

  ASSEMBLE --> CALL["M: Model call<br/>(model + decoding params)"]
  CALL --> TOOL{"Tool call requested?"}

  TOOL -->|yes| EXEC["T: Tool / MCP execution<br/>(permissions + sandbox)"]
  EXEC --> MEM{"Persist to long-term memory?"}
  MEM -->|yes| LTMW["LTM write<br/>(consent + retention policy)"]
  MEM -->|no| ASSEMBLE
  LTMW --> ASSEMBLE

  TOOL -->|no| POST["K: Post-guardrails<br/>(output filtering + safe handling)"]
  POST --> OUT["Response"]
```

**Any change in P, M, R, T, or K creates a new AASU.**

### 2.2 Configuration Snapshot Principle

While LLM outputs are probabilistic, the security posture of an AASU is **configuration-deterministic**: if you change the configuration, you change the risk profile.

Small changes can materially alter:
- Prompt injection susceptibility
- Tool misuse risk
- Data leakage exposure (especially via retrieval)
- Escalation behavior across agents/tools

Security testing and certification must bind to a **configuration snapshot** (ideally a versioned manifest and/or configuration hash), not a model name.

---

## 3. Enterprise Deployment Patterns (Topology Matters)

In enterprise systems, AASUs rarely operate in isolation. They are deployed in directed topologies where outputs, retrieved context, and tool results flow between nodes.

### 3.1 Single AASU

```mermaid
flowchart LR
    User --> AASU
    AASU --> Output
```

**Primary security surface:**
- Prompt injection
- Insecure output handling (downstream parsing / actioning)
- Tool misuse (if tools are enabled)
- Sensitive information disclosure (if retrieval is enabled)

### 3.2 Sequential Chain Pattern (Chained Units)

User → AASU-1 → AASU-2 → AASU-3 → Output

```mermaid
flowchart LR
    User --> A1[AASU-1]
    A1 --> A2[AASU-2]
    A2 --> A3[AASU-3]
    A3 --> Output
```

**Key risks:**
- Cascading failure
- Injection amplification and persistence across steps
- Context contamination between stages
- Privilege escalation chains (especially if later nodes have broader tool permissions)

**Testing implications:**
- Per-unit adversarial testing (each node as an AASU)
- Cross-unit validation (how attacks propagate)
- Multi-stage attack simulation (end-to-end)

### 3.3 Parallel Agent Fabric (Router + Multiple AASUs)

User → Router → Multiple Independent AASUs → Output(s)

```mermaid
flowchart LR
    User --> Router
    Router --> A1[AASU-A]
    Router --> A2[AASU-B]
    Router --> A3[AASU-C]
    A1 --> Output
    A2 --> Output
    A3 --> Output
```

**Key risks:**
- Surface area expansion (more prompts, tools, corpora, and policies)
- Policy inconsistency between agents
- Routing manipulation (attacker influences which AASU is invoked)
- Privilege skew (one agent has “too much” authority)

**Testing implications:**
- Independent unit testing per AASU
- Routing logic testing (manipulation, downgrade/upgrade paths)
- Cross-agent policy audits (consistency and least privilege)

### 3.4 Hybrid Directed AI Graph (Graph of AASUs)

Nodes = AASUs  
Edges = data-flow, context-flow, or tool-result reinjection relationships

```mermaid
flowchart TD
    User --> R[Router]
    R --> A1[AASU-1]
    R --> A2[AASU-2]
    A1 --> B1[AASU-3]
    A2 --> B1
    B1 --> C1[AASU-4]
    C1 --> Output
```

**Key risks:**
- Emergent systemic behavior (graph-level, not node-level)
- Recursive tool abuse / repeated execution loops
- Cross-branch contamination (one branch pollutes another)
- Graph-level privilege escalation (pivoting along edges)

This pattern requires graph-based security modeling in addition to per-AASU testing.

---

## 4. Formal Threat Model (AASU-Aware)

### 4.1 Assets

- Sensitive data (PII, financial, proprietary)
- Tool capabilities (refunds, exports, writes, admin actions)
- Retrieval corpora and vector indices
- Model credentials, API keys, and service accounts
- Session state, conversation memory, and orchestration state

### 4.2 Threat Actors

- External attackers
- Malicious insiders
- Prompt injection adversaries
- Supply chain document attackers (malicious content inserted into corpora)
- Automated adversarial bots

### 4.3 Trust Boundaries

1. User → Application
2. Application → Model Provider
3. Model/Orchestrator → Tool Execution Environment
4. Retrieval Layer → Data Stores / Vector DBs
5. Agent → Agent (in chained or multi-agent systems)

```mermaid
flowchart LR
  U[User] -->|TB1| APP[Application]

  subgraph ENT["Enterprise boundary"]
    APP --> ORCH[Orchestrator / Router]

    ORCH --> RET[Retrieval layer]
    RET -->|TB4| DATA[(Data stores / Vector DB)]

    ORCH -->|TB3| TOOL[Tool / MCP runtime]
    TOOL --> SYS[(Enterprise systems)]

    ORCH --> STM[Short-term memory profile]
    ORCH --> LTM[Long-term memory profile]
    STM --> MSTORE[(Memory store)]
    LTM --> MSTORE
    ORCH --> KG[Knowledge graph]
    ORCH --> CG[Context graph profile]
    CG --> KG
    ORCH --> SK[Skill package registry]
    ORCH --> BOM[AIBOM docs]
    ORCH --> ATT[Attestation bundle]
    ORCH --> LOG[Audit logs / telemetry]

    ORCH --> A1[AASU-1]
    ORCH --> A2[AASU-2]
    A1 <-->|TB5| A2
  end

  ORCH -->|TB2| LLM[Model provider API]
```

### 4.4 Data-Flow Considerations

- Context expansion via retrieval (RAG)
- Tool outputs reinjected into prompts (tool-result → context)
- Cross-agent message passing
- Memory persistence between sessions

### 4.5 Representative Abuse Cases

- Prompt hierarchy override (system/developer instructions subverted)
- Tool escalation (inducing unauthorized tool calls)
- Retrieval poisoning (malicious documents or embeddings influencing outputs/actions)
- Cross-agent privilege pivot (low-privilege agent → high-privilege agent)
- Recursive execution abuse (loops, runaway actions, excessive agency)

---

## 5. Multi-Layer Validation Model (Unit → Orchestration → Graph)

Security validation must reflect architectural complexity. The AASU model supports a three-layer approach:

```mermaid
flowchart TB
  L1["Layer 1 — AASU-level testing<br/>(nodes / configurations)"]:::layer
  L2["Layer 2 — Orchestration testing<br/>(edges / data flows)"]:::layer
  L3["Layer 3 — Attack-graph testing<br/>(paths / topology)"]:::layer

  L1 --> L2 --> L3

  classDef layer fill:#f8f9fa,stroke:#adb5bd,color:#343a40;
```

### Layer 1: AASU-Level (Configuration-Level) Testing

Test each AASU as a configuration-bound unit:
- Prompt injection resistance (including obfuscation and multilingual bypass attempts)
- Tool misuse simulation (schema abuse, parameter injection, permission boundary probing)
- Retrieval leakage validation (sensitive info disclosure, over-broad retrieval, prompt injection via retrieved docs)
- Output integrity and unsafe downstream handling checks
- Robustness testing (edge-case inputs, jailbreak variants, policy evasion)

### Layer 2: Orchestration-Level Testing

Test the orchestration and data flows between AASUs:
- Injection propagation across nodes
- Retry-path exploitation (how failures/retries change behavior or privileges)
- State poisoning (memory, cached context, intermediate artifacts)
- Boundary drift detection (policies or constraints weakening across steps)

### Layer 3: Attack-Graph (System-Level) Testing

Test the full directed graph as an attack surface:
- Multi-agent privilege escalation and pivots along edges
- Routing manipulation and downgrade/upgrade attacks
- Cross-AASU exfiltration (retrieval → tool → output)
- Graph traversal risk modeling (what an attacker can reach from an entry point)

---

## 6. Governance, Versioning, and Audit Readiness

```mermaid
flowchart LR
  DEV["Define / update AASU config<br/>(P, M, R, T, K)"] --> MAN["Generate manifest<br/>(versioned snapshot)"]
  MAN --> EXT["Bind extension assets<br/>(skills, STM/LTM, KG/CG)"]
  EXT --> HASH["Compute AASU ID<br/>(configuration hash)"]
  HASH --> BOM["Generate/update AIBOM"]
  BOM --> ATT["Create signed attestation bundle"]

  ATT --> T1["Layer 1 tests<br/>(AASU-level)"]
  T1 --> T2["Layer 2 tests<br/>(orchestration)"]
  T2 --> T3["Layer 3 tests<br/>(attack-graph)"]

  T3 --> RISK["Risk review + sign-off<br/>(Security / GRC)"]
  RISK --> DEP["Deploy certified snapshot"]
  DEP --> MON["Monitor + retain evidence<br/>(logs, traces, metrics)"]

  MON --> CHG{"Config / dependency change?"}
  CHG -->|yes| DEV
  CHG -->|no| DEP
```

### 6.1 Minimum AASU Versioning Requirements

Each AASU should maintain, at minimum:
- Configuration ID (or configuration hash)
- Prompt version
- Model version
- Tool/MCP version
- Retrieval version (if present)
- Parameter/constraint set (runtime guardrails)

**Any modification invalidates prior certification** for that AASU configuration snapshot.

### 6.2 Audit-Ready Outcomes Enabled by AASU Governance

- Configuration-hash binding of test results and red-team findings
- Mandatory retesting on configuration change
- Node/path/topology coverage metrics for complex systems
- Traceable certification statements tied to specific AASU IDs
- Risk acceptance tied to explicit configuration snapshots (not “the chatbot in general”)

### 6.3 Implementation Profile Update (2026-02-28): Skills, Memory, Graph Context, AIBOM, and Attestations

For operational governance in regulated environments, this implementation profile adds first-class assets and relationship controls while preserving the core AASU tuple `(P,M,R,T,K)`.

**Design principles:**
- Keep AASU core unchanged for conceptual stability.
- Treat skills as **separate assets**, not inline prompt/memory text.
- Split memory into distinct **short-term** and **long-term** profiles.
- Distinguish durable **knowledge graph** from runtime **context graph profile**.
- Attach model inventory and supply-chain evidence through **AIBOM** and **attestation bundles**.

**Required relationship controls (production profile):**
- Every AASU references exactly one short-term memory profile.
- Every production AASU references exactly one long-term memory profile.
- If context graph profile is used, a knowledge graph reference is mandatory.
- Production AASUs require attestation linkage and model AIBOM linkage.

**Representative CI classes:**
- `skill_package`
- `memory_short_term_profile`
- `memory_long_term_profile`
- `knowledge_graph`
- `context_graph_profile`
- `aibom_document`
- `attestation_bundle`

**Representative relationships:**
- `uses_skill`
- `uses_short_term_memory`
- `uses_long_term_memory`
- `uses_knowledge_graph`
- `uses_context_graph_profile`
- `context_graph_derived_from`
- `stores_memory_in`
- `indexes_from_corpus`
- `attests`

```mermaid
flowchart LR
  AASU["ci:aasu:*"] -->|uses_skill| SK["ci:skill_package:*"]
  AASU -->|uses_short_term_memory| STM["ci:memory_short_term_profile:*"]
  AASU -->|uses_long_term_memory| LTM["ci:memory_long_term_profile:*"]
  AASU -->|uses_knowledge_graph| KG["ci:knowledge_graph:*"]
  AASU -->|uses_context_graph_profile| CG["ci:context_graph_profile:*"]
  CG -->|context_graph_derived_from| KG
  STM -->|stores_memory_in| STORE["ci:store:memory:*"]
  LTM -->|stores_memory_in| STORE
  AIBOM["ci:aibom_document:*"] -->|attests| MODEL["ci:model:*"]
  ATT["ci:attestation_bundle:*"] -->|attests| AASU
  ATT -->|attests| AIBOM
```

---

## 7. Standards and Technique Alignment (OWASP + MITRE ATLAS)

Taxonomies evolve. The mappings below reflect the referenced versions used in the source documents and should be updated to match the exact versions adopted by your organization.

### 7.1 OWASP Top 10 for LLM Applications (2023) Mapping

| OWASP ID | Category | AASU Impact Area |
|---|---|---|
| LLM01 | Prompt Injection | Prompt (P), Retrieval (R) |
| LLM02 | Insecure Output Handling | Output layer, downstream parsers |
| LLM03 | Training Data Poisoning | Model (M), Retrieval (R) |
| LLM04 | Model Denial of Service | Runtime (K), Orchestration |
| LLM05 | Supply Chain Vulnerabilities | Model provider, embeddings |
| LLM06 | Sensitive Information Disclosure | Retrieval (R), Prompt (P) |
| LLM07 | Insecure Plugin Design | Tooling (T) |
| LLM08 | Excessive Agency | Tooling (T), Orchestration |
| LLM09 | Overreliance | Human-in-the-loop absence |
| LLM10 | Model Theft | Model serving, API access |

### 7.2 OWASP Top 10 for LLM Applications (2025) Mapping

| OWASP ID | Risk Category | AASU Component |
|---|---|---|
| LLM01:2025 | Prompt Injection | P, R |
| LLM02:2025 | Sensitive Information Disclosure | R, P |
| LLM03:2025 | Supply Chain | M, T |
| LLM04:2025 | Data & Model Poisoning | M, R |
| LLM05:2025 | Improper Output Handling | Output layer |
| LLM06:2025 | Excessive Agency | T, Orchestration |
| LLM07:2025 | System Prompt Leakage | P |
| LLM08:2025 | Vector & Embedding Weaknesses | R |
| LLM09:2025 | Misinformation | P, R |
| LLM10:2025 | Unbounded Consumption | K |

### 7.3 OWASP Top 10 for Agentic Applications (2026) Mapping

| ASI ID | Risk Category | Impact Area |
|---|---|---|
| ASI01 | Agent Goal Hijack | P, Orchestration |
| ASI02 | Tool Misuse | T |
| ASI03 | Identity & Privilege Abuse | T |
| ASI04 | Agentic Supply Chain | MCP / tool ecosystem |
| ASI05 | Unexpected Code Execution | Tool runtime |
| ASI06 | Memory Poisoning | Short-term/Long-term Memory Profiles, Context Graph |
| ASI07 | Inter-Agent Insecurity | Routing |
| ASI08 | Cascading Failures | Sequential chains |
| ASI09 | Human-Agent Trust Exploitation | UX |
| ASI10 | Rogue Agents | Runtime |

### 7.4 MITRE ATLAS Technique Mapping

| ATLAS Technique | Description | Relevant AASU Component |
|---|---|---|
| AML.TA0001 | Initial Access | Prompt layer |
| AML.TA0002 | Execution | Tool invocation |
| AML.TA0003 | Persistence | Session memory |
| AML.TA0004 | Privilege Escalation | Tool chaining |
| AML.TA0005 | Defense Evasion | Prompt obfuscation |
| AML.TA0006 | Credential Access | Tool misuse |
| AML.TA0007 | Discovery | Retrieval probing |
| AML.TA0008 | Lateral Movement | Cross-agent pivot |
| AML.TA0009 | Exfiltration | Tool export, retrieval |
| AML.TA0010 | Impact | Tool-based destructive action |

---

## 8. Formal Model Summary

**AASU = (P, M, R, T, K)**

**AI System = Directed Graph of AASUs**

**Governance Extension Assets = {Skills, Short-Term Memory, Long-Term Memory, Knowledge Graph, Context Graph Profile, AIBOM, Attestations}**

**Security Risk = f(Configuration, Topology, Privilege Edges, Routing Logic)**

Testing coverage (conceptually) must account for:
- **AASU coverage** (per-node testing against each configuration snapshot)
- **Graph coverage** (edge/path/topology testing across the deployed system)

---

## 9. Conclusion

Modern AI systems are configuration-bound entities deployed in directed topologies.

The Atomic AI Security Unit (AASU) model enables:
- Precise scoping for testing and red teaming
- Architecture-aware validation for chained and multi-agent systems
- Version-bound governance with audit-ready evidence
- Regulatory defensibility through configuration-linked certification

Organizations that adopt AASU-based validation move from ad-hoc model testing to structured AI security engineering.

---

**End of Consolidated White Paper (v2.2)**
