# The Complete Master Guide to Tokens in Claude Code

Welcome to the end-to-end mastery guide on Token architecture, Prompt Caching, and CLI optimization for Claude Code. By the end of this document, you will understand exactly how the system is wired under the hood, why you are getting billed what you are, and how to operate the CLI like a top 1% power user.

---

## 1. What Are Tokens and How Are They Used?
Tokens are the fundamental unit of computation for Large Language Models (LLMs). One token is roughly equal to 3/4 of a word (e.g., "hamburger" is broken into "ham", "bur", "ger"). 

**The Golden Rule of LLMs:** Models are completely **stateless**. They have no internal memory of your conversation. 
Every single time you press Enter, Claude Code takes your *entire* conversation history, packages it into a massive text payload, and sends it to Anthropic’s servers. The server reads the entire package from line 1, generates a response, and forgets you exist until you press Enter again.

### What Happens When You Open a Session? (The Payload & Initialization)
When you open a session (e.g., by typing `claude` in your terminal) and send your first message, Claude Code undergoes a specific boot and payload-construction sequence. The final payload is constructed in a strict **static-first order** to maximize prompt caching:

1. **Environment & Config Bootstrapping:** Before anything is sent, Claude Code reads your local configuration (`~/.claude/settings.json`), evaluates any lifecycle hooks like `PreToolUse`, and prepares your terminal environment.
2. **Loading Context Files (CLAUDE.md):** The system hunts for `CLAUDE.md` files. It first loads the global rulebook from `~/.claude/CLAUDE.md` and then specifically pulls in the local `./CLAUDE.md` in your current working directory. The contents of these files are injected directly into the system prompt to guide Claude's behavior for the session.
3. **MCP Server Initialization:** Claude Code boots up any configured Model Context Protocol (MCP) servers in the background. Instead of injecting the massive schemas for every MCP tool into the context, it loads **MCP Stubs (~120 tokens)**—just the names of the available tools. The full schemas are deferred and lazy-loaded only when you actually invoke them.
4. **System Prompt & Built-in Tools (~4,200 tokens):** The core instruction set defining Claude's personality, safety rails, and roughly 50 built-in JSON schemas (like Bash execution, File Reading, Web Search) are placed at the very top of the payload.
5. **Project Context (~2,500+ tokens):** Your loaded `CLAUDE.md` guidelines, memory summaries (`MEMORY.md`), and environmental data are appended. (See Section 7 for details).
6. **Conversation History:** Every prior user message, assistant reply, and **tool result** (such as file reads or bash outputs) from the session is included.
7. **Your New Prompt:** Finally, the actual text you just typed is placed at the end.

*Cost grows quadratically.* If your history is 50,000 tokens long, every single prompt you type bills you for 50,000 input tokens.

---

## 2. Prompt Caching: Your Cost Savior
If Claude Code billed you full price for reading those 50,000 tokens on every turn, it would cost a fortune. To fix this, Anthropic uses **Prompt Caching**.

* **How it works:** Anthropic's servers remember the "prefix" of your payload. Because Claude Code puts the system prompt and old history at the very beginning of the payload (the prefix), the server says, "I've seen this exact 49,000-token chunk 10 seconds ago. I don't need to re-read it."
* **The Economics:** A cache hit costs **~90% less** (billed at 0.1x the normal input rate). Cache writes (when the prefix changes) cost slightly more (1.25x), but they pay for themselves immediately on the next turn.
* **The TTL (Time to Live):** Caches live on Anthropic's servers for exactly **5 minutes**. (If you set `ENABLE_PROMPT_CACHING_1H=1` or use the API plan, it negotiates a 1-hour TTL). If you idle past the TTL, the cache drops. Your next prompt will be a full, 100% uncached re-read.

---

## 3. How Tokens "Leak" (The Cache-Killers)
Token leakage happens when you accidentally break the prompt cache or blindly dump data into the context window. 

### The Cache-Killers (Avoid Mid-Session)
Prompt caching relies on **exact prefix matching**. Doing any of the following mid-session shatters the cache and forces a massive bill on your next turn:
- **Switching Models:** e.g., using `/model` to switch from Sonnet to Opus mid-conversation.
- **Adding/Removing MCP Servers:** e.g., running `/mcp add` or removing a server.
- **Changing Effort:** e.g., typing `/effort high`.
- **Using `/compact`:** (More on this below).

### The Context Hogs
- **File Reads:** The #1 context killer. A single source file read is ~1,100 to 2,400 tokens. 
- **Bash Command Spills:** If you tell Claude to run `npm install`, the raw stdout is injected into the context as a "Tool Result". A 5,000-line error log is 5,000 lines of pure token waste.
- **Raw Web Scrapes:** Giving Claude raw HTML instead of a markdown version.

---

## 4. The CLI Commands Deep Dive

### `/clear` (The MVP Command)
* **What it does:** Wipes the conversation history completely.
* **When to use it:** Between every unrelated task. This is your most powerful cost-saving tool.

### `/compact` (The Last Resort)
* **What it does:** Asks the LLM to write a summarized summary of your conversation, then replaces your history with it.
* **The Danger:** It is a **Cache-Killer**. Furthermore, if you `/compact` a thread that has already been compacted, you get a "summary of a summary" and Claude will hallucinate.
* **When to use it:** *Only* when your context reaches 80%+ capacity and you cannot use `/clear`. **Do not use this proactively at 50%**.

### `/rewind` (The Pro's Undo)
* **What it does:** Truncates the conversation history back a few turns ("forget the last 3 things we talked about.")
* **Why it's amazing:** Because it cuts off the end of the payload, the **prefix remains exactly the same**. `/rewind` is highly cache-friendly. Use this instead of `/compact` when Claude makes a mistake.

### `/resume`
* **What it does:** Opens a previous session (`claude --resume`).
* **Token impact:** Unless you resumed it within the 5-min/1-hour TTL window, the cache is gone. Your first prompt is a full, uncached read.

### `/context` and `/usage`
* **`/context`:** Visualizes what is eating your window right now.
* **`/usage`:** Shows your session token burn, rolling 5-hour API limits, and expenses.

---

## 5. Skills, MCPs, and Subagents

### Bash Commands and Errors
When Claude runs a bash command, the terminal output is returned as a JSON `tool_result`. 
* **Pro-tip:** When prompting Claude to search logs, explicitly tell it: *"Run the tests but pipe the output to `head -n 50`."* 

### MCP (Model Context Protocol)
Attaching an MCP server used to inject 10k-20k tokens per turn. Claude Code now uses **`defer_loading`** (injecting only ~120-token names until called). 
* **Rule:** Still disable idle MCP servers using `/mcp`. 

### Subagents (The Ultimate Hack)
When you tell Claude to "Research this directory," it spawns a Subagent.
* **Why it matters:** The subagent opens an *isolated context window*. It can read 50 files and consume 100,000 tokens. When it finishes, that window is destroyed, and it returns a lean 500-token summary to your main session. 
* **Rule:** Push all heavy reading to subagents.

---

## 6. End-to-End Best Practices Summary

1. **Never switch models mid-task.** 
2. **Keep `CLAUDE.md` under 200 lines.** 
3. **Use `/clear` relentlessly.** 
4. **Prefer `/rewind` over `/compact`.** 
5. **Scope your reads.** Use `grep` instead of reading 3,000-line monolithic files.
6. **Watch the TTL clock.** 

---

## 7. The File Ecosystem: Global vs. Local Context

### The Core Files
1. **`CLAUDE.md` (The Rulebook):** Master instructions. Global (`~/.claude/CLAUDE.md`) applies to every project; Local (`./CLAUDE.md`) applies to the current workspace. **Loaded every turn.**
2. **`MEMORY.md` (The Auto-Journal):** Claude writes here to remember architecture for future sessions.
3. **`settings.json`:** Configures the CLI tool itself (base URLs, models, hooks).
4. **`Skills/`:** Instead of putting 1,000 lines in `CLAUDE.md`, put them in a `SKILL.md`. Claude only loads a one-line description into the context, and lazy-loads the massive markdown file only when needed.

---

## 8. Pro-User Secrets, Hooks, and Advanced CLI Flags

If you want to operate Claude Code like a true pro, you must master the hidden CLI flags, advanced hooks, and third-party observability tools.

### `.claudeignore` (Protecting your Context)
Just like `.gitignore`, you should never let Claude blindly read `.env` files, build logs, or `node_modules`. 
* **How to do it (The Official Way):** While the community built npm wrappers, the official GitHub repository (`anthropic/claude-code`) recommends using **permission rules**. You can deny access natively by adding this to your `~/.claude/settings.json`:
  ```json
  "permissions": {
    "deny": [
      "Read(node_modules/**)",
      "Read(.env*)",
      "Read(dist/**)"
    ]
  }
  ```
  This physically blocks Claude from reading those directories and prevents accidental token leakage.

### `ccusage` and Live Statuslines
To get granular data on Cached vs. Uncached tokens, install `ccusage` (`npm install -g ccusage`). 
* Run `ccusage daily` to see a beautiful cost breakdown.
* **The Statusline Hack:** You can embed this token burn directly into the Claude Code typing prompt! Add this to your `~/.claude/settings.json`:
  ```json
  { "statusLine": { "type": "command", "command": "ccusage statusline" } }
  ```

### Advanced CLI Flags
* **`--fork-session`**: Imagine you are 50,000 tokens deep into a session, and you want to try an experimental approach. If you just `/clear`, you lose the state. If you branch using `--fork-session`, Claude duplicates the state into a parallel track. **Bonus:** It inherits the prompt cache of the parent!
* **`--allowedTools` / `--disallowedTools`**: Block Claude from running bash commands entirely (`--disallowedTools bash`).
* **`--system-prompt-file`**: Override the default system prompt entirely for specific tasks.
* **`--permission-mode` and `--output-format stream-json`**: Run Claude completely headlessly in CI/CD pipelines.

### The "!" Prefix Shortcut
Instead of asking Claude to "run git status", you can type `! git status` directly into your prompt. The CLI will execute the command locally and feed the raw stdout directly into the next prompt window, saving a tool-call turn.

### The `MAX_THINKING_TOKENS` Budget Guardrail
Extended reasoning models (like Claude 3.7 or DeepSeek) "think" before they write. These thinking tokens are billed as output tokens.
* If a model gets stuck in a loop, it can burn thousands of thinking tokens. You can cap this by setting the `MAX_THINKING_TOKENS` environment variable (e.g., `MAX_THINKING_TOKENS=4000`).
* Set it to `0` to disable extended thinking entirely for cheap tasks.

### Lifecycle Hooks
In your `~/.claude/settings.json`, you can define scripts that fire at specific points:
* **`PreToolUse`**: Run a script *before* Claude executes a bash command. You can use this to auto-deny destructive commands like `rm -rf`.
* **`PostToolUse`**: Filter massive logs. E.g., pipe a 100MB test output through a script that only returns the failure lines to Claude.
* **`UserPromptSubmit`**: Inject current state (like the current Git branch name or stock ticker price) right as you hit Enter.

---

## 9. The System Prompt Leak & Customizing the "Prompt OS"

In March 2026, developers discovered that Claude Code’s source code was accessible via an exposed source map file in the npm package. This led to the creation of the famous GitHub repository **`Piebald-AI/claude-code-system-prompts`**, which tracks and extracts every internal instruction Anthropic feeds to the model.

### How the "Prompt OS" Actually Works
By reading the leaked prompts, the community discovered that Claude Code does **not** use a single, monolithic system prompt. Instead, it operates like an operating system, dynamically assembling instructions from dozens of fragments based on what you are doing:
- **Base Prompts:** The core rules governing tone and safety.
- **Tool Prompts:** Instructions injected only when a specific tool (like bash or file-read) is active.
- **Mode Prompts:** Completely different instruction sets load depending on if you are in the default mode, or if a Subagent is in `Plan`, `Explore`, or `Task` mode.

### Modifying the Source (`tweakcc`)
Because the source logic is known, power users use a tool called **`tweakcc`**. 
This tool allows you to physically patch your local Claude Code installation. You can edit the internal system prompt fragments (e.g., changing Claude's core logic for how it parses code, or altering its safety rails) and recompile the CLI to run your own customized version of the agent!

*Added by AGY study*
