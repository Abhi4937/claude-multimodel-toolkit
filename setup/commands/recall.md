---
description: Retrieve relevant snippets from hub logs + knowledge WITHOUT reading whole files
argument-hint: <topic or keywords>
allowed-tools: Grep, Read
---

Find prior work / decisions on: **$ARGUMENTS**

Do this token-efficiently — DO NOT read whole files:
1. First read `C:\dev\_hub\sessions\INDEX.md` (small) and scan for matching tags/titles.
2. **Grep** (case-insensitive, with a few lines of context) across:
   - `C:\dev\_hub\sessions\` (session logs)
   - `C:\dev\_hub\knowledge\` (durable facts)
   Use the query terms + obvious synonyms.
3. Return ONLY:
   - the matching **file path(s)**, and
   - the relevant **snippet lines** (with minimal context).
4. If one log is clearly the right one and the user needs more, read just that **section**
   (use offset/limit around the grep hit) — never the whole file.

Report concisely as: `Found in <path>: <snippet>`. If nothing matches, say so and suggest broader terms.
Never dump entire logs into context.
