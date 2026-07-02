---
description: Ask Gemini 3.1 Pro (Vertex, credit-funded) from inside a Claude session
argument-hint: <question or task>
allowed-tools: Bash(python:*)
---

Get Gemini 3.1 Pro's answer on: $ARGUMENTS

Run: `python C:\dev\_hub\scripts\ask_gemini.py "$ARGUMENTS"` and show me Gemini's response.
If I referenced specific files, add `--file <path>` for each so Gemini sees them.

Use this for a second opinion, an alternate approach, or to offload a self-contained
reasoning/writing task to Gemini (funded by GCP credits, not Claude tokens for the generation).
Note: orchestrating this still costs some Claude tokens (Gemini's output enters context) -
for fully token-free Gemini use the `gemini` PowerShell wrapper directly instead.
