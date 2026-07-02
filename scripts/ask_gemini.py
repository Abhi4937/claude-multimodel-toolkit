#!/usr/bin/env python3
r"""
ask_gemini.py - ask Gemini 3.1 Pro (on Vertex, via Express API key). Stdlib only.

Uses GEMINI_NOTES_KEY (Vertex Express key scoped to aiplatform). Funded by GCP credits,
capped by the billing kill-switch. See knowledge/gemini-vertex-express.md.

Usage:
  gemini "explain gamma exposure in options"
  gemini --file report.md "summarize the key risks"
  type notes.txt | gemini "turn this into bullet points"
  gemini --system "You are a Python expert" "review this diff for bugs" --file diff.txt
"""
import argparse
import json
import os
import sys
import urllib.request

MODEL = "gemini-3.1-pro-preview"
ENDPOINT = "https://aiplatform.googleapis.com/v1/publishers/google/models/{m}:generateContent?key={k}"


def ask(prompt, system, model=MODEL):
    key = os.environ.get("GEMINI_NOTES_KEY")
    if not key:
        sys.exit("GEMINI_NOTES_KEY not set (Vertex Express key). setx GEMINI_NOTES_KEY \"...\"")
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 8000},
    }
    req = urllib.request.Request(ENDPOINT.format(m=model, k=key),
                                data=json.dumps(payload).encode("utf-8"),
                                headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        sys.exit(f"Gemini error {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="*", help="the question/instruction")
    ap.add_argument("--file", action="append", default=[], help="file(s) whose contents to include")
    ap.add_argument("--system", default="You are a helpful, precise expert assistant.")
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()

    prompt = " ".join(args.prompt).strip()
    stdin_text = "" if sys.stdin.isatty() else sys.stdin.read()
    if stdin_text:
        prompt = (prompt + "\n\n" + stdin_text).strip()
    for f in args.file:
        try:
            prompt += f"\n\n--- FILE: {f} ---\n" + open(f, encoding="utf-8", errors="ignore").read()
        except OSError as e:
            sys.exit(f"cannot read {f}: {e}")
    if not prompt:
        sys.exit("no prompt (pass text, --file, or pipe stdin)")

    print(ask(prompt, args.system, args.model))


if __name__ == "__main__":
    main()
