---
description: Scaffold a handoff task note in C:\dev\_hub and route it to a worker terminal
argument-hint: [task description]
---

Create a handoff for: $ARGUMENTS

Steps:
1. Decide the target worker by risk × size (see the `token-model-routing` skill):
   - mechanical/rename/format → `nv` (nv_batch.py)
   - coding/refactor/tests/backtester/strategies → `claude-glm`
   - Gemini-agent coding/reasoning (alternative to GLM) → `claude-gemini`
   - research/long-context/video/web → `agy`
   Never route risk-critical logic away from Opus.
2. Write `C:\dev\_hub\tasks\<today>-<slug>.md` using `C:\dev\_hub\tasks\_TEMPLATE.md`:
   fill frontmatter (`from: opus`, `to: <worker>`, `status: todo`, `created: <today>`)
   and the `## Task`, `## Context files` (exact paths), `## Change` (precise), `## Test` sections.
3. Append one line to `C:\dev\_hub\STATE.md`: `- [todo] tasks/<file> → <worker> — <desc>`.
4. Tell me the exact command to run, e.g.:
   - `claude-glm`     then: "read C:\dev\_hub\tasks\<file> and do it"
   - `claude-gemini`  then: "read C:\dev\_hub\tasks\<file> and do it"
   - `agy`            then: "read C:\dev\_hub\tasks\<file> and do it"
   - `python C:\dev\_hub\scripts\nv_batch.py --from-task C:\dev\_hub\tasks\<file> <files>`

Keep the note tight and specific. Do not start doing the work yourself.
