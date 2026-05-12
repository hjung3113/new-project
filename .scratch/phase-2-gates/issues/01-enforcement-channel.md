# ROO-7 Decide enforcement channel for phase gate

Status: ready-for-human

## Decision

Selected channel: **both pre-commit and CI**.

- Pre-commit provides fast local feedback before push.
- CI provides authoritative enforcement for pull-request merge.
- CI required status check is the non-bypassable control; pre-commit is a convenience guardrail.

## Rationale

Evaluated options:

1. Pre-commit only: fast but bypassable.
2. CI only: reliable but slower feedback.
3. Both pre-commit and CI: best blend of feedback speed and enforcement reliability.

Decision criteria coverage:

- Developer feedback speed: pre-commit catches failures early.
- Enforcement reliability: CI with required checks enforces at merge time.
- Ease of bypass/exception handling: local bypass possible for emergencies, but CI remains mandatory.
- Setup and maintenance cost: moderate; mitigated by one shared command used in both channels.
- Phase 3 onboarding compatibility: strong; newcomers benefit from local guardrails plus centralized policy.

## Bypass / Exception Policy

- Local pre-commit bypass (`git commit --no-verify`) is allowed only for temporary tooling issues or emergency commits.
- Bypassed commits still must pass CI before merge.
- CI bypass is not allowed by default.
- Any temporary CI exception must include issue reference, owner, and expiry date.

## Validation commands and workflow trigger

Canonical command (local and CI):

```bash
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.json
```

Additional Phase 2 command (after ROO-8 path semantics decision):

- changed-path enforcement command to verify edits stay within `allowed_paths`.

Trigger points:

- local pre-commit hook
- CI pull-request workflow with required status check

## Follow-up implementation issue

- Create child issue: **Implement dual-channel phase gate enforcement (pre-commit + required CI)**.
- Scope:
  - wire shared phase-gate command into pre-commit
  - run same command in CI PR job
  - document required-check policy and exception process

## Comments

- 2026-05-11: Decision documented from ROO-7 analysis session.
