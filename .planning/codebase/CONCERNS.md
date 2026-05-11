# CONCERNS - Harness Risks and Follow-Ups

**Analysis date:** 2026-05-11

## Active Concerns

### Prompt-level gates are not mechanical

- **Risk**: Roo rules can instruct agents, but cannot stop filesystem writes or commits.
- **Current mitigation**: `.scratch/phase-state.json` records explicit phase, plan, allowed paths, verification, checkpoint, and next action.
- **Follow-up**: Phase 2 should add validation and changed-path checks.

### Template adoption still needs a bootstrap path

- **Risk**: A target team may copy the harness but leave template-specific wording or stale phase docs in place.
- **Current mitigation**: `.planning/ROADMAP.md` includes Phase 3 for consumer onboarding.
- **Follow-up**: Add a concise adoption checklist that distinguishes template internals from target-project memory.

### Example implementation is intentionally absent

- **Risk**: Without a sample phase, adopters may not see how red evidence, allowed paths, and checkpoint updates fit together.
- **Current mitigation**: Phase 4 is reserved for an example ETL slice.
- **Follow-up**: Add the example only after mechanical enforcement scope is decided, or explicitly document why prompt-only enforcement is acceptable.

### Stale handoff references can drift

- **Risk**: Temporary handoffs can become misleading if they duplicate planning state.
- **Current mitigation**: `.planning/HANDOFF-PROTOCOL.md` requires handoffs to point to durable docs instead of becoming the source of truth.
- **Follow-up**: Keep future handoffs short and update `.planning/STATE.md` before ending work.

## Non-Concerns

- Lack of app source is expected; this repository is a harness template.
- `.scratch/phase-state.json` being in `done` is expected after Phase 1; new work should start a new `discuss` or `plan` state.
