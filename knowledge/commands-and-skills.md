# Commands & Skills — reference

Custom slash commands and skills built for the multi-model + token-saving workflow.
See also [[how-to-operate]] · [[token-model-routing (skill)]].

## Slash commands (`~/.claude/commands/`)
| Command | Function | When to use |
|---|---|---|
| **`/handoff [task]`** | Picks the worker by risk×size, writes a task note to `C:\dev\_hub\tasks\<date>-<slug>.md` (from `_TEMPLATE.md`), adds a `STATE.md` line, and prints the exact command to run it | Delegating work to `claude-glm` / `agy` / `nv` |
| **`/lean`** | Prints the MCP keep/disable checklist for the current task + reminds `/context`, `/clear`, `/rewind` | Session feels heavy / starting a task |
| **`/token-report`** | Runs `npx ccusage daily` → summarizes today's & this month's cost by model | Checking spend |
| **`/log-session [title]`** | Writes a structured session log (discussed · built · files changed · decisions & why · issues & fixes · redo steps · verified vs pending · tools · studies · links · next) to `C:\dev\_hub\sessions\<project>\`, and appends a tagged line to `sessions/INDEX.md`. **Local, never pushed to GitHub** | Before `/compact` or closing |
| **`/recall <topic>`** | Greps `sessions/INDEX.md` + logs + knowledge, returns **only matching snippets + paths** (never whole files) | Finding past work cheaply |
| **`/gemini <q>`** | Ask **Gemini 3.1 Pro** (Vertex, credit-funded) from inside a Claude session | second opinion / offload a reasoning task |

## PowerShell terminal wrappers (in `model-profiles.ps1`, dot-sourced from $PROFILE)
| Wrapper | Launches |
|---|---|
| `opus` | Opus 4.8 brain (subagents→Sonnet) |
| `claude-glm` | GLM-5.2 coding agent (z.ai) |
| `claude-gemini` | Gemini 3.1 Pro agent (LiteLLM proxy → Vertex; auto-starts proxy :4000) |
| `agy` | Gemini 3.1 Pro (Antigravity) |
| `gemini "..."` | one-shot Gemini 3.1 Pro (Vertex), zero Claude tokens |
| `ytnotes "URL" ...` | YouTube → notes pipeline (nvidia/glm/vertex) |

## Skill (`~/.claude/skills/`)
| Skill | Function | Activation |
|---|---|---|
| **`token-model-routing`** | Routing brain: terminal roster, work distribution (risk×size), Obsidian-hub handoff protocol, token discipline (`/clear`>`/rewind`>`/compact`, MCP mgmt), graphify rule, privacy | **Auto-loads on-demand** when routing/token decisions arise — never invoked manually |

## Notes
- `/handoff`, `/lean`, `/token-report` are active now. `/log-session` + `/recall` register as slash commands after a **shell restart** (created 2026-07-02).
- The skill loads itself when relevant; otherwise only its one-line description sits in context (cheap).
- Commands live globally in `~/.claude/commands/` → available in `opus` AND `claude-glm` (same Claude Code). Not in `agy` (different tool).
