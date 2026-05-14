# Roo Slash Commands

These commands are the user-facing entry points for the template.

| Command | Mode | Purpose |
| --- | --- | --- |
| `/simple` | `orchestrator` | Run the lightweight path for focused questions, small low-risk edits, docs tweaks, harmless command runs, mechanical cleanup, and tiny locally verified changes. |
| `/feature` | `orchestrator` | Route ordinary application behavior or refactoring into the TDD workflow when no narrower owner applies. |
| `/bugfix` | `orchestrator` | Run the root-cause workflow for broken behavior, failing tests, wrong output, regressions, or unknown cause. |
| `/etl` | `orchestrator` | Run the ETL workflow for parser, normalization, correction, state, matching, merge, buffering, writer flow, replay, or restart safety. |
| `/db` | `orchestrator` | Run the DB workflow for MSSQL schema, EF migration, SQL, indexes, transactions, Dapper, `SqlBulkCopy`, `MERGE`, or persistence migrations. |
| `/ops` | `orchestrator` | Route operational work for logs, metrics, processing events, retry boundaries, worker polling, graceful shutdown, dashboards, or runbooks. |
| `/adr` | `architect` | Run the architecture workflow for durable design decisions, boundaries, state models, tradeoffs, or implementation planning. |
| `/review` | `review` | Run the read-only review workflow for code, SQL, ETL, tests, performance, or operations risk. |
| `/issues` | `docs-issues` | Convert docs and plans into PRDs, local tracker issues, acceptance criteria, and implementation slices. |
| `/doctor` | `orchestrator` | Run `workflow-harness-doctor` for read-only harness diagnostics covering planning, Roo command/mode, DB context config, and diff-before-mutation readiness. |

Slash commands stay thin. Use `.roo/rules-orchestrator/rules.md` for exclusive routing and tie breakers; use the workflow skill or owning mode for the actual sequence.

## Automation Flags

Any workflow that uses the phase gate may receive these prompt flags:

- `--auto`: select recommended low-risk defaults, record auditable `auto_selected` entries, and stop for destructive, external, security-sensitive, irreversible, broad-scope, or ambiguous product-direction choices.
- `--chain`: run one phase's reviewed `discuss -> plan -> execute` path with recommended defaults only when `.scratch/phase-state.json` is verified or written with `phase=execute`, matching `plan_id`, `approved=true`, `automation_mode=chain`, durable pointers, non-empty `allowed_paths`, non-empty `verification`, and no unresolved P1 adversarial review finding.

Flags do not skip phase-local `discuss`, alignment summary, adversarial review, plan approval evidence, or verification.
