#!/usr/bin/env python3
"""Install, upgrade, and validate the reusable Roo harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


HARNESS_VERSION = "0.3.0"
MANIFEST_PATH = Path("harness/manifest.json")
CLEAN_SKELETON = Path("harness/skeleton/clean")
INSTALL_STATE = Path(".harness/installed-manifest.json")
CONTAMINATION_PATTERNS = (
    re.compile(r"\bPR\s*#\d+\b", re.IGNORECASE),
    re.compile(r"\bDB context snapshot\b", re.IGNORECASE),
    re.compile(r"\bhjung3113/new-project\b", re.IGNORECASE),
    re.compile(r"\bPhase\s+[0-9]+.*(?:implemented|complete|완료)", re.IGNORECASE),
    re.compile(r"\bunder PR review\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class ManifestEntry:
    path: PurePosixPath
    source: PurePosixPath
    policy: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Install the clean harness skeleton into a target project.")
    init_parser.add_argument("--target", required=True, type=Path)
    init_parser.add_argument("--dry-run", action="store_true")

    upgrade_parser = subparsers.add_parser("upgrade", help="Update harness-owned files in a target project.")
    upgrade_parser.add_argument("--target", required=True, type=Path)
    upgrade_parser.add_argument("--dry-run", action="store_true")
    upgrade_parser.add_argument("--force", action="store_true", help="Overwrite locally modified harness-owned files.")

    check_parser = subparsers.add_parser("check", help="Validate harness structure and policy.")
    check_parser.add_argument("--target", type=Path, default=None)
    check_parser.add_argument("--base", default=None, help="Optional git base ref for changed-path checks.")
    check_parser.add_argument("--worktree", action="store_true", help="Check staged and unstaged paths against allowed_paths.")

    args = parser.parse_args(argv)
    root = repo_root()

    if args.command == "init":
        install(root=root, target=args.target, dry_run=args.dry_run)
        return 0
    if args.command == "upgrade":
        return upgrade(root=root, target=args.target, dry_run=args.dry_run, force=args.force)
    if args.command == "check":
        check(root=root, target=args.target, base=args.base, worktree=args.worktree)
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


def install(*, root: Path, target: Path, dry_run: bool = False) -> None:
    entries = load_manifest(root)
    target = target.resolve()
    destinations = [
        (entry, source_path(root, entry), destination_path(target, entry))
        for entry in entries
        if entry.policy != "exclude"
    ]
    existing = [str(entry.path) for entry, _, destination in destinations if destination.exists() or destination.is_symlink()]
    if existing:
        raise SystemExit("Refusing to overwrite existing files during init: " + ", ".join(existing))

    if dry_run:
        return

    target.mkdir(parents=True, exist_ok=True)
    for _, source, destination in destinations:
        if not dry_run:
            write_copy(source, destination)

    write_install_state(root=root, target=target, entries=entries)


def upgrade(*, root: Path, target: Path, dry_run: bool = False, force: bool = False) -> int:
    if not (root / MANIFEST_PATH).exists():
        raise SystemExit("Upgrade must be run from a harness source tree with harness/manifest.json.")
    entries = load_manifest(root)
    target = target.resolve()
    installed = read_install_state(target)
    installed_paths = installed.get("files", {})
    existing_manifest_paths = [
        entry for entry in entries if (target / entry.path).exists() or (target / entry.path).is_symlink()
    ]
    if installed.get("version") is None and not existing_manifest_paths:
        raise SystemExit("Target is not initialized. Run init before upgrade.")
    conflicts = 0

    for entry in entries:
        if entry.policy not in {"harness-owned", "managed"}:
            continue

        source = source_path(root, entry)
        destination = destination_path(target, entry)
        new_hash = file_hash(source)

        if destination.exists() and not force:
            old_hash = installed_paths.get(str(entry.path), {}).get("sha256")
            current_hash = file_hash(destination)
            if not old_hash or current_hash != old_hash:
                conflicts += 1
                conflict_path = target / ".harness/conflicts" / f"{entry.path}.new"
                if not dry_run:
                    write_copy(source, conflict_path)
                continue

        if not dry_run:
            write_copy(source, destination)
            installed.setdefault("files", {})[str(entry.path)] = {
                "policy": entry.policy,
                "sha256": new_hash,
            }

    installed["version"] = HARNESS_VERSION
    if not dry_run:
        write_json(target / INSTALL_STATE, installed)
    return 1 if conflicts else 0


def check(*, root: Path, target: Path | None = None, base: str | None = None, worktree: bool = False) -> None:
    root = root.resolve()
    if not (root / MANIFEST_PATH).exists():
        check_installed_target(root)
        if base:
            check_changed_paths(root, base)
        if worktree:
            check_worktree_paths(root)
        return

    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    if manifest.get("version") != HARNESS_VERSION:
        raise SystemExit(f"Manifest version mismatch: expected {HARNESS_VERSION}")

    entries = load_manifest(root)
    missing = [str(entry.source) for entry in entries if entry.policy != "exclude" and not source_path(root, entry).exists()]
    if missing:
        raise SystemExit(f"Manifest sources missing: {', '.join(missing)}")

    check_clean_skeleton(root)
    check_json(root / ".roomodes")
    check_json(root / ".scratch/phase-state.schema.json")
    check_json(root / ".scratch/phase-state.example.json")
    check_json(root / ".scratch/phase-state.json")
    check_command_modes(root)
    check_phase_state_paths(root)
    check_phase_reference_drift(root)

    check_target = (target or root).resolve()
    if target:
        check_installed_target(check_target)
    if base:
        check_changed_paths(check_target, base)
    if worktree:
        check_worktree_paths(check_target)


def load_manifest(root: Path) -> list[ManifestEntry]:
    data = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    entries = []
    for item in data.get("files", []):
        entries.append(
            ManifestEntry(
                path=PurePosixPath(item["path"]),
                source=PurePosixPath(item["source"]),
                policy=item["policy"],
            )
        )
    return entries


def source_path(root: Path, entry: ManifestEntry) -> Path:
    if entry.source.is_absolute():
        raise SystemExit(f"Absolute manifest sources are not allowed: {entry.source}")
    path = (root / entry.source).resolve()
    if not is_relative_to(path, root.resolve()):
        raise SystemExit(f"Manifest source escapes repository: {entry.source}")
    return path


def destination_path(target: Path, entry: ManifestEntry) -> Path:
    if entry.path.is_absolute():
        raise SystemExit(f"Manifest destination escapes target: {entry.path}")
    parts = entry.path.parts
    if not parts or any(part in {"", ".", ".."} for part in parts) or re.match(r"^[A-Za-z]:", parts[0]):
        raise SystemExit(f"Manifest destination escapes target: {entry.path}")
    destination = (target / Path(*parts)).resolve(strict=False)
    if not is_relative_to(destination, target.resolve(strict=False)):
        raise SystemExit(f"Manifest destination escapes target: {entry.path}")
    return destination


def write_copy(source: Path, destination: Path) -> None:
    assert_safe_write_destination(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def assert_safe_write_destination(destination: Path) -> None:
    for candidate in (destination, *destination.parents):
        if candidate.is_symlink():
            raise SystemExit(f"Refusing to write through symlink: {candidate}")
        if candidate == candidate.parent:
            break


def write_install_state(*, root: Path, target: Path, entries: Iterable[ManifestEntry]) -> None:
    files = {}
    for entry in entries:
        if entry.policy == "exclude":
            continue
        destination = target / entry.path
        files[str(entry.path)] = {
            "policy": entry.policy,
            "sha256": file_hash(destination),
        }
    write_json(
        target / INSTALL_STATE,
        {
            "version": HARNESS_VERSION,
            "source": str(root),
            "files": files,
        },
    )


def read_install_state(target: Path) -> dict[str, object]:
    path = target / INSTALL_STATE
    if not path.exists():
        return {"version": None, "files": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def check_installed_target(target: Path) -> None:
    installed_path = target / INSTALL_STATE
    if not installed_path.exists():
        raise SystemExit(f"Target is missing {INSTALL_STATE}")
    installed = json.loads(installed_path.read_text(encoding="utf-8"))
    if installed.get("version") is None:
        raise SystemExit("Target install state is missing version.")
    missing = []
    for path_text in installed.get("files", {}):
        destination = target / normalize_path(path_text)
        if not destination.exists():
            missing.append(path_text)
    if missing:
        raise SystemExit("Installed target is missing files: " + ", ".join(missing))
    for relative in (
        ".roomodes",
        ".scratch/phase-state.schema.json",
        ".scratch/phase-state.example.json",
        ".scratch/phase-state.json",
    ):
        path = target / relative
        if path.exists():
            check_json(path)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_clean_skeleton(root: Path) -> None:
    skeleton = root / CLEAN_SKELETON
    if not skeleton.exists():
        raise SystemExit(f"Missing clean skeleton: {CLEAN_SKELETON}")
    offenders: list[str] = []
    for path in skeleton.rglob("*"):
        if path.is_file() and is_text_file(path):
            text = path.read_text(encoding="utf-8")
            if any(pattern.search(text) for pattern in CONTAMINATION_PATTERNS):
                offenders.append(str(path.relative_to(root)))
    if offenders:
        raise SystemExit("Clean skeleton contamination detected: " + ", ".join(offenders))


def check_json(path: Path) -> None:
    json.loads(path.read_text(encoding="utf-8"))


def check_command_modes(root: Path) -> None:
    modes = json.loads((root / ".roomodes").read_text(encoding="utf-8"))
    known = {mode["slug"] for mode in modes.get("customModes", [])}
    unknown: list[str] = []
    for command in (root / ".roo/commands").glob("*.md"):
        text = command.read_text(encoding="utf-8")
        match = re.search(r"^mode:\s*([A-Za-z0-9_-]+)\s*$", text, re.MULTILINE)
        if match and match.group(1) not in known:
            unknown.append(f"{command.relative_to(root)} -> {match.group(1)}")
    if unknown:
        raise SystemExit("Commands reference unknown Roo modes: " + ", ".join(unknown))


def check_phase_reference_drift(root: Path) -> None:
    stale = (
        "Phase 2 should add mechanical",
        "Future mechanical enforcement belongs to Phase 2",
        "Phase 3 for consumer onboarding",
        "Phase 4 is reserved for an example ETL slice",
    )
    offenders = []
    for path in (root / ".planning").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for phrase in stale:
            if phrase in text:
                offenders.append(f"{path.relative_to(root)}: {phrase}")
    if offenders:
        raise SystemExit("Stale phase reference detected: " + "; ".join(offenders))


def check_phase_state_paths(root: Path) -> None:
    state_path = root / ".scratch/phase-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    missing = []
    for key in ("state_path", "plan_path", "checkpoint_path"):
        value = state.get(key)
        if isinstance(value, str) and value and not (root / normalize_path(value)).exists():
            missing.append(f"{key}={value}")
    if missing:
        raise SystemExit("Phase-state paths are missing: " + ", ".join(missing))


def check_changed_paths(target: Path, base: str) -> None:
    state_path = target / ".scratch/phase-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("phase") not in {"execute", "done"} or state.get("approved") is not True:
        raise SystemExit("Changed-path check requires phase=execute or phase=done with approved=true")
    changed = git_changed_paths(target, base)
    denied = [
        path
        for path in changed
        if not path_allowed(path, state.get("allowed_paths", []), state.get("blocked_paths", []))
    ]
    if denied:
        raise SystemExit("Changed paths outside allowed_paths: " + ", ".join(denied))


def check_worktree_paths(target: Path) -> None:
    state = json.loads((target / ".scratch/phase-state.json").read_text(encoding="utf-8"))
    if state.get("phase") not in {"execute", "done"} or state.get("approved") is not True:
        raise SystemExit("Worktree changed-path check requires phase=execute or phase=done with approved=true")
    changed = sorted(set(git_worktree_paths(target)))
    denied = [
        path
        for path in changed
        if not path_allowed(path, state.get("allowed_paths", []), state.get("blocked_paths", []))
    ]
    if denied:
        raise SystemExit("Worktree paths outside allowed_paths: " + ", ".join(denied))


def git_changed_paths(target: Path, base: str) -> list[str]:
    output = subprocess.check_output(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=target,
        text=True,
    )
    return [line.strip() for line in output.splitlines() if line.strip()]


def git_worktree_paths(target: Path) -> list[str]:
    outputs = [
        subprocess.check_output(["git", "diff", "--name-only"], cwd=target, text=True),
        subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=target, text=True),
        subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=target, text=True),
    ]
    return [line.strip() for output in outputs for line in output.splitlines() if line.strip()]


def path_allowed(path: str, allowed: Iterable[str], blocked: Iterable[str]) -> bool:
    normalized = normalize_path(path)
    if matches_any(normalized, blocked):
        return False
    return matches_any(normalized, allowed)


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    for pattern in patterns:
        normalized = normalize_path(pattern)
        if normalized.endswith("/"):
            if path.startswith(normalized):
                return True
        elif path == normalized:
            return True
    return False


def normalize_path(path: str) -> str:
    normalized = os.path.normpath(path).replace(os.sep, "/")
    if normalized == "." or normalized.startswith("../") or normalized == "..":
        raise ValueError(f"Unsafe relative path: {path}")
    if path.endswith("/") and not normalized.endswith("/"):
        normalized += "/"
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def is_text_file(path: Path) -> bool:
    return path.suffix in {".md", ".json", ".txt", ".yml", ".yaml", ".toml", ".sh", ".py"} or path.name in {
        "AGENTS.md",
        ".roomodes",
        ".gitignore",
    }


if __name__ == "__main__":
    raise SystemExit(run())
