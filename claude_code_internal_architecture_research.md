# Deep Research Report: Claude Code Internal Architecture & Execution Flow
**Type:** Technical Deep Dive / NotebookLM-Style Research
**Subject:** Claude Code CLI (Under the Hood)
**Focus:** Lifecycle from Initialization to Execution, File Ecosystem, Context Management

---

## Executive Summary
This document serves as a comprehensive teardown of how the Claude Code CLI functions internally. It covers the exact execution lifecycle from the moment a session is initialized, dissects the ecosystem of configuration and context files, and details the mechanics of context window management, caching, and tool execution.

---

## Part 1: The Boot Sequence (Opening a Session)

What exactly happens in the first 500 milliseconds after you type `claude` in your terminal?

### 1. Environment & Pre-Flight Checks
1. **Node.js Initialization:** Claude Code is an npm-distributed CLI tool. It starts a Node.js process and immediately verifies API keys and network connectivity to Anthropic's endpoints.
2. **Global Config Loading:** It reads `~/.claude/settings.json`. This file acts as the master registry for things like API base URLs, telemetry settings, preferred models, and permission rules (e.g., global `.claudeignore` equivalents).
3. **Bootstrapping Hooks:** If any `PreSession` hooks are defined in `settings.json`, they are executed now.

### 2. Context Aggregation & The `CLAUDE.md` Cascade
Before talking to the LLM, Claude Code must understand the rules of engagement.
1. **Global Rules:** It parses `~/.claude/CLAUDE.md` (the global instructions).
2. **Local Rules:** It crawls up from the current working directory to find a project-specific `./CLAUDE.md`.
3. **Injection:** The contents of these markdown files are appended to the internal *System Prompt*.

### 3. Subsystem Initialization
1. **Memory Journaling:** It reads `./.claude/MEMORY.md` (if it exists) to recall historical architecture decisions from past sessions.
2. **Model Context Protocol (MCP):** Background processes are spawned for any registered MCP servers. To save tokens, the system injects only "MCP Stubs" (the names and brief descriptions of available tools, roughly 120 tokens) into the context window rather than the full schemas.

### 4. Payload Construction (The Static-First Strategy)
The final payload sent to the Anthropic API is engineered for **Prompt Caching**. It follows a strict order:
1. Base System Prompt (Persona + Safety rules)
2. Tool Schemas (Built-in Bash, File Read, etc.)
3. `CLAUDE.md` & `MEMORY.md` contents
4. MCP Stubs
5. The historical conversation log (User Prompts + Assistant Replies + Tool Results)
6. The *new* User Prompt.

*Insight:* By keeping the top 80% of the payload completely static, Anthropic's servers can cache the prompt, reducing costs by 90% and latency drastically.

---

## Part 2: The File Ecosystem (What is Used & When)

| File / Location | When is it loaded? | Purpose |
| :--- | :--- | :--- |
| `~/.claude/settings.json` | On Boot | Master configurations, hooks, and denial rules (e.g., `deny: ["Read(node_modules/**)"]`). |
| `~/.claude/CLAUDE.md` | On Boot (Every turn) | Global behavioral rules applied to all projects. |
| `./CLAUDE.md` | On Boot (Every turn) | Project-specific conventions (e.g., "Use Next.js 14 App Router"). |
| `./.claude/MEMORY.md` | On Boot (Every turn) | Auto-maintained journal where Claude writes important project architecture facts for its future self. |
| `SKILL.md` (Inside Skills folder) | Lazy-Loaded | Complex operational guides. Claude only loads the title/description initially, and reads the full file only when it decides it needs that specific skill. |

---

## Part 3: Internal Mechanics of Commands

When you use slash commands (e.g., `/clear`), they are intercepted by the CLI parser *before* hitting the LLM.

### `/clear`
- **Internal Action:** Destroys the local session array holding the `User -> Assistant -> Tool_Result` history.
- **Cache Impact:** Excellent. Resets the context window, leaving only the highly-cached System Prefix.

### `/rewind`
- **Internal Action:** Pops the last *N* message pairs off the session array.
- **Cache Impact:** Excellent. Because it only truncates the *end* of the payload, the static prefix remains intact, allowing a 90% cache hit on the next turn.

### `/compact`
- **Internal Action:** Takes the current 100k-token history, sends a hidden prompt to the LLM asking for a dense summary, and replaces the massive history array with the single summary string.
- **Cache Impact:** Destructive. Alters the middle of the payload, shattering the prompt cache and causing a 100% full-price cache miss on the next turn.

### `/mcp`
- **Internal Action:** Dynamically attaches or detaches a background MCP server process.
- **Cache Impact:** Destructive. Because the MCP Stubs are located in the static prefix, changing them modifies the prefix, breaking the cache.

---

## Part 4: Tool Execution Loop (The "Action" Phase)

When Claude decides to execute a bash command or read a file, the following internal loop occurs:

1. **The Generation:** The LLM stops generating conversational text and outputs a strict JSON blob matching a tool schema (e.g., `execute_bash` with `command: "npm run build"`).
2. **The Interception:** The Claude Code CLI intercepts this JSON. It pauses the LLM stream.
3. **The Hook (PreToolUse):** If configured in `settings.json`, a pre-execution hook runs (e.g., a script that scans the command for destructive flags like `rm -rf`).
4. **The Execution:** The CLI runs the command in a hidden pty (pseudo-terminal) or reads the file from disk.
5. **The Hook (PostToolUse):** The raw output can be intercepted (e.g., piping a 50MB log file through a filter to only return the `ERROR:` lines).
6. **The Re-Injection:** The CLI packages the output into a `tool_result` JSON object, appends it to the conversation history array, and automatically triggers a new LLM request: "Here is the result of your command. Continue."

### The Danger of "Tool Spills"
If `npm install` outputs 5,000 lines of verbose logs, Claude Code blindly appends all 5,000 lines into the `tool_result`. This bloats the conversation history, wasting thousands of tokens on every subsequent turn.

---

## Part 5: Subagents & Context Isolation

For complex tasks (e.g., "Research this directory"), Claude Code spawns **Subagents**.

**How Subagents Work Internally:**
1. The CLI forks a completely new, empty session array.
2. It assigns the subagent a specific "Mode Prompt" (e.g., the *Researcher* persona).
3. The subagent executes tools, reads hundreds of files, and fills up its own 150,000-token context window.
4. When finished, the subagent summarizes its findings.
5. The CLI takes that summary, injects it back into your *Main Session* as a `tool_result`, and completely deletes the subagent's massive 150,000-token history.

*Why this is genius:* It allows Claude to process millions of tokens of background research without polluting your main conversation history, keeping your ongoing token costs extremely low.

---

## Conclusion
Claude Code operates less like a simple chat wrapper and more like a full **Prompt Operating System**. By mastering the static-first payload structure, managing the `CLAUDE.md` file ecosystem, and aggressively isolating context-heavy tasks into subagents, developers can manipulate the internal mechanics to achieve Opus-level reasoning at Sonnet-level costs.

*Added by AGY study*
