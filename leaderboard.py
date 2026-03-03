# ============================================================
#  Paul Bros  –  Leaderboard
#  Desktop  : saves/loads leaderboard.json in the game folder
#  Browser  : uses window.localStorage via Pygbag's JS bridge
# ============================================================

import json
import os

_DIR              = os.path.dirname(os.path.abspath(__file__))
LEADERBOARD_FILE  = os.path.join(_DIR, "leaderboard.json")
LEADERBOARD_KEY   = "paul_bros_leaderboard"
MAX_ENTRIES       = 10

# ── detect browser environment (Pygbag exposes platform.window) ─
try:
    import platform as _platform
    _localStorage = _platform.window.localStorage
    _WEB = True
except Exception:
    _localStorage = None
    _WEB = False


def _raw_load() -> list:
    if _WEB and _localStorage:
        try:
            raw = _localStorage.getItem(LEADERBOARD_KEY)
            if raw:
                return json.loads(raw)
        except Exception:
            pass
        return []
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def _raw_save(board: list):
    if _WEB and _localStorage:
        try:
            _localStorage.setItem(LEADERBOARD_KEY, json.dumps(board))
        except Exception:
            pass
        return
    try:
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(board, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_leaderboard() -> list:
    """Return top-MAX_ENTRIES entries sorted descending by score."""
    return _raw_load()[:MAX_ENTRIES]


def save_entry(name: str, score: int) -> list:
    """Insert entry, keep top MAX_ENTRIES. Returns updated board."""
    board = _raw_load()
    board.append({"name": (name.strip() or "Player")[:12], "score": int(score)})
    board.sort(key=lambda e: e["score"], reverse=True)
    board = board[:MAX_ENTRIES]
    _raw_save(board)
    return board
