# Defining the Atomic AI Security Unit (AASU)

## White Paper v1.2 -- Publish Ready Edition

**Document ID:** AASU-WP-1.2\
**Version:** 1.2 (Publish-Ready with Diagrams and Control Mapping)\
**Date:** 2026-02-21\
**Audience:** CISO, AI Security Engineering, AppSec, ML Engineering,
Platform Teams, Risk/GRC, Audit\
**Classification:** Public / External Distribution Ready

------------------------------------------------------------------------

# Executive Summary

Enterprise GenAI systems are composed of configuration-bound components
including prompts, models, retrieval layers, and tool execution
frameworks. Security failures in modern AI systems are rarely model-only
issues. They are configuration, orchestration, and topology issues.

This paper formalizes:

-   The **Atomic AI Security Unit (AASU)**
-   Architecture-aware testing patterns
-   A three-layer validation methodology
-   A formal threat model structure
-   Mapping to OWASP Top 10 for LLM Applications (2023) and MITRE ATLAS

------------------------------------------------------------------------

# 1. The Atomic AI Security Unit (AASU)

## 1.1 Formal Definition

AASU = (P, M, R, T, K)

Where:

-   P = Prompt Package
-   M = Model Instance and Parameters
-   R = Retrieval Configuration
-   T = Tool/MCP Configuration
-   K = Runtime Constraints

Any change in P, M, R, T, or K creates a new AASU.

------------------------------------------------------------------------

## 1.2 Implementation Governance Profile (2026-02-28)

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

# 2. Architecture Patterns with Mermaid Diagrams

## 2.1 Single AASU

``` mermaid
flowchart LR
    User --> AASU
    AASU --> Output
```

Security Surface: - Prompt injection - Model hallucination - Tool misuse
(if enabled) - Data leakage (if retrieval enabled)

------------------------------------------------------------------------

## 2.2 Sequential Chain Pattern

``` mermaid
flowchart LR
    User --> A1[AASU-1]
    A1 --> A2[AASU-2]
    A2 --> A3[AASU-3]
    A3 --> Output
```

Characteristics: - Cascading propagation - Injection persistence -
Privilege escalation chains - Context contamination

------------------------------------------------------------------------

## 2.3 Parallel Agent Fabric

``` mermaid
flowchart LR
    User --> Router
    Router --> A1[AASU-A]
    Router --> A2[AASU-B]
    Router --> A3[AASU-C]
    A1 --> Output
    A2 --> Output
    A3 --> Output
```

Characteristics: - Surface area expansion - Policy inconsistency -
Routing manipulation risk

------------------------------------------------------------------------

## 2.4 Hybrid Directed Graph

``` mermaid
flowchart TD
    User --> R[Router]
    R --> A1[AASU-1]
    R --> A2[AASU-2]
    A1 --> B1[AASU-3]
    A2 --> B1
    B1 --> C1[AASU-4]
    C1 --> Output
```

Characteristics: - Multi-path traversal - Privilege pivots - Recursive
tool invocation - Emergent graph-level vulnerabilities

------------------------------------------------------------------------

# 3. Formal Threat Model Section

## 3.1 Assets

-   Sensitive data (PII, financial, proprietary)
-   Tool capabilities (refunds, exports, writes)
-   Retrieval corpora
-   Model credentials and API keys
-   Session state and conversation memory

## 3.2 Threat Actors

-   External attackers
-   Malicious insiders
-   Prompt injection adversaries
-   Supply chain document attackers
-   Automated adversarial bots

## 3.3 Trust Boundaries

1.  User → Application
2.  Application → Model Provider
3.  Model → Tool Execution Environment
4.  Retrieval Layer → Data Stores
5.  Agent → Agent (in chained systems)

## 3.4 Data Flow Considerations

-   Context expansion via retrieval
-   Tool-generated outputs reinjected into prompts
-   Cross-agent message passing
-   Memory persistence between sessions

## 3.5 Abuse Cases

-   Prompt hierarchy override
-   Tool escalation
-   Retrieval poisoning
-   Cross-agent privilege pivot
-   Recursive execution abuse

------------------------------------------------------------------------

# 4. Three-Layer Validation Model

## Layer 1: AASU-Level Testing

-   Prompt injection resistance
-   Tool misuse simulation
-   Retrieval leakage validation
-   Output integrity checks
-   Robustness and multilingual bypass testing

## Layer 2: Orchestration Testing

-   Injection propagation across nodes
-   Retry path exploitation
-   State poisoning
-   Boundary drift detection

## Layer 3: Attack-Graph Testing

-   Multi-agent privilege escalation
-   Routing downgrades
-   Cross-AASU exfiltration
-   Graph traversal risk modeling

------------------------------------------------------------------------

# 5. OWASP Top 10 for LLM Applications (2023) Mapping

  OWASP ID   Category                           AASU Impact Area
  ---------- ---------------------------------- ----------------------------------
  LLM01      Prompt Injection                   Prompt (P), Retrieval (R)
  LLM02      Insecure Output Handling           Output layer, downstream parsers
  LLM03      Training Data Poisoning            Model (M), Retrieval (R)
  LLM04      Model Denial of Service            Runtime (K), Orchestration
  LLM05      Supply Chain Vulnerabilities       Model provider, embeddings
  LLM06      Sensitive Information Disclosure   Retrieval (R), Prompt (P)
  LLM07      Insecure Plugin Design             Tooling (T)
  LLM08      Excessive Agency                   Tooling (T), Orchestration
  LLM09      Overreliance                       Human-in-the-loop absence
  LLM10      Model Theft                        Model serving, API access

------------------------------------------------------------------------

# 6. MITRE ATLAS Technique Mapping

  ATLAS Technique   Description            Relevant AASU Component
  ----------------- ---------------------- -------------------------------
  AML.TA0001        Initial Access         Prompt layer
  AML.TA0002        Execution              Tool invocation
  AML.TA0003        Persistence            Session memory
  AML.TA0004        Privilege Escalation   Tool chaining
  AML.TA0005        Defense Evasion        Prompt obfuscation
  AML.TA0006        Credential Access      Tool misuse
  AML.TA0007        Discovery              Retrieval probing
  AML.TA0008        Lateral Movement       Cross-agent pivot
  AML.TA0009        Exfiltration           Tool export, retrieval
  AML.TA0010        Impact                 Tool-based destructive action

------------------------------------------------------------------------

# 7. Governance and Audit Readiness

AASU-based governance enables:

-   Configuration-hash binding of test results
-   Mandatory retesting on config change
-   Node, path, and topology coverage metrics
-   Traceable certification statements
-   Risk acceptance tied to specific configuration IDs

------------------------------------------------------------------------

# 8. Conclusion

AI systems must be tested as configuration-bound graph structures, not
monolithic models.

The AASU model provides:

-   Architectural clarity
-   Test scoping precision
-   Red team repeatability
-   Governance defensibility
-   Regulatory alignment

This v1.2 edition extends the AASU model with visual topology diagrams,
a formal threat model, and industry-standard control mapping to OWASP
and MITRE ATLAS.

------------------------------------------------------------------------

**End of White Paper v1.2**
