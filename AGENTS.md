## Agent skills

### Issue tracker

Issues and PRDs are tracked as local markdown files under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Triage uses the default Matt Pocock skill labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

This repo uses the single-context domain docs layout: root `CONTEXT.md` plus `docs/adr/` when those files exist. See `docs/agents/domain.md`.

### Planning state

Fresh sessions must start with `.planning/STATE.md`, then `.planning/ROADMAP.md`, then the active phase checkpoint under `.planning/phases/`. Use `.scratch/phase-state.json` as the live phase gate only after reading the durable planning docs.

When a phase, checkpoint, blocker, or next action changes, update `.planning/STATE.md` and the active phase `*-CHECKPOINTS.md` before ending the session.
