# Toolkit research agent

Researches 100 apps: auth, self-serve vs gated, API surface, MCP server coverage,
buildability, and evidence URLs. Two-pass pipeline + adversarial verifier +
human stratified sample. Outputs a self-contained `index.html` case study page.

## Setup

```bash
pip install anthropic

cp .env.example .env
# edit .env — add ANTHROPIC_API_KEY at minimum
```

Optional Composio MCP tools: set `COMPOSIO_API_KEY` and `COMPOSIO_MCP_URL`
(read-only least-privilege key only). The pipeline runs fine without them.

## Run

```bash
# 1. Smoke test (5 apps, inspect output by eye)
python agent.py --limit 5 --out smoke.json

# 2. Full run — resumable; ctrl-c and re-run to continue
python agent.py --out results.json

# 3. Dead-link / SSRF-safe evidence check
python check_links.py results.json          # → link_check.json

# 4. Human stratified sample (20 apps, 2 per category, seed=7)
python sample_check.py make                 # → human_check.csv
#   Open docs by hand, fill *_human + human_evidence_url + root_cause columns
python sample_check.py score                # → verification.json

# 5. Build self-contained HTML page
python build.py                             # → index.html
```

Deploy `index.html` + `results.json` to any static host (Vercel, Netlify,
GitHub Pages). No build step needed to view.

## Pipeline

1. **Draft** — web search + fetch official docs → structured JSON row
   (auth, self_serve, api_type, api_breadth, existing_mcp, buildable, evidence, extras).
2. **Verify** — separate adversarial agent re-opens each evidence URL and
   searches for contradicting docs. Marks fields ok / wrong / unverifiable.
3. **Revise** — wrong fields returned to researcher with specific objections (one round).
4. **Flag** — still-disputed or low-confidence rows get `needs_human=true`.
5. **Human** — stratified 20-app sample hand-checked; pass-1 vs final accuracy scored.

## Env vars

| Var | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(required)* | Anthropic API key |
| `MODEL` | `claude-sonnet-4-5` | Model name |
| `MAX_APPS` | `150` | Hard spend cap per run |
| `MAX_SEARCHES` | `8` | Web-search calls per model turn |
| `COMPOSIO_API_KEY` | *(optional)* | Composio read-only key |
| `COMPOSIO_MCP_URL` | *(optional)* | Composio MCP server URL |

## Cost & known limits

- Rough cost: ~\$0.10–0.25 per app at Claude Sonnet prices (search + verify + possible revise).
- Full 100-app run: estimate **\$10–25** and **1–2 hours** at 5 workers.
- JS-heavy or login-walled docs pages may not be fetchable; those apps get
  `confidence=low` and `needs_human=true`.
- Rate limits from Anthropic may slow the run; the agent retries with backoff.
- Never commit `.env`. Rotate any key ever pasted into a chat.

## Security

Agent reads untrusted web pages: read-only tools, output schema-validated,
page HTML-escaped + strict CSP, SSRF-safe link check, secrets via env only.
Full threat model: `SECURITY.md`.
