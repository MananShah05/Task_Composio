# Master Prompt: Composio AI Product Ops Take-Home

Paste this whole file into your coding agent (Claude Code, Cursor, etc.). Attach `apps.csv` (the 100 apps).

---

## 0. Role

You are a senior AI product-ops engineer. Build a research pipeline plus a single self-explanatory HTML case study. Accuracy matters more than anything else, then clarity of presentation. Do not fabricate. Every claim needs an evidence URL you actually opened.

## 1. Use case (understand this first)

Composio turns apps into tools that AI agents call (toolkits, MCP servers, agent skills). Before building a toolkit for an app, a product-ops person researches it:

- What auth does it use (OAuth2, API key, Basic, token, other)?
- Can a developer get credentials alone for free or a trial (self-serve), or is it gated (paid plan, admin approval, partnership, contact sales)?
- How big and what shape is the public API (REST, GraphQL, SOAP, none)? Does an MCP server already exist?
- Could it be an agent toolkit today? If not, what is the main blocker?

Doing this by hand for hundreds of apps does not scale. This assignment is a small real version: research 100 apps with an agent, find patterns, and prove the agent is trustworthy. The reviewer reads one page in about two minutes with no narration. The patterns are the headline, not the 100 rows.

Reviewer will check: (a) are findings correct, (b) are patterns insightful, (c) is the agent real and honest about where a human was needed, (d) is verification real, with accuracy rising from a lower first pass to a higher final pass because of the loops, (e) is the page clear to both a human and an agent.

## 2. Inputs

`apps.csv` columns: `id, app, category, hint`. 100 apps across 10 categories: CRM, Support, Comms, Marketing/Ads, Ecommerce, Data/SEO/Scraping, Dev/Infra, Productivity/PM, Finance, AI/Research/Media. Some entries are odd on purpose (open-source CLIs like Sherlock and Mermaid CLI, Telegram, apps with no clear public API, apps named by request like fanbasis, iPayX, Paygent Connect). Odd cases are valid findings: "no public API" or "CLI only, no auth" is a correct answer.

## 3. Fields to capture per app

| Field | Allowed values / format |
|---|---|
| category, one_liner | one line on what the app does |
| auth | list: oauth2, api_key, basic, bearer_token, jwt, other, none |
| auth_notes | flows, scopes, app-review or partner approval, token lifetime |
| self_serve | yes / trial / paid_required / admin_approval / partner_gated / contact_sales / unknown |
| self_serve_notes | how a dev actually gets credentials today |
| api_type | list: rest, graphql, soap, sdk_only, cli, none |
| api_breadth | narrow / medium / broad, with endpoint areas |
| existing_mcp | official / community / none / unknown, plus URL |
| buildable | yes / partial / no |
| blocker | main blocker or "none" (examples: app review, paid tier, no API, partner only, rate limits, per-tenant host, no OAuth for multi-user) |
| evidence | list of docs URLs actually opened |
| confidence | high / medium / low |
| extras ("and more") | add 3 to 4 useful fields: rate limits, webhooks support, sandbox or test mode, pricing needed for API, multi-tenant base URL, SDK languages, last docs update. Pick ones that help a toolkit decision |

Rules: official docs first. Never answer from memory alone. Cite only opened URLs. Unknown is allowed and must lower confidence. A gated app with evidence is a correct finding, not a failure.

## 4. Build the research agent

Use Python and the Anthropic SDK with web search and fetch tools. Use Composio's SDK / MCP for tool access where it fits (spirit of the role); keep it optional so the repo runs without it. Pipeline:

1. **Draft pass.** Per app, researcher agent searches and fetches official docs, returns strict JSON per the schema. Run concurrently (about 5 workers), resumable, retries on errors.
2. **Verifier pass.** A separate adversarial agent, with a different prompt, re-opens each cited URL and searches for contradicting docs. Per field: ok / wrong / unverifiable plus correction and URL.
3. **Revise loop.** Wrong fields go back to the researcher with the objections. One or two rounds.
4. **Flag.** Fields still disputed, or low confidence, set `needs_human = true`.
5. **Optional third check.** Browser-use or a headless browser on pages the fetch tool cannot render (JS-heavy docs, login-walled portals). Record which apps needed it.
6. **Log everything** (pass1, verify1, pass2, verify2, final) so the page can show how accuracy moved.

Keep a per-app log of time, tool calls, and failures. Record apps that defeated the agent (blocked docs, no public docs, contradictory sources). Say so plainly.

## 5. Verification (most important)

- Draw a stratified sample of 20 apps (2 per category, fixed random seed). Mix of easy and odd apps.
- For each, a human opens the real docs and records truth for: auth, self_serve, buildable, existing_mcp, plus blocker.
- Compute accuracy per field for pass 1 (raw first draft) vs final (after verifier + revise + human flags). Report both numbers.
- List every miss: app, field, agent answer, truth, proof URL, and the root cause (stale docs, marketing page vs API docs, paywalled docs, ambiguous terms like "trial", hallucinated URL).
- Report verifier stats: how many wrong fields it caught, false alarms, what it missed.
- Do not tune the numbers. Honest 78% to 91% beats a fake 99%.

## 6. Pattern analysis (the headline)

Cluster and state plainly, with counts:

- Dominant auth method overall and per category. How many are OAuth2 only vs API key only vs both.
- Self-serve vs gated by category. Which categories hide behind approval (Ads APIs, WhatsApp, Amazon SP-API, LinkedIn, Salesforce partner flows, enterprise-only finance data).
- Most common blocker, ranked.
- Easy wins: self-serve + broad API + (ideally) no existing MCP. List them.
- Needs outreach: partner-gated or contact-sales apps. List them.
- No-API or odd cases: CLIs, scrapers, tools with unofficial APIs.
- Where existing MCP servers already cover an app (build vs adopt).
- Recommended build order (tiers: now / needs OAuth app review / needs outreach / skip).
- Three to five surprising findings, one line each.

## 7. Deliverable: one self-contained HTML page

Static, no build step needed to view, works from a deployed link. Sections in this order:

1. **Headline patterns** at top. Big numbers, bars, plain sentences. Readable in 30 seconds.
2. **Findings table.** All 100 rows, sortable and filterable (category, verdict, auth, self-serve), evidence links per row, flag icon on human-checked rows, expandable row detail.
3. **Build-order matrix.** Easy win / needs approval / needs outreach / skip.
4. **The agent.** Diagram of draft, verify, revise, human flow. What it does, what tools it uses, where a human was needed and why, cost and time per app.
5. **Proof.** Link to repo, run command, and ideally a live trigger (small endpoint or a "research one app" demo) so the reviewer can run it on a new app.
6. **Verification.** Sample size, per-field accuracy pass 1 vs final (bar chart), table of hits and misses with root causes, human-check evidence.
7. **Where it failed.** Honest list of apps that defeated the agent and agent weaknesses.
8. **For machines.** Link `results.json` and `llms.txt` or an embedded `<script type="application/json">` so an agent can consume the findings. Clear semantic HTML.

Design: clean, responsive, dark-mode aware, no external dependencies beyond optional system fonts, loads fast, skimmable. Clarity over decoration.

## 8. Repo and README

Repo contains: `apps.csv`, `agent.py`, verifier, `sample_check.py`, `build.py` (embeds JSON into the HTML), `results.json`, `human_check.csv`, `verification.json`, `README.md`. README: setup, env vars, run commands (smoke test with `--limit 5`, full run, sample, score, build), model used, cost, known limits.

## 9. Constraints and honesty

- Use AI tooling freely, but every line must be explainable in the interview. Add short code comments on non-obvious choices.
- If the agent got things wrong or an app defeated it, say so on the page.
- No paid accounts needed. Gated behind payment or partnership with evidence is a valid result.
- Never invent URLs. Verify every evidence link resolves (add a link-check step).
- Target under 8 hours total. Submit early.

## 9b. Security requirements (treat as senior Composio engineer)

- Web content is untrusted. Defend against prompt injection: read-only tools, no write/send tools, prompts say fetched text is data, flag suspected injection and force human review.
- Never trust model output: validate against enum allowlists, cap lengths, strip HTML, keep only https URLs, reject private/localhost/metadata hosts (SSRF).
- Published page: escape all data before rendering, strict CSP, rel=noopener on links, safe JSON embedding in script tag.
- Secrets from env only, never logged or committed; `.env.example`, `.gitignore`; least-privilege read-only Composio key.
- Spend caps, timeouts, atomic writes, CSV formula-injection guard, SECURITY.md with threat model.

## 10. Execution order

1. Smoke test on 5 apps; inspect output by eye; fix prompts.
2. Run all 100; spot-check 10 quickly for obvious errors; fix schema or prompts; re-run only the bad ones.
3. Run verifier + revise loop; save pass1 and final snapshots.
4. Human sample of 20; score; list misses and root causes.
5. Write pattern analysis from the data, not intuition.
6. Build the page; test on mobile width; deploy (Vercel / Netlify / GitHub Pages).
7. Final self-review against the reviewer checklist in section 1. Fix gaps.

Report back with: live URL, repo URL, accuracy numbers (pass 1 vs final), list of human interventions, and top 5 patterns.
