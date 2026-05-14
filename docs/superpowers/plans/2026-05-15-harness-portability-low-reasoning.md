# Harness Portability Low-Reasoning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `.scratch/reports/harness-portability-low-reasoning-review.md` recommended fixes 2-8 while intentionally excluding recommended fix 1.

**Architecture:** Keep source-harness behavior in `scripts/harness.py` and source-only tests in `scripts/test_harness.py`. Install a smaller target-safe smoke test into initialized targets. Treat `AGENTS.md` and `README.md` required phrases as validation invariants until managed-block merge exists.

**Tech Stack:** Python standard library, `unittest`, Roo harness manifest and markdown skeleton files.

---

### Task 1: Target First Action And Phase 0 Placeholders

**Files:**
- Modify: `harness/skeleton/clean/README.md`
- Modify: `harness/skeleton/clean/.planning/STATE.md`
- Create: `harness/skeleton/clean/.planning/phases/00-planning-hydration/00-CONTEXT.md`
- Create: `harness/skeleton/clean/.planning/phases/00-planning-hydration/00-01-PLAN.md`
- Create: `harness/skeleton/clean/.planning/phases/00-planning-hydration/00-REVIEW.md`
- Create: `harness/skeleton/clean/.planning/phases/00-planning-hydration/00-VERIFICATION.md`
- Create: `harness/skeleton/clean/.planning/phases/00-planning-hydration/00-01-SUMMARY.md`
- Modify: `harness/manifest.json`
- Test: `scripts/test_harness.py`

- [ ] Add a failing test that initializes a target and asserts README/STATE contain the same boxed first action, the README start order includes `AGENTS`, `STATE`, `ROADMAP`, `.planning/codebase/**`, active phase docs, and `.scratch/phase-state.json`, and Phase 0 companion docs are installed.
- [ ] Run `python3 -m unittest scripts.test_harness.HarnessToolTests.test_init_installs_first_action_and_phase_zero_placeholders -v`; expect failure.
- [ ] Add the skeleton markdown files and manifest entries.
- [ ] Run the focused test again; expect pass.

### Task 2: Target-Safe Distributed Smoke Tests

**Files:**
- Create: `scripts/target_smoke_test.py`
- Modify: `harness/manifest.json`
- Modify: `scripts/test_harness.py`

- [ ] Add a failing test that `init` installs `scripts/test_harness.py` from `scripts/target_smoke_test.py`, then runs it inside the target.
- [ ] Run the focused test; expect failure.
- [ ] Implement the smoke test with checks that work in a target repo: `scripts/harness.py check`, JSON phase state parse, required harness files exist.
- [ ] Run the focused test again; expect pass.

### Task 3: Target Drift, Retired Files, And Guardrail Phrases

**Files:**
- Modify: `scripts/harness.py`
- Modify: `scripts/test_harness.py`

- [ ] Add failing tests for `check --target`: current source manifest missing in old target, retired installed file, stale/mutated `AGENTS.md`, and stale/mutated `README.md`.
- [ ] Run the focused tests; expect failures.
- [ ] Update `check_installed_target` to accept current source entries, compare current required files, report retired files, and check required phrases.
- [ ] Run the focused tests again; expect pass.

### Task 4: Upgrade Retires Removed Harness Files

**Files:**
- Modify: `scripts/harness.py`
- Modify: `scripts/test_harness.py`

- [ ] Add failing tests for `upgrade`: remove unmodified retired harness-owned files and conflict on locally modified retired files.
- [ ] Run the focused tests; expect failures.
- [ ] Update `upgrade` to compare installed state against the current manifest and remove/report retired harness-owned or managed files safely.
- [ ] Run the focused tests again; expect pass.

### Task 5: Execute Approval Semantics For Every Mode

**Files:**
- Modify: `scripts/harness.py`
- Modify: `scripts/test_harness.py`
- Modify: `.roo/skills/workflow-phase-gate/SKILL.md`

- [ ] Add failing tests for manual execute missing `allowed_paths`, `verification`, durable pointers, and approval provenance.
- [ ] Run the focused tests; expect failures.
- [ ] Require every `phase=execute` and `approved=true` state to include non-empty `plan_id`, `allowed_paths`, `verification`, `state_path`, `plan_path`, `checkpoint_path`, `approved_by`, and `approved_at`. Keep chain-specific `auto_selected` requirements.
- [ ] Run the focused tests again; expect pass.

### Task 6: Hydration Pass-0 Limit And Command Onboarding

**Files:**
- Modify: `.roo/commands/README.md`
- Modify: `.roo/skills/workflow-planning-hydration/SKILL.md`
- Modify: `.roo/skills/workflow-simple-task/SKILL.md`
- Modify: `scripts/test_harness.py`

- [ ] Add failing tests that command docs highlight the fresh-target command subset, hydration pass 0 limits outputs, and `/simple` allows one-or-two-file harness/docs/setup edits without subtask tooling.
- [ ] Run the focused tests; expect failures.
- [ ] Update the markdown workflows with those contracts.
- [ ] Run focused tests and then `python3 scripts/harness.py check`; expect pass.
