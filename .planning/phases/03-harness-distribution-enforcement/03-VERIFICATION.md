# Phase 3 Verification - Harness Distribution and Enforcement

Final local run on 2026-05-14:

```bash
python3 -m unittest scripts/test_harness.py
python3 -m unittest scripts/test_db_context_snapshot.py
python3 -m py_compile scripts/harness.py scripts/test_harness.py
python3 scripts/harness.py check
python3 scripts/harness.py check --worktree
jq . .roomodes >/dev/null
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.json
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.example.json
tmp="$(mktemp -d)"; python3 scripts/harness.py init --target "$tmp/target"; python3 scripts/harness.py check --target "$tmp/target"; (cd "$tmp/target" && python3 scripts/harness.py check)
```

## Results

- `python3 -m unittest scripts/test_harness.py`: passed, 12 tests.
- `python3 -m unittest scripts/test_db_context_snapshot.py`: passed, 9 tests.
- `python3 -m py_compile scripts/harness.py scripts/test_harness.py`: passed.
- `python3 scripts/harness.py check`: passed.
- `python3 scripts/harness.py check --worktree`: passed.
- `jq . .roomodes >/dev/null`: passed.
- `phase-state.json` AJV validation: passed.
- `phase-state.example.json` AJV validation: passed.
- Installed-target lifecycle smoke test: passed.
