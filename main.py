#!/usr/bin/env python3
# ============================================================
#  Paul Bros  –  Main entry point & game loop
#
#  Run:  python main.py
#  Requires: pygame  (pip install pygame)
#
#  Controls:
#    A / LEFT   – move left
#    D / RIGHT  – move right
#    SPACE / UP / W  – jump
#    ESC – quit / back to menu
# ============================================================

import os
import sys
import math
import asyncio
import pygame
import random

from settings    import *
from sprites     import (Player, Goomba, GroundTile, BrickTile, QuestionBlock,
                         PipeTile, Coin, Kostas, FlagPole, Cloud, ScorePopup,
                         OrchideeA2Popup, StarBlock, Star, BrickDebris, draw_text)
from level_data  import (LEVEL_1, LEVEL_2, LEVEL_3, CLOUDS_L2, CLOUDS_L3,
                         PLAYER_START, CLOUDS)
from leaderboard import fetch_scores, post_score

# ── Web (Pygbag) detection ───────────────────────────────
try:
    import platform as _pl
    _WEB = hasattr(_pl, "window")
except Exception:
    _WEB = False


# ── State constants ──────────────────────────────
STATE_MENU        = "menu"
STATE_NAME_INPUT  = "name_input"
STATE_PLAYING     = "playing"
STATE_DEAD        = "dead"
STATE_GAMEOVER    = "gameover"
STATE_WIN         = "win"
STATE_LEADERBOARD = "leaderboard"
STATE_SAVING      = "saving"
STATE_TRANSITION  = "transition"   # level 1 → level 2 cinematic


# ── Camera ──────────────────────────────────────────────────
class Camera:
    """Horizontal-scroll camera with smooth lerp."""

    def __init__(self, level_pixel_width):
        self.x           = 0.0
        self._level_w    = level_pixel_width
        self._smooth     = 0.08   # lerp factor (lower = smoother)

    def update(self, player_rect):
        # keep player at ~1/3 from the left of screen
        desired = player_rect.centerx - SCREEN_WIDTH // 3
        desired = max(0, min(desired, self._level_w - SCREEN_WIDTH))
        # smooth interpolation
        self.x += (desired - self.x) * self._smooth
        # snap if very close
        if abs(self.x - desired) < 0.5:
            self.x = desired

    def apply(self, rect):
        """Return a shifted rect for drawing."""
        return rect.move(-int(self.x), 0)

    def apply_xy(self, x, y):
        return x - int(self.x), y


# ── Touch / on-screen controls ───────────────────────────
class TouchControls:
    """Renders three on-screen buttons and tracks multi-touch state."""
    _R     = 44
    _ALPHA = 140

    def __init__(self):
        self.left  = False
        self.right = False
        self.jump  = False
        self._finger_btn: dict = {}   # finger_id -> button name
        pad = 18
        r   = self._R
        by  = SCREEN_HEIGHT - pad - r
        self._rects = {
            "left":  pygame.Rect(pad,               by - r, r * 2, r * 2),
            "right": pygame.Rect(pad + r * 2 + 18,  by - r, r * 2, r * 2),
            "jump":  pygame.Rect(SCREEN_WIDTH - pad - r * 2, by - r, r * 2, r * 2),
        }

    def _btn_at(self, fx, fy):
        for name, rect in self._rects.items():
            if rect.collidepoint(fx, fy):
                return name
        return None

    def finger_down(self, fx, fy, fid):
        name = self._btn_at(fx, fy)
        if name:
            self._finger_btn[fid] = name
            setattr(self, name, True)

    def finger_up(self, fid):
        name = self._finger_btn.pop(fid, None)
        if name and name not in self._finger_btn.values():
            setattr(self, name, False)

    def finger_motion(self, fx, fy, fid):
        old = self._finger_btn.get(fid)
        new = self._btn_at(fx, fy)
        if old == new:
            return
        if old and old not in [v for k, v in self._finger_btn.items() if k != fid]:
            setattr(self, old, False)
        if new:
            self._finger_btn[fid] = new
            setattr(self, new, True)
        else:
            self._finger_btn.pop(fid, None)

    def reset(self):
        self.left = self.right = self.jump = False
        self._finger_btn.clear()

    def draw(self, surface):
        for name, rect in self._rects.items():
            active = getattr(self, name)
            base   = 230 if active else 150
            btn    = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(btn, (base, base, base, self._ALPHA), btn.get_rect())
            cx, cy = rect.width // 2, rect.height // 2
            ic = (30, 30, 30, 240)
            if name == "left":
                pts = [(cx + 13, cy - 14), (cx - 11, cy), (cx + 13, cy + 14)]
            elif name == "right":
                pts = [(cx - 13, cy - 14), (cx + 11, cy), (cx - 13, cy + 14)]
            else:  # jump
                pts = [(cx, cy - 16), (cx - 14, cy + 10), (cx + 14, cy + 10)]
            pygame.draw.polygon(btn, ic, pts)
            surface.blit(btn, rect)


# ── Virtual keys (keyboard + touch merged) ──────────────────
class VirtualKeys:
    """Wraps pygame key state + TouchControls for Player._handle_input."""

    def __init__(self, kb, touch):
        self._kb    = kb
        self._touch = touch

    def __getitem__(self, key):
        if self._kb[key]:
            return True
        if key in (pygame.K_LEFT,  pygame.K_a)              and self._touch.left:
            return True
        if key in (pygame.K_RIGHT, pygame.K_d)              and self._touch.right:
            return True
        if key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w) and self._touch.jump:
            return True
        return False


# ── Level loader ─────────────────────────────────────────────
def load_level(tile_map, cloud_data=None):
    if cloud_data is None:
        cloud_data = CLOUDS
    """
    Parse the tile_map list of strings and return sprite groups + metadata.
    Returns
    -------
    solid_tiles    : pygame.sprite.Group  – all collidable static tiles
    ground_tiles   : pygame.sprite.Group  – subset (for drawing)
    question_blocks: pygame.sprite.Group  – ? blocks
    enemies        : pygame.sprite.Group
    all_sprites    : pygame.sprite.Group  – everything (for drawing order)
    flag           : FlagPole | None
    level_pix_w    : int   – pixel width of the level
    clouds         : list[Cloud]
    """
    solid_tiles     = pygame.sprite.Group()
    question_blocks = pygame.sprite.Group()
    enemies         = pygame.sprite.Group()
    coins           = pygame.sprite.Group()
    all_sprites     = pygame.sprite.Group()
    flag            = None

    rows = len(tile_map)
    cols = max(len(row) for row in tile_map)

    for row_i, row_str in enumerate(tile_map):
        for col_i, ch in enumerate(row_str):
            x = col_i * TILE_SIZE
            y = row_i * TILE_SIZE

            if ch == 'G':
                t = GroundTile(col_i, row_i)
                solid_tiles.add(t)
                all_sprites.add(t)

            elif ch == 'B':
                t = BrickTile(col_i, row_i)
                solid_tiles.add(t)
                all_sprites.add(t)

            elif ch == '?':
                qb = QuestionBlock(col_i, row_i)
                question_blocks.add(qb)
                all_sprites.add(qb)

            elif ch == 'S':   # star block
                sb = StarBlock(col_i, row_i)
                question_blocks.add(sb)
                all_sprites.add(sb)

            elif ch == 'T':
                # pipe top (solid, 2-tile-wide visual drawn on 1 tile)
                t = PipeTile(col_i, row_i, top=True)
                solid_tiles.add(t)
                all_sprites.add(t)

            elif ch == '|':
                t = PipeTile(col_i, row_i, top=False)
                solid_tiles.add(t)
                all_sprites.add(t)

            elif ch == '_':
                # thin floating platform
                t = _PlatformTile(col_i, row_i)
                solid_tiles.add(t)
                all_sprites.add(t)

            elif ch == 'E':
                # enemy spawns at bottom of cell (standing on ground)
                e = Goomba(x + TILE_SIZE // 2, (row_i + 1) * TILE_SIZE)
                enemies.add(e)
                # NOT added to all_sprites yet; done separately so they draw on top

            elif ch == 'C':
                c = Coin(x + TILE_SIZE // 2, y + TILE_SIZE // 2)
                coins.add(c)
                all_sprites.add(c)

            elif ch == 'K':   # Kostas coin
                k = Kostas(x + TILE_SIZE // 2, y + TILE_SIZE // 2)
                coins.add(k)
                all_sprites.add(k)

            elif ch == 'F':
                flag = FlagPole(col_i, row_i)
                # flag added separately to draw on top of everything

    # add enemies after tiles so they draw over backgrounds
    for e in enemies:
        all_sprites.add(e)
    if flag:
        all_sprites.add(flag)

    level_pix_w = cols * TILE_SIZE
    clouds      = [Cloud(*c) for c in cloud_data]

    return (solid_tiles, question_blocks, enemies, coins,
            all_sprites, flag, level_pix_w, clouds)


# ── Floating platform tile ───────────────────────────────────
class _PlatformTile(pygame.sprite.Sprite):
    _image = None

    def __init__(self, col, row):
        super().__init__()
        if _PlatformTile._image is None:
            s    = TILE_SIZE
            surf = pygame.Surface((s, s // 3))
            surf.fill((100, 60, 20))
            pygame.draw.rect(surf, (60, 30, 5), (0, 0, s, s // 3), 2)
            _PlatformTile._image = surf
        self.image = _PlatformTile._image
        # collision rect is the full TILE_SIZE square for simplicity
        self._coll = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE,
                                 TILE_SIZE, TILE_SIZE)
        self.rect  = self._coll


# ── HUD drawing ──────────────────────────────────────────────
def draw_hud(surface, score, lives, coins_count, player_name=""):
    hud = pygame.Surface((SCREEN_WIDTH, 40), pygame.SRCALPHA)
    hud.fill((0, 0, 0, 120))
    surface.blit(hud, (0, 0))

    draw_text(surface, "PAUL BROS",            20,  10, 8,  YELLOW)
    draw_text(surface, f"SCORE  {score:06d}",  20, 220, 8,  WHITE)
    draw_text(surface, f"LIVES  x{lives}",     20, 480, 8,  WHITE)
    draw_text(surface, f"KOSTAS {coins_count:02d}", 20, 620, 8, (60, 210, 110))
    if player_name:
        draw_text(surface, player_name, 15, SCREEN_WIDTH - 8, 13,
                  (200, 200, 200), center=False)


# ── Name input screen ────────────────────────────────────────
def draw_name_input(surface, name_buf, cursor_visible, board):
    surface.fill(SKY)
    pygame.draw.rect(surface, GROUND_BODY, (0, SCREEN_HEIGHT - 80, SCREEN_WIDTH, 80))
    pygame.draw.rect(surface, GROUND_TOP,  (0, SCREEN_HEIGHT - 80, SCREEN_WIDTH, 14))

    draw_text(surface, "SUPER PAUL BROS", 58, SCREEN_WIDTH // 2, 42, YELLOW, center=True)
    draw_text(surface, "Enter your name:", 28, SCREEN_WIDTH // 2, 118, WHITE, center=True)

    # text box
    bw, bh = 320, 46
    bx = SCREEN_WIDTH // 2 - bw // 2
    by = 155
    pygame.draw.rect(surface, (20, 20, 50),  (bx, by, bw, bh), border_radius=8)
    pygame.draw.rect(surface, YELLOW,        (bx, by, bw, bh), 3, border_radius=8)
    cursor = "|" if cursor_visible else " "
    draw_text(surface, name_buf + cursor, 28, SCREEN_WIDTH // 2, by + 8, WHITE, center=True)

    draw_text(surface, "Then press  ENTER  (or tap PLAY)  to start",
              17, SCREEN_WIDTH // 2, 215, GRAY, center=True)

    # big PLAY button
    play_bw, play_bh = 180, 50
    play_bx = SCREEN_WIDTH // 2 - play_bw // 2
    play_by = 240
    pygame.draw.rect(surface, GREEN,      (play_bx, play_by, play_bw, play_bh), border_radius=10)
    pygame.draw.rect(surface, DARK_GREEN, (play_bx, play_by, play_bw, play_bh), 3, border_radius=10)
    draw_text(surface, "PLAY !", 26, SCREEN_WIDTH // 2, play_by + 11, WHITE, center=True)

    # mini leaderboard
    if board:
        draw_text(surface, "Top Scores", 20, SCREEN_WIDTH // 2, 312, YELLOW, center=True)
        medal_col = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]
        for i, entry in enumerate(board[:5]):
            col = medal_col[i] if i < 3 else WHITE
            draw_text(surface,
                      f"{i+1}. {entry['name']:<12}  {entry['score']:>6}",
                      18, SCREEN_WIDTH // 2, 336 + i * 26, col, center=True)


# ── Leaderboard screen ────────────────────────────────────────
def draw_leaderboard(surface, board, score, player_name, won):
    surface.fill((0, 10, 40))
    if not player_name:
        # Opened from menu – no game played yet
        draw_text(surface, "LEADERBOARD", 56, SCREEN_WIDTH // 2, 28, YELLOW, center=True)
    else:
        title_col  = YELLOW if won else RED
        title_text = "YOU WIN!" if won else "GAME OVER"
        draw_text(surface, title_text, 56, SCREEN_WIDTH // 2, 28, title_col, center=True)
        draw_text(surface, f"Your score:  {score:06d}", 24,
                  SCREEN_WIDTH // 2, 100, WHITE, center=True)

    draw_text(surface, "LEADERBOARD", 26, SCREEN_WIDTH // 2, 135, (150, 150, 220), center=True)
    pygame.draw.line(surface, (90, 90, 170),
                     (SCREEN_WIDTH // 2 - 230, 165),
                     (SCREEN_WIDTH // 2 + 230, 165), 2)
    medal_col = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]
    for i, entry in enumerate(board):
        is_me   = (entry["name"] == player_name and entry["score"] == score)
        row_col = (255, 255, 80) if is_me else (medal_col[i] if i < 3 else WHITE)
        mark    = "\u25b6" if is_me else " "
        line    = f"{mark}{i+1:>2}. {entry['name']:<14} {entry['score']:>6}"
        draw_text(surface, line, 19, SCREEN_WIDTH // 2, 176 + i * 27, row_col, center=True)

    draw_text(surface, "Press ENTER or tap to continue",
              21, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 55, GRAY, center=True)


# ── Saving screen ──────────────────────────────────────────────
def draw_saving(surface):
    surface.fill((0, 10, 40))
    draw_text(surface, "Saving score...", 36,
              SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20, YELLOW, center=True)
    draw_text(surface, "Connecting to leaderboard", 20,
              SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 28, GRAY, center=True)


# Rect used by both draw_menu() and the event handler to detect START clicks
_MENU_START_BTN = pygame.Rect(0, 0, 220, 56)   # x/y set inside draw_menu
_MENU_LB_BTN    = pygame.Rect(0, 0, 220, 44)   # x/y set inside draw_menu

# ── Menu screen ───────────────────────────────────────────────
def draw_menu(surface, board):
    surface.fill(SKY)
    pygame.draw.rect(surface, GROUND_BODY, (0, SCREEN_HEIGHT - 80, SCREEN_WIDTH, 80))
    pygame.draw.rect(surface, GROUND_TOP,  (0, SCREEN_HEIGHT - 80, SCREEN_WIDTH, 14))

    draw_text(surface, "SUPER PAUL BROS",
              78, SCREEN_WIDTH // 2, 60, YELLOW, center=True)
    draw_text(surface, "World  1 - 2",
              30, SCREEN_WIDTH // 2, 140, WHITE,  center=True)

    # ── big START button ──
    sbw, sbh = 220, 56
    sbx = SCREEN_WIDTH // 2 - sbw // 2
    sby = 180
    _MENU_START_BTN.topleft = (sbx, sby)
    pygame.draw.rect(surface, GREEN,      (sbx, sby, sbw, sbh), border_radius=12)
    pygame.draw.rect(surface, DARK_GREEN, (sbx, sby, sbw, sbh), 3, border_radius=12)
    draw_text(surface, "START", 32, SCREEN_WIDTH // 2, sby + 16, WHITE, center=True)

    # ── LEADERBOARD button ──
    lbw, lbh = 220, 44
    lbx = SCREEN_WIDTH // 2 - lbw // 2
    lby = sby + sbh + 14
    _MENU_LB_BTN.topleft = (lbx, lby)
    pygame.draw.rect(surface, DARK_BLUE, (lbx, lby, lbw, lbh), border_radius=10)
    pygame.draw.rect(surface, BLUE,      (lbx, lby, lbw, lbh), 3, border_radius=10)
    draw_text(surface, "LEADERBOARD", 22, SCREEN_WIDTH // 2, lby + 15, WHITE, center=True)

    # Instructions - shifted down to avoid overlap
    draw_text(surface, "A/D or \u2190/\u2192  Move          SPACE/\u2191  Jump",
              18, SCREEN_WIDTH // 2, 320, GRAY,   center=True)
    draw_text(surface, "Stomp enemies \u00b7 collect coins \u00b7 reach the flag!",
              16, SCREEN_WIDTH // 2, 345, GRAY,   center=True)

    if board:
        draw_text(surface, "Top 3:", 18, SCREEN_WIDTH // 2, 375, YELLOW, center=True)
        medal_col = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]
        for i, entry in enumerate(board[:3]):
            draw_text(surface,
                      f"{i+1}. {entry['name']}  {entry['score']:06d}",
                      16, SCREEN_WIDTH // 2, 400 + i * 22, medal_col[i], center=True)
# ── Gradient sky ──────────────────────────────────────────────
_sky_gradient      = None
_sky_gradient_dark = None

def _draw_dark_sky(surface):
    global _sky_gradient_dark
    if _sky_gradient_dark is None:
        _sky_gradient_dark = pygame.Surface((1, SCREEN_HEIGHT))
        top    = (5,  5,  30)
        bottom = (15, 5,  70)
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(top[0] + (bottom[0] - top[0]) * t)
            g = int(top[1] + (bottom[1] - top[1]) * t)
            b = int(top[2] + (bottom[2] - top[2]) * t)
            _sky_gradient_dark.set_at((0, y), (r, g, b))
    surface.blit(pygame.transform.scale(_sky_gradient_dark,
                 (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
    # draw a few pixel stars for ambience
    for i in range(40):
        sx = (i * 397 + 53)  % SCREEN_WIDTH
        sy = (i * 211 + 17)  % (SCREEN_HEIGHT // 2)
        brightness = 160 + int(40 * math.sin(pygame.time.get_ticks() * 0.001 + i))
        pygame.draw.circle(surface, (brightness, brightness, brightness), (sx, sy), 1)

def _draw_gradient_sky(surface):
    global _sky_gradient
    if _sky_gradient is None:
        _sky_gradient = pygame.Surface((1, SCREEN_HEIGHT))
        top    = (70, 140, 220)
        bottom = (160, 210, 250)
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(top[0] + (bottom[0] - top[0]) * t)
            g = int(top[1] + (bottom[1] - top[1]) * t)
            b = int(top[2] + (bottom[2] - top[2]) * t)
            _sky_gradient.set_at((0, y), (r, g, b))
    surface.blit(pygame.transform.scale(_sky_gradient, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))


# ── Main Game class ───────────────────────────────────────────
class Game:
    def __init__(self):
        if not _WEB:
            os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        pygame.init()
        pygame.display.set_caption(TITLE)

        # ── window size: desktop max 900px wide, height proportional ──
        if not _WEB:
            info  = pygame.display.Info()
            win_w = min(900, info.current_w)
            win_h = win_w * SCREEN_HEIGHT // SCREEN_WIDTH
        else:
            win_w, win_h = SCREEN_WIDTH, SCREEN_HEIGHT
        self._win_size = (win_w, win_h)
        self.screen    = pygame.display.set_mode(self._win_size)
        # internal canvas always at logical resolution (800×600)
        self._canvas   = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock     = pygame.time.Clock()
        self.state  = STATE_MENU

        # leaderboard (loaded async in background)
        self._leaderboard     = []
        self._save_task       = None   # asyncio.Task for post_score
        self._lb_fetch_task   = None   # asyncio.Task for fetch_scores
        self._player_name     = ""
        self._won             = False

        # name-input state
        self._name_buf       = ""
        self._cursor_timer   = 0
        self._cursor_visible = True

        # persistent stats across lives
        self._score      = 0
        self._lives      = STARTING_LIVES
        self._coins      = 0
        self._dead_timer  = 0
        self._win_timer   = 0
        self._trans_timer = 0   # level-transition frames counter

        # touch controls
        self.touch = TouchControls()

        self._level_data = None
        self._level_num  = 1

    # ── level init ───────────────────────────────────────────

    def _load_level(self):
        if self._level_num == 2:
            level_map   = LEVEL_2
            cloud_data  = CLOUDS_L2
        elif self._level_num == 3:
            level_map   = LEVEL_3
            cloud_data  = CLOUDS_L3
        else:
            level_map   = LEVEL_1
            cloud_data  = CLOUDS
        (self.solid_tiles, self.question_blocks,
         self.enemies, self.coins_group,
         self.all_sprites, self.flag,
         self.level_pix_w, self.clouds) = load_level(level_map, cloud_data)

        col, row = PLAYER_START
        px = col * TILE_SIZE + TILE_SIZE // 2
        py = (row + 1) * TILE_SIZE
        self.player   = Player(px, py)
        self.camera   = Camera(self.level_pix_w)

        # score_ref is a mutable list so sprites can increment it
        self._score_ref = [self._score]

        # popup group (kept separate so it draws last)
        self.popups = pygame.sprite.Group()

    # ── level transition / win ───────────────────────────────

    def _trigger_win(self):
        """Award end-of-level bonus then advance or declare final win."""
        self._score += 5000
        self._score_ref[0] = self._score
        if self._level_num == 1:
            # Show transition cinematic, then load level 2
            self._level_num   = 2
            self._trans_timer = 0
            self.state        = STATE_TRANSITION
        elif self._level_num == 2:
            # Show transition cinematic, then load level 3
            self._level_num   = 3
            self._trans_timer = 0
            self.state        = STATE_TRANSITION
        else:
            self._won  = True
            self.state = STATE_WIN

    # ── run ──────────────────────────────────────────────────

    async def run(self):
        # Fetch leaderboard in background while game starts
        self._lb_fetch_task = asyncio.create_task(fetch_scores())
        while True:
            self.clock.tick(FPS)
            self._handle_events()

            if self.state == STATE_MENU:
                # Update leaderboard when background fetch completes
                if self._lb_fetch_task and self._lb_fetch_task.done():
                    try:
                        self._leaderboard = self._lb_fetch_task.result() or []
                    except Exception:
                        pass
                    self._lb_fetch_task = None
                draw_menu(self._canvas, self._leaderboard)

            elif self.state == STATE_NAME_INPUT:
                # On web: poll JS overlay for submitted name
                if _WEB and getattr(self, '_waiting_web_name', False):
                    try:
                        import platform as _plat
                        if _plat.window.__pb_name_done:
                            self._name_buf = str(_plat.window.__pb_name_value)[:12]
                            self._waiting_web_name = False
                            self._start_game()
                    except Exception:
                        pass
                self._cursor_timer += 1
                if self._cursor_timer >= 30:
                    self._cursor_timer   = 0
                    self._cursor_visible = not self._cursor_visible
                draw_name_input(self._canvas, self._name_buf,
                                self._cursor_visible, self._leaderboard)

            elif self.state == STATE_PLAYING:
                self._update()
                self._draw()

            elif self.state == STATE_TRANSITION:
                self._trans_timer += 1
                self._draw_transition()
                # At frame 120 silently load level 2 (during the fade-in phase)
                if self._trans_timer == 120:
                    self._load_level()
                if self._trans_timer >= 200:
                    self.state = STATE_PLAYING

            elif self.state == STATE_DEAD:
                self._draw()
                self._dead_timer -= 1
                if self._dead_timer <= 0:
                    if self._lives > 0:
                        self._load_level()
                        self.state = STATE_PLAYING
                    else:
                        self._save_task = asyncio.create_task(
                            post_score(self._player_name, self._score))
                        self.state = STATE_SAVING

            elif self.state in (STATE_GAMEOVER, STATE_WIN):
                self._save_task = asyncio.create_task(
                    post_score(self._player_name, self._score))
                self.state = STATE_SAVING

            elif self.state == STATE_SAVING:
                draw_saving(self._canvas)
                if self._save_task and self._save_task.done():
                    try:
                        self._leaderboard = self._save_task.result() or []
                    except Exception:
                        self._leaderboard = []
                    self._save_task = None
                    self.state = STATE_LEADERBOARD

            elif self.state == STATE_LEADERBOARD:
                draw_leaderboard(self._canvas, self._leaderboard,
                                 self._score, self._player_name, self._won)

            # scale canvas to actual window and flip
            pygame.transform.smoothscale(self._canvas, self._win_size, self.screen)
            pygame.display.flip()
            await asyncio.sleep(0)   # yield to browser / event loop

    # ── events ───────────────────────────────────────────────

    # ── helper: go to name input ─────────────────────────
    def _go_name_input(self):
        self._name_buf       = ""
        self._cursor_timer   = 0
        self._cursor_visible = True
        self._waiting_web_name = False
        if _WEB:
            # Check if it's mobile (touch device) before showing HTML overlay
            try:
                import platform as _plat
                is_mobile = _plat.window.eval("(navigator.maxTouchPoints > 0) || /Mobi|Android/i.test(navigator.userAgent)")
                if is_mobile:
                    _plat.window.eval("pbAskName()")
                    self._waiting_web_name = True
            except Exception:
                pass
        if not self._waiting_web_name:
            pygame.key.start_text_input()
        self.state = STATE_NAME_INPUT

    def _start_game(self):
        pygame.key.stop_text_input()
        self._player_name = self._name_buf.strip() or "Player"
        self._score     = 0
        self._lives     = STARTING_LIVES
        self._coins     = 0
        self._won       = False
        self._level_num = 1
        self._load_level()
        self.touch.reset()
        self.state = STATE_PLAYING

    # ── events ─────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ── touch events (desktop only; browser uses JS gesture controller) ─
            if not _WEB:
                if event.type == pygame.FINGERDOWN:
                    fx = event.x * SCREEN_WIDTH
                    fy = event.y * SCREEN_HEIGHT
                    self.touch.finger_down(fx, fy, event.finger_id)
                    if self.state == STATE_MENU:
                        if not any(r.collidepoint(fx, fy)
                                   for r in self.touch._rects.values()):
                            self._go_name_input()  # any tap on menu → name input
                    elif self.state == STATE_NAME_INPUT:
                        # PLAY button area
                        if 240 <= fy <= 290:
                            self._start_game()
                        # Name Input box area: force open overlay on Web if tapped
                        elif 150 <= fy <= 205 and _WEB:
                            try:
                                import platform as _plat
                                _plat.window.eval("pbAskName()")
                                self._waiting_web_name = True
                            except Exception: pass
                    elif self.state == STATE_LEADERBOARD:
                        self.state = STATE_MENU
                        self._won  = False

                if event.type == pygame.FINGERUP:
                    self.touch.finger_up(event.finger_id)

                if event.type == pygame.FINGERMOTION:
                    self.touch.finger_motion(
                        event.x * SCREEN_WIDTH, event.y * SCREEN_HEIGHT,
                        event.finger_id)

            # ── text input (mobile IME / on-screen keyboard) ─
            if event.type == pygame.TEXTINPUT:
                if self.state == STATE_NAME_INPUT and len(self._name_buf) < 12:
                    self._name_buf += event.text

            # ── keyboard ────────────────────────────────
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == STATE_PLAYING:
                        self.touch.reset()
                        self.state = STATE_MENU
                    elif self.state in (STATE_NAME_INPUT, STATE_LEADERBOARD, STATE_SAVING):
                        pygame.key.stop_text_input()
                        self.state = STATE_MENU
                        self._won  = False
                    else:
                        pygame.quit()
                        sys.exit()

                if self.state == STATE_MENU:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._go_name_input()
                    elif event.key == pygame.K_l:
                        self.state = STATE_LEADERBOARD

                elif self.state == STATE_NAME_INPUT:
                    if event.key == pygame.K_RETURN:
                        self._start_game()
                    elif event.key == pygame.K_BACKSPACE:
                        self._name_buf = self._name_buf[:-1]

                elif self.state == STATE_LEADERBOARD:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = STATE_MENU
                        self._won  = False
                        # Refresh leaderboard in background for next visit
                        self._lb_fetch_task = asyncio.create_task(fetch_scores())

            # ── mouse click (desktop START / PLAY buttons) ───────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # scale window coords → canvas coords
                _mx, _my = event.pos
                mx = _mx * SCREEN_WIDTH  // self._win_size[0]
                my = _my * SCREEN_HEIGHT // self._win_size[1]
                if self.state == STATE_MENU:
                    if _MENU_START_BTN.collidepoint(mx, my):
                        self._go_name_input()
                    elif _MENU_LB_BTN.collidepoint(mx, my):
                        self.state = STATE_LEADERBOARD
                elif self.state == STATE_NAME_INPUT:
                    # replicate the PLAY button rect from draw_name_input
                    play_bx = SCREEN_WIDTH // 2 - 90
                    if pygame.Rect(play_bx, 240, 180, 50).collidepoint(mx, my):
                        self._start_game()
                elif self.state == STATE_LEADERBOARD:
                    self.state = STATE_MENU
                    self._won  = False
                    self._lb_fetch_task = asyncio.create_task(fetch_scores())

    # ── update ───────────────────────────────────────────────

    def _update(self):
        keys  = pygame.key.get_pressed()
        vkeys = VirtualKeys(keys, self.touch)

        # -- player --
        self.player.update(vkeys,
                           list(self.solid_tiles),          # question blocks handled separately in _move
                           self.question_blocks,
                           self.all_sprites,
                           self._score_ref)
        self._score = self._score_ref[0]

        # -- question block animations --
        self.question_blocks.update()

        # -- update dynamic popups spawned inside all_sprites (orchidee, score texts) --
        for spr in list(self.all_sprites):
            if isinstance(spr, Star):
                spr.update(list(self.solid_tiles))
            elif isinstance(spr, (ScorePopup, OrchideeA2Popup, BrickDebris)):
                spr.update()

        # -- star pickup --
        for spr in list(self.all_sprites):
            if isinstance(spr, Star) and self.player.hitbox.colliderect(spr.rect):
                spr.kill()
                self.player.star_powered = 600   # 10 seconds
                popup = ScorePopup(self.player.rect.centerx,
                                   self.player.rect.top - 10,
                                   "SUPER PAUL!", (255, 220, 0), size=28)
                self.popups.add(popup)

        # -- enemies --
        solid_list = list(self.solid_tiles) + list(self.question_blocks)
        for enemy in list(self.enemies):
            enemy.update(solid_list)

        # -- popup texts --
        self.popups.update()

        # -- coins + kostas (popups + collectibles) --
        for c in list(self.coins_group):
            c.update()

        # pick up coins / kostas
        for c in list(self.coins_group):
            if self.player.hitbox.colliderect(c.rect) and not c.scored:
                c.scored = True
                self._coins += 1
                self._score += 100
                self._score_ref[0] = self._score
                label = "+100 KOSTAS" if isinstance(c, Kostas) else "+100"
                popup = ScorePopup(c.rect.centerx, c.rect.top - 10, label, COIN_YELLOW)
                self.popups.add(popup)
                c.kill()

        # pop-up coins from all_sprites (spawned by question block hits)
        for spr in list(self.all_sprites):
            if isinstance(spr, Coin) and spr.scored:
                spr.kill()
            elif isinstance(spr, Coin) and self.player.hitbox.colliderect(spr.rect):
                spr.scored = True
                self._coins += 1
                self._score += 100
                self._score_ref[0] = self._score
                popup = ScorePopup(spr.rect.centerx, spr.rect.top, "+100", COIN_YELLOW)
                self.popups.add(popup)
                spr.kill()

        # camera
        self.camera.update(self.player.rect)

        # -- player ↔ enemy collisions --
        if not self.player.dead and self.player.invincible == 0:
            for enemy in list(self.enemies):
                if not enemy.alive_flag:
                    continue
                if self.player.hitbox.colliderect(enemy.rect):
                    if self.player.star_powered > 0:
                        # star power: kill enemy on any contact
                        enemy.stomp()
                        self.player.vy = JUMP_SPEED * 0.4
                        self._score += 200
                        self._score_ref[0] = self._score
                        popup = ScorePopup(enemy.rect.centerx,
                                           enemy.rect.top - 10, "★ +200", YELLOW)
                        self.popups.add(popup)
                    # stomp check: player falling + above enemy's center
                    elif (self.player.vy > 0 and
                            self.player.hitbox.bottom < enemy.rect.centery + 10):
                        enemy.stomp()
                        self.player.vy = JUMP_SPEED * 0.55   # bounce
                        self._score += 200
                        self._score_ref[0] = self._score
                        popup = ScorePopup(enemy.rect.centerx,
                                           enemy.rect.top - 10, "STOMP! +200", RED)
                        self.popups.add(popup)
                    else:
                        # hurt player
                        if self.player.hurt():
                            self._lives -= 1
                            if self._lives <= 0:
                                self.player.trigger_death()

        # -- player death (fell in pit or no lives) --
        if self.player.dead:
            if self.player.hitbox.top > SCREEN_HEIGHT + 100:
                # If fell off the right end of the level → win instead
                if self.player.hitbox.centerx >= self.level_pix_w - TILE_SIZE * 5:
                    self._trigger_win()
                else:
                    self._dead_timer = 90
                    self.state = STATE_DEAD
            return

        # -- right edge of level → win (walked/jumped past flag) --
        if self.player.hitbox.right >= self.level_pix_w:
            self._trigger_win()
            return

        # -- flag / win condition --
        if self.flag and self.player.hitbox.colliderect(self.flag.trigger_rect):
            self._trigger_win()

        # -- level boundary (left) --
        if self.player.hitbox.left < 0:
            self.player.hitbox.left = 0
            self.player.rect.midbottom = self.player.hitbox.midbottom

    # ── draw ─────────────────────────────────────────────────

    # ── transition cinematic ──────────────────────────────────────

    def _draw_transition(self):
        t  = self._trans_timer   # 0 → 200
        cv = self._canvas

        if t < 60:
            # Phase 1 (0–60): previous level fades to black
            if self._level_num == 3:
                _draw_dark_sky(cv)
            else:
                _draw_gradient_sky(cv)

            alpha = int(t / 60 * 255)
            veil  = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            veil.fill((0, 0, 0))
            veil.set_alpha(alpha)
            cv.blit(veil, (0, 0))

        elif t < 120:
            # Phase 2 (60–120): black with twinkling stars + title card
            cv.fill((0, 0, 0))

            # animated stars
            for i in range(80):
                sx = (i * 397 + 53)  % SCREEN_WIDTH
                sy = (i * 211 + 17)  % SCREEN_HEIGHT
                bri = 80 + int(130 * abs(math.sin(
                    pygame.time.get_ticks() * 0.0025 + i)))
                pygame.draw.circle(cv, (bri, bri, bri), (sx, sy), 1)

            # text fade-in (frames 60–80 = 20 frames)
            text_a = min(255, int((t - 60) / 20 * 255))

            # purple glow line behind title
            glow = pygame.Surface((480, 80), pygame.SRCALPHA)
            glow.fill((120, 50, 200, 60))
            cv.blit(glow, (SCREEN_WIDTH // 2 - 240,
                           SCREEN_HEIGHT // 2 - 100))

            def _txt(text, size, y, col):
                ts  = pygame.font.SysFont("Arial Black", size, bold=True)
                img = ts.render(text, True, col)
                img.set_alpha(text_a)
                cv.blit(img, img.get_rect(center=(SCREEN_WIDTH // 2, y)))

            if self._level_num == 3:
                _txt("Level  3",      52, SCREEN_HEIGHT // 2 - 80, (220, 180, 255))
                _txt("Cieli Infiniti", 40, SCREEN_HEIGHT // 2 - 20, (160,  80, 255))
            else:
                _txt("Level  2",      52, SCREEN_HEIGHT // 2 - 80, (220, 180, 255))
                _txt("Notte Oscura",   40, SCREEN_HEIGHT // 2 - 20, (160,  80, 255))
            _txt("", 18,
                 SCREEN_HEIGHT // 2 + 44, (160, 160, 200))

        else:
            # Phase 3 (120–200): new level's sky fades in
            if self._level_num == 2:
                _draw_dark_sky(cv)
            else:
                _draw_gradient_sky(cv)
            fade  = max(0, 200 - t)           # 80 → 0
            alpha = int(fade / 80 * 255)
            if alpha > 0:
                veil = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                veil.fill((0, 0, 0))
                veil.set_alpha(alpha)
                cv.blit(veil, (0, 0))

    # ── draw ──────────────────────────────────────────────────

    def _draw(self):
        cv = self._canvas
        if self._level_num == 2:
            _draw_dark_sky(cv)
        else:
            _draw_gradient_sky(cv)

        # clouds (parallax)
        for cloud in self.clouds:
            cloud.draw(cv, self.camera.x)

        # all tile / enemy / coin sprites
        for spr in self.all_sprites:
            draw_rect = self.camera.apply(spr.rect)
            if -100 < draw_rect.x < SCREEN_WIDTH + 100:
                cv.blit(spr.image, draw_rect)

        # player (draw with flicker if invincible)
        if not self.player.dead:
            show = True
            if self.player.invincible > 0:
                show = (self.player.invincible // 5) % 2 == 0
            if show:
                cv.blit(self.player.image, self.camera.apply(self.player.rect))

        # popup score texts (no camera offset – drawn above tiles)
        for pop in self.popups:
            cv.blit(pop.image, self.camera.apply(pop.rect))

        # coins group (standing coins not in all_sprites)
        for c in self.coins_group:
            cv.blit(c.image, self.camera.apply(c.rect))

        # HUD
        draw_hud(cv, self._score, self._lives, self._coins, self._player_name)

        # touch controls (drawn only on desktop; browser uses HTML overlay buttons)
        if not _WEB:
            self.touch.draw(cv)

        # dead screen overlay
        if self.state == STATE_DEAD:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            cv.blit(overlay, (0, 0))
            draw_text(cv, "CONJO!", 60,
                      SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40, RED, center=True)
            lives_msg = (f"Lives left: {self._lives}" if self._lives > 0
                         else "No lives left…")
            draw_text(cv, lives_msg, 30,
                      SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30, WHITE, center=True)


# ── Entry point ───────────────────────────────────────────────
async def main():
    game = Game()
    await game.run()

asyncio.run(main())
