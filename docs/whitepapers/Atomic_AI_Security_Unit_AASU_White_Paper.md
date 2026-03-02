# Defining the Atomic AI Security Unit (AASU)

## A Formal Security Model for Testing, Red Teaming, and Validation of Enterprise GenAI Systems

**Version:** 1.0\
**Classification:** White Paper

------------------------------------------------------------------------

# Executive Summary

Enterprise AI systems are no longer single-model deployments. Modern
GenAI applications integrate:

-   Large Language Models (LLMs)
-   Application-layer prompts
-   Retrieval-Augmented Generation (RAG)
-   Model Context Protocol (MCP) or tool invocation layers
-   Multi-agent orchestration logic

Most organizations incorrectly treat the model as the unit under test.

This white paper introduces a formal security abstraction:

> **Atomic AI Security Unit (AASU)**

An AASU defines the smallest configuration-bound AI system instance that
must be treated as a single unit for security testing, red teaming, and
governance validation.

------------------------------------------------------------------------

# 1. The Core Problem

Traditional application security assumes deterministic software
behavior.\
Modern GenAI systems are configuration-driven and behaviorally emergent.

Two systems using the same model can exhibit entirely different risk
profiles depending on:

-   Prompt structure\
-   Tool access\
-   Retrieval configuration\
-   Decoding parameters

**The model is not the unit of risk.\
The configuration is the unit of risk.**

------------------------------------------------------------------------

# 2. The Atomic AI Security Unit (AASU)

## 2.1 Definition

An AASU is a tightly bound, versioned configuration consisting of:

1.  Application Prompt\
2.  Model Instance\
3.  RAG Configuration (if present)\
4.  MCP / Tooling Layer (if present)\
5.  Runtime Parameters

If any element changes, a new AASU is formed.

------------------------------------------------------------------------

## 2.2 Behavioral Determinism Principle

While LLM outputs are probabilistic, the security posture of an AASU is
configuration-deterministic.

Changes in:

-   Prompt wording\
-   Tool schema\
-   Retrieval thresholds\
-   Temperature settings

can materially alter:

-   Prompt injection susceptibility\
-   Tool misuse risk\
-   Data leakage exposure\
-   Escalation behavior

Security testing must bind to a configuration snapshot, not a model
name.

------------------------------------------------------------------------

# 3. Enterprise Deployment Patterns

## 3.1 Sequential Chained Units

User → AASU-1 → AASU-2 → AASU-3 → Output

### Risks

-   Cascading failure\
-   Injection amplification\
-   Context contamination\
-   Privilege escalation chains

### Testing Requirements

-   Per-unit adversarial testing\
-   Cross-unit validation\
-   Multi-stage attack simulation

------------------------------------------------------------------------

## 3.2 Parallel Agent Fabric

User → Router → Multiple Independent AASUs

### Risks

-   Surface area expansion\
-   Policy inconsistency\
-   Routing manipulation\
-   Privilege skew

### Testing Requirements

-   Independent unit testing\
-   Routing logic testing\
-   Cross-agent policy audits

------------------------------------------------------------------------

## 3.3 Hybrid Directed AI Graph

Nodes = AASUs\
Edges = Data flow relationships

### Risks

-   Emergent systemic behavior\
-   Recursive tool abuse\
-   Cross-branch contamination\
-   Graph-level privilege escalation

Requires graph-based security modeling.

------------------------------------------------------------------------

# 4. Layered Security Validation Framework

## Layer 1: Configuration-Level Testing

-   Prompt injection testing\
-   Tool misuse simulation\
-   RAG leakage validation

## Layer 2: Orchestration-Level Testing

-   Cross-unit contamination\
-   Injection persistence\
-   State poisoning

## Layer 3: System-Level Attack Graph Testing

-   Multi-agent escalation\
-   Cross-agent exfiltration\
-   Recursive invocation abuse

------------------------------------------------------------------------

# 5. Governance and Versioning

Each AASU must maintain:

-   Configuration ID\
-   Prompt version\
-   Model version\
-   Tool version\
-   Retrieval version\
-   Parameter set

Any modification invalidates prior certification.

------------------------------------------------------------------------

# 6. Formal Model Summary

AASU = {Prompt, Model, RAG, MCP, Parameters, Memory, Skills}

AI System = Directed Graph of AASUs

Security Risk = f(Configuration, Topology, Privilege Edges, Routing
Logic)

Testing Coverage = Σ (AASU Coverage + Graph Coverage)

------------------------------------------------------------------------

# 7. Conclusion

Modern AI systems are configuration-bound entities deployed in directed
topologies.

Security validation must reflect architectural complexity.

The Atomic AI Security Unit (AASU) model enables:

-   Precise scoping\
-   Architecture-aware red teaming\
-   Version-bound governance\
-   Regulatory defensibility

Organizations that adopt AASU-based validation move from ad-hoc model
testing to structured AI security engineering.

------------------------------------------------------------------------

**End of White Paper**
