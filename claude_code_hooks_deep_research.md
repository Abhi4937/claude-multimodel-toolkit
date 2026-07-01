# Deep Research Report: Claude Code Lifecycle Hooks
**Type:** Technical Deep Dive / NotebookLM-Style Research
**Subject:** Claude Code CLI Automation & Middleware (Hooks)
**Focus:** Definition, Internal Mechanics, Comprehensive Hook Roster, and Advanced Implementations

---

## Executive Summary
In the context of the Claude Code CLI, **Hooks** represent one of the most powerful paradigms for power users. They transform Claude Code from a passive, stateless chatbot into a highly programmable, event-driven Agentic Operating System. This document explores the internal mechanics of hooks, details every available hook in the lifecycle, and provides concrete engineering patterns for using them to enhance security, reduce token costs, and dynamically inject context.

---

## 1. What Are Hooks?
At their core, **Hooks** are user-defined scripts or terminal commands that the Claude Code CLI automatically executes at specific milestones during its internal event loop. 

Think of them as "middleware" or "interceptors." When Claude transitions from one state to another (e.g., from *thinking* to *running a bash command*, or from *receiving a command output* to *updating its context window*), it triggers an event. If a hook is bound to that event in your configuration, Claude pauses its core process, hands control over to your script, waits for your script to return a result, and then resumes operation.

Hooks are configured locally or globally via the `settings.json` file (typically located at `~/.claude/settings.json`).

---

## 2. Why Are They Used? (The Three Pillars)

Engineers deploy hooks to solve three fundamental problems inherent to Large Language Models (LLMs) interacting with local environments:

1. **Security & Guardrails:** LLMs hallucinate. If an LLM hallucinates a command like `rm -rf /` or `git reset --hard` on an unsaved repository, the results are catastrophic. Hooks provide a deterministic, programmatic veto power over the probabilistic LLM.
2. **Token Economy (Cost & Latency):** LLMs are billed by the token. Injecting a 50,000-line error log into the context window costs real money and degrades the model's focus. Hooks act as data filters, condensing massive outputs into lean, token-efficient summaries.
3. **Dynamic State Injection:** LLMs are completely stateless. To make an LLM aware of the current system state (e.g., the current Git branch, or if a local Docker container is running), you must explicitly tell it. Hooks automate the gathering and injection of this environmental telemetry.

---

## 3. Comprehensive List of Hooks & Lifecycle Usage

Below is the chronological sequence of hooks available in the Claude Code lifecycle, detailing exactly what they do, when to use them, and their primary benefits.

### A. The `PreSession` Hook (Initialization)
- **What it does:** Fires immediately when the `claude` command is typed, before the network connection to Anthropic is established and before the first prompt is accepted.
- **When to use it:** 
  - To verify that required infrastructure (like a local database or Docker daemon) is running before the agent begins work.
  - To automatically pull the latest Git changes.
  - To authenticate third-party CLI tools (e.g., refreshing AWS tokens).
- **Benefits:** Ensures a pristine, predictable environment. Prevents Claude from wasting tokens trying to debug "Connection Refused" errors caused by un-started local services.

### B. The `UserPromptSubmit` Hook (The State Injector)
- **What it does:** Fires the exact moment the user presses `Enter`, but *before* the payload is packaged and sent to the LLM. It allows modification or augmentation of the user's prompt.
- **When to use it:**
  - To automatically append system state telemetry to your query.
  - *Example:* A hook script runs `git status --short` and appends `"Current git status: [M src/main.js]"` silently to the end of your prompt.
- **Benefits:** Eliminates the need for the user to manually type out context. The agent always has real-time awareness of the system state at the moment the query is sent.

### C. The `PreToolUse` Hook (The Security Guard)
- **What it does:** Fires after the LLM decides to use a tool (like `execute_bash` or `file_read`), but **before** the tool actually executes on the local machine. The hook receives the exact JSON parameters the LLM generated.
- **When to use it:**
  - **Command Whitelisting/Blacklisting:** Parsing the proposed bash command. If it contains `rm`, `drop`, or `sudo`, the hook aborts the tool call and returns a synthetic error to Claude: *"Action denied by system policy."*
  - **Directory Sandboxing:** Ensuring that a `file_write` tool is only modifying files inside a specific `/tmp` or `./src` directory, preventing the agent from modifying system files outside the repository.
- **Benefits:** Absolute, programmatic safety. It allows developers to confidently run Claude Code in fully autonomous, unmonitored modes without fear of system destruction.

### D. The `PostToolUse` Hook (The Data Filter)
- **What it does:** Fires **after** a tool has executed on the local machine, but **before** the output (stdout/stderr) is sent back to the LLM's context window as a `tool_result`. The hook receives the raw output and can mutate it.
- **When to use it:**
  - **Log Truncation:** If `npm run test` generates 50,000 lines of output, a `PostToolUse` hook script can intercept the output, pipe it through `grep -i "error\|fail"`, and return only the 20 lines that actually matter to the LLM.
  - **PII Scrubbing:** If Claude reads a local database dump, the hook can use Regex to automatically redact emails, passwords, or API keys before they are sent to Anthropic's servers.
- **Benefits:** Massive token savings (reducing API costs), drastically lower latency (sending 20 lines over the network instead of 50,000), and compliance/privacy enforcement.

---

## 4. How to Configure Hooks (Technical Implementation)

Hooks are bound by defining shell commands or mapping to custom scripts inside your `~/.claude/settings.json`.

**Example Configuration:**
```json
{
  "hooks": {
    "PreToolUse": {
      "command": "node ~/.claude/scripts/security-check.js"
    },
    "PostToolUse": {
      "command": "python3 ~/.claude/scripts/log-minimizer.py"
    },
    "UserPromptSubmit": {
      "command": "sh ~/.claude/scripts/inject-git-status.sh"
    }
  }
}
```

### The Interception Mechanics
When Claude triggers a hook like `PostToolUse`, it streams the raw data (e.g., the bash output) to your script's `stdin`. Your script processes the data, and whatever your script prints to `stdout` is what Claude ultimately receives as the final payload. If your script exits with a non-zero status code (e.g., `exit 1`), Claude registers it as a tool failure.

---

## 5. Advanced Engineering Patterns

Top 1% power users combine hooks to create highly sophisticated agentic loops:

1. **The "Continuous Integration" Agent:**
   - **`PreSession`**: Runs a linter to ensure code is clean before Claude starts.
   - **`PreToolUse`**: Blocks any command that modifies the `main` branch directly.
   - **`PostToolUse`**: Compresses Webpack build logs so Claude only sees the specific compilation errors.
2. **The "Cost-Capped" Hook:**
   - A `UserPromptSubmit` hook that reads the current API usage for the day. If costs exceed a hard-coded $5 limit, the hook artificially rejects the prompt, forcing the user to switch to a cheaper local model (like Llama 3) via an MCP proxy.

## Conclusion
Hooks are the bridge between Claude's probabilistic reasoning and the deterministic safety required for local development. By mastering `PreToolUse` and `PostToolUse`, engineers can sandbox the agent, slash token expenditures, and build workflows that run autonomously, securely, and hyper-efficiently.

*Added by AGY study*
