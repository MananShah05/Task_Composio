"""Embed results.json + verification.json + link_check.json into template.html -> index.html.

Security: data is untrusted (derived from web content). Escape every '<', '>',
'&' and the JS line separators so the JSON can never close the <script> tag or
break out of the literal. The page also HTML-escapes at render time.

Usage:
  python build.py                 # builds index.html from results.json + verification.json
  python build.py --no-links      # skip link_check.json (if not yet run)
"""
import argparse, json, os, sys

PLACEHOLDER = "/*DATA*/null"


def js_safe(obj):
    """JSON-encode and escape chars that could break an inline <script> block."""
    s = json.dumps(obj, ensure_ascii=True)   # ensure_ascii kills U+2028/2029 too
    return (s
            .replace("<",  r"\u003c")
            .replace(">",  r"\u003e")
            .replace("&",  r"\u0026"))


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    print(f"  (no {path}, using default)", file=sys.stderr)
    return default


def main():
    ap = argparse.ArgumentParser(description="Embed JSON data into the HTML template")
    ap.add_argument("--template",   default="template.html")
    ap.add_argument("--out",        default="index.html")
    ap.add_argument("--results",    default="results.json")
    ap.add_argument("--verify",     default="verification.json")
    ap.add_argument("--links",      default="link_check.json")
    ap.add_argument("--no-links",   action="store_true")
    args = ap.parse_args()

    with open(args.template) as f:
        t = f.read()

    if t.count(PLACEHOLDER) != 1:
        sys.exit(f"ERROR: template placeholder '{PLACEHOLDER}' missing or duplicated.")

    results    = load_json(args.results, [])
    verify     = load_json(args.verify,  None)
    link_check = None if args.no_links else load_json(args.links, None)

    payload = {
        "results":    results,
        "verification": verify,
        "link_check": link_check,
    }

    out_html = t.replace(PLACEHOLDER, js_safe(payload))
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(out_html)

    n_apps  = len(results)
    n_human = sum(1 for r in results if r.get("needs_human"))
    n_mcp   = sum(1 for r in results
                  if r.get("final", {}).get("existing_mcp", "").lower()
                  not in ("none", "unknown", ""))
    print(f"index.html built: {n_apps} apps, {n_human} human-flagged, {n_mcp} with MCP.")


if __name__ == "__main__":
    main()
