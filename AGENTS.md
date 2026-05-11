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

## Codex Cloud

This repository can be used from Codex Cloud after connecting `hjung3113/new-project` in ChatGPT Codex.

Use `docs/codex-cloud-setup.md` when creating or updating the Codex Cloud environment. The setup command should be:

```bash
bash scripts/codex-cloud-setup.sh
```

This repo is currently a Roo/Codex harness template, not an application implementation. There is no package manager lockfile or app dependency install step yet. Do not invent `npm`, `dotnet`, or database commands until application code is added.

For any new Codex task:

1. Read `AGENTS.md`.
2. Read `.planning/STATE.md`.
3. Read `.planning/ROADMAP.md`.
4. Read the active phase checkpoint named in `.planning/STATE.md`.
5. Read `.scratch/phase-state.json`.

If `.scratch/phase-state.json` is not `phase=execute` with `approved=true`, do not modify application code. Documentation, harness, and setup changes are allowed only when the user explicitly asks for those repository-control changes.

When asked to review a pull request, prioritize phase-gate violations, accidental application-code edits outside `allowed_paths`, missing verification evidence, and mismatches between README, `.roo/**`, `.planning/**`, and `.scratch/phase-state.json`.
