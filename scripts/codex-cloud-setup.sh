#!/usr/bin/env bash
set -euo pipefail

echo "Codex Cloud setup for hjung3113/new-project"
echo "Repository type: Roo/Codex harness template"

required_paths=(
  "AGENTS.md"
  "README.md"
  ".planning/STATE.md"
  ".planning/ROADMAP.md"
  ".scratch/phase-state.json"
  ".scratch/phase-state.schema.json"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "Missing required path: $path" >&2
    exit 1
  fi
done

if command -v jq >/dev/null 2>&1; then
  jq . .scratch/phase-state.json >/dev/null
else
  echo "jq is not installed; skipping JSON syntax check"
fi

echo "No application dependencies to install yet."
echo "Setup complete."
