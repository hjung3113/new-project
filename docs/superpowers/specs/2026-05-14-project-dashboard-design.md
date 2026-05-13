# Project Dashboard Static HTML Generator Design

## Purpose

Create a script-generated HTML dashboard that makes the repository's planning state understandable at a glance. The dashboard should help a human see current progress, remaining work, active gates, blockers, verification evidence, and relevant planning documents without reading every file under `.planning/` and `.scratch/`.

## Scope

The first version will add a dependency-free Python static generator:

- Script: `scripts/project_dashboard.py`
- Output: `.scratch/reports/project-dashboard.html`
- Runtime: Python standard library only
- Usage: `python3 scripts/project_dashboard.py`

The generated HTML will be a single self-contained file with inline CSS and minimal inline JavaScript only when useful for in-page navigation or filtering. It will not require a local server, package manager, database, or network access.

## Data Sources

The generator will read these repository files when present:

- `.planning/STATE.md` for current milestone, active phase, checkpoint, next action, blockers, progress, and last updated metadata.
- `.planning/ROADMAP.md` for the phase list, completion state, goals, success criteria, and progress table.
- `.planning/phases/**` for phase-level context, plan, checkpoints, review, verification, and summary files.
- `.scratch/phase-state.json` for live phase gate state, approval status, plan pointer, allowed paths, blocked paths, acceptance criteria, verification commands, notes, and next action.
- `.scratch/**/issues/*.md` for local issue cards.
- `docs/**`, `README.md`, and `AGENTS.md` as a document inventory with path, first heading, document category, and link target rather than fully rendered content.

Missing optional files should produce visible warnings in the dashboard rather than failing generation. Invalid JSON in `.scratch/phase-state.json` should fail generation with a clear terminal error because that file is a live gate contract.

## Extraction Rules

The implementation will keep parsing intentionally conservative:

- Parse YAML-like frontmatter in `.planning/STATE.md` using simple line-based rules.
- Parse Markdown headings and checklist bullets for roadmap and phase documents.
- Parse issue files by frontmatter if available, otherwise use the first heading as the title.
- Do not implement a complete Markdown renderer.
- Escape all document-derived text before embedding it in HTML.

This keeps the generator robust enough for the repository's current document style without adding dependencies or creating a new document format.

## Dashboard Layout

The dashboard will use the approved hybrid layout:

1. Header summary: project name, milestone, current status, progress percentage, last update, and generated timestamp.
2. Left summary rail: active phase, active checkpoint, live gate state, approval status, blockers, and next action.
3. Main roadmap kanban: phases grouped into Done, In Progress, and Remaining columns so completed and remaining work are visible at a glance.
4. Phase detail sections: each phase shows available context, plan, checkpoints, review, verification, summary, and document links.
5. Verification section: commands and evidence from `.scratch/phase-state.json` and phase verification files.
6. Issue section: local issue cards discovered under `.scratch/**/issues/*.md`.
7. Document inventory section: `docs/**`, `README.md`, `AGENTS.md`, and selected `.planning/codebase/**` files grouped by category.
8. Warning section: missing files, inconsistent pointers, stale or unresolved state, and absent active checkpoint files.

## Consistency Checks

The generator will surface warnings for conditions such as:

- `.scratch/phase-state.json` references a missing `state_path`, `plan_path`, or `checkpoint_path`.
- `.planning/STATE.md` active checkpoint differs from `phase-state.json.current_checkpoint`.
- Roadmap progress and STATE frontmatter progress disagree.
- Phase folders are present but not listed in the roadmap.
- Issue files are present but not referenced by any active phase context.
- Referenced core documents such as `README.md`, `AGENTS.md`, or `docs/phase-gate-harness.md` are missing.

Warnings should appear both in terminal output and in the generated HTML.

## Non-Goals

- No live server in the first version.
- No package manager, framework, Vite, React, or external CSS.
- No full Markdown rendering.
- No mutation of planning state.
- No automatic phase-state repair.
- No attempt to infer application implementation progress beyond what the documents say.

## Verification

Initial verification will run:

```bash
python3 -m py_compile scripts/project_dashboard.py
python3 scripts/project_dashboard.py
test -f .scratch/reports/project-dashboard.html
python3 scripts/harness.py check
```

If a future change adds tests for the parser, they should remain standard-library `unittest` tests.

## Open Decisions

None. The user selected the hybrid layout and static Python generator.
