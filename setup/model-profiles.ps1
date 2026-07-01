# model-profiles.ps1 — Claude Code multi-model terminal profiles
# Usage: dot-source from your $PROFILE:   . C:\dev\trading_concepts\scripts\model-profiles.ps1
#
# TERMINALS:
#   opus / claude → Opus 4.8 brain      (Claude Pro $20/mo subscription; subagents→Sonnet)
#   claude-glm    → GLM-5.2 worker      (Z.ai Coding Plan Lite, ZAI_KEY)
#   claude-vertex → Claude on Vertex    (Opus/Sonnet overflow, $300 GCP credits)
#   agy           → Gemini 3.1 Pro      (Antigravity CLI, free via Jio)
#
# Key setup (run once, then restart shell):
#   setx ZAI_KEY                     "your-zai-coding-plan-key"
#   setx ANTHROPIC_VERTEX_PROJECT_ID "your-gcp-project-id"
#   setx CLOUD_ML_REGION             "us-east5"
#   setx NVIDIA_API_KEY              "nvapi-..."   (for C:\dev\_hub\scripts\nv_batch.py)

# ---------------------------------------------------------------------------
# Profile 1: Opus 4.8 brain — run: opus   (or plain `claude`)
# Uses Claude Pro subscription. `opus` routes SUBAGENTS to Sonnet (spares the scarce
# Opus 5-hr limit) without polluting global settings.json (which would break glm/vertex).
# USE FOR: architecture, risk-critical review, hard bugs, planning
# ---------------------------------------------------------------------------
function opus {
    $env:CLAUDE_CODE_SUBAGENT_MODEL    = "claude-sonnet-4-6"          # subagents → Sonnet (spare scarce Opus)
    $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "claude-haiku-4-5-20251001"  # background/compaction → Haiku
    try { claude @args }
    finally { Remove-Item Env:CLAUDE_CODE_SUBAGENT_MODEL, Env:ANTHROPIC_DEFAULT_HAIKU_MODEL -ErrorAction SilentlyContinue }
}

# ---------------------------------------------------------------------------
# Profile 2: GLM-5.2 heavy coding worker (Z.ai Coding Plan, direct endpoint)
# USE FOR: website coding, refactors, tests, backtester, boilerplate
# ---------------------------------------------------------------------------
function claude-glm {
    if (-not $env:ZAI_KEY) {
        Write-Host "ZAI_KEY not set. Run: setx ZAI_KEY 'your-key'" -ForegroundColor Yellow
        return
    }
    $env:ANTHROPIC_BASE_URL              = "https://api.z.ai/api/anthropic"
    $env:ANTHROPIC_AUTH_TOKEN            = $env:ZAI_KEY
    $env:API_TIMEOUT_MS                  = "3000000"
    $env:ANTHROPIC_DEFAULT_SONNET_MODEL  = "glm-5.2"
    $env:ANTHROPIC_DEFAULT_OPUS_MODEL    = "glm-5.2"
    $env:ANTHROPIC_DEFAULT_HAIKU_MODEL   = "glm-4.7"        # background + compaction → cheaper (z.ai doc value)
    $env:CLAUDE_CODE_SUBAGENT_MODEL      = "glm-4.7"        # subagents → cheaper
    $env:CLAUDE_CODE_AUTO_COMPACT_WINDOW = "1000000"        # use GLM-5.2's real 1M window (not Claude Code's 200K default)
    try { claude --model "glm-5.2" @args }
    finally {
        Remove-Item Env:ANTHROPIC_BASE_URL, Env:ANTHROPIC_AUTH_TOKEN, Env:API_TIMEOUT_MS, `
                    Env:ANTHROPIC_DEFAULT_SONNET_MODEL, Env:ANTHROPIC_DEFAULT_OPUS_MODEL, `
                    Env:ANTHROPIC_DEFAULT_HAIKU_MODEL, Env:CLAUDE_CODE_SUBAGENT_MODEL, `
                    Env:CLAUDE_CODE_AUTO_COMPACT_WINDOW -ErrorAction SilentlyContinue
    }
}

# ---------------------------------------------------------------------------
# Profile 3: Claude on Vertex AI — OPUS/SONNET OVERFLOW (metered by $300 GCP credits)
# USE FOR: brain work when the Pro plan's Opus 5-hr limit is exhausted.
# NOTE: Vertex's Anthropic-compatible API serves CLAUDE models only (NOT Gemini —
#       Gemini goes through `agy`). Claude Code talks to Vertex natively via CLAUDE_CODE_USE_VERTEX.
# Setup once: gcloud auth login; gcloud auth application-default login;
#             gcloud config set project <proj>; gcloud services enable aiplatform.googleapis.com;
#             enable Anthropic Claude in Vertex Model Garden.
# VERIFY exact Vertex model IDs in Model Garden and override via env if needed:
#   VERTEX_OPUS_MODEL / VERTEX_SONNET_MODEL / VERTEX_HAIKU_MODEL
# ---------------------------------------------------------------------------
function claude-vertex {
    if (-not $env:ANTHROPIC_VERTEX_PROJECT_ID) {
        Write-Host "ANTHROPIC_VERTEX_PROJECT_ID not set. Run: setx ANTHROPIC_VERTEX_PROJECT_ID 'your-gcp-project'" -ForegroundColor Yellow
        return
    }
    $opusModel   = if ($env:VERTEX_OPUS_MODEL)   { $env:VERTEX_OPUS_MODEL }   else { "claude-opus-4-8" }
    $sonnetModel = if ($env:VERTEX_SONNET_MODEL) { $env:VERTEX_SONNET_MODEL } else { "claude-sonnet-4-6" }
    $haikuModel  = if ($env:VERTEX_HAIKU_MODEL)  { $env:VERTEX_HAIKU_MODEL }  else { "claude-haiku-4-5@20251001" }
    $region      = if ($env:CLOUD_ML_REGION)     { $env:CLOUD_ML_REGION }     else { "us-east5" }

    $env:CLAUDE_CODE_USE_VERTEX         = "1"
    $env:CLOUD_ML_REGION                = $region
    $env:ANTHROPIC_DEFAULT_HAIKU_MODEL  = $haikuModel   # background/compaction (cheap, on Vertex)
    $env:CLAUDE_CODE_SUBAGENT_MODEL     = $sonnetModel   # subagents → Sonnet on Vertex
    $env:API_TIMEOUT_MS                 = "3000000"
    try { claude --model $opusModel @args }
    finally {
        Remove-Item Env:CLAUDE_CODE_USE_VERTEX, Env:CLOUD_ML_REGION, `
                    Env:ANTHROPIC_DEFAULT_HAIKU_MODEL, Env:CLAUDE_CODE_SUBAGENT_MODEL, `
                    Env:API_TIMEOUT_MS -ErrorAction SilentlyContinue
    }
}

# ---------------------------------------------------------------------------
# Profile 4: agy — Gemini via Antigravity (free, Jio-backed)
# USE FOR: same as claude-gemini but free tier; just run: agy
# (no wrapper needed — agy.exe handles Gemini natively)
# ---------------------------------------------------------------------------
