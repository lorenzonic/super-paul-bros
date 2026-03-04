# ============================================================
#  Paul Bros  –  Level data
#
#  Tile legend:
#    G  = ground tile (solid brown/grass)
#    B  = brick block (solid)
#    ?  = question block (A2 orchidee on hit, +500 pts)
#    S  = star block (bouncing star power-up)
#    T  = pipe top  (solid, opening visual)
#    |  = pipe body (solid)
#    _  = floating platform (solid, thin look)
#    E  = Goomba spawn (replaced by sprite, not a tile)
#    C  = coin pickup
#    K  = Kostas coin (+100 pts, gold coin with K)
#    F  = flag-pole spawn position (decorative, triggers win)
#    (space) = empty
#
#  All rows must be the same length (160 chars wide).
#  Each character represents one TILE_SIZE×TILE_SIZE cell.
#  Row 0 = top of level, row 14 = bottom of screen.
# ============================================================

# helper: pad/truncate any row to exactly 160 chars
def _r(s, w=160):
    return (s + " " * w)[:w]

LEVEL_1 = [
    # col  0         1         2         3         4         5         6         7         8         9         10        11        12        13        14        15
    # col  0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
    "                                                                                                                                                                ",  # row  0
    "                                                                                                                                                                ",  # row  1
    "                                                                                                                                                                ",  # row  2
    "                    KKKKK                              KKKKK                              KKKKK                              KKKKK                              ",  # row  3
    "                                                                                                                                                                ",  # row  4
    "               KKKK                         KKKK                         KKKK                         KKKK                         KKKK                         ",  # row  5
    "          B?B   SB?         ?B?             B?B         ?S?           B?B?              ?B?           BS?             B?B            ?S?B?            B?B       ",  # row  6
    "                                 ____               ____                   ____              ____               ____                                            ",  # row  7
    "                    BBBB                BBBB                  BBBB            BBBBBB              BBBB                    BBBBB                 BBBB            ",  # row  8
    "               T                                                                                                                                                ",  # row  9
    "           T E       E        E       E       E T    E       E       E T       E        E      E     E   T     E      E       E       E  T    E      E    E   F ",  # row 10
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG  GGGGGGGGGGGGGGGGGGGG  GGGGGGGGGGGGGGGGGGGG  GGGGGGGGGGGGGGGGGGGGGGGGGGG",  # row 11
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG  GGGGGGGGGGGGGGGGGGGG  GGGGGGGGGGGGGGGGGGGG  GGGGGGGGGGGGGGGGGGGGGGGGGGG",  # row 12
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG  GGGGGGGGGGGGGGGGGGGG  GGGGGGGGGGGGGGGGGGGG  GGGGGGGGGGGGGGGGGGGGGGGGGGG",  # row 13
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG  GGGGGGGGGGGGGGGGGGGG  GGGGGGGGGGGGGGGGGGGG  GGGGGGGGGGGGGGGGGGGGGGGGGGG",  # row 14
]

# Spawn position for Paul (column, row)
PLAYER_START = (2, 10)

# Background clouds  (x, y, scale)
CLOUDS = [
    (200,  60, 1.2), (500,  40, 0.9), (750,  70, 1.0),
    (1100, 50, 1.3), (1400, 65, 0.8), (1700, 45, 1.1),
    (2000, 75, 1.0), (2300, 55, 0.9), (2700, 70, 1.2),
    (3000, 40, 1.0), (3400, 65, 1.1), (3800, 50, 0.9),
    (4200, 75, 1.2), (4600, 45, 1.0), (5000, 60, 1.3),
    (5500, 40, 0.8), (5900, 70, 1.1), (6300, 55, 0.9),
]

# ── Level 2 – Notte Oscura ────────────────────────────────────
# Dark theme: many wide pits, dense enemies, fewer safe spots.
# Ground sections (cols): 0-11, 17-28, 34-45, 51-62, 68-79, 85-96, 102-113, 119-159
# 7 pits (5 tiles wide each) at cols 12-16, 29-33, 46-50, 63-67, 80-84, 97-101, 114-118

_GROUND_L2 = "GGGGGGGGGGGG     " * 7 + "G" * 41   # 160 chars exactly

LEVEL_2 = [
    _r(""),                                                                                  # row  0
    _r(""),                                                                                  # row  1
    _r(""),                                                                                  # row  2
    _r("    K    K    K    K    K    K    K    K    K    K    K    K    K    K    K    K    K    K    K    K"),  # row  3  (20 K coins)
    _r(""),                                                                                  # row  4
    _r(""),                                                                                  # row  5
    _r("  ?S?B    S?B?   B?B    ?S?B   B?BS   ?B?S   S?B?   B?B    ?S?B   B?BS"),           # row  6
    _r("                     ____                 ____                 ____                 ____                 ____"),  # row  7
    _r("  BBBBB           BBBBB           BBBBB           BBBBB           BBBBB           BBBBB           BBBBB"),        # row  8
    _r(""),                                                                                  # row  9
    # row 10: enemies (5-7 per solid section) + flag F at col 158
    (  "  E E E E  E"   # sec0  cols  0-11
     + "     "          # pit   cols 12-16
     + "E  E  E  E  "   # sec1  cols 17-28
     + "     "          # pit   cols 29-33
     + " E E  E E  E"   # sec2  cols 34-45
     + "     "          # pit   cols 46-50
     + "EE  EE  E  E"   # sec3  cols 51-62
     + "     "          # pit   cols 63-67
     + "E  E  E  E  "   # sec4  cols 68-79
     + "     "          # pit   cols 80-84
     + " EE E  E E E"   # sec5  cols 85-96
     + "     "          # pit   cols 97-101
     + "E E  EE  E E"   # sec6  cols 102-113
     + "     "          # pit   cols 114-118
     + "  E  E  E  E  E  E  E  E  E  E  E  E   F "  # finale cols 119-159 (41 chars, F at col 158)
    ),
    _GROUND_L2,   # row 11
    _GROUND_L2,   # row 12
    _GROUND_L2,   # row 13
    _GROUND_L2,   # row 14
]

# Clouds for level 2 (sparse, pale – moonlit night)
CLOUDS_L2 = [
    (400,  40, 0.6), (1000, 55, 0.5), (1800, 30, 0.7),
    (2600, 45, 0.5), (3300, 20, 0.6), (4100, 50, 0.4),
    (4900, 35, 0.7), (5700, 45, 0.5),
]
