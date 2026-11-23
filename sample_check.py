"""Human verification harness.

1) python sample_check.py make   -> picks stratified sample (2/category = 20),
   writes human_check.csv. YOU open docs, fill *_human columns with the truth.
2) python sample_check.py score  -> accuracy per field, pass-1 vs final,
   writes verification.json for the HTML page.

Keys scored: auth, self_serve, buildable, existing_mcp.
Pass-1 = raw first draft. Final = after verifier + revise loop.
"""
import csv, json, random, sys
from collections import defaultdict

KEYS = ["auth", "self_serve", "buildable", "existing_mcp"]

ROOT_CAUSE_HINTS = {
    # map field -> likely root causes to remind human reviewer
    "auth":          "stale docs / marketing page vs API page / ambiguous 'trial'",
    "self_serve":    "login-walled portal / paywalled docs / changed pricing tier",
    "buildable":     "partner-only scope / JS-heavy undocumented endpoints",
    "existing_mcp":  "community MCP not indexed / unofficial package",
}


def norm(v):
    """Order-insensitive compare: list or 'a, b' string -> sorted tokens; free text -> first word."""
    if isinstance(v, str) and "," in v:
        v = [t for t in v.replace(" ", "").split(",") if t]
    if isinstance(v, list):
        return ",".join(sorted(str(x).lower().strip() for x in v))
    return str(v).lower().split(" ")[0].strip() if v else ""


def cell(v):
    """Neutralise CSV/Excel formula injection: values come from untrusted web-derived output."""
    v = str(v)
    return "'" + v if v[:1] in ("=", "+", "-", "@", "\t", "\r") else v


def make():
    R = json.load(open("results.json"))
    random.seed(7)   # fixed seed -> reproducible stratified sample
    by = defaultdict(list)
    for r in R:
        by[r["category"]].append(r)

    rows = []
    for cat, rs in by.items():
        for r in random.sample(rs, min(2, len(rs))):
            row = {"id": r["id"], "app": cell(r["app"]), "category": cat}
            for k in KEYS:
                row[f"{k}_pass1"] = cell(json.dumps(r["pass1"].get(k)))
                row[f"{k}_final"] = cell(json.dumps(r["final"].get(k)))
                row[f"{k}_human"] = ""    # YOU fill these
            row["human_evidence_url"] = ""
            row["root_cause"]         = ""   # fill if agent was wrong
            rows.append(row)

    w = csv.DictWriter(
        open("human_check.csv", "w", newline=""),
        fieldnames=list(rows[0]),
    )
    w.writeheader()
    w.writerows(rows)
    print(f"Wrote human_check.csv ({len(rows)} rows).")
    print("Fill *_human columns + human_evidence_url + root_cause for every miss.")
    print(f"\nRoot cause hints per field: {json.dumps(ROOT_CAUSE_HINTS, indent=2)}")


def score():
    rows = [r for r in csv.DictReader(open("human_check.csv")) if r.get("auth_human")]
    if not rows:
        sys.exit("No filled rows in human_check.csv (fill *_human columns first).")

    out = {
        "n":       len(rows),
        "fields":  {},
        "misses":  [],
        "verifier_stats": {},
    }

    for k in KEYS:
        p = f = 0
        for r in rows:
            raw_human = r[f"{k}_human"]
            # human column may be plain text or JSON
            try:
                h_val = json.loads(raw_human) if raw_human.startswith(("[", '"')) else raw_human
            except json.JSONDecodeError:
                h_val = raw_human
            h   = norm(h_val)
            p1  = norm(json.loads(r[f"{k}_pass1"]))
            fin = norm(json.loads(r[f"{k}_final"]))
            p  += (p1  == h)
            f  += (fin == h)
            if fin != h:
                out["misses"].append({
                    "app":        r["app"],
                    "field":      k,
                    "agent":      fin,
                    "truth":      h,
                    "url":        r.get("human_evidence_url", ""),
                    "root_cause": r.get("root_cause", ""),
                })
        out["fields"][k] = {
            "pass1": round(p / len(rows), 3),
            "final": round(f / len(rows), 3),
        }

    # Verifier stats from results.json (if available)
    try:
        R = json.load(open("results.json"))
        caught_total  = sum(r.get("_meta", {}).get("verifier_caught", 0) for r in R)
        human_flagged = sum(1 for r in R if r.get("needs_human"))
        out["verifier_stats"] = {
            "total_apps":         len(R),
            "fields_caught":      caught_total,
            "human_flagged_rows": human_flagged,
        }
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    json.dump(out, open("verification.json", "w"), indent=1)
    print("verification.json written.")
    print(json.dumps(out["fields"], indent=1))
    if out["misses"]:
        print(f"\nMisses ({len(out['misses'])}):")
        for m in out["misses"]:
            print(f"  {m['app']} / {m['field']}: agent={m['agent']} truth={m['truth']}"
                  + (f"  root_cause={m['root_cause']}" if m["root_cause"] else ""))


{
    "make":  make,
    "score": score,
}[sys.argv[1] if len(sys.argv) > 1 else ""]()
