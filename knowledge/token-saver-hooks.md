# Token-Saver Hooks

A single fail-open **PreToolUse** hook (`setup/hooks/token_saver_hook.py`, matcher `Read|Bash`)
that stops expensive input from ever entering context. Registered in `~/.claude/settings.json`.

## The 8 guards
| # | Trigger | Action |
|---|---|---|
| 1 | Read `.pdf/.docx/.pptx/.xlsx/.html/.epub` | convert once via **markitdown** → `<file>.md`, deny raw + point to the `.md` |
| 2 | Read a text file > 1500 lines with **no** offset/limit | deny → "scope with offset/limit or Grep/serena" |
| 3 | Read `.ipynb` | strip cell **outputs** → `<file>.slim.md`, read that |
| 3 | Read big `.csv` | header + schema + first 30 rows → `<file>.head.md` |
| 4 | Read `.log` | error lines + last 200 lines → `<file>.tail.txt` |
| 5 | Read same file twice in a session (unchanged, un-scoped) | deny → "already in context" |
| 6 | Bash `pytest/npm/build/pip/docker/...` without a limiting pipe | deny → "re-run piped `| tail`/`| grep`" |
| 7 | Bash `ls -R` / `dir /s` / `tree` / recursive `find` | deny → "scope it / use Glob" |
| 8 | Read `.html` | folded into #1 (markitdown) |

Images (`.png/.jpg/...`) are **allowed as vision by default** (fidelity) — convert manually if you want.

## Escape hatches (when you WANT the raw/full read)
- Put **`raw`** in the filename, OR create a sibling **`<file>.rawread`**, then re-read.
- Use **offset/limit** on the original (counts as scoped → allowed).
- Disable ALL guards for a session: set env **`TOKENSAVER_OFF=1`**.

## Design guarantees
- **Fail-open:** any error (bad input, markitdown missing) → the tool is ALLOWED. It can never wedge a session.
- **Cache:** conversions (`.md/.slim.md/.head.md/.tail.txt`) are reused until the source changes.
- **Only PreToolUse** — it prevents spend up front (PostToolUse can't reliably shrink already-captured output).

## Dependency
`pip install "markitdown[all]"` (for #1/#8). Everything else is stdlib. Path in settings.json:
`python "C:/dev/_hub/setup/hooks/token_saver_hook.py"`.

## Tuning
Edit the constants at the top of the hook: `BIG_FILE_LINES` (1500), `CSV_PREVIEW_ROWS` (30), `LOG_TAIL_LINES` (200),
or the `MEDIA_EXT` / noisy-command regex.

## Note on visual content
For diagrams/charts/screenshots where layout matters, use the escape hatch so Claude reads the
**original image/PDF via vision** — markdown extraction loses the visual. See [[statelessness-strategy]].
