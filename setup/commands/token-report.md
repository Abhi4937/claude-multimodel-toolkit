---
description: Show daily/monthly token cost via ccusage
allowed-tools: Bash(npx:*), Bash(ccusage:*)
---

Run `npx ccusage daily` (it will fetch ccusage on first use). Summarize in <=5 lines:
- today's total cost and token count,
- this month's total,
- the top model by spend.
If ccusage fails to run, say so and suggest `npm i -g ccusage`.
