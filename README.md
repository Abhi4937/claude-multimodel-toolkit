# claude-multimodel-toolkit

A single-machine setup for running Claude Code across multiple models with strict token
discipline, file-based cross-terminal coordination, and a hard billing safety cap.
This repo doubles as the **hub** (`tasks/`, `knowledge/`, `scripts/`) and the **toolkit** (`setup/`).

> Private repo. Contains no secrets (keys are supplied locally via `setx`). Session logs and
> live task notes are git-ignored. See `setup/INSTALL.md` to deploy on a new machine.

## Model roster (route by risk × size)
| Terminal / tool | Model | Cost | Use for |
|---|---|---|---|
| `opus` / `claude` | Opus 4.8 (Claude Pro) | flat | architecture, planning, risk-critical review, hard bugs |
| `claude-glm` | GLM-5.2 (1M ctx) | $16/mo flat | coding, refactors, tests |
| `agy` | Gemini 3.1 Pro | free | research, long-context, video→notes |
| `nv_batch.py` | NVIDIA deepseek-v4-pro | free | mechanical transforms |
| `claude-vertex` | Claude on Vertex | real money — off by default | Opus overflow (credits don't cover Claude) |

## What's in here
- **`setup/`** — deploy kit: `commands/` (5 slash commands), `skills/token-model-routing/`,
  `model-profiles.ps1` (terminal wrappers), `settings.permissions-snippet.json`, `INSTALL.md`.
- **`knowledge/`** — the operating manual: `how-to-operate.md`, `statelessness-strategy.md`,
  `commands-and-skills.md`, `project-CLAUDE.md.template`.
- **`scripts/nv_batch.py`** — free NVIDIA chore worker.
- **`gcp-killswitch/`** — auto-disable-billing Cloud Function + `DEPLOY.md` (true hard spend cap).
- **`tasks/` + `STATE.md`** — the handoff bus (live notes are git-ignored; `_TEMPLATE.md` kept).
- **`sessions/`** — session logs (git-ignored, local only).

## Custom commands
`/handoff` (delegate a task) · `/lean` (MCP hygiene) · `/token-report` (ccusage) ·
`/log-session` (save a session log) · `/recall <topic>` (grep history, no full reads).

## Core ideas
- **Route by risk × size:** Opus only for judgment/risk work; everything else offloads to cheap/free tiers.
- **File-based coordination:** terminals don't share context — they share the hub + repo files.
- **Token discipline:** `/clear` between tasks, `/rewind` over `/compact`, scoped reads, `permissions.deny`.
- **Two memory layers:** decisions → memory + `knowledge/`; codebase → serena. See `knowledge/statelessness-strategy.md`.

See `knowledge/how-to-operate.md` for the day-to-day workflow.
