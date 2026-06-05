Critically review the most recently generated code or document output.

Check for ALL of the following — do not skip any:

**Hallucinations & library issues:**
- [ ] Are all imported libraries real and available on PyPI?
- [ ] Do all referenced API endpoints/methods actually exist in the libraries used?
- [ ] Are version constraints realistic (not future versions)?

**Security issues:**
- [ ] SQL injection risks (raw queries without parameterization)
- [ ] Hardcoded credentials or API keys
- [ ] Missing authentication on endpoints that need it
- [ ] Unvalidated user input passed to shell or file system

**Architecture alignment:**
- [ ] Does the code match the design in docs/architecture.md?
- [ ] Is the NotificationChannel abstract base class used correctly?
- [ ] Are database models consistent with the schema in docs/architecture.md?

**Code quality:**
- [ ] Are there obvious logic errors or off-by-one bugs?
- [ ] Does the code handle errors or just let exceptions propagate silently?
- [ ] Are tests actually testing the right things, or are they trivial?

**Output format:**
List every problem found with:
- Severity: BLOCKING / WARNING / MINOR
- Location: file + line or section
- Issue description
- Suggested fix

Then append to docs/decision-log.md what was rejected and why:
```
## [DATE] — Validation: [component]
**Rejected:** [what and why]
**Accepted:** [what passed]
**Corrections applied:** [list]
```

Summarize findings in Hungarian.
