Implement the component named in $ARGUMENTS.

Before writing any code:
1. Read docs/architecture.md to understand where this component fits
2. Read .claude/rules/tech-stack.md for the chosen libraries
3. Read .claude/rules/process.md for process rules

Implementation steps:
1. Write the implementation code in src/ following the architecture
2. Write unit tests in tests/ using pytest
3. Ensure the code follows the abstract base class pattern where applicable (NotificationChannel)
4. All code and comments in English

After writing code, immediately run /validate on the output.

Then append to docs/prompt-history.md:
```
## [DATE] [TIME] — implement: $ARGUMENTS

**Prompt given:** [the exact prompt used]
**What I received:** [brief description of generated output]
**What I rejected:** [list anything rejected and why]
**What I accepted:** [final output description]
**Corrections made:** [list]
```

Finally, summarize in Hungarian what was implemented and whether any decisions were made that should be logged with /decide.
