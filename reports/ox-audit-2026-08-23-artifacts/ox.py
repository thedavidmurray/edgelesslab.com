#!/usr/bin/env python3.11
"""Ox fan-out audit harness for edgelesslab.com.
Free stealth/ox-alpha via OpenRouter. Stdlib only (no pip deps).
Phases: chunk | find | crawl | refute  (run individually or `all`).
Idempotent: skips cells whose output already exists.
"""
import sys, os, re, json, time, glob, hashlib, threading, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO = "/Users/djm/claude-projects/edgelesslab.com"
WORK = os.path.dirname(os.path.abspath(__file__))
MODEL = "stealth/ox-alpha"
CONC = 20
MAX_CHUNK_CHARS = 200_000
LIVE_BASE = "https://edgelesslab.com"

def load_key():
    with open("/Users/djm/claude-projects/.env") as f:
        for line in f:
            if line.strip().startswith("OPENROUTER_API_KEY="):
                return line.strip().split("=", 1)[1].strip().strip('"\'')
    raise SystemExit("no OPENROUTER_API_KEY")

KEY = load_key()
_print_lock = threading.Lock()
def log(*a):
    with _print_lock:
        print(*a, flush=True)

# ---- rate limiter: Nous/Ox ceiling is 120 req/min; hold 110 for safety margin ----
RATE_PER_MIN = 110
_rl_lock = threading.Lock()
_rl_times = []  # timestamps of recent calls
def rate_gate():
    while True:
        with _rl_lock:
            now = time.time()
            _rl_times[:] = [t for t in _rl_times if now - t < 60]
            if len(_rl_times) < RATE_PER_MIN:
                _rl_times.append(now)
                return
            wait = 60 - (now - _rl_times[0]) + 0.05
        time.sleep(max(wait, 0.1))

# ---------------- Ox call ----------------
def ox(prompt, system=None, max_tokens=4000, timeout=180, retries=3):
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": prompt}]
    body = json.dumps({"model": MODEL, "max_tokens": max_tokens, "messages": msgs}).encode()
    last = None
    for attempt in range(retries):
        try:
            rate_gate()
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions", data=body,
                headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.load(r)
            m = d.get("choices", [{}])[0].get("message", {})
            c = m.get("content") or m.get("reasoning") or ""
            if not c.strip():
                last = "empty content"; time.sleep(2 + attempt * 3); continue
            return c
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, Exception) as e:
            last = f"{type(e).__name__}: {str(e)[:80]}"
            time.sleep(3 + attempt * 5)
    return f"__OXERR__ {last}"

def parse_findings(text):
    """Robustly extract a list of finding dicts from an Ox reply.
    Handles code fences, prose preamble, nested strings, and truncated arrays.
    Uses json.JSONDecoder (string/nesting aware) — NOT naive brace counting."""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    dec = json.JSONDecoder()
    # 1) whole array/object starting at the first bracket
    for i in sorted(x for x in (t.find("["), t.find("{")) if x >= 0):
        try:
            obj, _ = dec.raw_decode(t[i:])
            if isinstance(obj, list): return [o for o in obj if isinstance(o, dict)]
            if isinstance(obj, dict): return [obj]
        except Exception:
            pass
    # 2) salvage: scan for individual complete {...} objects (survives truncation)
    out, idx = [], 0
    while True:
        j = t.find("{", idx)
        if j < 0: break
        try:
            obj, end = dec.raw_decode(t[j:])
            if isinstance(obj, dict): out.append(obj)
            idx = j + end
        except Exception:
            idx = j + 1
    return out

# back-compat alias
def parse_json_block(text):
    return parse_findings(text)

# ---------------- subsystems ----------------
def rel(p): return os.path.relpath(p, REPO)

SUBSYSTEMS = {
    "app-pages":   ["src/app/**/page.tsx", "src/app/**/layout.tsx", "src/app/**/*.tsx"],
    "app-api":     ["src/app/api/**/*.ts", "src/app/api/**/*.tsx", "src/app/**/route.ts"],
    "components":  ["src/components/**/*.tsx", "src/components/**/*.ts"],
    "lib":         ["src/lib/*.ts", "src/lib/*.tsx"],
    "lib-prompt-engine": ["src/lib/prompt-engine/**/*.ts", "src/lib/prompt-engine/**/*.tsx"],
    "lib-knowledge":     ["src/lib/knowledge/**/*.ts"],
    "hooks-types": ["src/hooks/**/*.ts", "src/hooks/**/*.tsx", "src/types/**/*.ts"],
    "workers":     ["workers/**/*.ts", "workers/**/*.js"],
    "scripts":     ["scripts/**/*.mjs", "scripts/**/*.js", "scripts/**/*.ts", "*.mjs"],
    "content":     ["content/**/*.md", "content/**/*.mdx"],
    "blog":        ["blog/**/*.md", "blog/**/*.mdx", "src/app/blog/**/*.mdx"],
    "docs":        ["docs/**/*.md", "DESIGN.md", "README.md", "AGENTS.md"],
    # lockfile BODIES excluded (huge, low-signal); their co-existence is a known finding
    # injected in synthesis. package.json carries the dependency list Ox needs.
    "config":      ["next.config.ts", "package.json", "tsconfig.json", "eslint.config.mjs",
                    "playwright.config.ts", "vitest.config.ts", "postcss.config.mjs",
                    "_headers", "_redirects", "CNAME"],
}

# dimension -> which subsystems it runs against
CODE_SUBS = ["app-pages", "app-api", "components", "lib", "lib-prompt-engine",
             "lib-knowledge", "hooks-types", "workers", "scripts"]
CONTENT_SUBS = ["app-pages", "content", "blog", "docs"]
MATRIX = {
    "correctness":   CODE_SUBS,
    "security":      ["app-pages", "app-api", "components", "lib", "lib-prompt-engine",
                      "lib-knowledge", "workers", "scripts", "config"],
    "performance":   ["app-pages", "components", "lib", "lib-prompt-engine", "workers", "config"],
    "accessibility": ["app-pages", "components"],
    "seo":           ["app-pages", "content", "blog", "config"],
    "content":       CONTENT_SUBS,
    "dependencies":  ["config"],
    "deploy":        ["config", "workers", "scripts"],
}

DIM_PROMPT = {
    "correctness": "logic bugs, broken/missing imports, null/undefined derefs, unhandled promise rejections, incorrect types, off-by-one, dead code paths, race conditions, and anything that would throw or render wrong at runtime",
    "security": "XSS (dangerouslySetInnerHTML, unescaped user input), IDOR/missing authz in API routes, secrets/API keys hardcoded in source, SSRF, injection, unsafe redirects, missing input validation, insecure CSP/headers, and prototype pollution",
    "performance": "oversized client bundles, missing dynamic imports, unoptimized images, blocking data fetches, N+1 patterns, missing memoization causing rerenders, large synchronous work, missing cache headers, and build-time slowness",
    "accessibility": "missing/empty alt text, missing aria labels, non-semantic markup, heading-order violations, low color contrast in inline styles, missing lang, focus traps, non-keyboard-operable controls, and unlabeled form inputs",
    "seo": "missing/duplicate <title>/meta description, missing canonical, missing/incorrect Open Graph & Twitter cards, missing structured data (JSON-LD), robots/noindex mistakes, sitemap inconsistencies, and thin/duplicate metadata",
    "content": "placeholder/lorem/TODO text left in, broken internal links, factual inconsistencies, typos in user-facing copy, inconsistent naming/branding, and stale dates or dead references",
    "dependencies": "outdated or known-vulnerable dependencies, the dual-lockfile hazard (both package-lock.json AND pnpm-lock.yaml present — CI drift risk), unused deps, version mismatches, and risky wildcard version ranges",
    "deploy": "static-export gotchas (next export limitations, API routes that won't work statically), _headers/_redirects/CNAME correctness, caching/security headers, CI config drift, and worker deployment misconfig",
}

SYSTEM = ("You are a rigorous senior code auditor. Report only real, specific, actionable issues. "
          "No vague advice, no praise, no filler. If you find nothing real, return an empty array. "
          "Output ONLY a JSON array. Each element: "
          '{"file":"<repo-relative path or best guess>","line":<int or null>,'
          '"severity":"critical|high|medium|low","title":"<short>","detail":"<what & why>",'
          '"evidence":"<exact snippet or specific reference>","fix":"<concrete fix>"}')

def collect_files(subsystem):
    files = []
    for pat in SUBSYSTEMS[subsystem]:
        for p in glob.glob(os.path.join(REPO, pat), recursive=True):
            if os.path.isfile(p) and p not in files:
                files.append(p)
    return sorted(set(files))

def build_chunks(subsystem):
    """Return list of (chunk_idx, text). Splits if over MAX_CHUNK_CHARS."""
    chunks, cur, cur_len = [], [], 0
    for p in collect_files(subsystem):
        try:
            txt = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if len(txt) > MAX_CHUNK_CHARS:
            txt = txt[:MAX_CHUNK_CHARS] + "\n...[TRUNCATED]..."
        header = f"\n\n===== FILE: {rel(p)} =====\n"
        if cur_len + len(header) + len(txt) > MAX_CHUNK_CHARS and cur:
            chunks.append("".join(cur)); cur, cur_len = [], 0
        cur.append(header + txt); cur_len += len(header) + len(txt)
    if cur:
        chunks.append("".join(cur))
    return chunks

# ---------------- phases ----------------
def phase_chunk():
    manifest = {}
    total_files = 0
    for s in SUBSYSTEMS:
        fs = collect_files(s)
        total_files += len(fs)
        manifest[s] = {"files": len(fs), "chunks": len(build_chunks(s))}
    json.dump(manifest, open(f"{WORK}/manifest.json", "w"), indent=2)
    log("MANIFEST:", json.dumps(manifest, indent=2))
    log("total files across subsystems (dedup within sub):", total_files)

def phase_find():
    cells = []
    for dim, subs in MATRIX.items():
        for s in subs:
            for ci, chunk in enumerate(build_chunks(s)):
                cells.append((dim, s, ci, chunk))
    log(f"phase_find: {len(cells)} finding cells")
    out = f"{WORK}/findings_raw.jsonl"
    done = set()
    if os.path.exists(out):
        for ln in open(out):
            try: done.add(json.loads(ln)["_cell"])
            except: pass
    def work(cell):
        dim, s, ci, chunk = cell
        cid = f"{dim}:{s}:{ci}"
        if cid in done: return (cid, "skip", 0)
        prompt = (f"Audit the following code/content from subsystem '{s}' of a Next.js "
                  f"static-export website for this dimension: {DIM_PROMPT[dim]}.\n\n"
                  f"Return the JSON array now.\n\n{chunk}")
        resp = ox(prompt, system=SYSTEM, max_tokens=8000)
        if resp.startswith("__OXERR__"):
            return (cid, "err:" + resp[:60], 0)
        arr = parse_findings(resp)
        n = 0
        with _print_lock, open(out, "a") as f:
            for it in arr:
                if not isinstance(it, dict): continue
                it["_cell"] = cid; it["dimension"] = dim; it["subsystem"] = s
                it["_id"] = hashlib.md5((cid + str(it.get("title", "")) + str(it.get("file", ""))).encode()).hexdigest()[:10]
                f.write(json.dumps(it) + "\n"); n += 1
        return (cid, "ok", n)
    run_pool(cells, work, "find")

def fetch_url(url, timeout=30):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OxAudit/1.0 (+edgelesslab audit)"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return -1, str(e)[:80]

def phase_crawl():
    sm = open(f"{REPO}/sitemap.xml").read()
    urls = re.findall(r"<loc>(.*?)</loc>", sm)
    log(f"phase_crawl: {len(urls)} urls")
    out = f"{WORK}/crawl.jsonl"
    findings_out = f"{WORK}/findings_live.jsonl"
    done = set()
    if os.path.exists(out):
        for ln in open(out):
            try: done.add(json.loads(ln)["url"])
            except: pass
    def work(url):
        if url in done: return (url, "skip", 0)
        status, html = fetch_url(url)
        # record raw crawl (status + link check happens in synthesis)
        rec = {"url": url, "status": status, "bytes": len(html)}
        with _print_lock, open(out, "a") as f:
            f.write(json.dumps(rec) + "\n")
        if status != 200 or not html:
            return (url, f"status={status}", 0)
        # trim html for Ox: head + first 40k of body
        head = html[:12000]
        body = html[12000:52000]
        prompt = (f"This is the rendered HTML of the live page {url} from edgelesslab.com. "
                  f"Audit it for SEO ({DIM_PROMPT['seo']}) and accessibility ({DIM_PROMPT['accessibility']}). "
                  f"Also flag any visibly broken/placeholder content. Return the JSON array now.\n\n"
                  f"<HEAD+START>\n{head}\n<BODY>\n{body}")
        resp = ox(prompt, system=SYSTEM, max_tokens=6000)
        if resp.startswith("__OXERR__"): return (url, "oxerr", 0)
        arr = parse_findings(resp)
        n = 0
        with _print_lock, open(findings_out, "a") as f:
            for it in arr:
                if not isinstance(it, dict): continue
                it["_cell"] = f"live:{url}"; it["dimension"] = "live-seo-a11y"
                it["subsystem"] = "live"; it["file"] = url
                it["_id"] = hashlib.md5((url + str(it.get("title", ""))).encode()).hexdigest()[:10]
                f.write(json.dumps(it) + "\n"); n += 1
        return (url, "ok", n)
    run_pool(urls, work, "crawl")

def phase_refute():
    raw = []
    for fn in ("findings_raw.jsonl", "findings_live.jsonl"):
        p = f"{WORK}/{fn}"
        if os.path.exists(p):
            for ln in open(p):
                try: raw.append(json.loads(ln))
                except: pass
    # dedup by _id
    seen = {}
    for it in raw:
        seen[it.get("_id")] = it
    findings = list(seen.values())
    log(f"phase_refute: {len(findings)} unique findings")
    out = f"{WORK}/findings_verified.jsonl"
    done = set()
    if os.path.exists(out):
        for ln in open(out):
            try: done.add(json.loads(ln)["_id"])
            except: pass
    sysv = ('You are a skeptical verifier. Given a claimed issue, decide if it is REAL and correctly '
            'described. Be adversarial: default to refuted if the evidence is vague, generic, or likely '
            'a false positive. Output ONLY JSON: {"verdict":"confirmed|refuted|uncertain",'
            '"reason":"<short>","severity_adjusted":"critical|high|medium|low"}')
    def work(it):
        fid = it.get("_id")
        if fid in done: return (fid, "skip", "")
        claim = json.dumps({k: it.get(k) for k in ("dimension","subsystem","file","line","severity","title","detail","evidence","fix")}, ensure_ascii=False)
        prompt = f"Claimed issue:\n{claim}\n\nIs this a real, correctly-described issue? Return the JSON verdict."
        resp = ox(prompt, system=sysv, max_tokens=1500)
        vlist = parse_findings(resp) if not resp.startswith("__OXERR__") else []
        v = vlist[0] if vlist else None
        it["verdict"] = (v or {}).get("verdict", "uncertain")
        it["verify_reason"] = (v or {}).get("reason", resp[:120])
        it["severity_final"] = (v or {}).get("severity_adjusted", it.get("severity", "medium"))
        with _print_lock, open(out, "a") as f:
            f.write(json.dumps(it) + "\n")
        return (fid, it["verdict"], "")
    run_pool(findings, work, "refute")

def run_pool(items, fn, label):
    t0 = time.time(); ok = err = skip = total_findings = 0
    with ThreadPoolExecutor(max_workers=CONC) as ex:
        futs = {ex.submit(fn, it): it for it in items}
        for i, fut in enumerate(as_completed(futs), 1):
            cid, status, n = fut.result()
            if status == "skip": skip += 1
            elif status == "ok": ok += 1; total_findings += n
            else: err += 1
            if i % 5 == 0 or status not in ("ok", "skip"):
                log(f"[{label} {i}/{len(items)}] {cid} -> {status} (+{n}) | ok={ok} err={err} skip={skip} f={total_findings} {time.time()-t0:.0f}s")
    log(f"[{label} DONE] ok={ok} err={err} skip={skip} findings={total_findings} wall={time.time()-t0:.0f}s")

if __name__ == "__main__":
    ph = sys.argv[1] if len(sys.argv) > 1 else "all"
    if ph in ("chunk", "all"): phase_chunk()
    if ph in ("find", "all"): phase_find()
    if ph in ("crawl", "all"): phase_crawl()
    if ph in ("refute", "all"): phase_refute()
    log("PHASE(S) COMPLETE:", ph)
