---
description: Write a structured session log to C:\dev\_hub\sessions\<project>\ (local, never committed)
argument-hint: [optional session title]
---

Write a durable log of THIS conversation so it survives /compact and /clear. Run this
BEFORE compacting or closing a session.

Steps:
1. Project = basename of the current working directory (or use $ARGUMENTS if it names one). Slugify it.
2. Path = `C:\dev\_hub\sessions\<project>\<YYYY-MM-DD>-<short-slug>.md` (create folders as needed).
   Use today's date. If a file with that name exists, append `-2`, `-3`, etc.
3. Write this structure, factual and scannable (aim for ~1 screen — summary, not transcript):
   ```
   # Session — <title>   (<date>)
   - Project / cwd: <path>
   - Terminals used: <opus / claude-glm / agy / nv / gcloud>
   - Models used: <Opus 4.8 / GLM-5.2 / deepseek-v4-pro / ...>

   ## What we discussed
   ## What we built / solved
   ## Files changed / created          (exact paths touched — for review/rollback)
   ## Decisions & why                  (each key choice + the reason, so it's not re-litigated)
   ## Issues found & how we fixed them
   ## Reproduce / redo steps           (exact commands + env vars set — to rebuild later)
   ## Verified vs pending              (what was actually tested vs assumed)
   ## Tools / skills / MCPs used
   ## Studies / research done          (include source links)
   ## Related links · cost             (plan file, prior/next log, commits/PR; rough token/$ spend)
   ## Open / next steps
   ```
4. Keep it tight — bullet points, not transcripts. Confirm the path written.
5. **Append a one-line entry to `C:\dev\_hub\sessions\INDEX.md`** so retrieval stays cheap:
   `- <YYYY-MM-DD> · <project> · <title> — tags: <comma keywords> → <relative path>`
   Pick 6–12 specific tags (feature/tool/error names) — these are what `/recall` greps on.

IMPORTANT: `C:\dev\_hub` is a local, non-git folder — these logs are NEVER pushed to GitHub.
Never write session logs inside a project repo (they'd get committed).
