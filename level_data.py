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
#    M  = Muscle Pill (ground pickup, grants muscle power 10 s)
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
PLAYER_START = (2, 10)      # Default (Level 1, 3)
PLAYER_START_L2 = (0, 10)   # Level 2 – start far left away from enemies
PLAYER_START_L4 = (0, 10)   # Level 4 – start far left away from enemies
PLAYER_START_L5 = (0, 10)   # Level 5 – start far left away from enemies

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
    _r(" " * 8 + "M" + " " * 61 + "M" + " " * 39 + "M"),  # row 9 – muscle pills
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
# Sky theme: floating islands with 3-tile gaps (manageable jumps).
# Bridge platforms sit above every gap to help the player.
#
# Island layout (col ranges):
#   0:  0- 9  |  1: 13-20  |  2: 24-33  |  3: 37-46  |  4: 50-59
#   5: 63-72  |  6: 76-85  |  7: 89-100 |  8:104-115  |  9:119-131 | 10:135-159
# Gaps (3 tiles wide): 10-12, 21-23, 34-36, 47-49, 60-62,
#                      73-75, 86-88, 101-103, 116-118, 132-134

_GROUND_L3 = (
    "G"*10 + " "*3 + "G"*8  + " "*3 + "G"*10 + " "*3 + "G"*10 + " "*3 +
    "G"*10 + " "*3 + "G"*10 + " "*3 + "G"*10 + " "*3 + "G"*12 + " "*3 +
    "G"*12 + " "*3 + "G"*13 + " "*3 + "G"*25
)   # 160 chars

# Bridge platforms centered above each gap (cols 11,22,35,48,61,74,87,102,117,133)
_BRIDGES_L3 = _r(
    " "*11 + "_" + " "*10 + "_" + " "*12 + "_" + " "*12 + "_" + " "*12 +
    "_" + " "*12 + "_" + " "*12 + "_" + " "*14 + "_" + " "*14 + "_" +
    " "*15 + "_"
)

LEVEL_3 = [
    _r(""),                                                                               # row 0
    _r(""),                                                                               # row 1
    # K coins on every island (row 2)
    _r(" "*3  + "KK" + " "*10 + "KK" + " "*11 + "KK" + " "*10 + "KK" +
       " "*11 + "KK" + " "*11 + "KK" + " "*11 + "KK" + " "*13 + "KK" +
       " "*13 + "KK" + " "*13 + "KK" + " "*20 + "KK"),
    # Bridge platforms at gap level (row 3) – first set of helpers
    _BRIDGES_L3,                                                                         # row 3
    # Question / ? blocks on islands (row 4)
    _r(" "*4  + "?" + " "*10 + "B?B" + " "*10 + "?" + " "*11 + "B?B" +
       " "*11 + "?" + " "*11 + "B?B" + " "*11 + "?" + " "*12 + "B?B" +
       " "*12 + "?" + " "*14 + "B?B" + " "*19 + "?"),
    _r(""),                                                                               # row 5
    # Brick combos on islands (row 6)
    _r(" "*3  + "B?B" + " "*9  + "B?B" + " "*9  + "B?B" + " "*9  + "B?B" +
       " "*9  + "B?B" + " "*9  + "B?B" + " "*9  + "B?B" + " "*11 + "B?B" +
       " "*11 + "B?B" + " "*13 + "B?B" + " "*18 + "B?B"),
    _r(""),                                                                               # row 7
    # Second set of bridge platforms (row 8) – same positions as row 3
    _BRIDGES_L3,                                                                         # row 8
    _r(" "*28 + "M" + " "*38 + "M" + " "*41 + "M"),                                     # row 9 – muscle pills
    # Enemies on islands (1 per island), Flag on last island (row 10)
    _r("E" + " "*13 + "E" + " "*10 + "E" + " "*12 + "E" +
       " "*12 + "E" + " "*12 + "E" + " "*12 + "E" + " "*13 + "E" +
       " "*13 + "E" + " "*46 + "F"),
    _GROUND_L3,   # row 11
    _GROUND_L3,   # row 12
    _GROUND_L3,   # row 13
    _GROUND_L3,   # row 14
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

# ── Level 4 – La Pizzeria ──────────────────────────────────
# Indoor pizzeria theme: solid ground throughout (no pits),
# wide table platforms to jump on, oven pipe pillars as obstacles,
# ingredient question-blocks, and PizzaEnemy bosses that throw slices.
#
# Tile layout (all rows padded to 160 chars by _r()):
#   Row 2  – K coins hovering above each table
#   Row 4  – Table platforms (6 × 6-wide __)
#   Row 5  – B?B / SB? ingredient blocks between tables
#   Row 6  – ? single blocks above the gaps
#   Row 8  – T oven-pipe tops (decorative + solid obstacles)
#   Row 10 – 6 PizzaEnemy spawns + Flag
#   Rows 11-14 – solid ground

LEVEL_4 = [
    _r(""),                                                    # row 0
    _r(""),                                                    # row 1
    # K coins floating above each table position
    _r(" "*15 + "KK" + " "*17 + "KK" + " "*17 + "KK" +
       " "*17 + "KK" + " "*17 + "KK" + " "*17 + "KK"),        # row 2
    _r(""),                                                    # row 3
    # 6 wide table platforms evenly spaced
    _r(" "*12 + "______" + " "*14 + "______" + " "*14 + "______" +
       " "*14 + "______" + " "*14 + "______" + " "*14 + "______"),   # row 4
    # ingredient / power-up blocks between the tables
    _r(" "*26 + "B?B" + " "*37 + "SB?" + " "*37 + "B?B"),     # row 5
    # single ? blocks (pizza topping power-ups!)
    _r(" "*15 + "?" + " "*19 + "?" + " "*19 + "?" +
       " "*19 + "?" + " "*19 + "?" + " "*19 + "?"),            # row 6
    _r(""),                                                    # row 7
    # Oven / forno pipe-tops as pillars
    _r(" "*14 + "T" + " "*19 + "T" + " "*19 + "T" + " "*19 +
       "T" + " "*19 + "T" + " "*19 + "T" + " "*19 + "T"),     # row 8
    _r(" "*30 + "M" + " "*39 + "M" + " "*49 + "M"),     # row 9 – muscle pills
    # 6 PizzaEnemy spawns spaced 20 tiles apart; Flag near the end
    _r(" "*5 + "E" + " "*19 + "E" + " "*19 + "E" + " "*19 +
       "E" + " "*19 + "E" + " "*19 + "E" + " "*44 + "F"),     # row 10
    "G" * 160,                                                 # row 11
    "G" * 160,                                                 # row 12
    "G" * 160,                                                 # row 13
    "G" * 160,                                                 # row 14
]

# Steam-puff "clouds" (warm, subtle – indoor pizzeria atmosphere)
CLOUDS_L4 = [
    (150,  45, 0.5), (450,  30, 0.4), (800,  50, 0.5),
    (1150, 35, 0.4), (1500, 48, 0.5), (1900, 28, 0.4),
    (2300, 42, 0.5), (2700, 35, 0.4), (3200, 50, 0.5),
    (3700, 30, 0.4), (4200, 45, 0.5), (4700, 32, 0.4),
    (5200, 48, 0.5), (5700, 28, 0.4), (6200, 42, 0.5),
]

# ── Level 5 – Office (Bier Enemy) ────────────────────────────────────
# Corporate vibe: desks, office décor, Bier enemies throwing bottles.

_GROUND_L5 = "G" * 160

LEVEL_5 = [
    _r(""),                                                                               # row 0
    _r(""),                                                                               # row 1
    _r(""),                                                                               # row 2
    _r("         BBBBB                        BBBBB                         BBBBB       "),  # row 3 – office desks
    _r(""),                                                                               # row 4
    _r("    ?       B?B       ?        B?B        ?         B?B        ?       B?B     "),  # row 5
    _r("   BBB                BBB                BBB                BBB               B"),   # row 6
    _r(""),                                                                               # row 7
    _r("  T    T      T     T      T      T     T       T      T       T      T       T"),   # row 8 – pillars
    _r(" " * 10 + "M" + " " * 30 + "M" + " " * 30 + "M" + " " * 39),                    # row 9 – muscle pills
    # Bier enemies (office workers) scattered across, Flag near end
    _r("   E             E                E                 E              E" + " " * 40 + "F"),  # row 10 – 5 enemies
    _GROUND_L5,   # row 11
    _GROUND_L5,   # row 12
    _GROUND_L5,   # row 13
    _GROUND_L5,   # row 14
]

# Office-themed clouds (fluorescent, subtle)
CLOUDS_L5 = [
    (200,  50, 0.4), (600,  40, 0.5), (1000, 60, 0.4),
    (1400, 45, 0.5), (1800, 55, 0.4), (2200, 40, 0.5),
    (2600, 50, 0.4), (3000, 45, 0.5), (3400, 55, 0.4),
    (3800, 40, 0.5), (4200, 50, 0.4), (4600, 45, 0.5),
    (5000, 55, 0.4), (5400, 40, 0.5), (5800, 50, 0.4),
]
