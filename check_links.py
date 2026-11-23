"""Verify every evidence URL resolves. SSRF-safe: https only, public IPs only,
no redirects to private hosts, small timeout, HEAD then GET fallback, no body kept.

python check_links.py results.json  -> link_check.json (ok / dead / blocked per URL)
Dead links on the page = invented citations. Fix or flag before submitting.

Exit code 0 = all ok, 1 = some dead/blocked.
"""
import concurrent.futures as cf, ipaddress, json, socket, sys, urllib.request
from urllib.parse import urlparse


def public_host(url: str) -> bool:
    """Return True only for https URLs resolving to a public IP."""
    try:
        p = urlparse(url)
        if p.scheme != "https" or not p.hostname or p.username:
            return False
        for _fam, *_, sa in socket.getaddrinfo(p.hostname, 443):
            ip = ipaddress.ip_address(sa[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
    except OSError:
        return False
    return True


class _Guard(urllib.request.HTTPRedirectHandler):
    """Re-check every redirect hop for private-host SSRF."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not public_host(newurl):
            raise urllib.error.URLError(f"redirect to non-public host blocked: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_Guard)

UA = "toolkit-research-linkcheck/1.1 (contact: repo owner)"


def check(url: str) -> tuple[str, str]:
    if not public_host(url):
        return url, "blocked"
    last = "unknown"
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(
                url, method=method,
                headers={"User-Agent": UA},
            )
            with _opener.open(req, timeout=10) as r:
                status = r.status
                return url, "ok" if status < 400 else f"http_{status}"
        except Exception as e:
            last = type(e).__name__
    return url, f"dead:{last}"


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python check_links.py results.json")

    rows = json.load(open(sys.argv[1]))
    urls = sorted({
        u
        for r in rows
        for u in (r.get("final", {}).get("evidence") or [])
        if u
    })
    print(f"Checking {len(urls)} unique evidence URLs …", flush=True)

    with cf.ThreadPoolExecutor(8) as ex:
        res = dict(ex.map(check, urls))

    out_path = "link_check.json"
    with open(out_path, "w") as f:
        json.dump(res, f, indent=1)

    bad = {u: s for u, s in res.items() if s != "ok"}
    print(f"{len(urls) - len(bad)}/{len(urls)} ok  |  {len(bad)} problems")
    if bad:
        for u, s in bad.items():
            print(f"  {s:20s}  {u}")

    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
