#!/usr/bin/env python3
"""
Post-process the Pygbag build output (build/web/index.html) to add:
  - Instant CSS loading overlay (visible before any JS runs)
  - Mobile viewport + fullscreen meta tags
  - Canvas auto-scale: letterbox in landscape, rotate+scale in portrait
  - Large HTML touch buttons (overlay divs) that dispatch keyboard events
    so they work at any canvas scale / orientation
"""

import re

TARGET = "build/web/index.html"

# ── CSS injected into <head> ─────────────────────────────────────────────────
CSS = """
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="mobile-web-app-capable" content="yes">
<style>
/* ── reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  width: 100%; height: 100%; background: #000;
  overflow: hidden; touch-action: none; user-select: none;
}

/* ── loading overlay (pure-CSS spinner, visible before any JS) ── */
#pb-loading {
  position: fixed; inset: 0; z-index: 9999;
  background: #1a1a2e;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  transition: opacity .45s ease;
}
#pb-loading.pb-hide { opacity: 0; pointer-events: none; }
#pb-loading .pb-title {
  color: #FFD700;
  font: 900 clamp(20px,8vw,46px)/1 'Arial Black', Arial, sans-serif;
  text-shadow: 3px 3px #8B0000;
  letter-spacing: 1px;
}
#pb-loading .pb-sub {
  color: #ccc; font: 16px/1.4 Arial, sans-serif; margin-top: 10px;
}
#pb-loading .pb-spin {
  width: 50px; height: 50px;
  border: 5px solid #333; border-top-color: #FFD700;
  border-radius: 50%;
  animation: pbspin .75s linear infinite;
  margin-top: 24px;
}
@keyframes pbspin { to { transform: rotate(360deg); } }
#pb-loading .pb-bar {
  width: min(240px, 60vw); height: 8px;
  background: #333; border-radius: 4px;
  margin-top: 16px; overflow: hidden;
}
#pb-loading .pb-fill {
  height: 100%; background: #FFD700; border-radius: 4px;
  animation: pbfill 7s cubic-bezier(.1,.6,.5,1) forwards;
}
@keyframes pbfill { from { width: 0; } to { width: 90%; } }

/* ── canvas wrapper ── */
#pb-wrap {
  position: fixed; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: #000;
}
canvas {
  display: block !important;
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  transform-origin: center center;
}

/* ── HTML touch buttons (portrait + landscape) ── */
.pb-btn {
  position: fixed;
  width: 72px; height: 72px;
  border-radius: 50%;
  border: 3px solid rgba(255,255,255,.4);
  background: rgba(200,200,200,.22);
  display: flex; align-items: center; justify-content: center;
  font-size: 28px; color: rgba(30,30,30,.9);
  cursor: pointer; z-index: 8000;
  -webkit-tap-highlight-color: transparent;
  transition: background .1s;
}
.pb-btn:active, .pb-btn.pb-active { background: rgba(255,255,255,.45); }

/* landscape positions */
#pb-left  { bottom: 24px; left:  22px; }
#pb-right { bottom: 24px; left: 106px; }
#pb-jump  { bottom: 24px; right: 22px; }

/* portrait: shift to lower-left / lower-right of the *screen* */
@media (orientation: portrait) {
  #pb-left  { bottom: 32px; left:  18px; }
  #pb-right { bottom: 32px; left: 104px; }
  #pb-jump  { bottom: 32px; right: 18px; }
}
</style>
"""

# ── JavaScript injected before </body> ───────────────────────────────────────
JS = r"""
<script>
(function () {
  "use strict";
  var GW = 800, GH = 600;          /* game canvas resolution */

  /* ── canvas scale ── */
  function scaleCanvas() {
    var c = document.querySelector("canvas");
    if (!c) return;
    var sw = window.innerWidth, sh = window.innerHeight;
    var portrait = sw < sh;
    var s, tx, ty;
    if (portrait) {
      /* rotate 90° so landscape game fills portrait screen */
      s  = Math.min(sh / GW, sw / GH);
      tx = (sw - GH * s) / 2;   /* horizontal centering after rotation */
      ty = (sh - GW * s) / 2;   /* vertical  centering after rotation */
      c.style.width  = GW + "px";
      c.style.height = GH + "px";
      /* translate to center, rotate, then scale */
      c.style.transform =
        "translate(" + (sw/2 - GW/2) + "px," + (sh/2 - GH/2) + "px)" +
        " rotate(90deg)" +
        " scale(" + s + ")";
    } else {
      s  = Math.min(sw / GW, sh / GH);
      tx = (sw - GW * s) / 2;
      ty = (sh - GH * s) / 2;
      c.style.width  = GW + "px";
      c.style.height = GH + "px";
      c.style.transform =
        "translate(" + tx + "px," + ty + "px) scale(" + s + ")";
    }
  }

  /* ── hide loading overlay ── */
  function hideLoading() {
    var el = document.getElementById("pb-loading");
    if (el && !el.classList.contains("pb-hide")) {
      el.classList.add("pb-hide");
      setTimeout(function () { el && el.remove(); }, 500);
    }
  }

  /* poll until canvas appears, then scale + hide loader */
  var poll = setInterval(function () {
    if (document.querySelector("canvas")) {
      clearInterval(poll);
      scaleCanvas();
      setTimeout(hideLoading, 350);
    }
  }, 150);

  window.addEventListener("resize", scaleCanvas);
  window.addEventListener("orientationchange", function () {
    setTimeout(scaleCanvas, 250);
  });

  /* ── fullscreen on first tap ── */
  document.addEventListener("pointerdown", function () {
    var el = document.documentElement;
    (el.requestFullscreen || el.webkitRequestFullscreen ||
     el.mozRequestFullScreen || function(){}).call(el);
  }, { once: true });

  /* ── HTML touch buttons → keyboard events ── */
  var BTNS = [
    { id: "pb-left",  label: "◀", key: "ArrowLeft",  code: "ArrowLeft"  },
    { id: "pb-right", label: "▶", key: "ArrowRight", code: "ArrowRight" },
    { id: "pb-jump",  label: "▲", key: " ",          code: "Space"      }
  ];

  function fireKey(type, key, code) {
    document.dispatchEvent(new KeyboardEvent(type,
      { key: key, code: code, bubbles: true, cancelable: true }));
  }

  BTNS.forEach(function (cfg) {
    var el = document.getElementById(cfg.id);
    if (!el) return;

    el.addEventListener("pointerdown", function (e) {
      e.preventDefault();
      el.classList.add("pb-active");
      fireKey("keydown", cfg.key, cfg.code);
    });
    el.addEventListener("pointerup",   function (e) {
      e.preventDefault();
      el.classList.remove("pb-active");
      fireKey("keyup", cfg.key, cfg.code);
    });
    el.addEventListener("pointerleave", function (e) {
      if (el.classList.contains("pb-active")) {
        el.classList.remove("pb-active");
        fireKey("keyup", cfg.key, cfg.code);
      }
    });
    el.addEventListener("touchstart", function(e){ e.preventDefault(); }, { passive: false });
  });

})();
</script>
"""

# ── HTML buttons (injected as siblings of the canvas) ────────────────────────
BTNS_HTML = """
<div id="pb-left"  class="pb-btn">◀</div>
<div id="pb-right" class="pb-btn">▶</div>
<div id="pb-jump"  class="pb-btn">▲</div>
"""

LOADING_HTML = """
<div id="pb-loading">
  <div class="pb-title">🍄 Super Paul Bros</div>
  <div class="pb-sub">Caricamento in corso…</div>
  <div class="pb-spin"></div>
  <div class="pb-bar"><div class="pb-fill"></div></div>
</div>
"""

# ── patch ────────────────────────────────────────────────────────────────────
with open(TARGET, "r", encoding="utf-8") as f:
    html = f.read()

# Remove Pygbag's own viewport meta if present to avoid duplicates
html = re.sub(r'<meta[^>]*name=["\']viewport["\'][^>]*>', '', html)

# Inject CSS + meta right after <head>
html = html.replace("<head>", "<head>\n" + CSS, 1)

# Inject loading overlay + buttons before </body>
html = html.replace("</body>", LOADING_HTML + BTNS_HTML + JS + "\n</body>", 1)

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)

print("✓ Patched", TARGET)
