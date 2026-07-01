#!/usr/bin/env python3
r"""
token_saver_hook.py  -  Claude Code PreToolUse hook (matcher: Read|Bash)

Prevents expensive input from ever entering context. Implements 8 token savers:
  1 media->md      PDF/Office/HTML Read  -> convert once (markitdown), read the .md
  2 big-file guard huge text Read w/o offset/limit -> deny, ask to scope
  3 notebook slim  .ipynb Read -> strip cell OUTPUTS to .slim.md
  3 csv slim       big .csv Read -> header + schema + N rows to .head.md
  4 log redirect   .log / huge .txt Read -> tail+errors slice to .tail.txt
  5 re-read block  same file Read twice this session (unchanged) -> deny
  6 verbose cmd    pytest/npm/build/pip/docker Bash w/o a limiting pipe -> ask to pipe
  7 recursive ls   ls -R / dir /s / find . / tree -> deny, ask to scope
  8 html->md       (folded into #1)

CONTRACT: exit 0 = allow (silent). exit 2 + stderr = block, stderr shown to Claude.
FAIL-OPEN: any error -> allow. Global off: set env TOKENSAVER_OFF=1.
ESCAPE HATCH per file: put "raw" in the path, OR create a sibling "<file>.rawread".
"""
import json
import os
import re
import sys
import time

BIG_FILE_LINES = 1500
CSV_PREVIEW_ROWS = 30
LOG_TAIL_LINES = 200

MEDIA_EXT = {".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".html", ".htm", ".epub"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"}
GENERATED_SUFFIXES = (".md", ".slim.md", ".head.md", ".tail.txt")


def allow():
    sys.exit(0)


def block(msg):
    sys.stderr.write(msg)
    sys.exit(2)


def _mtime(p):
    try:
        return os.path.getmtime(p)
    except OSError:
        return 0


def _fresh(out, src):
    """out exists and is newer than src."""
    return os.path.exists(out) and _mtime(out) >= _mtime(src)


def _has_escape(path):
    if "raw" in os.path.basename(path).lower():
        return True
    if os.path.exists(path + ".rawread"):
        return True
    return False


# ---------- #1 / #8  media + html -> markdown ----------
def convert_media(src):
    out = src + ".md"
    if not _fresh(out, src):
        from markitdown import MarkItDown  # imported lazily; failure -> caller allows
        text = MarkItDown().convert(src).text_content
        with open(out, "w", encoding="utf-8", errors="ignore") as f:
            f.write(text)
    block(
        f"[token-saver] '{os.path.basename(src)}' is heavy to read raw (pages become image tokens).\n"
        f"A markdown version is ready - Read this instead:\n  {out}\n"
        f"If you specifically need the VISUAL (diagram/chart/layout), create '{src}.rawread' "
        f"or put 'raw' in the path, then re-read the original."
    )


# ---------- #3  notebook: strip outputs ----------
def slim_notebook(src):
    out = src + ".slim.md"
    if not _fresh(out, src):
        nb = json.load(open(src, encoding="utf-8", errors="ignore"))
        parts = []
        for i, cell in enumerate(nb.get("cells", [])):
            ctype = cell.get("cell_type", "")
            source = "".join(cell.get("source", []))
            if ctype == "markdown":
                parts.append(source)
            elif ctype == "code":
                parts.append(f"```python\n{source}\n```")  # OUTPUTS dropped
        with open(out, "w", encoding="utf-8", errors="ignore") as f:
            f.write("\n\n".join(parts))
    block(
        f"[token-saver] '{os.path.basename(src)}' is a notebook (cell OUTPUTS bloat context).\n"
        f"A code+markdown-only version is ready - Read this instead:\n  {out}\n"
        f"Need the outputs? create '{src}.rawread' and re-read the original."
    )


# ---------- #3  csv: header + schema + preview ----------
def slim_csv(src):
    # only slim if it's actually big
    try:
        nlines = sum(1 for _ in open(src, encoding="utf-8", errors="ignore"))
    except OSError:
        allow()
    if nlines <= CSV_PREVIEW_ROWS + 5:
        allow()  # small csv, let it through
    out = src + ".head.md"
    if not _fresh(out, src):
        import csv
        with open(src, encoding="utf-8", errors="ignore", newline="") as f:
            rows = []
            reader = csv.reader(f)
            header = next(reader, [])
            for i, r in enumerate(reader):
                if i >= CSV_PREVIEW_ROWS:
                    break
                rows.append(r)
        lines = [
            f"# {os.path.basename(src)} - preview",
            f"- total data rows: {nlines - 1}",
            f"- columns ({len(header)}): {', '.join(header)}",
            "",
            "| " + " | ".join(header) + " |",
            "| " + " | ".join("---" for _ in header) + " |",
        ]
        for r in rows:
            lines.append("| " + " | ".join(r) + " |")
        with open(out, "w", encoding="utf-8", errors="ignore") as f:
            f.write("\n".join(lines))
    block(
        f"[token-saver] '{os.path.basename(src)}' has {nlines-1} rows - reading it all is costly.\n"
        f"Header + schema + first {CSV_PREVIEW_ROWS} rows are ready - Read this instead:\n  {out}\n"
        f"Need the full data? use offset/limit on the original, or create '{src}.rawread'."
    )


# ---------- #4  log / huge text: tail + errors slice ----------
def slim_log(src):
    out = src + ".tail.txt"
    if not _fresh(out, src):
        lines = open(src, encoding="utf-8", errors="ignore").read().splitlines()
        errs = [l for l in lines if re.search(r"error|fail|warn|exception|traceback", l, re.I)]
        tail = lines[-LOG_TAIL_LINES:]
        body = (
            f"# slice of {os.path.basename(src)} ({len(lines)} lines)\n\n"
            f"## error/warn lines ({len(errs)}, capped 200)\n" + "\n".join(errs[:200]) +
            f"\n\n## last {LOG_TAIL_LINES} lines\n" + "\n".join(tail)
        )
        with open(out, "w", encoding="utf-8", errors="ignore") as f:
            f.write(body)
    block(
        f"[token-saver] '{os.path.basename(src)}' is a log - reading it whole floods context.\n"
        f"An error+tail slice is ready - Read this instead:\n  {out}\n"
        f"Need more? Grep the original, or create '{src}.rawread'."
    )


# ---------- #5  re-read blocker (session state) ----------
def read_state_path(session_id):
    d = os.path.join(os.environ.get("TEMP", "/tmp"), "claude_tokensaver")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"reads_{session_id or 'na'}.json")


def check_reread(session_id, path, tool_input):
    if tool_input.get("offset") or tool_input.get("limit"):
        return  # scoped reads may target different slices - don't block those
    sp = read_state_path(session_id)
    try:
        state = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
    except Exception:
        state = {}
    key = os.path.abspath(path)
    mt = _mtime(path)
    prev = state.get(key)
    if prev is not None and abs(prev - mt) < 1e-6:
        block(
            f"[token-saver] '{os.path.basename(path)}' was already read this session and is unchanged - "
            f"it's still in context. Don't re-read; scroll up or Grep it.\n"
            f"If you truly must, create '{path}.rawread'."
        )
    state[key] = mt
    try:
        json.dump(state, open(sp, "w", encoding="utf-8"))
    except Exception:
        pass


# ---------- #2  big-file guard ----------
def big_file_guard(path, tool_input):
    if tool_input.get("offset") or tool_input.get("limit"):
        allow()  # already scoped
    try:
        nlines = sum(1 for _ in open(path, encoding="utf-8", errors="ignore"))
    except OSError:
        allow()
    if nlines > BIG_FILE_LINES:
        block(
            f"[token-saver] '{os.path.basename(path)}' is {nlines} lines - reading it whole is costly.\n"
            f"Scope it: use Read with offset/limit, or Grep/serena find_symbol to jump to the part you need.\n"
            f"If you really need the whole file, create '{path}.rawread' and re-read."
        )


# ---------- #6 / #7  bash guards ----------
def bash_guard(cmd):
    c = cmd.strip()
    # #7 recursive listing
    if re.search(r"\bls\s+-[a-zA-Z]*R", c) or re.search(r"\bdir\b.*/s", c, re.I) \
       or re.search(r"\btree\b", c) or re.search(r"\bfind\s+[^|]*(?<!-name )\-print", c):
        block("[token-saver] Recursive listing can dump thousands of paths. Scope it: a specific dir, "
              "`--maxdepth`, or use the Glob tool. Add nothing to bypass if truly needed.")
    # #6 verbose command without a limiting pipe/quiet flag
    noisy = re.search(r"\b(pytest|jest|npm (run )?(test|build)|yarn (test|build)|"
                      r"pip install|npm install|docker build|terraform (plan|apply)|gradle|mvn)\b", c, re.I)
    already_scoped = re.search(r"(\|\s*(tail|head|grep|rg)\b|>\s|--quiet|\s-q\b|--silent)", c, re.I)
    if noisy and not already_scoped:
        block(f"[token-saver] '{noisy.group(0)}' is verbose and floods context.\n"
              f"Re-run piped, e.g.:  {c} 2>&1 | tail -50   (or | grep -Ei 'error|fail' | tail -40).\n"
              f"Then use /rewind after reading to reclaim tokens.")


def main():
    if os.environ.get("TOKENSAVER_OFF") == "1":
        allow()
    raw = sys.stdin.read()
    data = json.loads(raw) if raw.strip() else {}
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}
    session_id = data.get("session_id", "")

    if tool == "Bash":
        bash_guard(ti.get("command", ""))
        allow()

    if tool != "Read":
        allow()

    path = ti.get("file_path", "")
    if not path or not os.path.exists(path):
        allow()
    low = path.lower()
    if _has_escape(path) or low.endswith(GENERATED_SUFFIXES):
        allow()

    ext = os.path.splitext(low)[1]
    if ext in MEDIA_EXT:
        convert_media(path)
    if ext == ".ipynb":
        slim_notebook(path)
    if ext == ".csv":
        slim_csv(path)
    if ext == ".log":
        slim_log(path)
    if ext in IMAGE_EXT:
        allow()  # keep vision by default (fidelity); convert manually if wanted

    # plain text / code: re-read blocker then big-file guard
    check_reread(session_id, path, ti)
    big_file_guard(path, ti)
    allow()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # FAIL OPEN - never wedge the session
        sys.exit(0)
