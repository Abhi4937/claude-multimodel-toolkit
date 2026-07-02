#!/usr/bin/env python3
r"""
yt_notes.py - YouTube -> detailed research notes -> Obsidian. No Claude; free/cheap models.

Pipeline:
  transcript (youtube-transcript-api)
  -> optional web research (ddgs, free)
  -> optional section snapshots (yt-dlp low-res + ffmpeg)
  -> notes via chosen LLM(s)  (OpenAI-compatible)
  -> save <title>.<model>.md (+ snapshots) into the Obsidian vault

Models: nvidia (deepseek-v4-pro, FREE) | glm (glm-5.2) | gemini (gemini-3.1-pro-preview)
Compare quality: --models nvidia,glm,gemini  -> one file per model.

Setup: pip install yt-dlp youtube-transcript-api ddgs openai ; ffmpeg on PATH (for --snaps).
Keys (env): NVIDIA_API_KEY, ZAI_KEY, GEMINI_NOTES_KEY (or GEMINI_API_KEY).

Usage:
  python yt_notes.py "https://youtu.be/XXXX" --research --snaps 6 --models nvidia,glm,gemini
  python yt_notes.py "URL"                       # nvidia only, no research/snaps
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

DEFAULT_VAULT = r"C:\dev\trading_concepts\In-Depth Notes\YouTube"

MODELS = {
    "nvidia": {"base": "https://integrate.api.nvidia.com/v1",
               "keys": ["NVIDIA_API_KEY"], "model": "deepseek-ai/deepseek-v4-pro"},
    "glm":    {"base": "https://api.z.ai/api/coding/paas/v4",
               "keys": ["ZAI_KEY"], "model": "glm-5.2"},
    "gemini": {"base": "https://generativelanguage.googleapis.com/v1beta/openai/",
               "keys": ["GEMINI_NOTES_KEY", "GEMINI_API_KEY"], "model": "gemini-3.1-pro-preview"},
}


def log(*a):
    print("[yt_notes]", *a, file=sys.stderr)


def video_id(url):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else url


def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s).strip()
    return re.sub(r"[\s]+", "-", s)[:80] or "video"


# ---------- metadata ----------
def get_meta(url):
    import yt_dlp
    opts = {"quiet": True, "skip_download": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "id": info.get("id"),
        "title": info.get("title", "Untitled"),
        "uploader": info.get("uploader", ""),
        "duration": info.get("duration", 0) or 0,
        "webpage_url": info.get("webpage_url", url),
        "chapters": info.get("chapters") or [],
    }


# ---------- transcript ----------
def get_transcript(vid):
    from youtube_transcript_api import YouTubeTranscriptApi
    try:
        fetched = YouTubeTranscriptApi().fetch(vid)  # v1.x API
        return [{"text": s.text, "start": s.start, "duration": s.duration} for s in fetched]
    except Exception:
        return YouTubeTranscriptApi.get_transcript(vid)  # legacy API


# ---------- web research (free, keyless) ----------
def extract_topics(transcript_text, n=6):
    # crude keyword picks: longest capitalized-ish phrases + frequent words
    words = re.findall(r"[A-Za-z][A-Za-z0-9'-]{3,}", transcript_text)
    freq = {}
    for w in words:
        lw = w.lower()
        if lw in _STOP:
            continue
        freq[lw] = freq.get(lw, 0) + 1
    top = sorted(freq, key=freq.get, reverse=True)[:n]
    return top


_STOP = set("this that with have your from they will what when就 there their about которые which would could into more than then them这 been being your yours また like just really going know think thing things gonna kind actually because able".split())


def research(topics, per=3):
    try:
        from ddgs import DDGS
    except Exception:
        try:
            from duckduckgo_search import DDGS
        except Exception:
            return ""
    out = []
    try:
        with DDGS() as ddg:
            for t in topics:
                out.append(f"### {t}")
                for r in ddg.text(t, max_results=per):
                    out.append(f"- {r.get('title','')}: {r.get('body','')[:300]} ({r.get('href','')})")
    except Exception as e:
        log("research skipped:", e)
        return ""
    return "\n".join(out)


# ---------- snapshots ----------
def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import glob
    hits = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\*FFmpeg*\**\ffmpeg.exe"), recursive=True)
    return hits[0] if hits else None


def snapshots(url, meta, n, outdir):
    if n <= 0:
        return []
    ff = _ffmpeg()
    if not ff:
        log("ffmpeg not found; skipping snapshots")
        return []
    dur = meta["duration"]
    if not dur:
        return []
    # timestamps: chapter starts if available, else evenly spaced
    if meta["chapters"]:
        times = [c.get("start_time", 0) for c in meta["chapters"]][:n]
        labels = [c.get("title", f"ch{i}") for i, c in enumerate(meta["chapters"])][:n]
    else:
        step = dur / (n + 1)
        times = [step * (i + 1) for i in range(n)]
        labels = [f"{int(t//60)}m{int(t%60):02d}s" for t in times]
    os.makedirs(outdir, exist_ok=True)
    import yt_dlp
    vpath = os.path.join(tempfile.gettempdir(), f"ytnotes_{meta['id']}.mp4")
    if not os.path.exists(vpath):
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True,
                                   "format": "worst[ext=mp4]/worst", "outtmpl": vpath}) as ydl:
                ydl.download([url])
        except Exception as e:
            log("video download failed; skipping snapshots:", e)
            return []
    shots = []
    for t, lab in zip(times, labels):
        img = os.path.join(outdir, f"{meta['id']}_{int(t)}s.jpg")
        try:
            subprocess.run([ff, "-y", "-ss", str(int(t)), "-i", vpath, "-frames:v", "1",
                            "-q:v", "3", img], capture_output=True, timeout=60)
            if os.path.exists(img):
                shots.append((lab, img))
        except Exception as e:
            log("frame failed:", e)
    try:
        os.remove(vpath)
    except OSError:
        pass
    return shots


# ---------- LLM ----------
NOTES_SYSTEM = (
    "You are an expert researcher and study-note writer. From the video transcript "
    "(and any web-research context), produce DETAILED markdown study notes - NOT a shallow "
    "summary. Extract and EXPLAIN key concepts, definitions, mechanisms, examples, numbers, "
    "and actionable takeaways. Use clear headings and bullet structure. If web research is "
    "provided, weave it in and end with a '## Further context & sources' section. Be thorough."
)


def call_model(provider, system, user):
    cfg = MODELS[provider]
    key = next((os.environ[k] for k in cfg["keys"] if os.environ.get(k)), None)
    if not key:
        raise RuntimeError(f"{provider}: no API key set ({'/'.join(cfg['keys'])})")
    from openai import OpenAI
    client = OpenAI(base_url=cfg["base"], api_key=key)
    r = client.chat.completions.create(
        model=cfg["model"], temperature=0.3, max_tokens=8000,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return r.choices[0].message.content


def summarize(provider, prompt):
    return call_model(provider, NOTES_SYSTEM, prompt)


def hms(sec):
    sec = int(sec)
    return f"{sec // 3600}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def chunk_snippets(snips, budget):
    """Split transcript snippets into ~budget-char chunks; return (t0, t1, text)."""
    chunks, cur, clen = [], [], 0
    start = snips[0]["start"] if snips else 0
    for s in snips:
        cur.append(s)
        clen += len(s["text"]) + 1
        if clen >= budget:
            end = s["start"] + s.get("duration", 0)
            chunks.append((start, end, " ".join(x["text"] for x in cur)))
            cur, clen, start = [], 0, end
    if cur:
        end = cur[-1]["start"] + cur[-1].get("duration", 0)
        chunks.append((start, end, " ".join(x["text"] for x in cur)))
    return chunks


def summarize_long(provider, meta, snips, research_text, budget=60000):
    chunks = chunk_snippets(snips, budget)
    parts = []
    for i, (t0, t1, text) in enumerate(chunks, 1):
        log(f"  {provider}: part {i}/{len(chunks)} ({hms(t0)}-{hms(t1)})")
        user = (f"This is PART {i} of {len(chunks)} of the video '{meta['title']}', "
                f"covering {hms(t0)}-{hms(t1)}.\n\n## TRANSCRIPT (this part)\n{text}")
        if i == len(chunks) and research_text:
            user += "\n\n## WEB RESEARCH CONTEXT (integrate + add a sources section)\n" + research_text[:20000]
        user += "\n\nWrite DETAILED study notes for THIS part now (headings, concepts, examples, takeaways)."
        parts.append(f"## Part {i} - {hms(t0)} to {hms(t1)}\n\n" + call_model(provider, NOTES_SYSTEM, user))
    return "\n\n".join(parts)


def build_prompt(meta, transcript_text, research_text):
    p = [f"# Video: {meta['title']}\nChannel: {meta['uploader']} | URL: {meta['webpage_url']}\n",
         "## TRANSCRIPT\n" + transcript_text[:120000]]
    if research_text:
        p.append("\n## WEB RESEARCH CONTEXT (integrate this)\n" + research_text[:20000])
    p.append("\nWrite the detailed study notes now.")
    return "\n".join(p)


def write_note(vault, meta, notes, provider, shots):
    os.makedirs(vault, exist_ok=True)
    slug = slugify(meta["title"])
    fname = os.path.join(vault, f"{slug}.{provider}.md")
    lines = [f"# {meta['title']}", "",
             f"- Source: {meta['webpage_url']}", f"- Channel: {meta['uploader']}",
             f"- Notes model: {provider} ({MODELS[provider]['model']})", ""]
    if shots:
        lines.append("## Snapshots")
        for lab, img in shots:
            rel = os.path.relpath(img, vault).replace("\\", "/")
            lines.append(f"**{lab}**\n\n![{lab}]({rel})\n")
    lines.append(notes)
    with open(fname, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return fname


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--models", default="nvidia", help="comma list: nvidia,glm,gemini")
    ap.add_argument("--research", action="store_true", help="add free web-research enrichment")
    ap.add_argument("--snaps", type=int, default=0, help="number of section snapshots (0=off)")
    ap.add_argument("--vault", default=DEFAULT_VAULT)
    args = ap.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip() in MODELS]
    if not models:
        sys.exit("no valid --models (choose from nvidia,glm,gemini)")

    log("fetching metadata + transcript...")
    meta = get_meta(args.url)
    tr = get_transcript(meta["id"] or video_id(args.url))
    ttext = " ".join(s["text"] for s in tr)
    log(f"title='{meta['title']}' transcript={len(ttext)} chars")

    research_text = ""
    if args.research:
        log("web research...")
        research_text = research(extract_topics(ttext))

    shots = []
    if args.snaps > 0:
        log(f"extracting {args.snaps} snapshots...")
        shots = snapshots(args.url, meta, args.snaps, os.path.join(args.vault, "assets"))

    CHUNK_CHARS = 60000
    is_long = len(ttext) > CHUNK_CHARS * 1.3
    prompt = build_prompt(meta, ttext, research_text)
    for prov in models:
        try:
            if is_long:
                log(f"summarizing with {prov} (chunked - {len(ttext)} chars, whole video)...")
                notes = summarize_long(prov, meta, tr, research_text, CHUNK_CHARS)
            else:
                log(f"summarizing with {prov}...")
                notes = summarize(prov, prompt)
            path = write_note(args.vault, meta, notes, prov, shots)
            print(f"WROTE [{prov}] -> {path}")
        except Exception as e:
            print(f"FAILED [{prov}]: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
