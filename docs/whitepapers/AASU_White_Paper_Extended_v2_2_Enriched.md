# Defining the Atomic AI Security Unit (AASU)

## Enterprise-Grade AI Security Architecture & Validation Framework

### White Paper v2.2 -- Enriched Technical Edition

------------------------------------------------------------------------

**Document ID:** AASU-WP-2.2\
**Version:** 2.2 (Highly Enriched Edition)\
**Date:** 2026-02-23\
**Implementation Revision Note:** 2026-02-28 (v1alpha2 registry/governance extensions)\
**Intended Audience:**\
CISO \| AI Security Engineering \| Red Team \| ML Platform \| Risk & GRC
\| Enterprise Architecture \| Regulators

------------------------------------------------------------------------

# Executive Summary

Modern AI systems are not models.\
They are configuration-bound, tool-enabled, retrieval-augmented,
orchestrated computational graphs.

Traditional validation approaches that focus only on: - Model
evaluation - Prompt testing - Infrastructure penetration testing

are structurally incomplete.

This white paper introduces a rigorous and auditable model:

Atomic AI Security Unit (AASU)

and expands it into:

-   Architecture-aware threat modeling\
-   Multi-layer validation methodology\
-   Graph-based attack modeling\
-   OWASP 2025 LLM & Agentic mappings\
-   MITRE ATLAS alignment\
-   Governance & compliance model\
-   Coverage metrics framework\
-   Enterprise operating model
-   Skills, short/long-term memory, graph-context, AIBOM and attestation governance profile

------------------------------------------------------------------------

# 1. The Paradigm Shift in AI Security

## 1.1 From Model Security to Configuration Security

Security posture = f(configuration, topology, privilege graph)

Not:

Security posture = f(model)

------------------------------------------------------------------------

# 2. Atomic AI Security Unit (AASU)

AASU core = (P, M, R, T, K)  
AASU extension = (H, S)

Where:

P = Prompt Package\
M = Model & Parameters\
R = Retrieval Configuration\
T = Tool/MCP Layer\
K = Runtime Guardrails\
H = History/Memory Configuration\
S = Skill Configuration

Any change in P, M, R, T, K, H, or S creates a new AASU.

------------------------------------------------------------------------

## 2.1 Implementation Governance Profile (2026-02-28)

The operational profile keeps `(P,M,R,T,K)` unchanged while modeling
skills, memory, graph context, and attestations as separate governed
assets.

``` mermaid
flowchart LR
    AASU["AASU (P,M,R,T,K)"] -->|uses_skill| SK["Skill package"]
    AASU -->|uses_short_term_memory| STM["Short-term memory profile"]
    AASU -->|uses_long_term_memory| LTM["Long-term memory profile"]
    AASU -->|uses_knowledge_graph| KG["Knowledge graph"]
    AASU -->|uses_context_graph_profile| CG["Context graph profile"]
    CG -->|context_graph_derived_from| KG
    AIBOM["AIBOM document"] -->|attests| MODEL["Model CI"]
    ATT["Attestation bundle"] -->|attests| AASU
    ATT -->|attests| AIBOM
```

------------------------------------------------------------------------

# 3. Architecture Patterns

## Sequential Chain

``` mermaid
flowchart LR
    User --> A1["AASU-1<br/>(core + H,S)"]
    A1 --> A2["AASU-2<br/>(core + H,S)"]
    A2 --> A3["AASU-3<br/>(core + H,S)"]
    A3 --> Output
```

## Parallel Agent Fabric

``` mermaid
flowchart LR
    User --> Router
    Router --> A1["AASU-A<br/>(core + H,S)"]
    Router --> A2["AASU-B<br/>(core + H,S)"]
    Router --> A3["AASU-C<br/>(core + H,S)"]
```

## Hybrid Directed Graph

``` mermaid
flowchart TD
    User --> Router
    Router --> A1["AASU-1<br/>(core + H,S)"]
    Router --> A2["AASU-2<br/>(core + H,S)"]
    A1 --> B1["AASU-3<br/>(core + H,S)"]
    A2 --> B1
    B1 --> C1["AASU-4<br/>(core + H,S)"]
```

------------------------------------------------------------------------

# 4. OWASP Top 10 for LLM Applications (2025)

  OWASP ID     Risk Category                      AASU Component
  ------------ ---------------------------------- ------------------
  LLM01:2025   Prompt Injection                   P, R
  LLM02:2025   Sensitive Information Disclosure   R, P
  LLM03:2025   Supply Chain                       M, T
  LLM04:2025   Data & Model Poisoning             M, R
  LLM05:2025   Improper Output Handling           Output Layer
  LLM06:2025   Excessive Agency                   T, Orchestration
  LLM07:2025   System Prompt Leakage              P
  LLM08:2025   Vector & Embedding Weaknesses      R
  LLM09:2025   Misinformation                     P, R
  LLM10:2025   Unbounded Consumption              K

------------------------------------------------------------------------

# 5. OWASP Top 10 for Agentic Applications (2026)

  ASI ID   Risk Category                    Impact Area
  -------- -------------------------------- -------------------
  ASI01    Agent Goal Hijack                P, Orchestration
  ASI02    Tool Misuse                      T
  ASI03    Identity & Privilege Abuse       T
  ASI04    Agentic Supply Chain             MCP
  ASI05    Unexpected Code Execution        Tool runtime
  ASI06    Memory Poisoning                 H
  ASI07    Inter-Agent Insecurity           Routing
  ASI08    Cascading Failures               Sequential chains
  ASI09    Human-Agent Trust Exploitation   UX
  ASI10    Rogue Agents                     Runtime

------------------------------------------------------------------------

# 6. Conclusion

The AASU framework enables topology-aware, configuration-bound,
graph-based assurance for enterprise AI systems.

For operational implementation in regulated environments, the current
profile adds:

-   Skills as separate `skill_package` assets
-   Distinct short-term and long-term memory profiles
-   Knowledge graph (durable) and context graph profile (runtime)
-   AIBOM and attestation assets linked through relationship controls

These controls preserve the core AASU tuple while materially improving
change governance, auditability, and policy enforcement.

------------------------------------------------------------------------

End of White Paper v2.2
