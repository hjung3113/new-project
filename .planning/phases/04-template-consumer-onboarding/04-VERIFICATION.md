# Phase 4 Verification - Harness Sync, Compatibility, and Doctor

Verification evidence will be recorded here before the phase is closed.

Required commands:

```bash
python3 -m unittest scripts/test_harness.py
python3 -m unittest scripts/test_db_context_snapshot.py
python3 -m py_compile scripts/harness.py scripts/test_harness.py scripts/db_context_snapshot.py scripts/test_db_context_snapshot.py
python3 scripts/harness.py check
python3 scripts/harness.py doctor
jq . .roomodes >/dev/null
```

## Implementation Verification - 2026-05-14

- `python3 -m unittest scripts/test_harness.py`: passed, 20 tests.
- `python3 -m unittest scripts/test_db_context_snapshot.py`: passed, 16 tests.
- `python3 -m py_compile scripts/harness.py scripts/test_harness.py scripts/db_context_snapshot.py scripts/test_db_context_snapshot.py`: passed.
- `python3 scripts/harness.py check`: passed.
- `python3 scripts/harness.py doctor`: passed; healthy repo reports the read-only P3 `diff_before_mutation` advisory only.
- `jq . .roomodes >/dev/null`: passed.
- `python3 -m json.tool .roomodes >/dev/null`: passed.
- `python3 scripts/harness.py check --worktree`: passed.
- Installed-target smoke after adding clean skeleton sync fields and `.gitignore`: `init`, `check --target`, target-local `check`, and target-local `doctor` all exited 0. Doctor reports only the read-only P3 `diff_before_mutation` advisory on a fresh target.

## Red/Green Evidence

- #17 red: focused harness tests initially failed because `find_roadmap_state_sync_findings` did not exist and checkpoint pointer drift was not rejected.
- #17 green: roadmap/state sync helper and strict check added; harness suite passed.
- #18 red: focused DB snapshot tests initially failed because `--config`, `--env-file`, `--include-procedures`, and `apply_selection` did not exist.
- #18 green: Python config loader, selected snapshot metadata/filtering, and docs added; DB snapshot suite passed.
- #18 regression red: default `process_reference_only` was inverted by the config resolver.
- #18 regression green: default reference-only behavior restored and covered by `test_default_process_reference_only_remains_true`.
- #18 final-review red: cached offline selected mode ignored selected object options.
- #18 final-review green: offline cached reports now apply selected filters without connecting, covered by `test_offline_selected_snapshot_filters_cached_report_without_connecting`.
- #19 red: doctor tests initially failed because `collect_doctor_findings` and `render_doctor_report` did not exist.
- #19 green: read-only doctor command, structured findings, JSON/Markdown renderers, and Roo `/doctor` command added; harness suite passed.
- #19 final-review red: fresh installed targets reported generic P1 roadmap/state drift.
- #19 final-review green: clean skeleton now satisfies the sync invariant, covered by `test_installed_target_doctor_does_not_report_generic_sync_p1`.
