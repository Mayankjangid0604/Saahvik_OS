# Milestone 03 — Evidence & Research Engine

## Objective

Teach the CEO how to acquire knowledge.

The CEO must become capable of identifying missing information,
planning research,
collecting evidence,
evaluating source credibility,
and producing evidence-backed executive recommendations.

The CEO must NEVER treat unverified information as fact.

---

# Philosophy

The CEO should never ask:

"What should I do?"

Instead it should ask:

"What information am I missing?"

Only after identifying knowledge gaps should research begin.

Research is always driven by reasoning.

---

# Research Lifecycle

The CEO follows this process:

Observe

↓

Reason

↓

Identify Knowledge Gaps

↓

Generate Research Questions

↓

Plan Research

↓

Collect Evidence

↓

Evaluate Credibility

↓

Extract Facts

↓

Build Evidence

↓

Generate Findings

↓

Update Recommendations

↓

Reflect

↓

Repeat

---

# Knowledge Gaps

Implement domain models for knowledge gaps.

Each gap should contain:

- identifier
- description
- reason
- priority
- required evidence
- status

The CEO must explicitly recognise when it lacks information.

---

# Research Questions

The CEO must generate structured research questions.

Each question should include:

- objective
- context
- expected answer
- related goal
- priority

---

# Research Plan

Implement a research planning model.

Each plan should define:

- questions
- required evidence
- preferred source types
- stopping conditions
- success criteria

No execution logic belongs here.

---

# Evidence Model

Evidence is a first-class domain object.

Each evidence item must contain:

- identifier
- source
- source type
- retrieval timestamp
- confidence
- reliability
- supporting facts
- contradictions
- notes

Evidence must never exist without provenance.

---

# Fact Model

Facts must be separated from evidence.

Each fact should include:

- statement
- supporting evidence
- confidence
- status

Possible status:

- verified
- partially_verified
- disputed
- unknown

Facts never directly come from external systems.

Facts are derived from evidence.

---

# Source Model

Represent research sources independently.

Each source should include:

- name
- type
- authority
- reliability
- retrieval time
- freshness

No hardcoded providers.

The system must support future providers.

---

# Research Providers

Create interfaces only.

No provider should be tightly coupled.

Examples of future providers:

- Local knowledge
- Documents
- Web search
- APIs
- Databases

Do NOT implement provider-specific logic.

---

# Research Orchestrator

Create an application service that:

- receives research plans
- selects providers
- gathers evidence
- validates evidence
- builds facts
- returns findings

The orchestrator must depend only on ports.

---

# Findings

Implement structured findings.

Each finding contains:

- summary
- evidence used
- confidence
- unresolved questions
- recommendations

---

# Executive Recommendation

Every recommendation must reference findings.

Recommendations without evidence are invalid.

---

# Provenance

Every externally acquired fact must preserve:

- source
- retrieval time
- confidence
- evidence chain

Nothing should become anonymous knowledge.

---

# Runtime Research Log

Research activity must be logged separately.

Create:

logs/research.log

Research logs must never mix with:

- system logs
- thought logs

---

# Owner Approval

Design the approval boundary.

Do NOT implement user interaction.

Represent approval requests only.

The architecture must be ready for:

- paid APIs
- sensitive sources
- private documents

Actual approval belongs to a later milestone.

---

# Architecture

Maintain Clean Architecture.

Domain owns:

- evidence
- facts
- findings
- research plans
- sources

Application owns:

- orchestration

Infrastructure owns:

- provider implementations
- persistence

---

# Forbidden

Do NOT implement:

Internet browsing

Real web search

Browser automation

Employees

Departments

Projects

Execution

Code generation

Document generation

Tool execution

Memory evolution

Business workflows

Future milestones

---

# Tests

Verify:

Knowledge gaps are valid.

Research questions are valid.

Research plans are valid.

Evidence chains remain intact.

Facts require evidence.

Recommendations require findings.

Research orchestration works.

Research logging works.

Approval requests are represented correctly.

No forbidden functionality exists.

---

# Acceptance Criteria

Complete only when:

✓ All tests pass

✓ Knowledge gap framework works

✓ Research planning works

✓ Evidence model works

✓ Fact model works

✓ Provenance preserved

✓ Findings work

✓ Recommendation framework uses evidence

✓ Research logging works

✓ Approval boundary exists

✓ Clean Architecture preserved

✓ Documentation updated

✓ No future milestone implemented