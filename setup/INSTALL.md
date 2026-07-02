# Install — deploy this toolkit into a machine

Reproduces the multi-model + token-saving setup. Nothing here contains secrets — you supply keys via `setx`.

## 1. Commands + skill → `~/.claude/`
```powershell
Copy-Item setup\commands\*.md            $env:USERPROFILE\.claude\commands\ -Force
Copy-Item setup\skills\token-model-routing -Destination $env:USERPROFILE\.claude\skills\ -Recurse -Force
```

## 2. settings.json
Merge `setup/settings.permissions-snippet.json` (env caps + `permissions.deny`) into `~/.claude/settings.json`.
Do NOT paste any real API-key values into a committed file.

## 3. Terminal wrappers
Dot-source `setup/model-profiles.ps1` from your PowerShell `$PROFILE`:
```powershell
'. C:\path\to\model-profiles.ps1' | Add-Content $PROFILE
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned   # so the profile loads
```
Then set your keys (local only, never committed):
```powershell
setx ZAI_KEY 'your-zai-coding-plan-key'
setx NVIDIA_API_KEY 'nvapi-...'
# (optional Vertex, real money) setx ANTHROPIC_VERTEX_PROJECT_ID '...'; setx CLOUD_ML_REGION 'us-east5'
```
Gives you: `opus`, `claude-glm`, `agy` (Antigravity CLI, installed separately), `claude-vertex` (off by default).

## 4. Hub
The repo root IS the hub. Terminals reference `tasks/`, `knowledge/`, `scripts/nv_batch.py`, `STATE.md` by absolute path.
`sessions/` (logs), `scratch/`, and live `tasks/*.md` are git-ignored (local only).

## 5. NVIDIA chore worker
```powershell
pip install openai   # then: python scripts\nv_batch.py -i "..." <file>
```

## 5b. Token-saver hooks (8 automatic guards)
```powershell
pip install "markitdown[all]"   # for PDF/Office/HTML -> markdown conversion
```
Register the `PreToolUse` hook: merge the `hooks` block from `settings.permissions-snippet.json`
into `~/.claude/settings.json`, pointing `command` at `setup/hooks/token_saver_hook.py` (absolute path).
Details + escape hatches: `knowledge/token-saver-hooks.md`. Disable per-session with `TOKENSAVER_OFF=1`.

## 5c. YouTube -> notes pipeline (no Claude, free)
```powershell
pip install yt-dlp youtube-transcript-api ddgs openai
winget install --id Gyan.FFmpeg     # for --snaps
```
`scripts/yt_notes.py` turns a video into detailed research notes + chapter snapshots, saved to your
Obsidian vault. The `ytnotes` PowerShell wrapper (in model-profiles.ps1) runs it:
`ytnotes "URL" --research --snaps 4 --models nvidia,glm,gemini`. Keys: NVIDIA_API_KEY (free),
ZAI_KEY, GEMINI_NOTES_KEY. Zero Claude tokens.

## 6. (Optional) GCP billing kill-switch
See `gcp-killswitch/DEPLOY.md`. Only needed if you use a paid GCP service (e.g. Claude-on-Vertex).

## What NOT to commit
API keys, `~/.claude/settings.json` (has real keys), session logs, live task notes. The `.gitignore` guards these.
