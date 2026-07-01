# Statelessness Strategy — how memory + tools persist across sessions/terminals

Claude Code sessions are stateless (each starts fresh, `/clear` wipes context). Handle it in
layers. See also [[how-to-operate]].

## Two halves of the problem — handle separately
| Half | What it is | Where it's solved |
|---|---|---|
| **Decision memory** | goals, what was decided, preferences, specs | native `MEMORY.md` (Opus-only) + `_hub/knowledge/` (shared) |
| **Codebase memory** | avoid re-scanning the repo every session to relearn structure | **serena** (LSP nav, have it) ± `codebase-memory-mcp` (big repos) |
| **One-time deep map** | full architecture comprehension | understand-anything **graphify**, built once in `claude-glm`/`agy`, cached |

Rule: if a fact must outlive the session → write it (native memory or `knowledge/`). Otherwise it's gone.

## Tool / MCP availability per terminal
| | serena + local MCPs/plugins/skills | claude.ai connectors (Adobe/Gmail/…) | coordinates via |
|---|---|---|---|
| `opus` / `claude` | ✅ full | ✅ | shared config + hub |
| `claude-glm` | ✅ full (same Claude Code) — nudge GLM to use them | ❌ (z.ai auth, not Anthropic) | shared config + hub |
| `agy` | ❌ different tool (no Claude Code MCPs) | ❌ | **files only** — the hub + repo |

- `opus` and `claude-glm` share the same `~/.claude` config → same serena, LSPs, skills. Only the
  Anthropic-account connectors are off in glm. Run `/lean` in glm too (MCPs cost tokens there).
- `agy` is kept in loop ONLY through the shared filesystem: point it at `C:\dev\_hub\tasks\X.md`.

## codebase-memory-mcp — verdict
Persistent SQLite code knowledge-graph (call-tracing, impact, dead-code); queries the index instead of
re-reading files. Directly attacks the "rescan whole project" token cost. BUT overlaps heavily with
**serena** (already enabled). So:
- Decision memory is already solved (native + hub) — this tool doesn't help that half.
- For codebase memory you're mostly covered by serena. Add codebase-memory-mcp ONLY on the **large,
  recurring repo** (trading platform) if serena's live nav feels insufficient. Don't run both if redundant.
- Install once (global binary); **index only specific large repos**, not every project. Enable per-session
  via `/mcp`, disable when idle. Verify GitHub activity + that your main language is in its 9 full-LSP tier.
