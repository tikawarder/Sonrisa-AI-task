Create a git milestone commit for: $ARGUMENTS

Steps:
1. Run `git status` to see what changed
2. Summarize what was implemented in this milestone (in English)
3. Stage the relevant files (be explicit — no `git add .` without listing what's included)
4. Create a commit with a structured message:

```
feat: [milestone name in imperative mood]

- [bullet: what was implemented]
- [bullet: key decisions made]
- [bullet: what was rejected and why, if applicable]

Process: [one sentence on how AI was directed for this milestone]
```

5. Append to docs/progress.md:
```
## [DATE] — Milestone: $ARGUMENTS
**Completed:** [list]
**Decisions:** [link to decision-log entries]
**Next:** [what comes next]
```

6. Summarize in Hungarian: what was committed, what the next milestone should be.

IMPORTANT: Do NOT use `git add .` — explicitly list each file being staged and confirm with me before committing.
