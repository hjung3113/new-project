# Codex Cloud Setup

Use this guide to work on `hjung3113/new-project` from a phone through Codex Cloud.

## Connect the repository

1. Open `https://chatgpt.com/codex`.
2. Sign in with the ChatGPT account that has Codex access.
3. Select `Connect GitHub`.
4. Authorize the GitHub connector.
5. Grant access to `hjung3113/new-project`.

If the repository does not appear immediately, wait a few minutes and confirm the GitHub connector has access to the repo.

## Create the Codex Cloud environment

Create an environment for:

- Repository: `hjung3113/new-project`
- Branch: `main`
- Setup command:

```bash
bash scripts/codex-cloud-setup.sh
```

This project is currently a documentation and agent-harness template. It has no app runtime, package lockfile, database, or test project yet. Keep the environment setup lightweight until application code is added.

## Suggested task prompt from mobile

Use `Ask` for read-only questions:

```text
Read AGENTS.md, .planning/STATE.md, .planning/ROADMAP.md, the active checkpoint, and .scratch/phase-state.json. Summarize the current project state and the next safe action. Do not edit files.
```

Use `Code` only for explicit repo-control changes, for example:

```text
Update the Codex Cloud setup docs. Keep changes limited to AGENTS.md, docs/codex-cloud-setup.md, and scripts/codex-cloud-setup.sh. Run the documented verification commands.
```

For application implementation work, first create or update the phase plan and wait for execute approval in `.scratch/phase-state.json`.

## GitHub PR review

After Codex Cloud and code review are enabled for the repo, request a review in a PR comment:

```text
@codex review
```

For a focused review:

```text
@codex review for phase-gate violations and missing verification evidence
```

Codex should follow the review guidance in `AGENTS.md`.

## Verification commands

Run these after setup or harness changes:

```bash
bash scripts/codex-cloud-setup.sh
jq . .scratch/phase-state.json >/dev/null
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.json
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.example.json
rg -n "Codex Cloud|phase-state|checkpoint|workflow-phase-gate" AGENTS.md README.md docs .roo .planning
```
