# Gemini 3.1 Pro on Vertex via API key (Express mode) - working recipe

Hard-won. Use this to call Gemini on Vertex with an API KEY (funded by GCP credits,
no AI-Studio rate wall, kill-switch protected). This is the `vertex` model in yt_notes.py.

## The recipe
- **Endpoint (global, Express):**
  `POST https://aiplatform.googleapis.com/v1/publishers/google/models/<model>:generateContent?key=<API_KEY>`
- **Model:** `gemini-3.1-pro-preview`
- **Body = Vertex format** (NOT OpenAI): `{"systemInstruction":{"parts":[{"text":...}]},"contents":[{"role":"user","parts":[{"text":...}]}],"generationConfig":{...}}`
- **Key** must be scoped to **`aiplatform.googleapis.com`** (Agent Platform / Vertex), created in a
  billing-enabled project. Fix restriction: `gcloud services api-keys update <name> --api-target=service=aiplatform.googleapis.com`.

## Gotchas that cost hours
- **AI Studio API key (`generativelanguage`) != Vertex.** The `generativelanguage` endpoint gave
  429 "prepayment credits depleted" (its own billing, credits may not apply). VERTEX is the credit-funded path.
- **Key `API_KEY_SERVICE_BLOCKED` (403)** = key restricted to the wrong API. Point it at `aiplatform`.
- **`role` is required** in `contents` on Vertex (`"Please use a valid role"` 400 if missing).
- **PowerShell `417`** was a client `Expect:100-continue` quirk (`[Net.ServicePointManager]::Expect100Continue=$false`).
  Python `urllib`/`requests` don't have this - so the pipeline works fine.
- Express region here = `asia-southeast1`; older models (2.5-pro) 404 there, but `gemini-3.1-pro-preview` works on the global endpoint.

## Use
`ytnotes "URL" --models nvidia,glm,vertex`   (3-way quality comparison). Key env: `GEMINI_NOTES_KEY`.
Cost: drawn from GCP credits; capped by the `vertex-hard-cap` kill-switch (₹24k).
