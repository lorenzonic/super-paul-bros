# ============================================================
#  Paul Bros  –  Sprites
#  All game objects are drawn procedurally with pygame.draw
#  (the player will be swapped for a PNG in a future version)
# ============================================================

import os
import pygame
import math
import random
from settings import *


# ── Shared face image loader ─────────────────────────────────

_face_cache    = None   # None = not attempted; False = not found; Surface = loaded
_patrice_cache = None   # same pattern for patrice.png (enemy image)
_muscle_cache  = None   # same pattern for muscle.png


def _strip_white_bg(surface):
    """Make white/near-white pixels transparent on a surface."""
    arr = pygame.PixelArray(surface)
    w, h = surface.get_size()
    for xi in range(w):
        for yi in range(h):
            r, g, b, a = surface.unmap_rgb(arr[xi, yi])
            if r > 220 and g > 220 and b > 220:
                arr[xi, yi] = surface.map_rgb((0, 0, 0, 0))
    del arr
    return surface


def _get_face_image():
    """Load assets/paul_face.png once, strip white background, return Surface or None."""
    global _face_cache
    if _face_cache is not None:
        return _face_cache if _face_cache else None
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "paul_face.png")
    if not os.path.exists(path):
        _face_cache = False
        return None
    raw = pygame.image.load(path).convert_alpha()
    _strip_white_bg(raw)
    _face_cache = raw
    return raw


def _get_patrice_image():
    """Load assets/patrice.png once, strip white background, return Surface or None."""
    global _patrice_cache
    if _patrice_cache is not None:
        return _patrice_cache if _patrice_cache else None
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "patrice.png")
    if not os.path.exists(path):
        _patrice_cache = False
        return None
    raw = pygame.image.load(path).convert_alpha()
    _strip_white_bg(raw)
    _patrice_cache = raw
    return raw


def _get_muscle_image():
    """Load assets/muscle.png once, strip white background, return Surface or None."""
    global _muscle_cache
    if _muscle_cache is not None:
        return _muscle_cache if _muscle_cache else None
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "muscle.png")
    if not os.path.exists(path):
        _muscle_cache = False
        return None
    raw = pygame.image.load(path).convert_alpha()
    _strip_white_bg(raw)
    _muscle_cache = raw
    return raw


_orchidee_cache     = None
_piggy_frames_cache = None   # None = not attempted; False = not found; list = frames
_pizza_img_cache    = None   # cached pizza.png surface


def _load_gif_frames(path):
    """Load all frames from a GIF. Uses Pillow if available, else single pygame frame."""
    try:
        from PIL import Image as PILImage
        pil_img = PILImage.open(path)
        pil_img.seek(0)   # start from the beginning
        frames = []
        try:
            while True:
                # Do NOT use .copy() before convert: PIL internally composites each
                # frame on top of previous ones; copying breaks delta-encoded GIFs.
                frame = pil_img.convert("RGBA")
                w, h  = frame.size
                surf  = pygame.image.fromstring(frame.tobytes(), (w, h), "RGBA").convert_alpha()
                frames.append(surf)
                pil_img.seek(pil_img.tell() + 1)
        except EOFError:
            pass
        return frames or None
    except ImportError:
        try:
            return [pygame.image.load(path).convert_alpha()]
        except Exception:
            return None
    except Exception:
        return None


def _get_piggy_frames():
    """Load assets/piggy.gif once and return list of Surfaces (or None)."""
    global _piggy_frames_cache
    if _piggy_frames_cache is not None:
        return _piggy_frames_cache if _piggy_frames_cache else None
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "piggy.gif")
    if not os.path.exists(path):
        _piggy_frames_cache = False
        return None
    frames = _load_gif_frames(path)
    _piggy_frames_cache = frames if frames else False
    return _piggy_frames_cache if _piggy_frames_cache else None


def _get_orchidee_image():
    """Load assets/orchideeA2.png once, strip white background, return Surface or None."""
    global _orchidee_cache
    if _orchidee_cache is not None:
        return _orchidee_cache if _orchidee_cache else None
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "orchideeA2.png")
    if not os.path.exists(path):
        _orchidee_cache = False
        return None
    raw = pygame.image.load(path).convert_alpha()
    _strip_white_bg(raw)
    _orchidee_cache = raw
    return raw


def _get_pizza_image():
    """Load assets/pizza.png once, strip white background, return Surface or None."""
    global _pizza_img_cache
    if _pizza_img_cache is not None:
        return _pizza_img_cache if _pizza_img_cache else None
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "pizza.png")
    if not os.path.exists(path):
        _pizza_img_cache = False
        return None
    raw = pygame.image.load(path).convert_alpha()
    _strip_white_bg(raw)
    _pizza_img_cache = raw
    return raw


# ── Utility helpers ─────────────────────────────────────────

def draw_text(surface, text, size, x, y, color=WHITE, center=False):
    font = pygame.font.SysFont("Arial", size, bold=True)
    img  = font.render(str(text), True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(img, rect)


# ── Static tile sprites ──────────────────────────────────────

class GroundTile(pygame.sprite.Sprite):
    """Solid ground tile (grassy top + dirt body)."""
    _cache: dict = {}

    def __init__(self, col, row):
        super().__init__()
        self.image = GroundTile._make_image()
        self.rect  = self.image.get_rect(topleft=(col * TILE_SIZE, row * TILE_SIZE))

    @staticmethod
    def _make_image():
        if "ground" in GroundTile._cache:
            return GroundTile._cache["ground"]
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill(GROUND_BODY)
        pygame.draw.rect(surf, GROUND_TOP, (0, 0, TILE_SIZE, TILE_SIZE // 5))
        # subtle grid lines
        pygame.draw.line(surf, DARK_BROWN, (0, 0), (TILE_SIZE, 0), 1)
        pygame.draw.line(surf, DARK_BROWN, (0, 0), (0, TILE_SIZE), 1)
        GroundTile._cache["ground"] = surf
        return surf


class BrickTile(pygame.sprite.Sprite):
    """Breakable brick block."""
    _image = None

    def __init__(self, col, row):
        super().__init__()
        self.image = BrickTile._make_image()
        self.rect  = self.image.get_rect(topleft=(col * TILE_SIZE, row * TILE_SIZE))

    @staticmethod
    def _make_image():
        if BrickTile._image:
            return BrickTile._image
        s = TILE_SIZE
        surf = pygame.Surface((s, s))
        surf.fill(BRICK_COL)
        # brick pattern
        mid = s // 2
        pygame.draw.rect(surf, BRICK_DARK, (0,    0,   s,     2 ))
        pygame.draw.rect(surf, BRICK_DARK, (0,    mid, s,     2 ))
        pygame.draw.rect(surf, BRICK_DARK, (0,    0,   2,     s ))
        pygame.draw.rect(surf, BRICK_DARK, (mid//2, 0, 2,     mid))
        pygame.draw.rect(surf, BRICK_DARK, (mid + mid//2, mid, 2, s - mid))
        pygame.draw.rect(surf, BRICK_DARK, (s-2,  0,   2,     s ))
        BrickTile._image = surf
        return surf


class BrickDebris(pygame.sprite.Sprite):
    """Small brick fragment ejected when a brick is smashed."""
    def __init__(self, x, y, vx, vy):
        super().__init__()
        s = random.randint(5, 10)
        self.image = pygame.Surface((s, s))
        self.image.fill(BRICK_COL)
        pygame.draw.rect(self.image, BRICK_DARK, (0, 0, s, s), 1)
        self.rect  = self.image.get_rect(center=(x, y))
        self._vx   = vx
        self._vy   = vy
        self._life = 35
        self._alpha = 255

    def update(self):
        self._vy   += 0.65          # gravity
        self.rect.x += int(self._vx)
        self.rect.y += int(self._vy)
        self._life  -= 1
        self._alpha  = max(0, int(255 * self._life / 35))
        self.image.set_alpha(self._alpha)
        if self._life <= 0:
            self.kill()


class QuestionBlock(pygame.sprite.Sprite):
    """? block – hit from below to release a coin."""

    def __init__(self, col, row):
        super().__init__()
        self.active   = True
        self.col      = col
        self.row      = row
        self._timer   = 0           # bump animation timer
        self._offset  = 0           # vertical offset during bump
        self.image    = self._make_image(active=True)
        self.rect     = self.image.get_rect(topleft=(col * TILE_SIZE, row * TILE_SIZE))
        self._base_y  = self.rect.y

    @staticmethod
    def _make_image(active=True):
        s    = TILE_SIZE
        surf = pygame.Surface((s, s))
        bg   = QBLOCK_YELLOW if active else QBLOCK_USED
        surf.fill(bg)
        border = QBLOCK_DARK if active else DARK_BROWN
        pygame.draw.rect(surf, border, (0, 0, s, s), 3)
        # "?" or "•" glyph
        font = pygame.font.SysFont("Arial", s - 12, bold=True)
        glyph = "?" if active else "•"
        text = font.render(glyph, True, WHITE if active else GRAY)
        tr   = text.get_rect(center=(s // 2, s // 2))
        surf.blit(text, tr)
        return surf

    def bump(self):
        """Called when the player hits the block from below."""
        if self.active:
            self.active  = False
            self._timer  = 20
            self.image   = self._make_image(active=False)
            return True   # signal: spawn coin
        return False

    def update(self):
        if self._timer > 0:
            self._timer -= 1
            # smooth ease-out bounce
            t = self._timer / 20.0
            # sine ease: quick up then smooth return
            import math
            self._offset = -int(12 * math.sin(t * math.pi))
            self.rect.y = self._base_y + self._offset
        else:
            self._offset = 0
            self.rect.y  = self._base_y


class StarBlock(pygame.sprite.Sprite):
    """Special ? block that contains a star power-up."""

    def __init__(self, col, row):
        super().__init__()
        self.active  = True
        self.col     = col
        self.row     = row
        self._timer  = 0
        self._offset = 0
        self.image   = self._make_image(active=True)
        self.rect    = self.image.get_rect(topleft=(col * TILE_SIZE, row * TILE_SIZE))
        self._base_y = self.rect.y

    @staticmethod
    def _make_image(active=True):
        s    = TILE_SIZE
        surf = pygame.Surface((s, s))
        bg     = QBLOCK_YELLOW if active else QBLOCK_USED
        border = QBLOCK_DARK   if active else DARK_BROWN
        surf.fill(bg)
        pygame.draw.rect(surf, border, (0, 0, s, s), 3)
        font  = pygame.font.SysFont("Arial", s - 12, bold=True)
        glyph = "?" if active else "\u2022"   # same as QuestionBlock – star is a surprise
        text  = font.render(glyph, True, WHITE if active else GRAY)
        surf.blit(text, text.get_rect(center=(s // 2, s // 2)))
        return surf

    def bump(self):
        if self.active:
            self.active = False
            self._timer = 20
            self.image  = self._make_image(active=False)
            return True
        return False

    def update(self):
        if self._timer > 0:
            self._timer -= 1
            t = self._timer / 20.0
            self._offset = -int(12 * math.sin(t * math.pi))
            self.rect.y  = self._base_y + self._offset
        else:
            self._offset = 0
            self.rect.y  = self._base_y


class Star(pygame.sprite.Sprite):
    """Bouncing collectible star that grants super-saiyan power."""

    def __init__(self, x, y):
        super().__init__()
        self._t  = 0
        self.vy  = -7.0
        self.vx  = 2.0
        self.image = self._make_image()
        self.rect  = self.image.get_rect(midbottom=(x, y))

    @staticmethod
    def _make_image():
        size = 34
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2
        r_out, r_in = 15, 6
        pts = []
        for i in range(10):
            angle = math.radians(-90 + i * 36)
            r = r_out if i % 2 == 0 else r_in
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        pygame.draw.polygon(surf, (255, 220, 0), pts)
        pygame.draw.polygon(surf, (220, 160, 0), pts, 2)
        pygame.draw.circle(surf, WHITE, (cx - 3, cy - 5), 3)   # glint
        return surf

    def update(self, solid_tiles):
        self._t += 1
        self.vy  = min(self.vy + GRAVITY, MAX_FALL_SPEED)

        # horizontal
        self.rect.x += int(self.vx)
        for tile in solid_tiles:
            if self.rect.colliderect(tile.rect):
                self.vx = -self.vx
                self.rect.x += int(self.vx) * 2
                break

        # vertical
        self.rect.y += int(self.vy)
        for tile in solid_tiles:
            if self.rect.colliderect(tile.rect):
                if self.vy > 0:
                    self.rect.bottom = tile.rect.top
                    self.vy = -6.0   # bounce
                elif self.vy < 0:
                    self.rect.top = tile.rect.bottom
                    self.vy = 0
                break

        # spin visual (rotate image)
        angle = (self._t * 6) % 360
        base  = self._make_image()
        self.image = pygame.transform.rotate(base, angle)
        old_center = self.rect.center
        self.rect  = self.image.get_rect(center=old_center)

        if self.rect.top > SCREEN_HEIGHT + 60:
            self.kill()


# ── MusclePill – ground pickup that grants Muscle Power ─────

class MusclePill(pygame.sprite.Sprite):
    """Collectible pill on the ground. Grants muscle power for 10 seconds."""

    def __init__(self, x, y):
        super().__init__()
        self._t      = 0
        self._base_y = y
        self.image   = self._make_image()
        self.rect    = self.image.get_rect(midbottom=(x, y))

    @staticmethod
    def _make_image():
        w, h = 18, 34
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        # top half red, bottom half white – classic Italian pill
        pygame.draw.rect(surf, (220, 35, 35),  (0, 0,      w, h // 2), border_radius=10)
        pygame.draw.rect(surf, (240, 240, 240), (0, h // 2, w, h // 2), border_radius=10)
        # outline
        pygame.draw.rect(surf, (150, 15, 15), (0, 0, w, h), 2, border_radius=10)
        # dividing line
        pygame.draw.line(surf, (180, 180, 180), (1, h // 2), (w - 1, h // 2), 1)
        # glint on top half
        pygame.draw.circle(surf, (255, 120, 120, 160), (w // 3, h // 5), 3)
        return surf

    def update(self):
        self._t += 1
        bob = int(3 * math.sin(self._t * 0.08))
        self.rect.midbottom = (self.rect.centerx, self._base_y + bob)


class PipeTile(pygame.sprite.Sprite):
    """A pipe section (top or body). top=True draws the opening cap."""

    def __init__(self, col, row, top=False):
        super().__init__()
        self.image = self._make_image(top)
        self.rect  = self.image.get_rect(topleft=(col * TILE_SIZE, row * TILE_SIZE))

    @staticmethod
    def _make_image(top):
        s    = TILE_SIZE
        surf = pygame.Surface((s, s))
        surf.fill(PIPE_GREEN)
        pygame.draw.rect(surf, PIPE_DARK, (0, 0, s, s), 2)
        if top:
            # wider cap
            cap_w = int(s * 1.0)
            pygame.draw.rect(surf, PIPE_GREEN, (0, 0, cap_w, s // 4))
            pygame.draw.rect(surf, PIPE_DARK,  (0, 0, cap_w, s // 4), 2)
        return surf


class InvisibleBarrier(pygame.sprite.Sprite):
    """Thin invisible solid tile used inside pipe tops to block entry."""

    def __init__(self, col, row):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(topleft=(col * TILE_SIZE, row * TILE_SIZE))


# ── Animated coin (collectible) ──────────────────────────────

class Coin(pygame.sprite.Sprite):
    """Floating collectible coin with a spin animation."""
    FRAME_WIDTHS = [10, 7, 3, 7]   # simulate spin with width changes

    def __init__(self, x, y, popup=False):
        super().__init__()
        self._frame   = 0
        self._frame_t = 0
        self._popup   = popup
        self._vy      = -8 if popup else 0
        self.scored   = False

        # bounding rect
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(x, y))
        self._draw()

    def _draw(self):
        self.image.fill((0, 0, 0, 0))
        w = Coin.FRAME_WIDTHS[self._frame % len(Coin.FRAME_WIDTHS)]
        h = TILE_SIZE - 12
        cx, cy = TILE_SIZE // 2, TILE_SIZE // 2
        pygame.draw.ellipse(self.image, COIN_YELLOW, (cx - w//2, cy - h//2, w, h))
        pygame.draw.ellipse(self.image, COIN_DARK,   (cx - w//2, cy - h//2, w, h), 2)

    def update(self):
        self._frame_t += 1
        if self._frame_t % 6 == 0:
            self._frame += 1
            self._draw()

        if self._popup:
            self.rect.y += self._vy
            self._vy    += 0.8
            if self._vy > 0 and self.rect.y >= self.rect.y:
                # die after bounce-up + come back down
                pass
            if self._vy > 6:
                self.kill()


# ── Kostas coin (+100 pts) ───────────────────────────────────

class Kostas(pygame.sprite.Sprite):
    """Golden coin with a bold K. Worth +100 pts."""
    _font = None   # cached font

    def __init__(self, x, y):
        super().__init__()
        self.scored = False
        self._bob_t = 0
        self.image  = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.rect   = self.image.get_rect(center=(x, y))
        if Kostas._font is None:
            Kostas._font = pygame.font.SysFont("Arial Black", 18, bold=True)
        self._draw(0)

    def _draw(self, bob):
        self.image.fill((0, 0, 0, 0))
        r  = (TILE_SIZE - 4) // 2   # 18 px radius
        cx = TILE_SIZE // 2
        cy = TILE_SIZE // 2 + bob

        # ── coin body ────────────────────────────────────────
        # outer dark ring
        pygame.draw.circle(self.image, (180, 120,  0), (cx, cy), r)
        # main gold fill (slightly smaller)
        pygame.draw.circle(self.image, COIN_YELLOW, (cx, cy), r - 2)
        # inner lighter gold gradient (top half brighter)
        pygame.draw.circle(self.image, (255, 230, 80), (cx, cy - 2), r - 5)
        # edge shading (bottom-right darker rim)
        pygame.draw.circle(self.image, (200, 140, 10), (cx, cy), r - 2, 2)
        # top-left highlight (white shine)
        pygame.draw.circle(self.image, (255, 255, 200), (cx - r//3, cy - r//3), max(r//4, 4))

        # ── K letter ─────────────────────────────────────────
        k_surf = Kostas._font.render("K", True, (140, 80, 0))
        k_surf = pygame.transform.smoothscale(k_surf, (16, 18))
        kr = k_surf.get_rect(center=(cx, cy + 1))
        self.image.blit(k_surf, kr)

    def update(self):
        self._bob_t += 1
        bob = int(3 * math.sin(self._bob_t * 0.10))
        self._draw(bob)


# ── Score pop-up text ────────────────────────────────────────

class ScorePopup(pygame.sprite.Sprite):
    """Floating text popup that rises and fades out."""
    def __init__(self, x, y, text, color=YELLOW, size=24):
        super().__init__()
        self._text     = str(text)
        self._color    = color
        self._size     = size
        self._base_y   = y
        self._life     = 60   # frames visible
        self._max_life = 60
        self._vy       = -2.5  # initial upward speed
        self._rebuild()
        self.rect  = self.image.get_rect(center=(x, y))

    def _rebuild(self):
        # scale text size based on life (starts big, shrinks slightly)
        progress = self._life / self._max_life
        sz = max(12, int(self._size * (0.7 + 0.3 * progress)))
        font = pygame.font.SysFont("Arial", sz, bold=True)
        alpha = max(30, int(255 * progress))
        self.image = font.render(self._text, True, self._color)
        self.image.set_alpha(alpha)

    def update(self):
        self._vy *= 0.96  # decelerate
        self.rect.y += int(self._vy)
        self._life -= 1
        self._rebuild()
        if self._life <= 0:
            self.kill()
        if self._life <= 0:
            self.kill()


class OrchideeA2Popup(pygame.sprite.Sprite):
    """
    The orchideeA2.png image that scrolls upward out of a ? block.
    Starts hidden inside the block, rises ~3 tiles, then fades.
    """
    _SIZE = 80   # rendered size (square)

    def __init__(self, block_cx, block_top):
        super().__init__()
        img = _get_orchidee_image()
        if img:
            self._base = pygame.transform.smoothscale(img,
                             (self._SIZE, self._SIZE))
        else:
            # fallback: yellow "A2" text
            font = pygame.font.SysFont("Arial", 42, bold=True)
            self._base = font.render("A2", True, YELLOW)

        self._life     = 110   # total frames
        self._max_life = 110
        self._vy       = -3.2  # upward speed px/frame
        # start just above the block top, centred horizontally
        self.image = self._base.copy()
        self.rect  = self.image.get_rect(midbottom=(block_cx, block_top))

    def update(self):
        self._vy  *= 0.97           # decelerate
        self.rect.y += int(self._vy)
        self._life  -= 1

        # fade out in the last 40 frames
        progress = self._life / self._max_life
        alpha    = 255 if progress > 0.4 else int(255 * (progress / 0.4))
        self.image = self._base.copy()
        self.image.set_alpha(max(0, alpha))

        if self._life <= 0:
            self.kill()


# ── Flag (level end) ────────────────────────────────────────

class FlagPole(pygame.sprite.Sprite):
    """Decorative flag pole; touching the base triggers level clear."""

    def __init__(self, col, row_base):
        super().__init__()
        pole_h     = TILE_SIZE * 7
        surf_w     = TILE_SIZE * 2
        self.image = pygame.Surface((surf_w, pole_h), pygame.SRCALPHA)
        # pole
        cx = surf_w // 2
        pygame.draw.rect(self.image, FLAGPOLE, (cx - 3, 0, 6, pole_h))
        # flag
        pts = [(cx + 3, 10), (cx + 28, 22), (cx + 3, 34)]
        pygame.draw.polygon(self.image, FLAG_GREEN, pts)
        # ball on top
        pygame.draw.circle(self.image, YELLOW, (cx, 8), 8)
        self.rect = self.image.get_rect(bottomleft=(col * TILE_SIZE, (row_base + 1) * TILE_SIZE))

    @property
    def trigger_rect(self):
        """Small rect at the base for player collision."""
        return pygame.Rect(self.rect.centerx - 10, self.rect.bottom - TILE_SIZE,
                           20, TILE_SIZE)


# ── Decorative clouds (background) ──────────────────────────

class Cloud:
    def __init__(self, x, y, size=1.0):
        self.x    = x
        self.y    = y
        self.size = size

    def draw(self, surface, offset_x):
        sx = self.x - offset_x * 0.3   # parallax
        s  = self.size
        cx, cy = int(sx), int(self.y)
        r = int(20 * s)
        pygame.draw.circle(surface, CLOUD,        (cx,        cy),     r)
        pygame.draw.circle(surface, CLOUD,        (cx + r,    cy),     int(r * 0.8))
        pygame.draw.circle(surface, CLOUD,        (cx - r,    cy),     int(r * 0.75))
        pygame.draw.circle(surface, CLOUD_SHADOW, (cx,        cy + 4), int(r * 0.9))
        pygame.draw.circle(surface, CLOUD,        (cx,        cy),     r)


# ── Goomba enemy ────────────────────────────────────────────

class Goomba(pygame.sprite.Sprite):
    """Enemy whose body is patrice.png, touching the ground directly."""

    WALK_SPEED  = 1.5
    SPRITE_W    = 72
    SPRITE_H    = 72

    def __init__(self, x, y):
        super().__init__()
        self._anim_t     = 0
        self._walk_frame = 0
        self.vx          = -self.WALK_SPEED
        self.vy          = 0.0
        self.on_ground   = False
        self.alive_flag  = True
        self._death_t    = 0

        self.image = pygame.Surface((self.SPRITE_W, self.SPRITE_H), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(midbottom=(x, y))
        self._draw_alive()

    # ── drawing ─────────────────────────────────────────────

    def _draw_alive(self):
        self.image.fill((0, 0, 0, 0))
        w, h = self.SPRITE_W, self.SPRITE_H
        pat = _get_patrice_image()
        if pat:
            # crop to non-transparent bounding box so the image sits on the ground
            bounds = pat.get_bounding_rect()
            cropped = pat.subsurface(bounds)
            scaled = pygame.transform.smoothscale(cropped, (w, h))
            self.image.blit(scaled, (0, 0))
        else:
            # fallback procedural body
            pygame.draw.ellipse(self.image, BROWN,    (3, h // 3, w - 6, h * 2 // 3))
            pygame.draw.ellipse(self.image, BROWN,    (5, 2, w - 10, h // 2 + 4))
            pygame.draw.line(self.image, BLACK, (8, 10), (16, 14), 2)
            pygame.draw.line(self.image, BLACK, (w - 9, 10), (w - 17, 14), 2)
            pygame.draw.circle(self.image, WHITE, (14, 17), 5)
            pygame.draw.circle(self.image, WHITE, (w - 14, 17), 5)
            pygame.draw.circle(self.image, BLACK, (15, 18), 3)
            pygame.draw.circle(self.image, BLACK, (w - 13, 18), 3)

    def _draw_stomped(self):
        self.image.fill((0, 0, 0, 0))
        w, h = self.SPRITE_W, self.SPRITE_H
        pat = _get_patrice_image()
        if pat:
            bounds   = pat.get_bounding_rect()
            cropped  = pat.subsurface(bounds)
            squished = pygame.transform.smoothscale(cropped, (w - 4, 14))
            self.image.blit(squished, (2, h - 16))
        else:
            pygame.draw.ellipse(self.image, BROWN,     (2, h - 14, w - 4, 12))
            pygame.draw.ellipse(self.image, DARK_BROWN,(4, h - 12, w - 8, 8))

    # ── logic ────────────────────────────────────────────────

    def update(self, solid_tiles):
        if not self.alive_flag:
            self._death_t += 1
            if self._death_t > 30:
                self.kill()
            return

        # gravity
        self.vy = min(self.vy + GRAVITY, MAX_FALL_SPEED)

        # horizontal move
        self.rect.x += int(self.vx)
        self._resolve_horizontal(solid_tiles)

        # vertical move
        self.on_ground = False
        self.rect.y   += int(self.vy)
        self._resolve_vertical(solid_tiles)

        # walk animation (no longer redraws, kept for future use)
        self._anim_t += 1

        # fall off screen → remove
        if self.rect.top > SCREEN_HEIGHT + 50:
            self.kill()

    def _resolve_horizontal(self, tiles):
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vx < 0:
                    self.rect.left = tile.rect.right
                    self.vx = self.WALK_SPEED
                elif self.vx > 0:
                    self.rect.right = tile.rect.left
                    self.vx = -self.WALK_SPEED

    def _resolve_vertical(self, tiles):
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vy > 0:
                    self.rect.bottom = tile.rect.top
                    self.vy          = 0
                    self.on_ground   = True
                elif self.vy < 0:
                    self.rect.top = tile.rect.bottom
                    self.vy       = 0

    def stomp(self):
        """Called when the player lands on top of this enemy."""
        self.alive_flag = False
        self._death_t   = 0
        self._draw_stomped()


# ── Piggy – Level 3 animated GIF enemy ─────────────────────

class Piggy(Goomba):
    """Level-3 enemy: cycles through piggy.gif frames; same physics as Goomba."""

    FRAME_DURATION = 3   # game ticks per GIF frame (~20 fps animation at 60 fps)

    def __init__(self, x, y):
        # must be set BEFORE super().__init__() because it calls _draw_alive()
        self._gif_frame = 0
        self._gif_tick  = 0
        super().__init__(x, y)

    def _draw_alive(self):
        frames = _get_piggy_frames()
        if not frames:
            super()._draw_alive()
            return
        w, h = self.SPRITE_W, self.SPRITE_H
        scaled = pygame.transform.smoothscale(
            frames[self._gif_frame % len(frames)], (w, h))
        self.image.fill((0, 0, 0, 0))
        self.image.blit(scaled, (0, 0))

    def _draw_stomped(self):
        frames = _get_piggy_frames()
        if not frames:
            super()._draw_stomped()
            return
        w, h = self.SPRITE_W, self.SPRITE_H
        squished = pygame.transform.smoothscale(frames[0], (w - 4, 14))
        self.image.fill((0, 0, 0, 0))
        self.image.blit(squished, (2, h - 16))

    def update(self, solid_tiles):
        super().update(solid_tiles)
        if self.alive_flag:
            self._gif_tick += 1
            if self._gif_tick >= self.FRAME_DURATION:
                self._gif_tick   = 0
                frames = _get_piggy_frames()
                if frames:
                    self._gif_frame = (self._gif_frame + 1) % len(frames)
                    self._draw_alive()


# ── PizzaSlice – flying projectile thrown by PizzaEnemy ────

class PizzaSlice(pygame.sprite.Sprite):
    """A spinning pizza-slice projectile thrown by PizzaEnemy."""

    SPEED = 4.5

    def __init__(self, x, y, direction):
        super().__init__()
        self._angle     = 0
        self._direction = direction   # +1 right / -1 left
        self.vx = self.SPEED * direction
        self.vy = -1.5   # slight upward arc at launch
        w = h = 28
        img = _get_pizza_image()
        if img:
            self._base = pygame.transform.smoothscale(img, (w, h)).copy()
        else:
            # fallback: draw a simple triangular slice
            self._base = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.polygon(self._base, (230, 130, 30),
                                [(w // 2, 0), (0, h), (w, h)])
        self.image = self._base.copy()
        self.rect  = self.image.get_rect(center=(x, y))

    def update(self, solid_tiles=None):
        # gentle arc (less gravity than the player)
        self.vy = min(self.vy + GRAVITY * 0.4, MAX_FALL_SPEED * 0.4)
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        # spinning animation
        self._angle = (self._angle + 9 * self._direction) % 360
        self.image  = pygame.transform.rotate(self._base, self._angle)
        old_center  = self.rect.center
        self.rect   = self.image.get_rect(center=old_center)
        # despawn when well off-screen
        if (self.rect.right < -200 or self.rect.left > 160 * TILE_SIZE
                or self.rect.top > SCREEN_HEIGHT + 100):
            self.kill()
            return
        # despawn when hitting a solid tile
        if solid_tiles:
            for tile in solid_tiles:
                if self.rect.colliderect(tile.rect):
                    self.kill()
                    return


# ── PizzaEnemy – Level 4 pizza-throwing boss ────────────────

class PizzaEnemy(Goomba):
    """Level-4 enemy: displayed as pizza.png, throws spinning pizza slices."""

    SPRITE_W       = 100   # bigger than the default 72
    SPRITE_H       = 100
    SHOOT_INTERVAL = 110   # frames between shots (~1.8 s at 60 fps)

    def __init__(self, x, y):
        # slices and timer must be set BEFORE super().__init__() because
        # Goomba.__init__ calls _draw_alive() immediately.
        self.slices       = pygame.sprite.Group()
        self._shoot_timer = random.randint(0, 80)   # stagger first shots
        super().__init__(x, y)

    def _draw_alive(self):
        img = _get_pizza_image()
        if img:
            w, h = self.SPRITE_W, self.SPRITE_H
            scaled = pygame.transform.smoothscale(img, (w, h))
            self.image.fill((0, 0, 0, 0))
            self.image.blit(scaled, (0, 0))
        else:
            super()._draw_alive()

    def _draw_stomped(self):
        img = _get_pizza_image()
        if img:
            w, h = self.SPRITE_W, self.SPRITE_H
            squished = pygame.transform.smoothscale(img, (w - 4, 14))
            self.image.fill((0, 0, 0, 0))
            self.image.blit(squished, (2, h - 16))
        else:
            super()._draw_stomped()

    def update(self, solid_tiles):
        super().update(solid_tiles)
        if self.alive_flag:
            self._shoot_timer += 1
            if self._shoot_timer >= self.SHOOT_INTERVAL:
                self._shoot_timer = 0
                direction = 1 if self.vx >= 0 else -1
                cx = self.rect.right if direction > 0 else self.rect.left
                slc = PizzaSlice(cx, self.rect.centery, direction)
                self.slices.add(slc)


# ── Player ──────────────────────────────────────────────────

class Player(pygame.sprite.Sprite):
    """
    Paul – the player character.
    Drawn procedurally for now; replace self.image with a PNG later.

    Controls:
        Left / Right  →  Move
        Space / Up    →  Jump
    """

    # ── image cache for each state ───────────────────────────
    _img_cache: dict = {}

    def __init__(self, x, y):
        super().__init__()

        # physics
        self.vx          = 0.0
        self.vy          = 0.0
        self.on_ground   = False
        self._jumps_left = 0        # used to allow 1 jump
        self._coyote     = 0        # coyote time frames

        # state
        self.facing      = 1        # +1 right, -1 left
        self._anim_t     = 0
        self._walk_frame = 0
        self._state      = "idle"   # idle | walk | jump | fall

        # damage
        self.invincible  = 0        # countdown in frames
        self.dead          = False
        self._death_vy     = -12
        self.star_powered  = 0   # countdown frames (600 = 10 s)
        self.muscle_powered = 0  # countdown frames (600 = 10 s)

        self.image = self._render("idle", 1)
        self.rect  = self.image.get_rect(midbottom=(x, y))

        # small physics hitbox (independent of the large visual rect)
        HITBOX_W = 36
        HITBOX_H = 58
        self.hitbox = pygame.Rect(0, 0, HITBOX_W, HITBOX_H)
        self.hitbox.midbottom = self.rect.midbottom

    # ── rendering ────────────────────────────────────────────

    @classmethod
    def _render(cls, state, facing, walk_frame=0, star=False, muscle=False):
        key = (state, facing, walk_frame if state == "walk" else 0, star, muscle)
        if key in cls._img_cache:
            return cls._img_cache[key]

        W, H = (120, 150) if muscle else (80, 100)
        surf = pygame.Surface((W, H), pygame.SRCALPHA)

        if muscle:
            # use muscle.png instead of the normal face
            muscle_img = _get_muscle_image()
            if muscle_img:
                scaled = pygame.transform.smoothscale(muscle_img, (W, H))
            else:
                # fallback: normal face with red tint
                face_img = _get_face_image()
                scaled = pygame.transform.smoothscale(face_img, (W, H)) if face_img else pygame.Surface((W, H), pygame.SRCALPHA)
                tint = pygame.Surface((W, H), pygame.SRCALPHA)
                tint.fill((220, 40, 40, 90))
                scaled.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        else:
            face_img = _get_face_image()
            if face_img:
                scaled = pygame.transform.smoothscale(face_img, (W, H))
            else:
                scaled = pygame.Surface((W, H), pygame.SRCALPHA)
                pygame.draw.ellipse(scaled, CREAM, (10, 5, 60, 75))
                pygame.draw.circle(scaled, BLACK, (35, 35), 5)

            # star-power: golden tint overlay
            if star:
                tint = pygame.Surface((W, H), pygame.SRCALPHA)
                tint.fill((255, 220, 0, 80))
                scaled.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        surf.blit(scaled, (0, 0))

        if facing == 1:
            surf = pygame.transform.flip(surf, True, False)

        cls._img_cache[key] = surf
        return surf


    # ── update ───────────────────────────────────────────────

    def update(self, keys, solid_tiles, question_blocks, all_sprites, score_ref):
        if self.dead:
            self._death_update()
            return

        if self.star_powered > 0:
            self.star_powered -= 1
        if self.muscle_powered > 0:
            self.muscle_powered -= 1

        self._handle_input(keys)
        self._apply_physics()
        self._move(solid_tiles, question_blocks, all_sprites, score_ref)
        self._animate()

        if self.invincible > 0:
            self.invincible -= 1

        # fell off screen
        if self.hitbox.top > SCREEN_HEIGHT + 60:
            self.dead = True

    def _death_update(self):
        self.vy = min(self.vy + 0.6, 15)
        self.hitbox.y += int(self.vy)
        self.rect.midbottom = self.hitbox.midbottom

    def _handle_input(self, keys):
        # acceleration-based movement (smooth)
        moving = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            accel = ACCELERATION if self.on_ground else AIR_ACCEL
            self.vx -= accel
            self.facing = -1
            moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            accel = ACCELERATION if self.on_ground else AIR_ACCEL
            self.vx += accel
            self.facing = 1
            moving = True

        # clamp horizontal speed
        if abs(self.vx) > MOVE_SPEED:
            self.vx = MOVE_SPEED * (1 if self.vx > 0 else -1)

        # friction when not pressing keys
        if not moving:
            fric = FRICTION if self.on_ground else AIR_FRICTION
            self.vx *= fric
            if abs(self.vx) < 0.15:
                self.vx = 0

        # jump (with variable height: release early = lower jump)
        jump_pressed = (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w])
        jump_speed = JUMP_SPEED * 1.7 if self.muscle_powered > 0 else JUMP_SPEED
        if jump_pressed:
            if self.on_ground or self._coyote > 0:
                self.vy = jump_speed
                self.on_ground = False
                self._coyote = 0
                self._jump_held = True
        else:
            # cut jump short if released early
            if hasattr(self, '_jump_held') and self._jump_held and self.vy < jump_speed * 0.4:
                self.vy *= 0.55
            self._jump_held = False

    def _apply_physics(self):
        self.vy = min(self.vy + GRAVITY, MAX_FALL_SPEED)

    # ── brick smash helper ──────────────────────────────────
    def _smash_brick(self, tile, all_sprites, score_ref):
        cx, cy = tile.rect.centerx, tile.rect.centery
        for _ in range(6):
            vx = random.uniform(-3.5, 3.5)
            vy = random.uniform(-5.0, -1.5)
            all_sprites.add(BrickDebris(cx, cy, vx, vy))
        score_ref[0] += 50
        all_sprites.add(ScorePopup(cx, cy - 20, "+50", ORANGE, size=20))
        tile.kill()

    def _move(self, solid_tiles, question_blocks, all_sprites, score_ref):
        # ── horizontal (solid tiles only, NOT question blocks) ─
        self.hitbox.x += int(self.vx)

        to_smash_h = []
        for tile in solid_tiles:
            if self.hitbox.colliderect(tile.rect):
                if self.star_powered > 0 and isinstance(tile, BrickTile):
                    to_smash_h.append(tile)
                else:
                    if self.vx > 0:
                        self.hitbox.right = tile.rect.left
                    elif self.vx < 0:
                        self.hitbox.left  = tile.rect.right
        for tile in to_smash_h:
            self._smash_brick(tile, all_sprites, score_ref)

        # ── vertical (solid tiles) ────────────────────────────
        prev_ground    = self.on_ground
        self.on_ground = False
        self.hitbox.y += int(self.vy)
        vy_before = self.vy          # save BEFORE solid tiles may reset it
        to_smash_v = []
        for tile in solid_tiles:
            if self.hitbox.colliderect(tile.rect):
                if self.vy < 0 and self.star_powered > 0 and isinstance(tile, BrickTile):
                    to_smash_v.append(tile)
                elif self.vy > 0:
                    self.hitbox.bottom = tile.rect.top
                    self.vy            = 0
                    self.on_ground     = True
                elif self.vy < 0:
                    self.hitbox.top = tile.rect.bottom
                    self.vy         = 0
        for tile in to_smash_v:
            self._smash_brick(tile, all_sprites, score_ref)

        # ── question blocks: purely vertical, never horizontal ─
        for qb in question_blocks:
            # horizontal overlap check (without pushout)
            h_overlap = (self.hitbox.right > qb.rect.left and
                         self.hitbox.left  < qb.rect.right)
            if not h_overlap:
                continue

            # use vy_before so adjacent-brick pushout never masks the bump
            if vy_before < 0:
                # player was moving upward – bump from below
                if (self.hitbox.top <= qb.rect.bottom and
                        self.hitbox.centery >= qb.rect.centery):
                    self.hitbox.top = qb.rect.bottom
                    self.vy         = 0
                    if qb.bump():
                        if isinstance(qb, StarBlock):
                            star_spr = Star(qb.rect.centerx, qb.rect.top)
                            all_sprites.add(star_spr)
                        else:
                            popup = OrchideeA2Popup(qb.rect.centerx, qb.rect.top)
                            all_sprites.add(popup)
                            score_ref[0] += 500
                            pts = ScorePopup(qb.rect.centerx, qb.rect.top - 50,
                                             "+500", WHITE, size=22)
                            all_sprites.add(pts)
            elif self.vy >= 0:
                # landing on top
                if (self.hitbox.bottom >= qb.rect.top and
                        self.hitbox.top < qb.rect.top):
                    self.hitbox.bottom = qb.rect.top
                    self.vy            = 0
                    self.on_ground     = True

        # ── coyote time ───────────────────────────────────────
        if prev_ground and not self.on_ground:
            self._coyote = 8
        elif self._coyote > 0:
            self._coyote -= 1
        if self.on_ground:
            self._coyote = 0

        # sync visual rect to hitbox
        self.rect.midbottom = self.hitbox.midbottom

    def _animate(self):
        star   = self.star_powered > 0
        muscle = self.muscle_powered > 0
        if self.on_ground:
            if abs(self.vx) > 0.1:
                self._state   = "walk"
                self._anim_t += 1
                if self._anim_t % 8 == 0:
                    self._walk_frame ^= 1
            else:
                self._state      = "idle"
                self._walk_frame = 0
                self._anim_t     = 0
        else:
            self._state = "jump" if self.vy < 0 else "fall"

        base = self._render(self._state, self.facing, self._walk_frame,
                            star=star, muscle=muscle)

        if star:
            # draw golden pulsing aura around sprite
            bw, bh = base.get_size()
            pad  = 18
            canvas = pygame.Surface((bw + pad * 2, bh + pad * 2), pygame.SRCALPHA)
            t = pygame.time.get_ticks()
            for layer, (rw_add, rh_add, alpha) in enumerate(
                    [(16, 14, 40), (11, 9, 70), (6, 5, 100)]):
                pulse = 1.0 + 0.08 * math.sin(t * 0.008 + layer)
                rw = int((bw // 2 + rw_add) * pulse)
                rh = int((bh // 2 + rh_add) * pulse)
                aura = pygame.Surface((rw * 2, rh * 2), pygame.SRCALPHA)
                pygame.draw.ellipse(aura, (255, 220, 0, alpha),
                                    (0, 0, rw * 2, rh * 2))
                canvas.blit(aura, (pad + bw // 2 - rw,
                                   pad + bh // 2 - rh))
            canvas.blit(base, (pad, pad))
            self.image = canvas
            self.rect  = canvas.get_rect(midbottom=self.hitbox.midbottom)

        elif muscle:
            # draw red pulsing aura + bicep muscles on sides
            bw, bh = base.get_size()
            pad    = 22
            canvas = pygame.Surface((bw + pad * 2, bh + pad * 2), pygame.SRCALPHA)
            t = pygame.time.get_ticks()
            for layer, (rw_add, rh_add, alpha) in enumerate(
                    [(18, 16, 45), (12, 10, 75), (7, 6, 110)]):
                pulse = 1.0 + 0.10 * math.sin(t * 0.009 + layer)
                rw = int((bw // 2 + rw_add) * pulse)
                rh = int((bh // 2 + rh_add) * pulse)
                aura = pygame.Surface((rw * 2, rh * 2), pygame.SRCALPHA)
                pygame.draw.ellipse(aura, (255, 60, 60, alpha),
                                    (0, 0, rw * 2, rh * 2))
                canvas.blit(aura, (pad + bw // 2 - rw, pad + bh // 2 - rh))
            # bicep circles on both sides
            arm_y = pad + bh // 3
            for arm_x in (pad - 8, pad + bw + 8):
                pygame.draw.circle(canvas, (210, 35, 35), (arm_x, arm_y), 17)
                pygame.draw.circle(canvas, (255, 100, 80), (arm_x - 4, arm_y - 5), 7)
            canvas.blit(base, (pad, pad))
            self.image = canvas
            self.rect  = canvas.get_rect(midbottom=self.hitbox.midbottom)

        else:
            self.image = base
            self.rect  = base.get_rect(midbottom=self.hitbox.midbottom)

    def hurt(self):
        """Called when enemy touches player (from side/below)."""
        if self.invincible == 0:
            self.invincible = INVINCIBLE_FRAMES
            return True   # signal: lost a life
        return False

    def trigger_death(self):
        self.dead = True
        self.vy   = self._death_vy
