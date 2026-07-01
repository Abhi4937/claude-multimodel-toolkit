# The Ultimate Guide to Claude Code CLI Commands
**Focus:** Command Mechanics, Token Optimization, and Context Management

In Claude Code, every command you type natively (the slash commands) has a direct impact on your context window and your wallet. Understanding exactly what these commands do under the hood is the difference between spending $1 and $10 on the same coding session.

Here is the comprehensive breakdown of the top Claude Code commands, when to use them, and how they impact your token burn.

---

## 1. `/clear` (The MVP of Cost Savings)
**What it does:** Completely wipes your current conversation history array (the User -> Assistant -> Tool_Result loop).
**When to use it:** 
- Between every unrelated task.
- Immediately after finishing a massive feature.
- When Claude gets confused or stuck in a loop.

**How it saves tokens:** It resets your context window to zero. By dropping all the historical baggage, your next prompt only pays for the static System Prefix. If you do not use `/clear`, every new prompt you send forces you to pay for Claude to re-read everything you’ve talked about in the last two hours.

---

## 2. `/rewind` (The Pro's Undo Button)
**What it does:** Truncates the conversation history back by a few turns. (e.g., "Forget the last 3 things we talked about.")
**When to use it:** 
- When Claude makes a mistake and you want to try a different approach.
- When a tool (like bash) outputs a massive error log that you realize you didn't need.

**How it saves tokens (The Cache Saver):** Prompt Caching relies on **prefix matching**. Because `/rewind` only chops off the *end* of the conversation, the beginning (the prefix) remains perfectly intact. This means your next prompt gets a 90% cache discount. *Always use `/rewind` instead of typing "No that's wrong, try again."*

---

## 3. `/compact` (The Last Resort)
**What it does:** Pauses the session, asks the LLM to write a dense summary of everything discussed so far, and replaces the massive conversation history array with that single summary string.
**When to use it:** 
- **ONLY** when your context window is at 80%+ capacity and you absolutely cannot use `/clear` because you still need the historical context of the task.

**The Danger / Token Impact:** `/compact` is destructive. Because it replaces the middle of your payload with a new summary, it completely destroys the Prompt Cache prefix. Your next prompt will be billed as a 100% full-price, uncached read. Furthermore, if you compact multiple times, you get a "summary of a summary," which leads to severe AI hallucinations.

---

## 4. `/context`
**What it does:** Provides a visual breakdown of exactly what is eating your token window right now.
**When to use it:** 
- Whenever a session starts feeling sluggish.
- To diagnose if a rogue file read or a massive bash log (a "Tool Spill") is secretly hoarding your tokens.

**How it saves tokens:** It doesn't save tokens directly, but it gives you observability. If `/context` shows that a 50,000-line test output is in your window, you immediately know you need to `/rewind` to get rid of it.

---

## 5. `/usage`
**What it does:** Displays your session's input/output token burn, your total monetary expense, and your rolling Anthropic API limits.
**When to use it:** 
- At the end of a session to track your expenses.
- If you are on the $20/month Pro tier and want to check how close you are to your rate limit.

---

## 6. `/mcp`
**What it does:** Manages your Model Context Protocol (MCP) servers (e.g., attaching a local PostgreSQL database or a GitHub integration).
**When to use it:** 
- When you need Claude to access external APIs or databases.

**The Cache Warning:** Claude dynamically injects "MCP Stubs" (the names and descriptions of active tools) into the System Prefix. If you use `/mcp add` or `/mcp remove` mid-session, you are altering the System Prefix. This instantly destroys your prompt cache. **Best Practice:** Setup your MCPs at the very beginning of the session and do not touch them.

---

## 7. `/model`
**What it does:** Switches the LLM you are currently talking to (e.g., moving from Claude 3.5 Sonnet to Claude 3.7 Opus).
**When to use it:** 
- Start with a fast/cheap model for basic boilerplate, and switch to a heavy reasoning model for architecture.

**The Cache Warning:** Switching models completely invalidates the prompt cache on Anthropic's backend. Try to avoid switching back and forth frequently.

---

## 8. `/resume`
**What it does:** Opens a previous session from the local disk history.
**When to use it:** 
- When you want to pick up a project exactly where you left off yesterday.

**The Cache Warning:** Anthropic's prompt cache has a Time-To-Live (TTL) of exactly 5 minutes (or 1 hour on specific enterprise settings). If you `/resume` a session from yesterday, the cache is long gone. Your first prompt in the resumed session will be a massive, full-priced read of the entire historical context.

---

## Summary Checklist for Maximum Token Efficiency
1. **Never switch models mid-task.**
2. **Use `/clear` relentlessly** between tasks.
3. **Use `/rewind`** when Claude makes a mistake instead of scolding it.
4. **Avoid `/compact`** unless you are maxing out the context window.
5. **Use `/context`** to hunt down and eliminate massive bash logs.

*Added by AGY study*
