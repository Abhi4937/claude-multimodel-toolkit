---
name: token-model-routing
description: Use when deciding how to save tokens or which model/terminal to route a task to — cache discipline, /clear vs /rewind vs /compact, MCP management, subagent offloading, the HANDOFF/Obsidian-hub protocol, the claude/claude-glm/claude-vertex/agy/nv routing table, and the understand-anything (graphify) rule. Also when a session feels heavy or the user asks about token cost.
---

# Token & Model Routing

Source of truth for this machine's multi-model setup. Detailed reference in
`C:\dev\trading_concepts\MODEL_STRATEGY.md`. Plan: `~/.claude/plans/`.

## The one rule
**Route by risk × size.** Claude **Pro** = Opus is *scarce* (tight 5-hr limits) →
Opus only touches high-risk / high-judgment work; everything else offloads.

## Terminal roster
| Terminal / tool | Model | Use for |
|---|---|---|
| `opus` (or `claude`) | Opus 4.8 (Pro) | architecture, plan mode, **risk-critical review (mandatory gate)**, hard bugs |
| `claude-glm` | GLM-5.2 (Z.ai, `ZAI_KEY`) | coding, refactors, tests, backtester, strategies, boilerplate |
| `claude-vertex` | Claude on Vertex | **DISABLED by default — REAL card money** (GCP credits do NOT cover Marketplace/Claude). Use only if knowingly paying. Kill-switch caps at ₹24k. |
| `agy` | Gemini 3.1 Pro (Antigravity, free) | research, long-context, whole-repo, video→notes, web research — the Gemini path |
| `nv_batch.py` | NVIDIA free (deepseek-v4-pro / qwen-coder) | tier-0 mechanical transforms (rename/format/convert) |

Each terminal = one fixed backend (`ANTHROPIC_BASE_URL` is process-level; no mixing in one chat).
Subagent routing is per-terminal via the wrappers — never in global settings.json.

## Work distribution (risk × size)
- **Trivial mechanical** (rename, format, typo, config) → `nv_batch.py` (free) or Haiku subagent.
- **Boilerplate/scaffold** → nv → GLM.
- **Standard coding** (features, refactors, tests, backtester, strategies) → `claude-glm`.
- **Research / read-heavy** (docs, 1M-token, video→notes, web) → `agy`.
- **Codebase understanding / graph build** → `agy` or `claude-glm` once, cache output.
- **Architecture / planning / risk-critical / hard bugs** → `opus` (this terminal). Never delegate risk-critical.
- **Opus limit hit** → wait for Pro reset, or drop to `claude-glm` / `agy`. (`claude-vertex` is REAL money — credits don't cover Claude — so it's off by default.)

**Small work:** batch chores into ONE handoff checklist (don't drip); use in-plan
subagents for search/read; use nv for zero-judgment transforms. Opus does a small task
inline only when that's faster than writing a handoff.

## Handoff via the Obsidian hub `C:\dev\_hub`
Shared markdown bus all terminals read by **exact path** (Obsidian = human viewer only).
```
C:\dev\_hub\  STATE.md  tasks\  knowledge\  scripts\
```
Lifecycle: Opus writes `tasks\YYYY-MM-DD-<slug>.md` (frontmatter `from/to/status/created`,
`## Task/Context/Change/Test`) + a one-line `STATE.md` entry → tell the worker
"read C:\dev\_hub\tasks\X.md" → worker appends `## Result`, flips `status: done` →
Opus reads ONLY that note → risk-critical review. Use `/handoff` to scaffold.

**Memory split:** hub = shared across terminals, survives `/clear`; native `MEMORY.md` = Opus-only.
**Anti-leak:** read specific note paths, never scan the vault; STATE.md stays one line per task.

## Token discipline (every session)
- `/clear` between unrelated tasks (biggest saver). `/rewind` to abandon a dead path
  (cache-friendly). `/compact` only as last resort (cache-killer).
- Don't switch model/effort mid-task (invalidates prompt cache). Don't idle >5 min near the limit.
- Scope reads: serena `find_symbol` / go-to-def, `offset`/`limit`, never re-read. `permissions.deny`
  already blocks node_modules/dist/lockfiles/secrets.
- Disable idle MCPs via `/mcp`. Keep per task: tradingview (trading), serena, obsidian (notes).
  Drop: Adobe, Canva, Postman, Gmail, Calendar, Google Drive. `/lean` prints this.
- Offload verbose/exploratory work to subagents — only the summary returns.
- Diagnose with `/context` and `/usage`; `/token-report` (npx ccusage) for daily/monthly cost.

## Graphify (understand-anything) rule
The knowledge-graph build fans out many analyzer subagents (token-heavy). Run it **once per
repo** in `agy` or `claude-glm`, cache the output; Opus reads only the summary to make
architecture calls. Regenerate incrementally via `understand-diff`, never every session.

## Privacy
Core strategy / alpha / live-trading logic → Opus / Vertex / local only. Boilerplate / UI /
notes → any cheap model. Never send keys or secrets to any model.
