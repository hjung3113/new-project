# ROADMAP - Roo Harness Hardening

Granularity: standard. This roadmap is intentionally document-centered: each phase has a folder under `.planning/phases/` and can be resumed from its checkpoint documents.

## Phases

- [x] **Phase 1: Document-Centered Phase Continuity** - Add `.planning/` project memory, phase/checkpoint structure, and gate alignment so fresh sessions can continue without transcript state.
- [x] **Phase 2: DB Context Snapshot** - Add cache-first MSSQL metadata snapshot tooling and teach Roo workflows to use real DB shape without repeated database connections.
- [ ] **Phase 3: Mechanical Gate Enforcement** - Add pre-commit or CI checks that validate `.scratch/phase-state.json` and changed paths against the approved plan.
- [ ] **Phase 4: Template Consumer Onboarding** - Add concise bootstrap instructions for cloning this harness into a target C# ETL project.
- [ ] **Phase 5: Example ETL Slice** - Add a minimal sample phase plan for a real parser or writer change, proving the harness works end to end.

## Phase Details

### Phase 1: Document-Centered Phase Continuity

**Goal**: Make the repo self-resumable through `.planning/`, not chat memory.

**Depends on**: Current Roo harness scaffold.

**Success Criteria**:

1. `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, and `STATE.md` exist and identify the project, requirements, phases, current position, decisions, and next action.
2. The active phase folder contains context, plan, checkpoints, review, summary, and verification files.
3. `AGENTS.md` tells future agents to start from `.planning/STATE.md`.
4. `docs/phase-gate-harness.md` explains how `.scratch/phase-state.json` points back to `.planning/` docs.
5. The handoff file is rewritten to reference the durable docs and avoid stale Roo/C#-only review state.

**Plans**: 1 plan.

### Phase 2: DB Context Snapshot

**Goal**: Give Roo workflows cache-first access to real MSSQL metadata and routines without repeated database connections.

**Depends on**: Phase 1.

**Success Criteria**:

1. A local snapshot command reads `.db-context/latest.json` by default without connecting to DB.
2. Explicit refresh collects fixed catalog metadata for one master DB and many process DBs.
3. Refresh reuses cached database detail when object `modify_date` markers are unchanged.
4. DB, ETL, review, and ops workflows return `needs-db-context` when required DB context is missing or insufficient.

**Plans**: 1 plan.

### Phase 3: Mechanical Gate Enforcement

**Goal**: Convert prompt-level phase discipline into repository checks.

**Depends on**: Phase 1.

**Success Criteria**:

1. A local validation command verifies `.scratch/phase-state.json` against `.scratch/phase-state.schema.json`.
2. A changed-path check fails when implementation edits fall outside `allowed_paths`.
3. The enforcement workflow is documented with bypass policy and limitations.

**Plans**: TBD.

### Phase 4: Template Consumer Onboarding

**Goal**: Make a new project team able to adopt the harness without reading every rule file.

**Depends on**: Phase 1.

**Success Criteria**:

1. README or docs include a bootstrap checklist.
2. The checklist explains how to replace project placeholders, create initial `.planning/` docs, and start a first phase.
3. The checklist identifies which files are template internals and which are target-project memory.

**Plans**: TBD.

### Phase 5: Example ETL Slice

**Goal**: Prove the workflow against one realistic ETL change plan.

**Depends on**: Phase 2 or explicit user approval to keep enforcement prompt-only.

**Success Criteria**:

1. Example phase includes context, plan, red evidence, implementation scope, green evidence, summary, and review.
2. MSSQL test expectations use real container-backed checks.
3. The example can be copied into a target project as a starting template.

**Plans**: TBD.

## Progress

| Phase | Plans Complete | Status | Completed |
| --- | ---: | --- | --- |
| 1. Document-Centered Phase Continuity | 1/1 | Implemented | 2026-05-11 |
| 2. DB Context Snapshot | 1/1 | Implemented | 2026-05-13 |
| 3. Mechanical Gate Enforcement | 0/? | Not started | - |
| 4. Template Consumer Onboarding | 0/? | Not started | - |
| 5. Example ETL Slice | 0/? | Not started | - |

## Coverage

- REQ-continuity -> Phase 1.
- REQ-phase-checkpoints -> Phase 1 and all future phase folders.
- REQ-decision-capture -> Phase 1.
- REQ-verification-chain -> Phase 1 and all future phase summaries.
- REQ-gate-alignment -> Phase 1 and Phase 3.
