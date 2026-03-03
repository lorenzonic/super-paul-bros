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

/* ── canvas wrapper ── */
#pb-wrap { position:fixed; inset:0; bottom:0; display:flex; align-items:center; justify-content:center; background:#000; }
canvas  {
  display:block !important;
  position:static !important;
  inset:auto !important;
  margin:0 !important;
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
/* D-pad on-screen controls */
#pb-dpad {
  display: none;
  position: fixed; bottom: 0; left: 0; right: 0;
  height: 110px; z-index: 8500;
  background: rgba(0,0,0,.45);
  border-top: 1px solid rgba(255,255,255,.08);
  align-items: center;
  pointer-events: none;
}
#pb-dpad.pb-visible { display: flex; }
.pb-btn {
  pointer-events: all;
  width: 78px; height: 78px; border-radius: 50%;
  background: rgba(255,255,255,.15);
  border: 2px solid rgba(255,255,255,.38);
  color: #fff; font-size: 30px;
  display: flex; align-items: center; justify-content: center;
  user-select: none; -webkit-user-select: none;
  margin: 0 10px;
  transition: background .08s;
  cursor: pointer;
}
.pb-btn.pb-pressed { background: rgba(255,255,255,.42); }
#pb-btn-left  { margin-left: 18px; }
#pb-btn-jump  { margin-left: auto; margin-right: 18px;
  background: rgba(80,200,255,.22); border-color: rgba(80,200,255,.6);
  font-size: 26px; }
/* fullscreen button */
#pb-fs-btn {
  position: fixed; bottom: 12px; right: 12px; z-index: 9000;
  width: 38px; height: 38px; border-radius: 8px;
  background: rgba(255,255,255,.15); border: 2px solid rgba(255,255,255,.35);
  color: #fff; font-size: 18px; line-height: 1;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; user-select: none;
  transition: background .2s;
}
#pb-fs-btn:hover { background: rgba(255,255,255,.30); }

/* name input overlay (mobile web) */
#pb-name-overlay {
  display: none;
  position: fixed; inset: 0; z-index: 9600;
  background: rgba(0,8,32,.93);
  flex-direction: column; align-items: center; justify-content: center;
  font-family: 'Arial Black', Arial, sans-serif;
}
#pb-name-overlay.pb-visible { display: flex; }
#pb-name-overlay h2 { color: #FFD700; font-size: 28px; margin-bottom: 8px; text-shadow: 2px 2px #8B0000; }
#pb-name-overlay p  { color: #ccc; font-size: 14px; margin-bottom: 18px; font-family: Arial,sans-serif; }
#pb-name-inp {
  font-size: 24px; padding: 12px 18px; border-radius: 10px;
  border: 3px solid #FFD700; background: #111830; color: #fff;
  width: 270px; text-align: center; outline: none; letter-spacing: 2px;
}
#pb-name-inp::placeholder { color: #555; letter-spacing: 1px; }
#pb-name-ok {
  margin-top: 20px; padding: 14px 50px; font-size: 22px; font-weight: 900;
  background: #27ae60; color: #fff; border: none; border-radius: 12px;
  cursor: pointer; letter-spacing: 1px;
  box-shadow: 0 4px 12px rgba(0,0,0,.5);
}
#pb-name-ok:active { background: #1e8449; }
</style>
"""

# ── JavaScript ───────────────────────────────────────────────────────────────
JS = r"""
<script>
(function () {
  "use strict";
  var GW = 800, GH = 600;

  /* ── fix canvas: 800×600 on desktop, scale-to-fit on mobile ── */
  function fixCanvas() {
    var c = document.querySelector("canvas");
    if (!c) return;
    var dpadH = (isMobile && isMobile()) ? 110 : 0;
    var maxW  = window.innerWidth;
    var maxH  = window.innerHeight - dpadH;
    var scale = Math.min(maxW / GW, maxH / GH);
    if (scale >= 1) scale = 1;   /* never upscale */
    var dw = Math.floor(GW * scale);
    var dh = Math.floor(GH * scale);
    /* push the flexbox wrapper up to leave room for dpad */
    var wrap = document.getElementById("pb-wrap");
    if (wrap) wrap.style.bottom = dpadH + "px";
    c.style.cssText += "; position:static!important; width:" + dw + "px!important; height:" + dh + "px!important; transform:none!important; inset:auto!important; margin:0!important; ";
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

  /* ── name input overlay ── */
  window.__pb_name_done  = false;
  window.__pb_name_value = "Player";
  window.__pb_overlay_active = false;
  window.pbAskName = function () {
    var ov  = document.getElementById("pb-name-overlay");
    var inp = document.getElementById("pb-name-inp");
    if (!ov || !inp) return;
    inp.value = "";
    window.__pb_name_done  = false;
    window.__pb_overlay_active = true;
    ov.classList.add("pb-visible");
    setTimeout(function () { inp.focus(); inp.click(); }, 200);
  };
  function pbSubmitName() {
    var inp = document.getElementById("pb-name-inp");
    var ov  = document.getElementById("pb-name-overlay");
    var val = (inp ? inp.value.trim() : "") || "Player";
    window.__pb_name_value = val.substring(0, 12);
    window.__pb_name_done  = true;
    window.__pb_overlay_active = false;
    if (ov) ov.classList.remove("pb-visible");
  }
  var _nBtn = document.getElementById("pb-name-ok");
  var _nInp = document.getElementById("pb-name-inp");
  if (_nBtn) _nBtn.addEventListener("pointerdown", function (e) { e.stopPropagation(); pbSubmitName(); }, { passive: false });
  if (_nInp) _nInp.addEventListener("pointerdown", function (e) { e.stopPropagation(); }, { passive: false });
  if (_nInp) _nInp.addEventListener("keydown",     function (e) { if (e.key === "Enter") { e.preventDefault(); pbSubmitName(); } });

  function enterFullscreen() {
    /* try multiple targets for cross-browser support */
    var targets = [document.documentElement, document.body, document.querySelector("canvas")];
    for (var i = 0; i < targets.length; i++) {
      var el = targets[i];
      if (!el) continue;
      try {
        if      (el.requestFullscreen)            { el.requestFullscreen(); return; }
        else if (el.webkitRequestFullscreen)      { el.webkitRequestFullscreen(); return; }
        else if (el.mozRequestFullScreen)         { el.mozRequestFullScreen(); return; }
        else if (el.webkitEnterFullscreen)        { el.webkitEnterFullscreen(); return; }
      } catch(e) {}
    }
  }
  function isMobile() {
    return (navigator.maxTouchPoints > 0) || /Mobi|Android/i.test(navigator.userAgent);
  }

  /* button: intercept pointerdown BEFORE the swipe handler so preventDefault
     on the document doesn't swallow the gesture */
  var fsBtn = document.getElementById("pb-fs-btn");
  if (fsBtn) {
    fsBtn.addEventListener("pointerdown", function (e) {
      e.stopPropagation();   /* don't let swipe handler see this touch */
      e.preventDefault();
      enterFullscreen();
      /* visual feedback */
      fsBtn.style.background = "rgba(255,255,255,.55)";
      setTimeout(function () { fsBtn.style.background = ""; }, 300);
    }, { passive: false });
  }

  /* auto fullscreen on first touch (mobile only) – skip if touch was on button */
  var _fsTriggered = false;

  /* ── D-pad on-screen buttons ── */
  if (isMobile()) {
    var dpad = document.getElementById("pb-dpad");
    if (dpad) dpad.classList.add("pb-visible");
    /* move fs button above dpad */
    if (fsBtn) fsBtn.style.bottom = "122px";
  }

  function setupBtn(id, code, key) {
    var btn = document.getElementById(id);
    if (!btn) return;
    btn.addEventListener("pointerdown", function(e) {
      e.stopPropagation(); e.preventDefault();
      btn.classList.add("pb-pressed");
      press(code, key);
    }, { passive: false });
    function up(e) { e.preventDefault(); btn.classList.remove("pb-pressed"); release(code, key); }
    btn.addEventListener("pointerup",     up, { passive: false });
    btn.addEventListener("pointercancel", up, { passive: false });
    btn.addEventListener("pointerleave",  up, { passive: false });
  }
  setupBtn("pb-btn-left",  "ArrowLeft",  "ArrowLeft");
  setupBtn("pb-btn-right", "ArrowRight", "ArrowRight");

  var jumpBtn = document.getElementById("pb-btn-jump");
  if (jumpBtn) {
    jumpBtn.addEventListener("pointerdown", function(e) {
      e.stopPropagation(); e.preventDefault();
      jumpBtn.classList.add("pb-pressed");
      fireKey("keydown", " ", "Space");
      setTimeout(function() { fireKey("keyup", " ", "Space"); jumpBtn.classList.remove("pb-pressed"); }, 500);
    }, { passive: false });
  }

  document.addEventListener("pointerdown", function (e) {
    if (!_fsTriggered && isMobile() && e.target !== fsBtn) {
      _fsTriggered = true;
      enterFullscreen();
    }
  });



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
    /* ignore if touch started on a dpad button, fs button, or name overlay */
    if (e.target && e.target.closest && (e.target.closest("#pb-dpad") || e.target.closest("#pb-fs-btn") || e.target.closest("#pb-name-overlay"))) return;
    if (window.__pb_overlay_active) return;   /* name overlay shown: block game input */
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
      setTimeout(function () { fireKey("keyup", " ", "Space"); }, 500);
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
<div id="pb-dpad">
  <div class="pb-btn" id="pb-btn-left">&#9664;</div>
  <div class="pb-btn" id="pb-btn-right">&#9654;</div>
  <div class="pb-btn" id="pb-btn-jump">&#9650; JUMP</div>
</div>
<div id="pb-fs-btn" title="Fullscreen">&#x26F6;</div>
<div id="pb-name-overlay">
  <h2>Super Paul Bros</h2>
  <p>Enter your name to start</p>
  <input type="text" id="pb-name-inp" maxlength="12" placeholder="Your name..."
         autocomplete="off" autocorrect="off" autocapitalize="words" spellcheck="false">
  <button id="pb-name-ok">PLAY !</button>
</div>
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
