# Process Rules — How We Work

## Core Principle

Every AI-generated output must be critically evaluated before acceptance.
Sonrisa evaluates the PROCESS, not the code. Visible judgment = good evaluation.

## Mandatory Steps

### After every AI output
1. Run `/validate` — check for hallucinations, non-existent libraries, security issues, architecture drift
2. Document what was accepted, what was rejected, and WHY in `docs/decision-log.md`
3. At least 2–3 rejections must be documented across the full task

### For every design decision
- Use `/decide "question"` to log options considered and rationale
- Format: date + question + options + chosen + reason

### For every major implementation step
- Use `/implement [component]` — it auto-validates and logs the prompt
- Prompt text must be saved to `docs/prompt-history.md`

### For every milestone
- Use `/milestone "name"` — creates git commit + updates progress log
- Commit messages must be meaningful (not "add files", "update code")

## What Goes Into prompt-history.md

NOT a raw chat dump. Structured entries only:

```
## YYYY-MM-DD HH:MM — [component name]

**Prompt given:** "..."

**What I received:** [brief description]

**What I rejected:** [what and why]

**What I accepted:** [final output]

**Corrections made:** [list]
```

## Language Rule

- All code, comments, technical docs: English
- Communication with the user: Hungarian
- prompt-history.md entries: English (they are submitted to Sonrisa)
- decision-log.md entries: English (submitted to Sonrisa)
- Internal helper files (not committed): Hungarian is fine
