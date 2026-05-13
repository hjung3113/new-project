# Project Dashboard Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dependency-free Python script that generates a self-contained HTML dashboard from `.planning/`, `.scratch/`, and `docs/` project state.

**Architecture:** Add `scripts/project_dashboard.py` as a small standard-library module with clear parsing, consistency-check, rendering, and CLI boundaries. Add focused `unittest` coverage in `scripts/test_project_dashboard.py` using temporary fixture repositories so the generator can be verified without mutating real planning state.

**Tech Stack:** Python 3 standard library (`argparse`, `dataclasses`, `html`, `json`, `re`, `tempfile`, `unittest`, `pathlib`), static HTML/CSS, no package manager.

---

## File Structure

- Create `scripts/project_dashboard.py`
  - Owns data model dataclasses, Markdown/frontmatter extraction helpers, project-state loading, docs inventory loading, warning generation, HTML rendering, and CLI entrypoint.
- Create `scripts/test_project_dashboard.py`
  - Owns parser, warning, and HTML-generation tests using temporary repository fixtures.
- Generated at runtime, not committed: `.scratch/reports/project-dashboard.html`
  - The script creates this file when run.

The implementation should not edit `.planning/**`, `.scratch/phase-state.json`, roadmap files, phase files, or application code.

## Task 1: Add Parser and Loader Tests

**Files:**
- Create: `scripts/test_project_dashboard.py`

- [ ] **Step 1: Create failing parser tests**

Add this complete test file:

```python
#!/usr/bin/env python3
"""Tests for the static project dashboard generator."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import project_dashboard


class ProjectDashboardTests(unittest.TestCase):
    def test_parse_frontmatter_reads_scalars_and_nested_progress(self) -> None:
        text = """---
gsd_state_version: 1.0
milestone: m1
milestone_name: reusable low-reasoning Roo harness
status: ready for PR
last_updated: "2026-05-14T00:00:00.000Z"
progress:
  total_phases: 5
  completed_phases: 3
  percent: 60
---

# STATE
"""

        frontmatter = project_dashboard.parse_frontmatter(text)

        self.assertEqual("m1", frontmatter["milestone"])
        self.assertEqual("ready for PR", frontmatter["status"])
        self.assertEqual("5", frontmatter["progress.total_phases"])
        self.assertEqual("3", frontmatter["progress.completed_phases"])
        self.assertEqual("60", frontmatter["progress.percent"])

    def test_parse_roadmap_phases_detects_completed_and_open_items(self) -> None:
        text = """# ROADMAP

## Phases

- [x] **Phase 1: Document-Centered Phase Continuity** - Add planning memory.
- [ ] **Phase 2: Template Consumer Onboarding** - Add bootstrap checklist.
"""

        phases = project_dashboard.parse_roadmap_phases(text)

        self.assertEqual(2, len(phases))
        self.assertEqual("Phase 1: Document-Centered Phase Continuity", phases[0].title)
        self.assertTrue(phases[0].completed)
        self.assertEqual("Add bootstrap checklist.", phases[1].summary)
        self.assertFalse(phases[1].completed)

    def test_load_dashboard_data_reads_fixture_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture_repository(root)

            data = project_dashboard.load_dashboard_data(root)

            self.assertEqual("ready for PR", data.state.status)
            self.assertEqual("done", data.phase_state["phase"])
            self.assertEqual(2, len(data.roadmap_phases))
            self.assertEqual(1, len(data.issues))
            self.assertEqual(4, len(data.documents))
            self.assertEqual("CP-01", data.active_checkpoint)


def write_fixture_repository(root: Path) -> None:
    (root / ".planning/phases/01-first").mkdir(parents=True)
    (root / ".scratch/example/issues").mkdir(parents=True)
    (root / "docs/agents").mkdir(parents=True)
    (root / ".scratch").mkdir(exist_ok=True)

    (root / ".planning/STATE.md").write_text(
        """---
milestone: m1
milestone_name: Example milestone
status: ready for PR
last_updated: "2026-05-14T00:00:00.000Z"
progress:
  total_phases: 2
  completed_phases: 1
  percent: 50
---

# STATE

## Active Checkpoint

- **Checkpoint**: CP-01 - Example checkpoint.
- **Checkpoint file**: `.planning/phases/01-first/01-CHECKPOINTS.md`.

### Blockers

- None active.

## Next Action

Open a PR.
""",
        encoding="utf-8",
    )
    (root / ".planning/ROADMAP.md").write_text(
        """# ROADMAP

## Phases

- [x] **Phase 1: First** - Completed phase.
- [ ] **Phase 2: Second** - Upcoming phase.
""",
        encoding="utf-8",
    )
    (root / ".planning/phases/01-first/01-CHECKPOINTS.md").write_text(
        "# Checkpoints\n\n- [x] CP-01 - Example checkpoint.\n",
        encoding="utf-8",
    )
    (root / ".planning/phases/01-first/01-VERIFICATION.md").write_text(
        "# Verification\n\n```bash\npython3 scripts/harness.py check\n```\n",
        encoding="utf-8",
    )
    (root / ".scratch/phase-state.json").write_text(
        json.dumps(
            {
                "phase": "done",
                "plan_id": "example-01",
                "approved": True,
                "state_path": ".planning/STATE.md",
                "checkpoint_path": ".planning/phases/01-first/01-CHECKPOINTS.md",
                "current_checkpoint": "CP-01",
                "next_action": "Open a PR.",
                "allowed_paths": [".planning/", ".scratch/"],
                "blocked_paths": ["src/"],
                "acceptance_criteria": ["Dashboard fixture loads."],
                "verification": ["python3 scripts/harness.py check"],
            }
        ),
        encoding="utf-8",
    )
    (root / ".scratch/example/issues/01-example.md").write_text(
        "# Example Issue\n\n- Label: ready-for-agent\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("# Example Project\n\nHuman guide.\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("# Agent Instructions\n\nRules.\n", encoding="utf-8")
    (root / "docs/phase-gate-harness.md").write_text("# Phase Gate Harness\n\nDetails.\n", encoding="utf-8")
    (root / "docs/agents/domain.md").write_text("# Domain Docs\n\nDetails.\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m unittest scripts/test_project_dashboard.py
```

Expected: fail with `ModuleNotFoundError: No module named 'project_dashboard'`.

## Task 2: Implement Data Extraction

**Files:**
- Create: `scripts/project_dashboard.py`
- Modify: `scripts/test_project_dashboard.py`

- [ ] **Step 1: Add the minimal parser and loader implementation**

Create `scripts/project_dashboard.py` with this implementation:

```python
#!/usr/bin/env python3
"""Generate a static HTML dashboard from planning and phase-state documents."""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_OUTPUT = Path(".scratch/reports/project-dashboard.html")


@dataclass
class StateSummary:
    milestone: str = "Unknown milestone"
    milestone_name: str = "Unknown milestone"
    status: str = "Unknown status"
    last_updated: str = "Unknown"
    progress_percent: int = 0
    total_phases: int = 0
    completed_phases: int = 0
    active_checkpoint: str = "Unknown checkpoint"
    checkpoint_file: str = ""
    blockers: list[str] = field(default_factory=list)
    next_action: str = "No next action recorded."


@dataclass
class RoadmapPhase:
    title: str
    summary: str
    completed: bool
    raw_line: str


@dataclass
class PhaseDocument:
    phase_dir: str
    files: dict[str, str]
    headings: list[str]


@dataclass
class IssueCard:
    title: str
    path: str
    labels: list[str]


@dataclass
class DocumentLink:
    title: str
    path: str
    category: str


@dataclass
class DashboardData:
    root: Path
    state: StateSummary
    roadmap_phases: list[RoadmapPhase]
    phase_documents: list[PhaseDocument]
    phase_state: dict[str, object]
    issues: list[IssueCard]
    documents: list[DocumentLink]
    warnings: list[str]
    active_checkpoint: str


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    values: dict[str, str] = {}
    parents: list[tuple[int, str]] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, sep, value = line.strip().partition(":")
        if not sep:
            continue
        while parents and parents[-1][0] >= indent:
            parents.pop()
        clean_value = value.strip().strip('"').strip("'")
        full_key = ".".join([item[1] for item in parents] + [key.strip()])
        if clean_value:
            values[full_key] = clean_value
        else:
            parents.append((indent, key.strip()))
    return values


def parse_roadmap_phases(text: str) -> list[RoadmapPhase]:
    phases: list[RoadmapPhase] = []
    pattern = re.compile(r"^- \\[(?P<mark>[ xX])\\] \\*\\*(?P<title>[^*]+)\\*\\*(?: - (?P<summary>.*))?$")
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        phases.append(
            RoadmapPhase(
                title=match.group("title").strip(),
                summary=(match.group("summary") or "").strip(),
                completed=match.group("mark").lower() == "x",
                raw_line=line.strip(),
            )
        )
    return phases


def parse_headings(text: str) -> list[str]:
    headings: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            if title:
                headings.append(title)
    return headings


def first_heading(text: str, fallback: str) -> str:
    headings = parse_headings(text)
    return headings[0] if headings else fallback


def load_dashboard_data(root: Path) -> DashboardData:
    warnings: list[str] = []
    state_path = root / ".planning/STATE.md"
    roadmap_path = root / ".planning/ROADMAP.md"
    phase_state_path = root / ".scratch/phase-state.json"

    state_text = read_optional_text(state_path, warnings)
    roadmap_text = read_optional_text(roadmap_path, warnings)
    phase_state = load_phase_state(phase_state_path)

    state = parse_state_summary(state_text)
    roadmap_phases = parse_roadmap_phases(roadmap_text)
    phase_documents = load_phase_documents(root)
    issues = load_issues(root)
    documents = load_documents(root)

    warnings.extend(check_consistency(root, state, roadmap_phases, phase_documents, phase_state, issues, documents))

    return DashboardData(
        root=root,
        state=state,
        roadmap_phases=roadmap_phases,
        phase_documents=phase_documents,
        phase_state=phase_state,
        issues=issues,
        documents=documents,
        warnings=warnings,
        active_checkpoint=state.active_checkpoint,
    )
```

- [ ] **Step 2: Add the remaining extraction helpers**

Append these helpers to `scripts/project_dashboard.py`:

```python
def read_optional_text(path: Path, warnings: list[str]) -> str:
    if not path.exists():
        warnings.append(f"Missing optional file: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def parse_state_summary(text: str) -> StateSummary:
    frontmatter = parse_frontmatter(text)
    summary = StateSummary(
        milestone=frontmatter.get("milestone", "Unknown milestone"),
        milestone_name=frontmatter.get("milestone_name", "Unknown milestone"),
        status=frontmatter.get("status", "Unknown status"),
        last_updated=frontmatter.get("last_updated", "Unknown"),
        progress_percent=parse_int(frontmatter.get("progress.percent"), 0),
        total_phases=parse_int(frontmatter.get("progress.total_phases"), 0),
        completed_phases=parse_int(frontmatter.get("progress.completed_phases"), 0),
    )

    checkpoint = re.search(r"- \\*\\*Checkpoint\\*\\*: (?P<value>.+)", text)
    checkpoint_file = re.search(r"- \\*\\*Checkpoint file\\*\\*: `(?P<value>[^`]+)`", text)
    if checkpoint:
        summary.active_checkpoint = checkpoint.group("value").strip()
    if checkpoint_file:
        summary.checkpoint_file = checkpoint_file.group("value").strip()

    summary.blockers = parse_section_bullets(text, "Blockers")
    if not summary.blockers:
        summary.blockers = ["No blockers recorded."]

    next_action = parse_section_paragraph(text, "Next Action")
    if next_action:
        summary.next_action = next_action

    return summary


def parse_int(value: str | None, fallback: int) -> int:
    if value is None:
        return fallback
    try:
        return int(value)
    except ValueError:
        return fallback


def parse_section_bullets(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    in_section = False
    bullets: list[str] = []
    for line in lines:
        if line.startswith("#") and heading.lower() in line.lower():
            in_section = True
            continue
        if in_section and line.startswith("#"):
            break
        if in_section and line.strip().startswith("- "):
            bullets.append(line.strip()[2:].strip())
    return bullets


def parse_section_paragraph(text: str, heading: str) -> str:
    lines = text.splitlines()
    in_section = False
    paragraph: list[str] = []
    for line in lines:
        stripped = line.strip()
        if line.startswith("#") and heading.lower() in line.lower():
            in_section = True
            continue
        if in_section and line.startswith("#"):
            break
        if in_section and stripped:
            paragraph.append(stripped)
    return " ".join(paragraph)


def load_phase_state(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_phase_documents(root: Path) -> list[PhaseDocument]:
    phases_root = root / ".planning/phases"
    if not phases_root.exists():
        return []
    documents: list[PhaseDocument] = []
    for phase_dir in sorted(item for item in phases_root.iterdir() if item.is_dir()):
        files: dict[str, str] = {}
        headings: list[str] = []
        for path in sorted(phase_dir.glob("*.md")):
            relative = path.relative_to(root).as_posix()
            files[path.name] = relative
            headings.extend(parse_headings(path.read_text(encoding="utf-8"))[:2])
        documents.append(PhaseDocument(phase_dir=phase_dir.relative_to(root).as_posix(), files=files, headings=headings))
    return documents


def load_issues(root: Path) -> list[IssueCard]:
    issues: list[IssueCard] = []
    scratch = root / ".scratch"
    if not scratch.exists():
        return issues
    for path in sorted(scratch.glob("**/issues/*.md")):
        text = path.read_text(encoding="utf-8")
        labels = [line.split(":", 1)[1].strip() for line in text.splitlines() if line.lower().startswith("- label:")]
        issues.append(IssueCard(title=first_heading(text, path.stem), path=path.relative_to(root).as_posix(), labels=labels))
    return issues


def load_documents(root: Path) -> list[DocumentLink]:
    candidates: list[Path] = []
    for path in (root / "README.md", root / "AGENTS.md"):
        if path.exists():
            candidates.append(path)
    docs_root = root / "docs"
    if docs_root.exists():
        candidates.extend(sorted(docs_root.glob("**/*.md")))
    codebase_root = root / ".planning/codebase"
    if codebase_root.exists():
        candidates.extend(sorted(codebase_root.glob("*.md")))

    documents: list[DocumentLink] = []
    seen: set[str] = set()
    for path in candidates:
        relative = path.relative_to(root).as_posix()
        if relative in seen:
            continue
        seen.add(relative)
        text = path.read_text(encoding="utf-8")
        documents.append(DocumentLink(title=first_heading(text, path.stem), path=relative, category=document_category(relative)))
    return documents


def document_category(relative_path: str) -> str:
    if relative_path in {"README.md", "AGENTS.md"}:
        return "root"
    if relative_path.startswith(".planning/codebase/"):
        return "codebase"
    if relative_path.startswith("docs/agents/"):
        return "agent docs"
    if relative_path.startswith("docs/"):
        return "docs"
    return "other"


def check_consistency(
    root: Path,
    state: StateSummary,
    roadmap_phases: list[RoadmapPhase],
    phase_documents: list[PhaseDocument],
    phase_state: dict[str, object],
    issues: list[IssueCard],
    documents: list[DocumentLink],
) -> list[str]:
    warnings: list[str] = []
    for key in ("state_path", "plan_path", "checkpoint_path"):
        value = phase_state.get(key)
        if isinstance(value, str) and not (root / value).exists():
            warnings.append(f"phase-state references missing {key}: {value}")

    checkpoint = phase_state.get("current_checkpoint")
    if isinstance(checkpoint, str) and checkpoint and checkpoint not in state.active_checkpoint:
        warnings.append(
            f"STATE active checkpoint differs from phase-state current_checkpoint: {state.active_checkpoint} vs {checkpoint}"
        )

    if roadmap_phases and state.total_phases and len(roadmap_phases) != state.total_phases:
        warnings.append(f"STATE progress total_phases={state.total_phases} but ROADMAP lists {len(roadmap_phases)} phases")

    completed_count = sum(1 for phase in roadmap_phases if phase.completed)
    if roadmap_phases and state.completed_phases and completed_count != state.completed_phases:
        warnings.append(
            f"STATE progress completed_phases={state.completed_phases} but ROADMAP marks {completed_count} phases complete"
        )

    roadmap_text = " ".join(phase.title for phase in roadmap_phases)
    for document in phase_documents:
        phase_number = document.phase_dir.split("/", 1)[-1].split("-", 1)[0].lstrip("0")
        if phase_number and f"Phase {phase_number}" not in roadmap_text:
            warnings.append(f"Phase folder is present but not listed in ROADMAP: {document.phase_dir}")

    if issues and not phase_documents:
        warnings.append("Issue files are present but no phase documents were found.")

    document_paths = {document.path for document in documents}
    for required in ("README.md", "AGENTS.md", "docs/phase-gate-harness.md"):
        if required not in document_paths:
            warnings.append(f"Referenced core document is missing from inventory: {required}")

    return warnings
```

- [ ] **Step 3: Run parser tests and verify they pass**

Run:

```bash
python3 -m unittest scripts/test_project_dashboard.py
```

Expected: all 3 tests pass.

## Task 3: Implement HTML Rendering and CLI

**Files:**
- Modify: `scripts/project_dashboard.py`
- Modify: `scripts/test_project_dashboard.py`

- [ ] **Step 1: Add a failing HTML generation test**

Add this method inside `ProjectDashboardTests` in `scripts/test_project_dashboard.py`:

```python
    def test_generate_dashboard_writes_self_contained_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture_repository(root)
            output = root / ".scratch/reports/project-dashboard.html"

            written = project_dashboard.generate_dashboard(root=root, output=output)

            html = written.read_text(encoding="utf-8")
            self.assertEqual(output, written)
            self.assertIn("<!doctype html>", html.lower())
            self.assertIn("Example milestone", html)
            self.assertIn("Phase 1: First", html)
            self.assertIn("Example Issue", html)
            self.assertIn("Phase Gate Harness", html)
            self.assertIn("python3 scripts/harness.py check", html)
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
python3 -m unittest scripts/test_project_dashboard.py
```

Expected: fail with `AttributeError: module 'project_dashboard' has no attribute 'generate_dashboard'`.

- [ ] **Step 3: Add rendering and CLI functions**

Append this code to `scripts/project_dashboard.py`:

```python
def generate_dashboard(*, root: Path, output: Path) -> Path:
    data = load_dashboard_data(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(data), encoding="utf-8")
    for warning in data.warnings:
        print(f"warning: {warning}")
    print(f"wrote {output}")
    return output


def render_html(data: DashboardData) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    phase_state = data.phase_state
    approval = "approved" if phase_state.get("approved") is True else "not approved"
    gate_phase = str(phase_state.get("phase", "unknown"))
    verification = as_string_list(phase_state.get("verification"))
    acceptance = as_string_list(phase_state.get("acceptance_criteria"))
    allowed_paths = as_string_list(phase_state.get("allowed_paths"))
    blocked_paths = as_string_list(phase_state.get("blocked_paths"))

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project Dashboard</title>
  <style>{CSS}</style>
</head>
<body>
  <header class="hero">
    <div>
      <p class="eyebrow">{escape(data.state.milestone)}</p>
      <h1>{escape(data.state.milestone_name)}</h1>
      <p class="status">{escape(data.state.status)}</p>
    </div>
    <div class="progress-card">
      <div class="progress-value">{data.state.progress_percent}%</div>
      <div class="progress-bar"><span style="width:{bounded_percent(data.state.progress_percent)}%"></span></div>
      <p>{data.state.completed_phases}/{data.state.total_phases} phases complete</p>
    </div>
  </header>

  <main class="layout">
    <aside class="rail">
      <section>
        <h2>Current</h2>
        <dl>
          <dt>Checkpoint</dt><dd>{escape(data.state.active_checkpoint)}</dd>
          <dt>Gate</dt><dd><span class="pill">{escape(gate_phase)}</span> <span class="pill">{escape(approval)}</span></dd>
          <dt>Updated</dt><dd>{escape(data.state.last_updated)}</dd>
          <dt>Generated</dt><dd>{escape(generated_at)}</dd>
        </dl>
      </section>
      <section>
        <h2>Next Action</h2>
        <p>{escape(data.state.next_action)}</p>
      </section>
      <section>
        <h2>Blockers</h2>
        {render_list(data.state.blockers)}
      </section>
    </aside>

    <div class="content">
      {render_warnings(data.warnings)}
      <section class="panel">
        <div class="section-heading">
          <h2>Roadmap Board</h2>
          <p>Completed, active, and upcoming work from .planning/ROADMAP.md</p>
        </div>
        <div class="board">{render_phase_cards(data.roadmap_phases)}</div>
      </section>

      <section class="panel">
        <div class="section-heading">
          <h2>Live Gate</h2>
          <p>Allowed paths, blocked paths, acceptance criteria, and verification from .scratch/phase-state.json</p>
        </div>
        <div class="grid-two">
          <div><h3>Acceptance Criteria</h3>{render_list(acceptance)}</div>
          <div><h3>Verification</h3>{render_code_list(verification)}</div>
          <div><h3>Allowed Paths</h3>{render_code_list(allowed_paths)}</div>
          <div><h3>Blocked Paths</h3>{render_code_list(blocked_paths)}</div>
        </div>
      </section>

      <section class="panel">
        <div class="section-heading">
          <h2>Phase Details</h2>
          <p>Available phase documents and headings under .planning/phases/</p>
        </div>
        {render_phase_documents(data.phase_documents)}
      </section>

      <section class="panel">
        <div class="section-heading">
          <h2>Issues</h2>
          <p>Local issue cards under .scratch/**/issues/*.md</p>
        </div>
        <div class="issue-grid">{render_issues(data.issues)}</div>
      </section>

      <section class="panel">
        <div class="section-heading">
          <h2>Documents</h2>
          <p>Inventory from README.md, AGENTS.md, docs/**, and .planning/codebase/**</p>
        </div>
        <div class="issue-grid">{render_documents(data.documents)}</div>
      </section>
    </div>
  </main>
</body>
</html>
"""


CSS = """
:root {
  color-scheme: light;
  --ink: #17202a;
  --muted: #5f6b7a;
  --line: #d8dee8;
  --soft: #f5f7fa;
  --panel: #ffffff;
  --accent: #2563eb;
  --done: #147d3f;
  --warn: #b45309;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--ink);
  background: #eef2f6;
}
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 24px;
  padding: 32px;
  background: #111827;
  color: white;
}
.eyebrow { margin: 0 0 8px; color: #93c5fd; font-weight: 700; text-transform: uppercase; font-size: 12px; }
h1 { margin: 0; font-size: 34px; line-height: 1.1; letter-spacing: 0; }
.status { max-width: 900px; color: #d1d5db; font-size: 16px; }
.progress-card { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.18); padding: 18px; border-radius: 8px; }
.progress-value { font-size: 42px; font-weight: 800; }
.progress-bar { height: 10px; background: rgba(255,255,255,.18); border-radius: 999px; overflow: hidden; }
.progress-bar span { display: block; height: 100%; background: #60a5fa; }
.layout { display: grid; grid-template-columns: 320px minmax(0, 1fr); gap: 20px; padding: 20px; }
.rail, .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; }
.rail { padding: 18px; align-self: start; position: sticky; top: 20px; }
.rail section + section { margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--line); }
h2 { margin: 0 0 12px; font-size: 20px; }
h3 { margin: 0 0 10px; font-size: 15px; }
dt { font-size: 12px; color: var(--muted); font-weight: 700; margin-top: 12px; }
dd { margin: 4px 0 0; }
.pill { display: inline-block; border: 1px solid var(--line); border-radius: 999px; padding: 3px 8px; font-size: 12px; background: var(--soft); margin: 2px 4px 2px 0; }
.content { display: grid; gap: 20px; }
.panel { padding: 20px; }
.section-heading { display: flex; justify-content: space-between; gap: 18px; align-items: start; border-bottom: 1px solid var(--line); padding-bottom: 12px; margin-bottom: 16px; }
.section-heading p { margin: 0; color: var(--muted); font-size: 13px; }
.board { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; }
.phase-card { border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: var(--soft); }
.phase-card.done { border-color: #9bd4ae; background: #effaf3; }
.phase-card.active { border-color: #93c5fd; background: #eff6ff; }
.phase-card h3 { font-size: 16px; }
.phase-card p { color: var(--muted); font-size: 13px; }
.grid-two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
ul { margin: 0; padding-left: 20px; }
li + li { margin-top: 6px; }
code { background: #edf2f7; border: 1px solid #dbe3ec; padding: 2px 5px; border-radius: 4px; font-size: 12px; }
.phase-doc { border-top: 1px solid var(--line); padding: 14px 0; }
.phase-doc:first-of-type { border-top: 0; }
.doc-links { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.doc-links a { color: var(--accent); text-decoration: none; border: 1px solid var(--line); padding: 5px 8px; border-radius: 6px; }
.issue-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
.issue-card { border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: var(--soft); }
.warning { border: 1px solid #f59e0b; background: #fffbeb; color: #78350f; }
@media (max-width: 900px) {
  .hero, .layout, .grid-two { grid-template-columns: 1fr; }
  .rail { position: static; }
}
"""


def render_warnings(warnings: list[str]) -> str:
    if not warnings:
        return ""
    return f'<section class="panel warning"><h2>Warnings</h2>{render_list(warnings)}</section>'


def render_phase_cards(phases: list[RoadmapPhase]) -> str:
    if not phases:
        return '<p class="muted">No roadmap phases found.</p>'
    first_open_seen = False
    cards: list[str] = []
    for phase in phases:
        state = "done" if phase.completed else "active" if not first_open_seen else "upcoming"
        if not phase.completed:
            first_open_seen = True
        cards.append(
            f'<article class="phase-card {state}"><span class="pill">{escape(state)}</span>'
            f"<h3>{escape(phase.title)}</h3><p>{escape(phase.summary)}</p></article>"
        )
    return "".join(cards)


def render_phase_documents(documents: list[PhaseDocument]) -> str:
    if not documents:
        return "<p>No phase documents found.</p>"
    rendered: list[str] = []
    for document in documents:
        links = "".join(f'<a href="../../{escape(path)}">{escape(name)}</a>' for name, path in sorted(document.files.items()))
        headings = render_list(document.headings[:6])
        rendered.append(
            f'<article class="phase-doc"><h3>{escape(document.phase_dir)}</h3>{headings}'
            f'<div class="doc-links">{links}</div></article>'
        )
    return "".join(rendered)


def render_issues(issues: list[IssueCard]) -> str:
    if not issues:
        return "<p>No local issue cards found.</p>"
    cards: list[str] = []
    for issue in issues:
        labels = " ".join(f'<span class="pill">{escape(label)}</span>' for label in issue.labels)
        cards.append(
            f'<article class="issue-card"><h3>{escape(issue.title)}</h3><p><code>{escape(issue.path)}</code></p>{labels}</article>'
        )
    return "".join(cards)


def render_documents(documents: list[DocumentLink]) -> str:
    if not documents:
        return "<p>No documents found.</p>"
    cards: list[str] = []
    for document in documents:
        cards.append(
            f'<article class="issue-card"><h3>{escape(document.title)}</h3>'
            f'<p><code>{escape(document.path)}</code></p><span class="pill">{escape(document.category)}</span></article>'
        )
    return "".join(cards)


def render_list(items: Iterable[str]) -> str:
    values = list(items)
    if not values:
        return "<p>None recorded.</p>"
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in values) + "</ul>"


def render_code_list(items: Iterable[str]) -> str:
    values = list(items)
    if not values:
        return "<p>None recorded.</p>"
    return "<ul>" + "".join(f"<li><code>{escape(item)}</code></li>" for item in values) + "</ul>"


def as_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return []


def bounded_percent(value: int) -> int:
    return max(0, min(100, value))


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root to read.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="HTML file to write.")
    return parser.parse_args(argv)


def run(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    output = args.output
    if not output.is_absolute():
        output = root / output
    generate_dashboard(root=root, output=output)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
```

- [ ] **Step 4: Run dashboard tests and verify they pass**

Run:

```bash
python3 -m unittest scripts/test_project_dashboard.py
```

Expected: all 4 tests pass.

## Task 4: Verify Against the Real Repository

**Files:**
- Runtime output: `.scratch/reports/project-dashboard.html`
- No source edits expected unless verification reveals a specific bug.

- [ ] **Step 1: Compile the script**

Run:

```bash
python3 -m py_compile scripts/project_dashboard.py
```

Expected: exits 0 with no output.

- [ ] **Step 2: Generate the dashboard**

Run:

```bash
python3 scripts/project_dashboard.py
```

Expected: prints `wrote .scratch/reports/project-dashboard.html` or an absolute equivalent. Warnings are acceptable when they report real planning drift, but unexpected tracebacks are not acceptable.

- [ ] **Step 3: Confirm the generated file exists and contains key project state**

Run:

```bash
test -f .scratch/reports/project-dashboard.html
rg -n "reusable low-reasoning Roo harness|Roadmap Board|Live Gate|Phase Details|Issues" .scratch/reports/project-dashboard.html
```

Expected: `test` exits 0 and `rg` prints matching lines.

- [ ] **Step 4: Run the harness check**

Run:

```bash
python3 scripts/harness.py check
```

Expected: exits 0. If it fails because `.scratch/reports/project-dashboard.html` is an untracked changed path under current phase-gate rules, either add `.scratch/reports/` to generated artifact handling or document that reports are local generated output; do not weaken phase-gate checks broadly.

## Task 5: Final Review and Commit

**Files:**
- Add: `scripts/project_dashboard.py`
- Add: `scripts/test_project_dashboard.py`
- Generated local artifact: `.scratch/reports/project-dashboard.html`

- [ ] **Step 1: Review changed files**

Run:

```bash
git status --short
git diff -- scripts/project_dashboard.py scripts/test_project_dashboard.py
```

Expected: only the dashboard script, dashboard tests, and generated report should be new or modified. `.superpowers/` must not appear because it is ignored.

- [ ] **Step 2: Decide whether to commit the generated HTML**

Default: do not commit `.scratch/reports/project-dashboard.html` unless the user explicitly wants checked-in dashboard snapshots. The generator is the durable artifact; the HTML report is reproducible local output.

- [ ] **Step 3: Commit source and tests**

Run:

```bash
git add scripts/project_dashboard.py scripts/test_project_dashboard.py
git commit -m "feat: add project dashboard generator"
```

Expected: commit succeeds.

- [ ] **Step 4: Report verification evidence**

Report these commands and outcomes:

```bash
python3 -m unittest scripts/test_project_dashboard.py
python3 -m py_compile scripts/project_dashboard.py
python3 scripts/project_dashboard.py
test -f .scratch/reports/project-dashboard.html
python3 scripts/harness.py check
```

If any command was skipped or failed, report the exact reason and the remaining risk.

## Self-Review

- Spec coverage: The plan implements the static Python generator, dependency-free runtime, `.planning/`, `.scratch/`, and `docs/` data sources, hybrid layout, warnings, issue cards, document inventory, verification display, and standard-library tests.
- Placeholder scan: No TBD/TODO/fill-in placeholders remain.
- Type consistency: `StateSummary`, `RoadmapPhase`, `PhaseDocument`, `IssueCard`, and `DashboardData` are defined before use; tests call functions included in the implementation tasks.
