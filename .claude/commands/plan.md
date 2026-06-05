Read the file at task-04-feature-design-and-build.docx (use python-docx or extract XML) and also read .claude/rules/project-context.md.

Then produce TWO documents:

**1. docs/brief-interpretation.md** — Scope definition document:
- Original brief (verbatim)
- List every ambiguity in the brief
- For each ambiguity: state the chosen interpretation and WHY (justify it)
- Define what "important event" means in this system (concrete, measurable definition)
- Define what "flexible" means (concrete pattern chosen)
- In-scope vs out-of-scope table
- Write in English, structured markdown

**2. docs/architecture.md** — Technical architecture document:
- System overview: what components exist and how they connect
- Data flow: event detection → alert matching → notification dispatch
- Component responsibilities (one paragraph each)
- Database schema overview (table names and key relationships)
- API endpoints overview (grouped by resource)
- Extensibility points (where future channels plug in)
- Tech stack table with rationale (reference .claude/rules/tech-stack.md)
- Write in English, structured markdown

After writing both files, summarize in Hungarian what decisions were made and flag anything that needs my confirmation before implementation starts.

Log this planning session as the first entry in docs/prompt-history.md using the format defined in .claude/rules/process.md.
