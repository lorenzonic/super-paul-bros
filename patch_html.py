#!/usr/bin/env python3
"""
Post-process the Pygbag build output (build/web/index.html) to add:
  - Instant CSS loading overlay (visible before any JS runs)
  - Mobile viewport + fullscreen meta tags
  - Canvas auto-scale: letterbox in landscape, rotate+scale in portrait
  - Swipe-gesture controller: drag to move, flick up to jump
    (axes auto-corrected for portrait canvas rotation)
"""

import re

TARGET = "build/web/index.html"

# ── CSS ──────────────────────────────────────────────────────────────────────
CSS = """
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="mobile-web-app-capable" content="yes">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  width: 100%; height: 100%; background: #000;
  overflow: hidden; touch-action: none; user-select: none;
}

/* ── loading overlay ── */
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
  text-shadow: 3px 3px #8B0000; letter-spacing: 1px;
}
#pb-loading .pb-sub  { color: #ccc; font: 16px/1.4 Arial,sans-serif; margin-top:10px; }
#pb-loading .pb-spin {
  width:50px; height:50px;
  border:5px solid #333; border-top-color:#FFD700;
  border-radius:50%; animation:pbspin .75s linear infinite; margin-top:24px;
}
@keyframes pbspin { to { transform:rotate(360deg); } }
#pb-loading .pb-bar  { width:min(240px,60vw); height:8px; background:#333; border-radius:4px; margin-top:16px; overflow:hidden; }
#pb-loading .pb-fill { height:100%; background:#FFD700; border-radius:4px; animation:pbfill 20s cubic-bezier(.1,.6,.5,1) forwards; }
@keyframes pbfill { from{width:0} to{width:95%} }

/* ── canvas: fixed 800×600, centered ── */
#pb-wrap { position:fixed; inset:0; display:flex; align-items:center; justify-content:center; background:#000; }
canvas  {
  display:block !important;
  position:static !important;
  inset:auto !important;
  margin:0 !important;
  width:800px !important; height:600px !important;
  transform:none !important;
  image-rendering:pixelated; image-rendering:crisp-edges;
}

/* ── swipe joystick visual feedback ── */
#pb-joystick {
  position: fixed; pointer-events: none; z-index: 8000;
  display: none;
}
#pb-joystick .pb-base {
  position: absolute; transform: translate(-50%,-50%);
  width: 90px; height: 90px; border-radius: 50%;
  border: 3px solid rgba(255,255,255,.35);
  background: rgba(255,255,255,.08);
}
#pb-joystick .pb-knob {
  position: absolute; transform: translate(-50%,-50%);
  width: 44px; height: 44px; border-radius: 50%;
  background: rgba(255,255,255,.45);
  transition: left .04s, top .04s;
}
/* hint labels */
#pb-hint {
  position: fixed; bottom: 14px; left: 50%; transform: translateX(-50%);
  color: rgba(255,255,255,.38); font: 12px/1 Arial,sans-serif;
  pointer-events: none; z-index: 7999; letter-spacing: .5px;
}
</style>
"""

# ── JavaScript ───────────────────────────────────────────────────────────────
JS = r"""
<script>
(function () {
  "use strict";
  var GW = 800, GH = 600;

  /* ── fix canvas to exact 800×600, centered via flexbox parent ── */
  function fixCanvas() {
    var c = document.querySelector("canvas");
    if (!c) return;
    c.style.cssText += "; position:static!important; width:800px!important; height:600px!important; transform:none!important; inset:auto!important; margin:0!important; ";
  }

  /* ── hide loading overlay ── */
  function hideLoading() {
    var el = document.getElementById("pb-loading");
    if (el && !el.classList.contains("pb-hide")) {
      el.classList.add("pb-hide");
      setTimeout(function () { el && el.remove(); }, 500);
    }
  }
  /* Poll until the canvas exists AND has non-zero size (game rendering started) */
  var poll = setInterval(function () {
    var c = document.querySelector("canvas");
    if (c && c.width > 0 && c.height > 0) {
      clearInterval(poll); fixCanvas(); setTimeout(hideLoading, 800);
    }
  }, 200);
  /* Safety: hide loader after 30 s no matter what */
  setTimeout(hideLoading, 30000);

  window.addEventListener("resize", fixCanvas);
  window.addEventListener("orientationchange", function () { setTimeout(fixCanvas, 250); });



  /* ══════════════════════════════════════════════
     SWIPE GESTURE CONTROLLER
     In portrait mode the game canvas is rotated
     90° CW → we swap/negate axes accordingly.
  ══════════════════════════════════════════════ */
  var DEAD   = 22;   /* px dead-zone radius */
  var JUMP_T = 28;   /* px up-swipe threshold to trigger jump */

  var startX = null, startY = null, startTime = 0;
  var active = {};   /* currently held keys */
  var jumpFired = false;

  var joystick = document.getElementById("pb-joystick");
  var jBase    = joystick && joystick.querySelector(".pb-base");
  var jKnob    = joystick && joystick.querySelector(".pb-knob");

  /* convert screen delta → game axes (positive gameX = right, positive gameY = up) */
  function toGame(dx, dy) {
    return { x: dx, y: -dy };
  }

  function fireKey(type, key, code) {
    document.dispatchEvent(
      new KeyboardEvent(type, { key: key, code: code, bubbles: true, cancelable: true })
    );
  }
  function press(code, key) {
    if (!active[code]) { active[code] = true; fireKey("keydown", key, code); }
  }
  function release(code, key) {
    if (active[code]) { delete active[code]; fireKey("keyup", key, code); }
  }
  function releaseAll() {
    release("ArrowLeft",  "ArrowLeft");
    release("ArrowRight", "ArrowRight");
    release("Space",      " ");
    jumpFired = false;
  }

  function showJoystick(cx, cy, kx, ky) {
    if (!joystick) return;
    joystick.style.display = "block";
    jBase.style.left = cx + "px"; jBase.style.top = cy + "px";
    jKnob.style.left = kx + "px"; jKnob.style.top = ky + "px";
  }
  function hideJoystick() {
    if (joystick) joystick.style.display = "none";
  }

  document.addEventListener("pointerdown", function (e) {
    e.preventDefault();
    startX = e.clientX; startY = e.clientY;
    startTime = Date.now();
    jumpFired = false;
    showJoystick(startX, startY, startX, startY);
  }, { passive: false });

  document.addEventListener("pointermove", function (e) {
    if (startX === null) return;
    e.preventDefault();

    var rawDx = e.clientX - startX;
    var rawDy = e.clientY - startY;
    var g = toGame(rawDx, rawDy);   /* game-space delta */

    /* clamp knob to a circle radius of 45px for visual */
    var dist = Math.sqrt(rawDx*rawDx + rawDy*rawDy);
    var clamp = Math.min(dist, 45) / Math.max(dist, 1);
    showJoystick(startX, startY,
                 startX + rawDx * clamp,
                 startY + rawDy * clamp);

    /* ── horizontal movement ── */
    if (g.x > DEAD) {
      release("ArrowLeft", "ArrowLeft");
      press("ArrowRight", "ArrowRight");
    } else if (g.x < -DEAD) {
      release("ArrowRight", "ArrowRight");
      press("ArrowLeft", "ArrowLeft");
    } else {
      release("ArrowLeft", "ArrowLeft");
      release("ArrowRight", "ArrowRight");
    }

    /* ── jump (one-shot on upward flick) ── */
    if (g.y > JUMP_T && !jumpFired) {
      jumpFired = true;
      fireKey("keydown", " ", "Space");
      setTimeout(function () { fireKey("keyup", " ", "Space"); }, 80);
    }
  }, { passive: false });

  document.addEventListener("pointerup", function (e) {
    e.preventDefault();
    var dx = (startX !== null) ? Math.abs(e.clientX - startX) : 99;
    var dy = (startY !== null) ? Math.abs(e.clientY - startY) : 99;
    var dt = Date.now() - startTime;
    /* tap = short duration + tiny movement → fire Enter (advances menus) */
    if (dx < 15 && dy < 15 && dt < 320) {
      fireKey("keydown", "Enter", "Enter");
      setTimeout(function () { fireKey("keyup", "Enter", "Enter"); }, 60);
    }
    startX = null; startY = null; releaseAll(); hideJoystick();
  }, { passive: false });
  document.addEventListener("pointercancel", function (e) { e.preventDefault(); startX = null; startY = null; releaseAll(); hideJoystick(); }, { passive: false });

})();
</script>
"""

# ── HTML elements injected before </body> ────────────────────────────────────
OVERLAY_HTML = """
<div id="pb-loading">
  <div class="pb-title">Super Paul Bros</div>
  <div class="pb-sub">Loading&hellip;</div>
  <div class="pb-spin"></div>
  <div class="pb-bar"><div class="pb-fill"></div></div>
</div>
<div id="pb-joystick">
  <div class="pb-base"></div>
  <div class="pb-knob"></div>
</div>
<div id="pb-hint">&#8592; swipe to move &nbsp;|&nbsp; swipe up to jump &#8593;</div>
"""

# ── patch ────────────────────────────────────────────────────────────────────
with open(TARGET, "r", encoding="utf-8") as f:
    html = f.read()

# Remove any existing Pygbag viewport meta
html = re.sub(r'<meta[^>]*name=["\']viewport["\'][^>]*>', '', html)

# Inject CSS right after <head>
html = html.replace("<head>", "<head>\n" + CSS, 1)

# Inject overlay + JS before </body>
html = html.replace("</body>", OVERLAY_HTML + JS + "\n</body>", 1)

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)

print("✓ Patched", TARGET)
