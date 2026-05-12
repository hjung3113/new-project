# using-my-dotfiles — Meta-Skill

**Type**: Workflow | **Purpose**: Route Claude to appropriate external tools based on task type

## What It Does

Guides Claude Code to use the best available tool for each task:
- **Superpowers**: brainstorming, TDD, debugging, code review
- **OMC** (oh-my-claudecode): multi-agent orchestration, team workflows
- **Codex**: platform-specific agent systems

When external tools aren't available, provides simple fallback patterns.

## When to Use

**Automatic**: This skill activates at session start to establish task routing.

**Manual**: Re-invoke if workflow needs to change mid-session.

## Task Type Routing

| Task Type | Primary Tool | Fallback |
|-----------|-------------|----------|
| New feature/creative | `superpowers:brainstorming` | 3-approach comparison |
| Bug fix/unexpected | `superpowers:systematic-debugging` | Standard debugging |
| Test-driven dev | `superpowers:test-driven-development` | Basic test-first |
| Code review | `superpowers:receiving-code-review` | Checklist-based |
| Following plan | `superpowers:executing-plans` | Manual step-by-step |
| Multiple independent | `omc:dispatching-parallel-agents` | Sequential |
| Multi-agent work | `omc:team` | Manual coordination |

## Integration

Works with:
- `onboard-project`: Detects project type for routing
- `setup-docs-structure`: Ensures Diátaxis-compliant docs
- Hook bundle: Safety, quality gates, session continuity

## Customization

Edit `SKILL.md` to:
1. Add your preferred tools to routing table
2. Modify fallback patterns
3. Add project-specific routing logic
4. Update based on what works in your workflow

## Key Principle

> "Don't rebuild what exists. Route to proven tools, provide simple fallbacks."

This meta-sill doesn't implement workflows—it guides Claude to use the best available tool.
