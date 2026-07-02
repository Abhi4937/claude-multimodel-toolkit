# How to Operate — multi-model + token-saving cheat-sheet

Durable reference for running day-to-day work across the model terminals.
Readable by any terminal (opus / claude-glm / agy). Full rules: the `token-model-routing` skill.

## Terminal roster (route by risk × size)
| Terminal / tool | Model | Cost | Use for |
|---|---|---|---|
| `opus` (or `claude`) | Opus 4.8 (Pro) | flat | **brain** — architecture, plan mode, risk-critical review, hard bugs |
| `claude-glm` | GLM-5.2 (1M ctx) | $16 flat | coding, refactors, tests, backtester, strategies, boilerplate |
| `agy` | Gemini 3.1 Pro | free (Jio) | research, long-context, whole-repo, video→notes, web |
| `claude-gemini` | Gemini 3.1 Pro (Vertex) | GCP credits (kill-switch) | Gemini as a Claude Code **agent** (LiteLLM proxy :4000; experimental) |
| `gemini` / `/gemini` · `ytnotes --models vertex` | Gemini 3.1 Pro (Vertex) | credits | one-shot Q&A / notes pipeline |
| `nv_batch.py` | deepseek-v4-pro | free (NVIDIA) | mechanical transforms (rename/format/convert) |
| `claude-vertex` | Claude on Vertex | **REAL money — off by default** (GCP credits don't cover Claude) | only if knowingly paying |

Launch the brain terminal as **`opus`** (routes its subagents → Sonnet, sparing the scarce Pro Opus limit).

## Tool / MCP availability per terminal
| Terminal | serena + local MCPs/plugins/skills | claude.ai connectors (Adobe/Gmail/…) | coordinates via |
|---|---|---|---|
| `opus` / `claude` | ✅ full | ✅ | shared config + hub |
| `claude-glm` | ✅ full (same Claude Code) — nudge GLM to actually use them | ❌ (z.ai auth ≠ Anthropic) | shared config + hub |
| `claude-gemini` | ✅ full (Claude Code via proxy) — nudge it to use tools | ❌ (proxy auth ≠ Anthropic) | shared config + hub |
| `agy` | ❌ different tool — no Claude Code MCPs | ❌ | **files only** — the hub + repo |

- `opus` + `claude-glm` share the same `~/.claude` → same serena, LSPs, skills; only Anthropic-account
  connectors are off in glm. Run `/lean` in glm too (MCPs cost tokens there).
- `agy` is kept in loop ONLY via shared files: *"read `C:\dev\_hub\tasks\X.md`"*. See [[statelessness-strategy]].

## What persists across sessions (survives /clear)
- `~/.claude/CLAUDE.md` (auto every session) · `settings.json` · `token-model-routing` skill (on-demand)
- Commands: `/handoff` `/lean` `/token-report`
- Native memory `MEMORY.md` (Opus-only, per-project, auto-loads)
- **This hub `C:\dev\_hub`** (STATE · tasks · knowledge) — shared, read by ANY terminal
- **Ephemeral (lost at /clear):** the conversation, read files, tool output, any undocumented plan.
  → If a decision must outlive the session: write it to native memory (Opus-only) or `knowledge/` (shared).

## Daily workflow
1. Start in **`opus`** for judgment work (plan / architecture / risk review).
2. **`/clear` between unrelated tasks** — one task ≈ one session (keeps context lean & cheap).
3. Delegate execution: **`/handoff <task>`** → writes `tasks/<date>-<slug>.md` + STATE line → run in:
   coding → `claude-glm` · research → `agy` · mechanical → `python C:\dev\_hub\scripts\nv_batch.py`
4. Worker appends `## Result` in the same task note, flips `status: done`.
5. Back in `opus`, read **only that note** → risk-critical review gate.
6. Persist: cross-terminal facts → `knowledge/`; Opus-only notes → native memory.

## Session hygiene
- **Automatic guards:** a PreToolUse hook (`setup/hooks/token_saver_hook.py`) auto-blocks/redirects expensive reads — big files (use offset/limit), PDFs/Office (→ markdown), notebooks/CSV/logs (→ slim), re-reads, and verbose/recursive Bash. Escape hatch: add `raw` to the path, make `<file>.rawread`, or `TOKENSAVER_OFF=1`. See [[token-saver-hooks]].
- **Verbose output eating context?** Read it, then **`/rewind`** that turn to reclaim tokens (cache-friendly). Truncate noisy commands at the source (`| grep … | tail`). `MAX_MCP_OUTPUT_TOKENS` caps MCP output.
- **Before `/compact` or closing:** run **`/log-session`** → saves a structured summary to `C:\dev\_hub\sessions\<project>\` (local, never committed) + appends to `sessions/INDEX.md`.
- **To recall past work:** run **`/recall <topic>`** → greps `sessions/INDEX.md` + logs + knowledge and returns **only matching snippets + paths** (never loads whole logs). This is the cheap "search your history" — like a mini graphify over your notes.

## Token discipline (money + quota)
- `/clear` between tasks · `/rewind` (not `/compact`) to abandon a dead path.
- Don't switch model/effort mid-task (kills prompt cache). Don't idle >5 min near the limit.
- Scope reads (serena find_symbol, offset/limit); never re-read. `permissions.deny` blocks junk/secrets.
- **Batch** small chores into ONE handoff checklist — don't drip.
- Offload verbose/exploratory work to subagents — only the summary returns.
- `/lean` = MCP keep/disable checklist · `/context` + `/usage` when heavy.
- GLM quota: check the **z.ai dashboard** (statusline can't show it). GLM-5.2 burns 3× peak (11:30–15:30 IST), 2× off-peak → do heavy GLM off-peak.

## Graphify (understand-anything) rule
Understanding a repo? Run the **`understand`** skill INSIDE the repo, but in **`claude-glm` or `agy`**
(it fans out many analyzer agents — token-heavy). Cache the graph once; `opus` reads only the summary.
Update incrementally with **`understand-diff`**, never rebuild every session. See [[README]].

## Money safety (GCP)
- Project `gemini-for-claude-code-500917`: idle = ~₹0 (no VMs / no deployed Vertex endpoints).
- Kill-switch deployed: budget `vertex-hard-cap` ₹24,000 (credits excluded) → disables billing on overrun.
- Credits (₹28,710, expire 2026-09-10) cover **Gemini**, NOT Claude. agy already gives Gemini free.
