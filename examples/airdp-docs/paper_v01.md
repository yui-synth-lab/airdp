# AIRDP v3.0 Framework Technical Overview

## 1. Introduction to AIRDP v3.0
The AIRDP (AI-driven Iterative Development & Production) v3.0 framework is a specialized system designed for the automated generation and maintenance of high-fidelity Technical Framework Documentation. Unlike linear generation tools, AIRDP v3.0 operates as an iterative orchestration layer that manages complex documentation lifecycles through structural constraints and multi-agent collaboration. Its primary goal is to ensure that technical outputs remain architecturally consistent with a central source of truth while leveraging the unique strengths of various large language models (LLMs).

## 2. The 5-Phase Pipeline
The core of the AIRDP v3.0 framework is its 5-phase operational pipeline. This pipeline is inherently iterative, allowing for feedback loops that refine technical sections until they meet the required criteria. The AIRDP orchestration layer serves as the control plane for this pipeline, maintaining state and enforcing architectural boundaries, while individual LLM workers function as stateless execution units invoked within specific phase scopes.

### Phase 1: Seed
The **Seed** phase serves as the initialization point for a documentation cycle. During this phase, the system gathers initial requirements, defines the scope of the documentation task, and establishes the foundational context. This includes identifying the target `unit_objective` and the corresponding `unit_criteria` that will be used for validation later in the pipeline.

### Phase 2: Plan
In the **Plan** phase, the framework formulates a strategy for execution. This involves breaking down the `unit_objective` into actionable sub-tasks and determining the optimal orchestration of AI resources. The plan establishes the roadmap for the cycle, ensuring that the subsequent implementation aligns with the architectural requirements defined in the SSoT.

### Phase 3: Execute
The **Execute** phase is where the primary work is performed by the **Technical Documentation Writer (Executor)**. The Executor generates the technical content, adhering to the plan and the writing standards defined in the project configuration. This phase focuses on technical accuracy, idiomatic consistency, and precise terminology.

### Phase 4: Judge
The **Judge** phase is the primary quality control mechanism. The **Framework Architect (Validator)** reviews the output generated in the Execute phase against the **AIRDP v3.0 System Specification (SSoT)** and the pre-defined `unit_criteria`. If the output does not meet the standards, the Judge phase triggers a loop back to the Plan or Execute phases for further refinement. This iterative loop is critical for maintaining high architectural standards.

### Phase 5: Report
The **Report** phase concludes the cycle. It involves the finalization of the documentation artifacts and the generation of a comprehensive report detailing the results of the cycle. This phase ensures that all decisions, revisions, and validation results are documented for auditability and future reference.

## 3. Multi-AI Orchestration
AIRDP v3.0 leverages a sophisticated orchestration layer to integrate multiple AI models, including Gemini, Claude, Copilot, and Codex. The Orchestrator is a distinct architectural component—a coordination layer external to the LLMs—that manages the documentation lifecycle. It delegates tasks to LLM workers by issuing phase-specific prompts via API calls, where each LLM operates as a stateless execution unit within its assigned phase boundary.

Rather than treating these models as general-purpose workers, the framework assigns them specialized roles based on their inherent strengths:
- **Gemini/Claude**: Typically utilized for high-level architectural planning, complex reasoning, and validation (Validator roles).
- **Copilot/Codex**: Employed for localized technical implementation, code-focused documentation, and syntactic precision (Executor roles).

The Orchestrator maintains the integrity of the documentation lifecycle by controlling the pipeline flow and state management, ensuring that each contribution is integrated according to the SSoT without losing contextual consistency.

## 4. SSoT-Driven Quality Control
A defining characteristic of AIRDP v3.0 is its reliance on the **AIRDP v3.0 System Specification (SSoT)** as the primary arbiter of quality. The SSoT is a persistent, centralized source of truth that contains the governing constants, lexicon, and architectural rules for the project. 

SSoT-driven quality control is not merely a prompting technique; it is a structural constraint enforced at every phase of the pipeline. By referencing the SSoT, the framework ensures that terminology (such as Executor and Validator) is used consistently and that all technical claims remain synchronized with the underlying system architecture. The boundary of the framework is explicitly defined by the Orchestrator's enforcement of these SSoT constraints upon the stateless LLM workers.

## 5. Cumulative vs. Independent Pipeline Modes
AIRDP v3.0 supports two distinct operational modes that determine how artifacts are handled across iterations:

### Cumulative Mode
In **Cumulative Mode**, the framework treats documentation as a shared, evolving artifact. Each iteration builds upon the previous one, refining and expanding the existing content. This mode is ideal for complex, multi-section documents where internal consistency and cross-referencing are paramount.

### Independent Mode
In **Independent Mode**, the framework treats each `unit_objective` as a standalone task. Artifacts are generated and validated in isolation, without direct dependence on the state of other sections. This mode is suitable for modular documentation tasks or when speed and parallelism are prioritized over global document cohesion.

## Revision Notes
- **[R-1] Orchestrator–LLM Worker Relationship**: Explicitly defined the Orchestrator as a distinct architectural component (coordination layer) that invokes LLM workers as stateless execution units via API-driven, phase-specific prompts.
- **[R-2] Architectural Boundaries**: Added clarifying statements in Section 2 (Introduction) and Section 3 (Orchestration) to delineate the boundary between the AIRDP orchestration layer (control plane, state, SSoT enforcement) and the LLM workers (stateless execution).
- **Terminology Consistency**: Verified and synchronized use of "Executor", "Validator", and "SSoT" with the AIRDP v3.0 System Specification.
