#!/usr/bin/env python3
"""Plugin-hub: overzicht van alle Claude Code marketplaces, plugins en repos.

  python hub.py              overzicht per marketplace
  python hub.py web          visuele pagina in de browser, installeren met 1 klik
  python hub.py mine         wat je al hebt
  python hub.py all          alles, gegroepeerd per marketplace
  python hub.py search <q>   zoek op naam/omschrijving/categorie
  python hub.py cat          alle categorieen met aantallen
  python hub.py find <q>     zoek NIEUWE marketplace-repos op GitHub (via gh)
  python hub.py add <repo>   marketplace toevoegen (owner/repo)
  python hub.py translate    omschrijvingen naar het Nederlands vertalen (cache)

Omschrijvingen komen in het Nederlands als ze in translations.json staan; anders
blijven ze Engels. 'web' vult die cache zelf aan bij het opstarten.
"""
import json, os, subprocess, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
PLUGDIR = os.path.join(ROOT, "plugins")
OK, NO, PAUSE = "[x]", "[ ]", "[~]"

def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {} if default is None else default

def state():
    """-> (marketplaces, installed_keys, enabled_keys)"""
    known = load(os.path.join(PLUGDIR, "known_marketplaces.json"))
    installed = set(load(os.path.join(PLUGDIR, "installed_plugins.json")).get("plugins", {}))
    enabled = {k for k, v in load(os.path.join(ROOT, "settings.json")).get("enabledPlugins", {}).items() if v}
    mps = []
    for key, meta in known.items():
        loc = meta.get("installLocation") or os.path.join(PLUGDIR, "marketplaces", key)
        mf = load(os.path.join(loc, ".claude-plugin", "marketplace.json"))
        src = meta.get("source", {})
        mps.append({
            "key": key,
            "loc": loc,
            "repo": src.get("repo") or src.get("url") or src.get("source", "?"),
            "plugins": mf.get("plugins", []),
            "desc": (mf.get("description") or mf.get("metadata", {}).get("description") or "").strip(),
        })
    return mps, installed, enabled

def rel_path(src):
    """'./x' -> 'x'. Let op: str.strip('./') vreet ook de punt van '.claude-plugin'."""
    if src.startswith("./"):
        src = src[2:]
    return src.strip("/")

def source_url(p, m):
    """Web-link naar de plugin-broncode, zo goed als we hem kunnen afleiden."""
    base = "https://github.com/" + m["repo"] if "/" in str(m["repo"]) and "://" not in str(m["repo"]) else str(m["repo"])
    src = p.get("source")
    if isinstance(src, str):
        path = rel_path(src)
        return base + "/tree/HEAD/" + path if path else base
    if isinstance(src, dict):
        kind = src.get("source")
        if kind == "github" and src.get("repo"):
            return "https://github.com/" + src["repo"]
        url = (src.get("url") or "").removesuffix(".git")
        if kind == "git-subdir" and url:
            return url + "/tree/HEAD/" + src.get("path", "").strip("/")
        if url:
            return url
    return base if base.startswith("http") else ""

TRANS = os.path.join(HERE, "translations.json")

def save_trans(cache):
    tmp = TRANS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, sort_keys=True)
    os.replace(tmp, TRANS)

def translate_one(text):
    import urllib.parse, urllib.request
    url = ("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=nl&dt=t&q="
           + urllib.parse.quote(text[:4500]))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return "".join(seg[0] for seg in json.load(r)[0]).strip()

def translate_missing(texts, quiet=False):
    """Vult de vertaalcache aan. Zonder internet val je stil terug op Engels."""
    from concurrent.futures import ThreadPoolExecutor
    cache = load(TRANS)
    todo = sorted({" ".join(t.split()) for t in texts if t and " ".join(t.split()) not in cache})
    if not todo:
        return cache
    if not quiet:
        print("  {} omschrijvingen vertalen naar Nederlands...".format(len(todo)), flush=True)
    done = [0]

    def work(t):
        for _ in range(2):
            try:
                return t, translate_one(t)
            except Exception:
                pass
        return t, None

    with ThreadPoolExecutor(max_workers=5) as pool:
        for src, nl in pool.map(work, todo):
            done[0] += 1
            if nl:
                cache[src] = nl
            if not quiet and done[0] % 50 == 0:
                print("    {}/{}".format(done[0], len(todo)), flush=True)
    save_trans(cache)
    missed = len(todo) - sum(1 for t in todo if t in cache)
    if not quiet:
        print("  klaar{}".format(" ({} niet gelukt, blijven Engels)".format(missed) if missed else ""), flush=True)
    return cache

def nl_of(text, cache):
    return cache.get(" ".join((text or "").split()), text or "")

_CACHE = None

def tr(text):
    """Nederlands als het in de cache staat, anders het origineel."""
    global _CACHE
    if _CACHE is None:
        _CACHE = load(TRANS)
    return nl_of(text, _CACHE)

def local_description(p, m):
    """Marketplaces laten 'description' soms leeg; pak hem dan uit plugin.json zelf."""
    src = p.get("source")
    if not isinstance(src, str):
        return ""
    root = os.path.join(m["loc"], *[s for s in rel_path(src).split("/") if s])
    for cand in (os.path.join(root, ".claude-plugin", "plugin.json"), os.path.join(root, "plugin.json")):
        d = load(cand)
        if d.get("description"):
            return " ".join(str(d["description"]).split())
    return ""

def catalog():
    """Platte lijst van alle plugins uit alle marketplaces, met installatiestatus."""
    mps, installed, enabled = state()
    cache = load(TRANS)
    out = []
    for m in mps:
        for p in m["plugins"]:
            key = p.get("name", "?") + "@" + m["key"]
            en = " ".join((p.get("description") or "").split()) or local_description(p, m)
            out.append({
                "key": key,
                "name": p.get("name", "?"),
                "description": nl_of(en, cache),
                "description_en": en,
                "category": p.get("category") or "",
                "marketplace": m["key"],
                "repo": m["repo"],
                "url": source_url(p, m),
                "installed": key in installed,
                "enabled": key in enabled,
            })
    out.sort(key=lambda x: (not x["installed"], x["marketplace"], x["name"].lower()))
    return out

def mark(key, installed, enabled):
    if key not in installed:
        return NO
    return OK if key in enabled else PAUSE

def clip(s, n):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 3] + "..."

def cmd_overview(mps, installed, enabled):
    print("\nMARKETPLACES  (" + str(len(mps)) + ")\n")
    tot = have = 0
    for m in sorted(mps, key=lambda x: -len(x["plugins"])):
        n = len(m["plugins"])
        mine = sum(1 for p in m["plugins"] if p.get("name", "") + "@" + m["key"] in installed)
        tot += n
        have += mine
        print("  {:<30} {:>4} plugins  {:>3} geinstalleerd   {}".format(m["key"][:30], n, mine, m["repo"]))
        if m["desc"]:
            print("  {:<30} {}".format("", clip(tr(m["desc"]), 90)))
    print("\n  TOTAAL: {} plugins beschikbaar, {} geinstalleerd".format(tot, have))
    print("\n  visueel: python hub.py web   |   zoeken: python hub.py search <woord>")
    print("  wat heb ik: python hub.py mine\n")

def rows(mps, installed, enabled, pred=None):
    for m in mps:
        for p in m["plugins"]:
            key = p.get("name", "?") + "@" + m["key"]
            if pred and not pred(p, key, m):
                continue
            yield m, p, key

def show(rs, installed, enabled, group=True):
    cur = None
    n = 0
    for m, p, key in rs:
        if group and m["key"] != cur:
            cur = m["key"]
            print("\n  -- {} ({})".format(cur, m["repo"]))
        n += 1
        desc = p.get("description") or local_description(p, m)
        print("  {} {:<34} {}".format(mark(key, installed, enabled), clip(p.get("name", "?"), 34),
                                      clip(tr(desc), 78)))
        how = "id: " + key if key in installed else "install: /plugin install " + key
        cat = "[" + p["category"] + "]  " if p.get("category") else ""
        print("      {:<32} {}{}".format("", cat, how))
    print("\n  {} resultaten   {} = geinstalleerd+aan   {} = geinstalleerd maar uit   {} = nog niet\n".format(n, OK, PAUSE, NO))

def cmd_find(query):
    q = " ".join(query) if query else "claude-plugin"
    known_repos = {m["repo"] for m in state()[0]}
    try:
        out = subprocess.run(["gh", "search", "code", "--filename", "marketplace.json", q,
                              "--limit", "60", "--json", "repository"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
    except FileNotFoundError:
        print("  gh (GitHub CLI) niet gevonden.")
        return
    if out.returncode != 0:
        print("  gh fout: " + out.stderr.strip()[:300])
        return
    seen = []
    for it in json.loads(out.stdout or "[]"):
        r = it["repository"]["nameWithOwner"]
        if r not in seen:
            seen.append(r)
    print("\n  NIEUWE marketplace-repos voor '{}':\n".format(q))
    for r in seen:
        if r in known_repos:
            print("  {} {:<45} (heb je al)".format(OK, r))
        else:
            print("  {} {:<45} toevoegen: python hub.py add {}".format(NO, r, r))
    print()

def claude_bin():
    import shutil
    return shutil.which("claude") or shutil.which("claude.exe")

REPO_RE = __import__("re").compile(r"^[A-Za-z0-9._-]{1,60}/[A-Za-z0-9._-]{1,100}$")

def gh_search(query, limit=40):
    """Zoek GitHub-repos die een Claude Code marketplace bevatten. -> lijst dicts."""
    import shutil
    from concurrent.futures import ThreadPoolExecutor
    gh = shutil.which("gh") or shutil.which("gh.exe")
    if not gh:
        return {"error": "GitHub CLI (gh) niet gevonden"}
    try:
        r = subprocess.run([gh, "search", "code", "--filename", "marketplace.json", query,
                            "--limit", str(limit), "--json", "repository"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    except subprocess.TimeoutExpired:
        return {"error": "GitHub-zoekopdracht duurde te lang"}
    if r.returncode != 0:
        return {"error": (r.stderr or "gh gaf een fout").strip()[:300]}
    repos = []
    for it in json.loads(r.stdout or "[]"):
        name = it["repository"]["nameWithOwner"]
        if name not in repos:
            repos.append(name)
    have = {m["repo"] for m in state()[0]}

    def info(name):
        d = {"repo": name, "description": "", "stars": 0, "added": name in have,
             "url": "https://github.com/" + name}
        try:
            o = subprocess.run([gh, "api", "repos/" + name, "--jq",
                                '[.description // "", .stargazers_count] | @tsv'],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            if o.returncode == 0:
                parts = o.stdout.strip().split("\t")
                d["description"] = parts[0] if parts else ""
                d["stars"] = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        except Exception:
            pass
        return d

    with ThreadPoolExecutor(max_workers=8) as pool:
        out = list(pool.map(info, repos[:limit]))
    cache = translate_missing([d["description"] for d in out], quiet=True)
    for d in out:
        d["description_en"] = d["description"]
        d["description"] = nl_of(d["description"], cache)
    out.sort(key=lambda x: (x["added"], -x["stars"]))
    return {"repos": out}

def cmd_add(args):
    if not args:
        print("  gebruik: python hub.py add owner/repo")
        return
    exe = claude_bin()
    if not exe:
        print("  claude CLI niet gevonden in PATH.")
        return
    subprocess.run([exe, "plugin", "marketplace", "add", args[0]])

def cmd_translate(quiet=False):
    """Vertaal alle omschrijvingen die nog niet in de cache staan."""
    global _CACHE
    mps, _, _ = state()
    texts = [m["desc"] for m in mps]
    for m in mps:
        for p in m["plugins"]:
            texts.append(p.get("description") or local_description(p, m))
    _CACHE = translate_missing(texts, quiet=quiet)
    return _CACHE

def cmd_web(args):
    """Lokale pagina op 127.0.0.1 die echt kan installeren."""
    import http.server, secrets, threading, webbrowser
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    port = int(args[0]) if args and args[0].isdigit() else 8777
    token = secrets.token_urlsafe(18)
    page = os.path.join(HERE, "hub.html")

    class H(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _guard(self):
            """Alleen lokaal, alleen met het token van deze sessie."""
            host = (self.headers.get("Host") or "").split(":")[0]
            if host not in ("127.0.0.1", "localhost"):
                self._send(403, json.dumps({"ok": False, "error": "alleen lokaal"}))
                return False
            from urllib.parse import urlparse, parse_qs
            got = parse_qs(urlparse(self.path).query).get("t", [""])[0]
            if not secrets.compare_digest(got, token):
                self._send(403, json.dumps({"ok": False, "error": "verkeerd of ontbrekend token"}))
                return False
            return True

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/":
                try:
                    with open(page, "rb") as f:
                        return self._send(200, f.read(), "text/html; charset=utf-8")
                except OSError:
                    return self._send(500, b"hub.html niet gevonden", "text/plain; charset=utf-8")
            if path == "/api/data":
                if not self._guard():
                    return
                return self._send(200, json.dumps(catalog()))
            if path == "/api/search":
                if not self._guard():
                    return
                from urllib.parse import urlparse, parse_qs
                q = parse_qs(urlparse(self.path).query).get("q", [""])[0].strip()
                if not q:
                    return self._send(400, json.dumps({"error": "geen zoekterm"}))
                print("  GitHub zoeken: " + q)
                return self._send(200, json.dumps(gh_search(q)))
            self._send(404, json.dumps({"ok": False, "error": "onbekend pad"}))

        def do_POST(self):
            path = self.path.split("?")[0]
            if path not in ("/api/install", "/api/addrepo"):
                return self._send(404, json.dumps({"ok": False, "error": "onbekend pad"}))
            if not self._guard():
                return
            try:
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n) or b"{}")
            except Exception:
                return self._send(400, json.dumps({"ok": False, "error": "kapotte aanvraag"}))
            if path == "/api/addrepo":
                return self._addrepo(body.get("repo", ""))
            key = body.get("key", "")
            # whitelist: alleen namen die echt in een van je marketplaces staan
            if key not in {p["key"] for p in catalog()}:
                return self._send(400, json.dumps({"ok": False, "error": "onbekende plugin: " + str(key)[:80]}))
            exe = claude_bin()
            if not exe:
                return self._send(500, json.dumps({"ok": False, "error": "claude CLI niet gevonden"}))
            print("  installeren: " + key)
            try:
                # bewust geen -y: een plugin die een eigen commando wil draaien moet je
                # in de terminal zien en zelf goedkeuren.
                r = subprocess.run([exe, "plugin", "install", key, "-s", "user"],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
            except subprocess.TimeoutExpired:
                return self._send(200, json.dumps({"ok": False, "error": "duurde te lang (>10 min)"}))
            msg = (r.stdout + "\n" + r.stderr).strip()
            print("    " + ("gelukt" if r.returncode == 0 else "mislukt: " + msg[:200]))
            self._send(200, json.dumps({"ok": r.returncode == 0, "error": msg[:1500], "output": msg[:1500]}))

        def _addrepo(self, repo):
            repo = str(repo).strip()
            if not REPO_RE.match(repo):
                return self._send(400, json.dumps({"ok": False, "error": "geen geldige owner/repo"}))
            exe = claude_bin()
            if not exe:
                return self._send(500, json.dumps({"ok": False, "error": "claude CLI niet gevonden"}))
            print("  marketplace toevoegen: " + repo)
            before = len(catalog())
            try:
                r = subprocess.run([exe, "plugin", "marketplace", "add", repo],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
            except subprocess.TimeoutExpired:
                return self._send(200, json.dumps({"ok": False, "error": "duurde te lang (>10 min)"}))
            msg = (r.stdout + "\n" + r.stderr).strip()
            added = len(catalog()) - before
            print("    " + ("gelukt, +{} plugins".format(added) if r.returncode == 0 else "mislukt: " + msg[:200]))
            self._send(200, json.dumps({"ok": r.returncode == 0, "added": added, "error": msg[:1500]}))

    cmd_translate(quiet=False)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), H)
    url = "http://127.0.0.1:{}/?t={}".format(port, token)
    n = len(catalog())
    print("\n  Plugin Hub draait: " + url)
    print("  {} plugins. Stoppen: Ctrl+C. Na installeren: Claude Code herstarten.\n".format(n))
    if "noopen" not in args:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("  gestopt.")
        srv.shutdown()

def main():
    a = sys.argv[1:]
    c = a[0] if a else "overview"
    if c == "find":
        return cmd_find(a[1:])
    if c == "add":
        return cmd_add(a[1:])
    if c in ("web", "serve", "html"):
        return cmd_web(a[1:])
    if c in ("translate", "vertaal"):
        cmd_translate()
        return
    mps, installed, enabled = state()
    if c == "overview":
        cmd_overview(mps, installed, enabled)
    elif c == "mine":
        show(rows(mps, installed, enabled, lambda p, k, m: k in installed), installed, enabled)
    elif c == "all":
        show(rows(mps, installed, enabled), installed, enabled)
    elif c == "cat":
        counts = {}
        for m, p, k in rows(mps, installed, enabled):
            counts[p.get("category", "overig")] = counts.get(p.get("category", "overig"), 0) + 1
        print()
        for name, n in sorted(counts.items(), key=lambda x: -x[1]):
            print("  {:<20} {:>4}    python hub.py search {}".format(name, n, name))
        print()
    elif c == "search":
        q = " ".join(a[1:]).lower()
        if not q:
            print("  gebruik: python hub.py search <woord>")
            return
        def hit(p, k, m):
            d = p.get("description") or local_description(p, m)
            blob = " ".join([str(p.get("name", "")), str(d), tr(d), str(p.get("category", ""))]).lower()
            return q in blob
        show(rows(mps, installed, enabled, hit), installed, enabled)
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
