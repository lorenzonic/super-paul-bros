# ============================================================
#  Paul Bros  –  Level 1 data
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
#    K  = Kostas coin (+100 pts, smiling face coin)
#    F  = flag-pole spawn position (decorative, triggers win)
#    (space) = empty
#
#  All rows must be the same length (160 chars wide).
#  Each character represents one TILE_SIZE×TILE_SIZE cell.
#  Row 0 = top of level, row 14 = bottom of screen.
# ============================================================

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
