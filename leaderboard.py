# ============================================================
#  Paul Bros  –  Leaderboard  (online via Supabase)
#
#  Setup (one-time, ~5 minutes):
#  1. Create a FREE project at https://supabase.com
#  2. Open SQL Editor and run:
#       CREATE TABLE leaderboard (
#         id         BIGSERIAL PRIMARY KEY,
#         name       TEXT    NOT NULL DEFAULT 'Player',
#         score      INTEGER NOT NULL DEFAULT 0,
#         created_at TIMESTAMPTZ DEFAULT NOW()
#       );
#       ALTER TABLE leaderboard ENABLE ROW LEVEL SECURITY;
#       CREATE POLICY "public read"
#         ON leaderboard FOR SELECT USING (true);
#       CREATE POLICY "public insert"
#         ON leaderboard FOR INSERT WITH CHECK (true);
#  3. Go to Settings → API, copy:
#       - "Project URL"  → SUPABASE_URL below
#       - "anon public"  → SUPABASE_KEY below
# ============================================================

import json
import os
import asyncio

# ── *** FILL THESE IN *** ──────────────────────────────────────────────────
SUPABASE_URL = "https://uxujadrfuwvsjmaovsix.supabase.co"
SUPABASE_KEY = "sb_publishable_HsDYt3yGvErDzmJLzlpV5A_5XcVCcxQ"
# ──────────────────────────────────────────────────────────────────────────

MAX_ENTRIES  = 30

_configured = (
    not SUPABASE_URL.startswith("https://YOUR_PROJECT") and
    SUPABASE_KEY != "YOUR_ANON_KEY"
)

# ── Detect browser environment ────────────────────────────────────────────
try:
    import platform as _platform
    _WEB = hasattr(_platform, "window")
except Exception:
    _WEB = False

# ── Fallback storage (localStorage / local file) ─────────────────────────
_DIR             = os.path.dirname(os.path.abspath(__file__))
_FALLBACK_FILE   = os.path.join(_DIR, "leaderboard.json")
_FALLBACK_KEY    = "paul_bros_leaderboard"


def _fallback_load() -> list:
    if _WEB:
        try:
            raw = _platform.window.localStorage.getItem(_FALLBACK_KEY)
            return json.loads(raw) if raw else []
        except Exception:
            return []
    if not os.path.exists(_FALLBACK_FILE):
        return []
    try:
        with open(_FALLBACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _fallback_save(board: list):
    if _WEB:
        try:
            _platform.window.localStorage.setItem(_FALLBACK_KEY, json.dumps(board))
        except Exception:
            pass
        return
    try:
        with open(_FALLBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(board, f, ensure_ascii=False, indent=2)
    except Exception:
        pass




# ── HTTP helpers ──────────────────────────────────────────────────────────
_API_HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
}


def _desktop_request(url: str, method: str = "GET", body=None):
    """Blocking HTTP request (desktop only)."""
    import urllib.request
    data = json.dumps(body).encode() if body is not None else None
    req  = urllib.request.Request(url, data=data, method=method)
    for k, v in _API_HEADERS.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read()
            return json.loads(content) if content.strip() else []
    except Exception as e:
        print(f"[leaderboard] request error: {e}")
        return None


async def _web_request(url: str, method: str = "GET", body=None):
    """Async HTTP request via Pygbag's JS fetch bridge."""
    try:
        import platform as _pl
    except Exception:
        return None

    hdrs    = json.dumps(_API_HEADERS)
    body_js = json.dumps(json.dumps(body)) if body is not None else "undefined"

    _pl.window.eval(
        "window.__pb_done=false;window.__pb_res=null;"
        f"fetch({json.dumps(url)},"
        "{" f"method:{json.dumps(method)},headers:{hdrs},body:{body_js}" "})"
        ".then(function(r){{return r.text();}})"
        ".then(function(d){{window.__pb_res=d;window.__pb_done=true;}})"
        ".catch(function(){{window.__pb_res='null';window.__pb_done=true;}});"
    )

    for _ in range(100):          # up to 15 s
        await asyncio.sleep(0.15)
        if _pl.window.eval("!!window.__pb_done"):
            raw = _pl.window.eval("window.__pb_res")
            if not raw or raw == "null":
                return None
            try:
                return json.loads(raw)
            except Exception:
                return []
    print("[leaderboard] fetch timeout")
    return None


def _dedup(rows: list) -> list:
    """Keep only the highest score per player name (case-insensitive)."""
    best = {}
    for row in rows:
        key = row.get("name", "").strip().lower()
        if key not in best or row.get("score", 0) > best[key].get("score", 0):
            best[key] = row
    result = sorted(best.values(), key=lambda r: r.get("score", 0), reverse=True)
    return result[:MAX_ENTRIES]


# ── Public async API ──────────────────────────────────────────────────────

async def fetch_scores() -> list:
    """Return top MAX_ENTRIES unique-player scores from Supabase (or fallback)."""
    if not _configured:
        return _fallback_load()[:MAX_ENTRIES]

    # fetch extra rows so dedup still gives us MAX_ENTRIES
    url = (f"{SUPABASE_URL}/rest/v1/leaderboard"
           f"?select=name,score&order=score.desc&limit=100")

    rows = await _web_request(url) if _WEB else _desktop_request(url)
    if rows is None:
        return _fallback_load()[:MAX_ENTRIES]
    return _dedup(rows)


async def post_score(name: str, score: int) -> list:
    """Insert a new score; return updated top-30 (de-duplicated)."""
    name  = (name.strip() or "Player")[:12]
    body  = {"name": name, "score": int(score)}

    if not _configured:
        board = _fallback_load()
        board.append(body)
        board.sort(key=lambda e: e["score"], reverse=True)
        board = board[:MAX_ENTRIES]
        _fallback_save(board)
        return board

    url = f"{SUPABASE_URL}/rest/v1/leaderboard"
    if _WEB:
        await _web_request(url, method="POST", body=body)
    else:
        _desktop_request(url, method="POST", body=body)

    return await fetch_scores()
