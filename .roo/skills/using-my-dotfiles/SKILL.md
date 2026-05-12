---
name: using-my-dotfiles
description: Meta-skill that guides Codex to use available external skills (Superpowers, OMC, Codex) based on context
type: workflow
---

# Using My Dotfiles Environment

This skill guides Codex to work effectively in your customized environment.

## Core Philosophy

This environment uses **external proven tools** rather than custom implementations:
- **Superpowers**: brainstorming, TDD, debugging, code review
- **OMC** (oh-my-Codex): multi-agent orchestration, team workflows
- **Codex**: platform-specific agent systems

When external tools are unavailable, this skill provides fallback guidance.

---

## Task Type Detection

Before starting any task, identify the task type:

| Task Type | Primary Tool | Fallback |
|-----------|-------------|----------|
| **New feature/creative work** | `superpowers:brainstorming` | 3-approach comparison |
| **Bug fix/unexpected behavior** | `superpowers:systematic-debugging` | Standard debugging steps |
| **Test-driven development** | `superpowers:test-driven-development` | Basic test-first prompts |
| **Code review needed** | `superpowers:receiving-code-review` | Checklist-based review |
| **Following a written plan** | `superpowers:executing-plans` | Manual step-by-step |
| **Multiple independent tasks** | `omc:dispatching-parallel-agents` | Sequential execution |
| **Complex multi-agent work** | `omc:team` | Manual coordination |

---

## Workflow Guidance

### 1. Start of Session

```
1. Read project AGENTS.md
2. Identify task type (use table above)
3. Check for available external skills
4. Invoke appropriate skill or use fallback
```

### 2. During Implementation

- **If stuck**: invoke `superpowers:brainstorming` to explore approaches
- **If tests fail**: invoke `superpowers:systematic-debugging`
- **If reviewing**: invoke `superpowers:receiving-code-review`
- **If planning**: invoke `superpowers:executing-plans`

### 3. Multi-Agent Collaboration

When multiple agents need to work together:

**If external tools available:**
1. Use `superpowers:executing-plans` for structured workflows
2. Use `omc:dispatching-parallel-agents` for independent tasks
3. Use `omc:team` for coordinated agent work

**If no external tools:**
1. **Planner**: Propose 2-3 approaches with trade-offs
2. **Reviewer**: Critique each approach, identify risks
3. **Human**: Choose or refine approach
4. **Executor**: Implement chosen approach step-by-step

---

## Environment Integration

This skill integrates with:

- **Project onboarding**: `onboard-project` skill detects project type
- **Documentation**: `setup-docs-structure` skill ensures Diátaxis pattern
- **Safety**: Hook bundle (block-destructive, tdd-gate, etc.)

---

## Customization

To customize this for your environment:

1. Add your preferred tools to the task type table
2. Modify fallback patterns to match your workflow
3. Add project-specific routing logic
4. Update this file as you discover what works

---

## Key Principle

> "Don't rebuild what exists. Route to proven tools, provide simple fallbacks."

This meta-skill doesn't implement workflows itself—it guides Codex to use the best available tool for each situation.
