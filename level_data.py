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

# ── Level 2 – Dark Night ────────────────────────────────────
# Dark theme: Varied terrain, treacherous jumps, and verticality.

# Ground pattern with pits
# Pits at cols: 20-25 (5), 50-55 (5), 90-100 (10), 130-135 (5)
_G1 = "G" * 20
_P1 = " " * 5
_G2 = "G" * 25
_P2 = " " * 5
_G3 = "G" * 35
_P3 = " " * 10
_G4 = "G" * 30
_P4 = " " * 5
_G5 = "G" * 25

_GROUND_L2 = _G1 + _P1 + _G2 + _P2 + _G3 + _P3 + _G4 + _P4 + _G5

LEVEL_2 = [
    _r(""),                                                                                  # row  0
    _r(""),                                                                                  # row  1
    _r(""),                                                                                  # row  2
    _r("                    KKK                         KKK                         KKK                         KKK                         KK"),
    _r("                                                                                    BBBBB                        "),
    _r("         K           BBBBB            K          BBBBB                  K                           K                           K                 "),
    _r("        BBB                    BBB                         BBB             ___ ___     BBB                         BBB                "),
    _r("                     ___                                                                                                          "),
    _r("                 T      T              T       T                  T       T                  T       T                  T         "),
    _r("                                                                                                                                  "),
    # Row 10: Enemies and obstacles on the ground layer
    (   "      E   ?   E     "     # 20 (Sec 1)
      + "     "                   # 5  (Pit 1)
      + "  T    K    ?    E   T  " # 25 (Sec 2)
      + " ___ "                   # 5  (Pit 2 platform)
      + "   E   B?B   E     S     E     " # 35 (Sec 3)
      + " _  __  _ "              # 10 (Pit 3 platforms)
      + "     T    E      E      T     "  # 30 (Sec 4)
      + "     "                   # 5  (Pit 4)
      + "  E      E         F     "   # 25 (Sec 5)
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

# ── Level 3 – Cieli Infiniti ──────────────────────────────────
# Sky theme: floating islands, minimal ground, verticality.

LEVEL_3 = [
    _r(""),                                                                                  
    _r(""),
    _r("                   KKK                         KKK                         KKK       "),
    _r("         ___                   ___                         ___                         ___"),
    _r("                  ?       ?               ?       ?                   ?       ?                   ?       ?"),
    _r(""),
    _r("      ?   B?B     ?   B?B     ?   B?B     ?   B?B     ?   B?B     ?   B?B     ?   B?B     ?   B?B"),
    _r(""),
    _r("    "),
    _r("      E         E         E         E         E         E         E         E         E         E"),
    _r("   BBB       BBB       BBB       BBB       BBB       BBB       BBB       BBB       BBB       BBB"),
    # Row 11: The "Floor" (broken into islands)
    (  "GGGGGG"      # Start
     + "      "      # 6
     + "GGGG  "      # 6
     + "      "      # 6
     + "  GG  "      # 6
     + "      "      # 6
     + " GGGG "      # 6
     + "      "      # 6
     + "GGGGGG"      # 6
     + "          "  # 10
     + "  GG  "      # 6
     + "      "      # 6
     + " GGGG "      # 6
     + "      "      # 6
     + "GGGGGG"      # 6
     + "      "      # 6
     + "  GG  "      # 6
     + "      "      # 6
     + " GGGG "      # 6
     + "      "      # 6
     + "GGGGGG"      # 6
     + "      "      # 6
     + "  GG  "      # 6
     + "      "      # 6
     + " GGGG "      # 6
     + "      "      # 6
     + "GGGGGGGGGGG   F " # End (16 chars)
    ),
    _r(""),
    _r(""),
    _r(""),
]

# Many clouds for the sky level
CLOUDS_L3 = [
    (100,  80, 1.2), (350,  20, 0.9), (600,  60, 1.0),
    (900,  40, 1.3), (1200, 70, 0.8), (1500, 30, 1.1),
    (1800, 50, 1.0), (2100, 90, 0.9), (2400, 40, 1.2),
    (2700, 60, 1.0), (3000, 30, 1.1), (3300, 70, 0.9),
    (3600, 50, 1.2), (3900, 80, 1.0), (4200, 40, 1.3),
    (4500, 60, 0.8), (4800, 20, 1.1), (5100, 70, 0.9),
    (5400, 50, 1.2), (5700, 80, 1.0),
    (6000, 40, 1.1), (6300, 60, 0.9),
]
