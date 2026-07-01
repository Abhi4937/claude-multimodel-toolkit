#!/usr/bin/env python3
r"""
nv_batch.py - Free NVIDIA (NIM) chore worker for tier-0/1 mechanical transforms.

Sends each input file (+ one instruction) to an NVIDIA-hosted open model and writes
the model's output back. Use for zero-judgment work: reformat, rename, convert,
scaffold, strip boilerplate. NOT for anything risk-critical (that stays on Opus).

Setup (one-time):
    1) Get a free key at https://build.nvidia.com  ->  set it:
         setx NVIDIA_API_KEY "nvapi-..."      (restart shell after)
    2) pip install openai

Usage:
    # transform files in place (writes <file>.out next to each, unless --inplace)
    python nv_batch.py -i "Convert this file's comments to Google style" file1.py file2.py

    # pick a model (default deepseek-v3; use qwen coder for code):
    python nv_batch.py --model qwen/qwen2.5-coder-32b-instruct -i "Add type hints" app.py

    # dry-run (print to stdout, don't write):
    python nv_batch.py -i "Summarize" notes.md --stdout

    # read the instruction from a hub task note's "## Change" section:
    python nv_batch.py --from-task C:\dev\_hub\tasks\2026-07-02-rename.md file1.py

Models worth knowing (all free on NIM):
    deepseek-ai/deepseek-v3               (default, strong general)
    qwen/qwen2.5-coder-32b-instruct       (code transforms)
    meta/llama-3.3-70b-instruct           (general)
    nvidia/llama-3.1-nemotron-70b-instruct
"""
import argparse
import os
import sys
from pathlib import Path

BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "deepseek-ai/deepseek-v4-pro"  # newer; falls to deepseek-v3 if unavailable


def get_client():
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("openai not installed. Run: pip install openai")
    key = os.environ.get("NVIDIA_API_KEY")
    if not key:
        sys.exit("NVIDIA_API_KEY not set. Run: setx NVIDIA_API_KEY \"nvapi-...\" then restart shell.")
    return OpenAI(base_url=BASE_URL, api_key=key)


def instruction_from_task(task_path: str) -> str:
    """Extract the '## Change' section from a hub task note."""
    text = Path(task_path).read_text(encoding="utf-8")
    lines = text.splitlines()
    out, grab = [], False
    for ln in lines:
        if ln.strip().lower().startswith("## change"):
            grab = True
            continue
        if grab and ln.startswith("## "):
            break
        if grab:
            out.append(ln)
    result = "\n".join(out).strip()
    if not result:
        sys.exit(f"No '## Change' section found in {task_path}")
    return result


def transform(client, model, instruction, content):
    resp = client.chat.completions.create(
        model=model,
        temperature=0.1,
        messages=[
            {"role": "system", "content":
                "You are a precise code/text transformer. Apply the user's instruction to the "
                "provided file content. Return ONLY the transformed file content, no explanations, "
                "no markdown fences."},
            {"role": "user", "content": f"INSTRUCTION:\n{instruction}\n\nFILE CONTENT:\n{content}"},
        ],
    )
    return resp.choices[0].message.content


def main():
    ap = argparse.ArgumentParser(description="Free NVIDIA chore worker.")
    ap.add_argument("files", nargs="+", help="files to transform")
    ap.add_argument("-i", "--instruction", help="transform instruction")
    ap.add_argument("--from-task", help="read instruction from a hub task note's ## Change section")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"NIM model id (default {DEFAULT_MODEL})")
    ap.add_argument("--inplace", action="store_true", help="overwrite the original file")
    ap.add_argument("--stdout", action="store_true", help="print result, do not write")
    args = ap.parse_args()

    if args.from_task:
        instruction = instruction_from_task(args.from_task)
    elif args.instruction:
        instruction = args.instruction
    else:
        sys.exit("Provide -i/--instruction or --from-task.")

    client = get_client()
    for f in args.files:
        p = Path(f)
        if not p.is_file():
            print(f"skip (not a file): {f}", file=sys.stderr)
            continue
        content = p.read_text(encoding="utf-8")
        print(f"[nv:{args.model}] {f} ...", file=sys.stderr)
        result = transform(client, args.model, instruction, content)
        if args.stdout:
            print(result)
        else:
            out = p if args.inplace else p.with_suffix(p.suffix + ".out")
            out.write_text(result, encoding="utf-8")
            print(f"  -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
