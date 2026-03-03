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
import asyncio
import pygame
import random

from settings    import *
from sprites     import (Player, Goomba, GroundTile, BrickTile, QuestionBlock,
                         PipeTile, Coin, Kostas, FlagPole, Cloud, ScorePopup,
                         OrchideeA2Popup, StarBlock, Star, BrickDebris, draw_text)
from level_data  import LEVEL_1, PLAYER_START, CLOUDS
from leaderboard import load_leaderboard, save_entry

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
def load_level(tile_map):
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
    clouds      = [Cloud(*c) for c in CLOUDS]

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


# Rect used by both draw_menu() and the event handler to detect START clicks
_MENU_START_BTN = pygame.Rect(0, 0, 220, 56)   # x/y set inside draw_menu

# ── Menu screen ───────────────────────────────────────────────
def draw_menu(surface, board):
    surface.fill(SKY)
    pygame.draw.rect(surface, GROUND_BODY, (0, SCREEN_HEIGHT - 80, SCREEN_WIDTH, 80))
    pygame.draw.rect(surface, GROUND_TOP,  (0, SCREEN_HEIGHT - 80, SCREEN_WIDTH, 14))

    draw_text(surface, "SUPER PAUL BROS",
              78, SCREEN_WIDTH // 2, 80, YELLOW, center=True)
    draw_text(surface, "World  1 - 1",
              30, SCREEN_WIDTH // 2, 183, WHITE,  center=True)

    # ── big START button ──
    sbw, sbh = 220, 56
    sbx = SCREEN_WIDTH // 2 - sbw // 2
    sby = 215
    _MENU_START_BTN.topleft = (sbx, sby)
    pygame.draw.rect(surface, GREEN,      (sbx, sby, sbw, sbh), border_radius=12)
    pygame.draw.rect(surface, DARK_GREEN, (sbx, sby, sbw, sbh), 3, border_radius=12)
    draw_text(surface, "START", 32, SCREEN_WIDTH // 2, sby + 11, WHITE, center=True)

    draw_text(surface, "A/D or ←/→  Move          SPACE/↑  Jump",
              18, SCREEN_WIDTH // 2, 291, GRAY,   center=True)
    draw_text(surface, "Stomp enemies · collect coins · reach the flag!",
              16, SCREEN_WIDTH // 2, 314, GRAY,   center=True)

    if board:
        draw_text(surface, "Top 3:", 17, SCREEN_WIDTH // 2, 348, YELLOW, center=True)
        medal_col = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]
        for i, entry in enumerate(board[:3]):
            draw_text(surface,
                      f"{i+1}. {entry['name']}  {entry['score']:06d}",
                      15, SCREEN_WIDTH // 2, 368 + i * 20, medal_col[i], center=True)

    tmp_player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 82)
    surface.blit(tmp_player.image,
                 tmp_player.image.get_rect(midbottom=(SCREEN_WIDTH // 2,
                                                       SCREEN_HEIGHT - 82)))


# ── Gradient sky ──────────────────────────────────────────────
_sky_gradient = None
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
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock  = pygame.time.Clock()
        self.state  = STATE_MENU

        # leaderboard
        self._leaderboard    = load_leaderboard()
        self._player_name    = ""
        self._won            = False

        # name-input state
        self._name_buf       = ""
        self._cursor_timer   = 0
        self._cursor_visible = True

        # persistent stats across lives
        self._score      = 0
        self._lives      = STARTING_LIVES
        self._coins      = 0
        self._dead_timer = 0
        self._win_timer  = 0

        # touch controls
        self.touch = TouchControls()

        self._level_data = None

    # ── level init ───────────────────────────────────────────

    def _load_level(self):
        (self.solid_tiles, self.question_blocks,
         self.enemies, self.coins_group,
         self.all_sprites, self.flag,
         self.level_pix_w, self.clouds) = load_level(LEVEL_1)

        col, row = PLAYER_START
        px = col * TILE_SIZE + TILE_SIZE // 2
        py = (row + 1) * TILE_SIZE
        self.player   = Player(px, py)
        self.camera   = Camera(self.level_pix_w)

        # score_ref is a mutable list so sprites can increment it
        self._score_ref = [self._score]

        # popup group (kept separate so it draws last)
        self.popups = pygame.sprite.Group()

    # ── run ──────────────────────────────────────────────────

    async def run(self):
        while True:
            self.clock.tick(FPS)
            self._handle_events()

            if self.state == STATE_MENU:
                draw_menu(self.screen, self._leaderboard)

            elif self.state == STATE_NAME_INPUT:
                self._cursor_timer += 1
                if self._cursor_timer >= 30:
                    self._cursor_timer   = 0
                    self._cursor_visible = not self._cursor_visible
                draw_name_input(self.screen, self._name_buf,
                                self._cursor_visible, self._leaderboard)

            elif self.state == STATE_PLAYING:
                self._update()
                self._draw()

            elif self.state == STATE_DEAD:
                self._draw()
                self._dead_timer -= 1
                if self._dead_timer <= 0:
                    if self._lives > 0:
                        self._load_level()
                        self.state = STATE_PLAYING
                    else:
                        self._leaderboard = save_entry(self._player_name, self._score)
                        self.state = STATE_LEADERBOARD

            elif self.state in (STATE_GAMEOVER, STATE_WIN):
                self._leaderboard = save_entry(self._player_name, self._score)
                self.state = STATE_LEADERBOARD

            elif self.state == STATE_LEADERBOARD:
                draw_leaderboard(self.screen, self._leaderboard,
                                 self._score, self._player_name, self._won)

            pygame.display.flip()
            await asyncio.sleep(0)   # yield to browser / event loop

    # ── events ───────────────────────────────────────────────

    # ── helper: go to name input ─────────────────────────
    def _go_name_input(self):
        self._name_buf       = ""
        self._cursor_timer   = 0
        self._cursor_visible = True
        self.state = STATE_NAME_INPUT
        pygame.key.start_text_input()

    def _start_game(self):
        pygame.key.stop_text_input()
        self._player_name = self._name_buf.strip() or "Player"
        self._score  = 0
        self._lives  = STARTING_LIVES
        self._coins  = 0
        self._won    = False
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
                        if 240 <= fy <= 290:
                            self._start_game()
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
                    elif self.state == STATE_NAME_INPUT:
                        pygame.key.stop_text_input()
                        self.state = STATE_MENU
                    else:
                        pygame.quit()
                        sys.exit()

                if self.state == STATE_MENU:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._go_name_input()

                elif self.state == STATE_NAME_INPUT:
                    if event.key == pygame.K_RETURN:
                        self._start_game()
                    elif event.key == pygame.K_BACKSPACE:
                        self._name_buf = self._name_buf[:-1]

                elif self.state == STATE_LEADERBOARD:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = STATE_MENU
                        self._won  = False

            # ── mouse click (desktop START / PLAY buttons) ───────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if self.state == STATE_MENU:
                    if _MENU_START_BTN.collidepoint(mx, my):
                        self._go_name_input()
                elif self.state == STATE_NAME_INPUT:
                    # replicate the PLAY button rect from draw_name_input
                    play_bx = SCREEN_WIDTH // 2 - 90
                    if pygame.Rect(play_bx, 240, 180, 50).collidepoint(mx, my):
                        self._start_game()
                elif self.state == STATE_LEADERBOARD:
                    self.state = STATE_MENU
                    self._won  = False

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
                self._dead_timer = 90
                self.state = STATE_DEAD
            return

        # -- flag / win condition --
        if self.flag and self.player.hitbox.colliderect(self.flag.trigger_rect):
            self._score += 5000
            self._score_ref[0] = self._score
            self._won = True
            self.state = STATE_WIN

        # -- level boundary --
        if self.player.hitbox.left < 0:
            self.player.hitbox.left = 0
            self.player.rect.midbottom = self.player.hitbox.midbottom

    # ── draw ─────────────────────────────────────────────────

    def _draw(self):
        _draw_gradient_sky(self.screen)

        # clouds (parallax)
        for cloud in self.clouds:
            cloud.draw(self.screen, self.camera.x)

        # all tile / enemy / coin sprites
        for spr in self.all_sprites:
            draw_rect = self.camera.apply(spr.rect)
            if -100 < draw_rect.x < SCREEN_WIDTH + 100:
                self.screen.blit(spr.image, draw_rect)

        # player (draw with flicker if invincible)
        if not self.player.dead:
            show = True
            if self.player.invincible > 0:
                show = (self.player.invincible // 5) % 2 == 0
            if show:
                self.screen.blit(self.player.image,
                                 self.camera.apply(self.player.rect))

        # popup score texts (no camera offset – drawn above tiles)
        for pop in self.popups:
            # convert world-space to screen-space
            screen_rect = self.camera.apply(pop.rect)
            self.screen.blit(pop.image, screen_rect)

        # coins group (standing coins not in all_sprites)
        for c in self.coins_group:
            self.screen.blit(c.image, self.camera.apply(c.rect))

        # HUD
        draw_hud(self.screen, self._score, self._lives, self._coins,
                 self._player_name)

        # touch controls (drawn only on desktop; browser uses HTML overlay buttons)
        if not _WEB:
            self.touch.draw(self.screen)

        # dead screen overlay
        if self.state == STATE_DEAD:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            self.screen.blit(overlay, (0, 0))
            draw_text(self.screen, "CONJO!", 60,
                      SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40, RED, center=True)
            lives_msg = (f"Lives left: {self._lives}" if self._lives > 0
                         else "No lives left…")
            draw_text(self.screen, lives_msg, 30,
                      SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30, WHITE, center=True)


# ── Entry point ───────────────────────────────────────────────
async def main():
    game = Game()
    await game.run()

asyncio.run(main())
