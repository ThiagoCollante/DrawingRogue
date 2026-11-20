import math
import os
import random
import sys
from collections import deque
import pygame

# =============================================================================
# CONFIG  -  everything you might want to tweak lives here
# =============================================================================

# --- Window -------------------------------------------------------------------
WIDTH, HEIGHT = 1920, 1080     # resolution of the game (it gets stretched to fit your screen)
FPS = 120
MAX_FRAME_TIME = 0.05          # seconds; longest step the physics will take in one frame
CAPTION = "Sprite Draw  |  Left click = draw  |  WASD/arrows = move  |  Q = next target  |  C = clear  |  F = fullscreen  |  R = reload ink"
START_FULLSCREEN = True       # True = the game starts in fullscreen (press F to switch any time)
BG_COLOR = (245, 235, 215)     # beige
TEXT_COLOR = (40, 40, 60)
SHADOW_COLOR = (0, 0, 0)       # colour of all shadows
SHADOW_ALPHA = 90              # 0-255, how see-through shadows are (lower = fainter)

# --- Overall size -------------------------------------------------------------
# 0.65 = how big things look compared to the old 1280x720 version (1.0 = that size, lower = smaller).
# It is multiplied by HEIGHT / 720, so a higher resolution keeps the same look, just sharper.
UI_SCALE = 0.65 * HEIGHT / 720


def sc(value):
    """A pixel size scaled by UI_SCALE."""
    return max(1, round(value * UI_SCALE))


# --- Player (the cat) ---------------------------------------------------------
CAT_HEIGHT = sc(200)               # px, how tall the cat is drawn (bigger = bigger cat)
PLAYER_RADIUS = sc(40)             # px, size of the collision circle (keep it roughly CAT_HEIGHT * 0.36)
PLAYER_MASS = 2000 * UI_SCALE ** 2             # higher = pushes enemies more easily (enemy mass = radius^2)
PLAYER_ACCEL = 2400 * UI_SCALE            # px/s^2 while a key is held
PLAYER_FRICTION = 8.0          # how quickly it slows down when you let go (higher = stops sooner)
PLAYER_MAX_SPEED = 320 * UI_SCALE         # px/s
CAT_FACES_RIGHT = True         # set to False if your cat sprites look to the LEFT
CAT_DEAD_FILE = "catdead.png"  # sprite shown when the cat dies (falls back to the normal one if missing)
DEAD_SHADOW_SCALE = 1.6        # shadow size when the cat is dead (1.0 = same as alive)
DEAD_SHADOW_LIFT = sc(25)      # px the shadow is moved UP when the cat is dead (0 = same spot as alive)
DEATH_ANIM_TIME = 1.0          # seconds the game keeps playing after the cat dies, before the death screen
WALK_SPEED_THRESHOLD = 20 * UI_SCALE      # px/s; faster than this counts as walking
WALK_FRAME_TIME = 0.15         # seconds each walking frame is shown (lower = faster steps)

# --- Levels and exp ---
EXP_FILE = "exp.png"
EXP_HEIGHT = sc(30)            # px, how tall the orb is drawn
EXP_PER_ENEMY = 1              # orbs an enemy drops when it dies
EXP_VALUE = 1                  # exp points each orb is worth
EXP_BASE_NEEDED = 5            # exp needed to go from lv1 to lv2
EXP_NEEDED_STEP = 3            # every level needs this much more than the one before
EXP_HOVER = sc(10)             # px the orb floats above the ground
EXP_BOB_HEIGHT = sc(10)        # px it bobs up and down
EXP_BOB_SPEED = 4.0            # bob speed (radians per second)
EXP_POP_SPEED = sc(260)        # px/s the orb is tossed out when it drops
EXP_POP_FRICTION = 5.0         # how quickly the toss slows down
EXP_MAGNET_RANGE = sc(220)     # orbs closer than this to the cat fly to it
EXP_MAGNET_DELAY = 0.35        # seconds after dropping before it can be magnetised
EXP_MAGNET_START = sc(250)     # px/s speed when the pull starts...
EXP_MAGNET_MAX = sc(1400)      # ...and the top speed it accelerates to
EXP_MAGNET_ACCEL = sc(3500)    # px/s^2
EXP_PICKUP_RADIUS = sc(28)     # px from the cat's feet where the orb is collected
XPBAR_ROTATE = -90               # degrees to turn the inkbar sprite before tiling (use -90 if your sprite is a vertical bar)
XPBAR_EMPTY_ALPHA = 60         # 0-255, how faint the part of the bar that isn't filled yet is
XPBAR_TEXT_GAP = 16            # px between the level text and the remaining text
XPBAR_SCALE = 0.5              # size of the bar sprite (1.0 = its own size; the proportions are always kept)
XPBAR_FONT_SIZE = 14           # size of the "lv" text on the bar

# --- Enemies ------------------------------------------------------------------
ENEMY_COUNT = 3                # how many slimes
SLIME_TARGET_OFFSET = sc(20)   # px the target ring is lowered on a slime (0 = centred on the collision circle)
SLIME_SHADOW_SCALE = 1.3       # slime shadow size compared to normal (big and small slimes)
SLIME_FILE = "normalslime.png"                    # the slime sprite (resting / crawling)
SLIME_CHARGING_FILE = "normalslimecharging.png"   # the slime sprite while it charges a crawl
SLIME_SIZE = 0.6               # slime height compared to the cat's (1.0 = as tall as the cat; keep it below 1)
SLIME_HITBOX_SCALE = 0.9       # collision circle compared to the sprite (1.0 = circle as big as the sprite)
SLIME_MASS = 1.5               # weight compared to the cat (higher = harder to push, shoves the cat harder)
SLIME_HEALTH = 10              # health of a big slime
SLIME_SPLIT_COUNT = 2          # how many smaller slimes it splits into when it dies
SLIME_SPLIT_HEALTH = 5         # health of each smaller slime (they don't split again)
SLIME_SPLIT_SIZE = 0.65        # size of a smaller slime compared to the big one
SLIME_SPLIT_SPEED = sc(300)    # px/s the smaller slimes are flung apart with
HIT_FLASH_TIME = 0.15          # seconds an enemy flashes white when it is hit
SLIME_REST_TIME = (1.2, 1.8)   # seconds it rests between crawls (random between these two)
SLIME_CHARGE_TIME = 0.8        # seconds the whole charge lasts (squash down + charging pose)
SLIME_SQUASH_TIME = 0.35       # seconds of the charge spent squashing down (the rest is the charging sprite)
SLIME_SQUASH = 0.25            # how flat it squashes (0.25 = 25% lower, and a bit wider)
SLIME_HOLD_SQUASH = 1.0        # how much of the squash is kept in the charging pose (1 = all of it, 0 = none)
SLIME_CHARGE_SHAKE = sc(2)     # px the slime trembles in the charging pose
SLIME_CRAWL_TIME = 0.3         # seconds of the fast push forward (shorter = faster slide)
SLIME_CRAWL_DISTANCE = sc(180) # px the push is aimed to cover towards the cat
SLIME_SLIDE_FRICTION = 14.0    # friction on the end of the slide: lower = skids (overshoots) further and longer
SLIME_SPRING_TIME = 0.15       # seconds it takes to spring up from the squash when the slide starts
SLIME_SPAWN_DISTANCE = sc(300) # px the slimes start away from the cat
ENEMY_FRICTION = 3.0           # how quickly pushed enemies slow down (lower = slide further)
RESTITUTION = 0.3              # bounciness of hits: 0 = no bounce, 1 = very bouncy

# --- Statue enemy -------------------------------------------------------------
STATUE_FILE = "normalstatue.png"
STATUE_CHARGING_FILE = "normalstatuecharging.png"
STATUE_COUNT = 1               # how many statues spawn
STATUE_SIZE = 0.85             # height compared to the cat (1.0 = as tall as the cat; keep it below 1)
STATUE_HITBOX_SCALE = 0.9
STATUE_MASS = 3.0              # compared to the cat
STATUE_HEALTH = 15
STATUE_SLAM_DAMAGE = 2         # health points taken if the cat is under it when it lands
STATUE_KNOCKBACK = sc(500)     # px/s the cat is shoved away by the slam
STATUE_REST_TIME = (1.5, 2.5)  # rest between attacks
STATUE_CHARGE_TIME = 1.2       # shaking + fading into the charging sprite
STATUE_SHAKE = sc(5)           # px it trembles while charging
STATUE_RISE_TIME = 0.15        # flying up off the screen (lower = faster)
STATUE_HOVER_TIME = 0.5        # off screen, before it drops
STATUE_FALL_TIME = 0.3         # the drop
STATUE_LOCK_TIME = 0.25        # the shadow stops following the cat this long before the drop
STATUE_TRACK_SPEED = 6.0       # how fast the shadow follows the cat
STATUE_LAND_TIME = 0.7         # seconds it sits stuck after landing (a chance to hit it)
STATUE_LAND_SQUASH = 0.35      # little squash when it lands
STATUE_LAND_SQUASH_TIME = 0.25
STATUE_SHADOW_START_SCALE = 2.2   # telegraph shadow starts this many times bigger...
STATUE_SHADOW_START_ALPHA = 12    # the shadow starts this faint and ends at SHADOW_ALPHA when it lands

# --- Targeting ring around the selected enemy ---------------------------------
TARGET_FILE = "target.png"     # the circle sprite (white and grey areas) in the assets folder
TARGET_RING_GAP = sc(50)            # target circle radius = enemy radius + this
TARGET_BOB_FRACTION = 0.15     # the circle grows/shrinks by this fraction of its size
TARGET_BOB_SPEED = 3.0         # grow/shrink speed (radians per second)
TARGET_SPIN_SPEED = 120        # degrees per second the sprite spins
TARGET_RANGE = sc(350)             # enemies closer than this to the player are "near"
TARGET_WHITE_LEVEL = 240       # brightness (0-255) that counts as "white" = the plain ink colour
TARGET_SHADE_STRENGTH = 1.0    # how dark the grey areas get: 0 = no shading, 1 = full

# --- Drawing / brush ----------------------------------------------------------
BRUSH_SCALE = 0.6 * UI_SCALE              # 1.0 = original size of the brush sprites
INK_COLOR = (15, 30, 110)      # dark blue (the final ink colour, also used by the targets)
INK_START_COLOR = (90, 170, 255)  # brighter colour that fresh ink starts with
INK_FADE_TIME = 0.5            # seconds it takes the fresh ink to fade into INK_COLOR
STAMP_SPACING = 0.2            # distance between stamps as a fraction of the brush size (smaller = smoother)

# --- Notebook (the "paper" you draw on) ---------------------------------------
NOTEBOOK_FILE = "notebook.png"            # the picture of the notebook
NOTEBOOK_AREA_FILE = "notebook_area.png"  # same picture, drawable zone painted red
NOTEBOOK_HEIGHT_FRACTION = 0.34           # visible notebook height as a fraction of the window
NOTEBOOK_MAX_W_FRACTION = 0.38             # ...but never wider than this fraction of the window
NOTEBOOK_PADDING = sc(24)                     # gap (px) between the notebook and the window edges

# --- Floor tiles --------------------------------------------------------------
TILES_FOLDER = "tiles"         # folder inside assets
TILE_BASE_NAME = "dirt"        # dirt.png = the floor tile; every other dirt*.png = a decoration
TILE_SIZE = sc(96)             # px, how wide one tile is drawn (decorations use the same scale)
TILE_DECOR_CHANCE = 0.04       # chance (0-1) that a tile also gets a decoration (low = rare)
TILE_DECOR_FLIP = True         # True = decorations are randomly mirrored for more variety
CHUNK_TILES = 8                # the floor is built in square chunks of this many tiles per side
CAMERA_SMOOTHING = 10.0        # how fast the camera catches up with the cat (higher = snappier, 0 = locked on)

# --- Falling page (when you clear the drawing with C) -------------------------
PAGE_FILE = "page.png"         # notebook.png with only the page left (same canvas size as notebook.png)
PAGE_GRAVITY = 1600 * UI_SCALE            # px/s^2, how fast the page speeds up while falling
PAGE_SPIN = 40                 # max degrees/s the page tilts while falling (counter-clockwise, into the curve)
PAGE_CURVE = 1200 * UI_SCALE              # px/s^3, how strongly the fall bends to the left (0 = straight down)

# --- Ink (drains while you draw, press R to refill) ---------------------------
SPELL_LABEL_SIZE = 18        # size of the spell name shown under the notebook (smaller = smaller text)
INK_DRAW_LENGTH = sc(3000)     # px of line a full ink bar can draw
INKBAR_HEIGHT_RATIO = 1.0      # height of the ink bar holder compared to the notebook's height
INKBAR_GAP = sc(24)            # px between the notebook and the ink bar holder
INKBAR_SMOOTHING = 8.0         # how fast the shown bar follows the real ink level (higher = snappier)
INKBAR_TINT = True             # True = the bar sprite is coloured with the ink colour (greys = darker); False = its own colours
INKER_TINT = True              # same for the inker sprite
HUD_FADE_ALPHA = 0.3           # how see-through the notebook / ink bar get when something is under them (0 = invisible, 1 = solid)
HUD_FADE_SPEED = 10.0          # how fast they fade in and out (higher = faster)

# --- Health (hearts) ----------------------------------------------------------
HEART_COUNT = 12               # number of hearts; each one holds 2 health points (full / half / empty)
HEART_COLUMNS = 6              # hearts per row (12 hearts with 6 per row = two rows)
HEART_SIZE = sc(44)            # px, how tall a heart is drawn
HEART_GAP = sc(8)              # px between hearts
HEART_EMPTY_SCALE = 0.75       # size of the empty heart compared to the others (1.0 = same size)
HEART_FULL_FILE = "heartfull.png"      # the three heart sprites in the assets folder
HEART_HALF_FILE = "hearthalf.png"
HEART_EMPTY_FILE = "heartempty.png"
HEART_TINT = True              # True = hearts are coloured with the ink colour (white areas = ink colour, greyer areas = lighter)
HEART_LIGHTEN = 1.0            # how much lighter the grey areas get (0 = not at all, 1 = fully)
SLIME_DAMAGE = 1               # health points a slime takes away when it touches the cat (1 = half a heart, 2 = a whole heart)
PLAYER_INVULN_TIME = 1.2       # seconds the cat can't be hurt again after a hit (it blinks)

# --- Reload animation (R) -----------------------------------------------------
INKER_HEIGHT = sc(35)          # px, how tall the inker is drawn
PENCIL_HEIGHT = sc(60)         # px, how tall the pencil is drawn
PENCIL_ANGLE_OFFSET = 0        # degrees; turn the pencil if your sprite does not point down
RELOAD_LIFT = sc(40)           # px the inker and pencil are raised above the cat's feet (higher = further up)
RELOAD_DISTANCE = sc(45)       # px from the cat's centre to the middle of the inker (smaller = closer to the cat)
RELOAD_SIDE_SPEED = 12.0       # how fast the inker slides to the other side when the cat turns around
RELOAD_HOVER = sc(16)          # px the pencil hovers above the inker between dips
RELOAD_DIP_DEPTH = 0.30        # how far the tip goes into the inker (fraction of the inker's height)
RELOAD_DIPS = 3                # how many times the pencil dips
RELOAD_POP_TIME = 0.30         # seconds the inker / the pencil take to puff into existence
RELOAD_TWIRL_TIME = 0.70       # seconds the pencil twirls
RELOAD_DIP_TIME = 0.45         # seconds per dip
RELOAD_OUT_TIME = 0.30         # seconds they take to puff away at the end
PUFF_COLOR = (255, 255, 255)   # colour of the puffs of smoke
PUFF_COUNT = 9                 # puffs per appearance

# --- Slash spell (draw a diagonal line + a semicircle to hit the targeted enemy) ---

SLASH_DAMAGE = 5               # damage the slash spell deals to the targeted enemy
SLASH_USE_TEMPLATE = True      # also accept the old traced-fang template match (a second way to pass)
SLASH_MATCH_THRESHOLD = 0.09    # was 0.15
SLASH_TILT = 15                 # was 25
SLASH_LINE_STRAIGHTNESS = 0.10  # was 0.18
SLASH_DIAG_MIN = 15            # the line's tilt from horizontal must be between these (degrees)
SLASH_DIAG_MAX = 75
SLASH_ALLOW_MIRROR = True      # True = the line may also fall to the right; False = only rise to the right
SLASH_END_TOLERANCE = 0.25      # was 0.4
SLASH_CURVE_MIN = 0.3           # was 0.15
SLASH_CURVE_MAX = 0.7           # was 0.9
# --- Slash animation (the sprite that swipes across the enemy) ---
SLASH_FILE = "slash.png"       # long on the x axis, with a red area
SLASH_COLOR = INK_COLOR        # the red area is painted in this colour
SLASH_LENGTH = sc(70)         # px, how long the sprite is when it is not stretched
SLASH_STRETCH = 2.2            # how many times longer it gets in the middle of the line
SLASH_REACH = sc(90)           # px from the enemy's edge to each end of the line
SLASH_TIME = 0.1               # seconds the whole swipe lasts
SLASH_FACES_RIGHT = True       # set to False if the tip of your sprite points to the LEFT

# --- Spell vanish effect (when a spell is drawn correctly) --------------------

SPELL_PAGE_COLOR = INK_START_COLOR  # the page turns into the bright version of the ink colour
SPELL_PAGE_GLOW = (10, 10, 0)       # added on top so it looks a bit brighter
SPELL_PURPLE_TIME = 0.35            # seconds the page takes to turn purple
SPELL_DISSOLVE_TIME = 0.7           # seconds it then takes to crumble into particles
SPELL_PARTICLES = 260               # particles in total
SPELL_PARTICLE_COLORS = [INK_START_COLOR, (150, 205, 255), (235, 245, 255), INK_COLOR]
SPELL_FIZZLE_TIME = 2.0             # seconds the "ink outside the page" message stays

# --- Chain spell (draw a long diagonal S to lock the targeted enemy in place) ---
CHAIN_TIME = 4.0               # seconds the enemy stays locked
CHAIN_ALL_ENEMIES = False      # False = only the targeted enemy, True = every enemy
CHAIN_FILE = "chain.png"       # the chain link (its left and right borders connect to itself)
CHAIN_END_FILE = "chainend.png"  # the end piece on the floor (its right border connects to the chain)
CHAIN_HEIGHT = sc(28)          # px, how tall the chain is drawn (the end piece uses the same scale)
CHAIN_TINT = True              # True = chains are coloured with the ink colour (greys = darker); False = their own colours
CHAIN_LINK_OVERLAP = 0         # px each link overlaps the previous one (raise it if you see gaps)
CHAIN_REACH = sc(90)           # px from the enemy's edge to the end piece on the floor
CHAIN_ATTACH = 0.85             # where the chain meets the enemy: fraction of its radius from the centre
CHAIN_ANGLES = (45, 135, 225, 315)  # directions of the 4 chains (degrees, 0 = right, 90 = down)
CHAIN_MASS_MULT = 1000         # a locked enemy counts this many times heavier, so the cat can't push it
CHAIN_WARN_TIME = 0.8          # seconds before the end that the chains start blinking
# recognition of the drawing
CHAIN_HOOK_TURN = 100           # was 140 (original 90)
CHAIN_MIN_ASPECT = 1.2          # was 2.0 (original 1.2)
CHAIN_DIAG_MIN = 15            # the drawing's tilt from horizontal must be between these (degrees)
CHAIN_DIAG_MAX = 80
CHAIN_ALLOW_MIRROR = True      # True = it may also lean to the left
CHAIN_HOOK_CONSISTENCY = 0.5    # was 0.7

# --- Ink area spell (draw a spiral to leave a slowing zone on the floor around the cat) ---
INK_AREA_RADIUS = sc(260)      # px, radius of the zone
INK_AREA_TIME = 8.0            # seconds the zone stays
INK_AREA_SLOW = 0.4            # enemies inside move at this fraction of their normal speed (0.4 = 40%)
INK_AREA_MAX = 3               # how many zones can exist at once (the oldest one goes first)
INK_AREA_POP_TIME = 0.3        # seconds the zone takes to grow when cast
INK_AREA_WARN_TIME = 1.0       # seconds the ring takes to speed up before it starts shrinking
INK_AREA_SHRINK_TIME = 0.6     # seconds the zone takes to shrink away at the very end
INK_AREA_SPIN_BOOST = 6.0      # how many times faster the ring spins by the time it starts shrinking
INK_AREA_FILL_ALPHA = 70       # 0-255, how see-through the fill is (the fill uses the ink colour)
INK_AREA_RING_FILE = "inkarearing.png"   # white tile that connects to itself along the x axis
INK_AREA_RING_HEIGHT = sc(80)            # px, how thick the ring is (the tile is scaled to this height)
INK_AREA_SPIN = 20                       # degrees per second the ring turns (negative = the other way)
INK_AREA_RING_TOP_OUT = True             # True = the top of the tile faces outwards; False = it faces inwards
INK_AREA_RING_QUALITY = 2                # the ring is built this many times bigger, then shrunk (smoother edges, slower start)
INK_AREA_RING_TILES = 10                  # how many tiles go around the ring (fewer = bigger tiles); 0 = automatic from the ring's thickness
INK_AREA_OUTLINE_WIDTH = sc(5)
INK_AREA_OUTLINE_COLOR = tuple(round(c * 0.55) for c in INK_COLOR)   # darker than the ink, fully solid
# recognition of the drawing
INK_AREA_MIN_TURN = 480         # was 540 (original 450)
INK_AREA_CONSISTENCY = 0.8      # was 0.85 (original 0.75)
INK_AREA_END_TOLERANCE = 0.3    # was 0.25 (original 0.35)
INK_AREA_ALLOW_MIRROR = True   # True = the spiral may turn either way

# --- Arrow spell (draw a "4": a straight stick with an angular arrowhead) ---
ARROW_FILE = "arrowprojectilespell.png"   # the projectile, with the point facing UP
ARROW_HEIGHT = sc(90)         # px, how big the arrow is drawn (its length before stretching)
ARROW_STRETCH = 2           # how many times longer it is stretched along its length (1 = not stretched)
ARROW_COLOR = INK_COLOR        # the red area of the sprite is painted in this colour
ARROW_SPEED = sc(1000)         # px/s
ARROW_RADIUS = sc(10)          # px, how wide its hit area is (added to each enemy's radius)
ARROW_PIERCE_DAMAGE = 2.5      # damage to every enemy it passes through
ARROW_HIT_DAMAGE = 5           # damage to the targeted enemy, where the arrow ends
ARROW_LIFETIME = 2.5           # seconds before it disappears if it never reaches its target
# recognition of the drawing
ARROW_SHAFT_RATIO = 0.4        # the straight stick must be at least this fraction of the whole stroke
ARROW_SHAFT_STRAIGHTNESS = 0.08 # was 0.12
ARROW_HEAD_TURN_MIN = 200      # degrees the head must turn in total...
ARROW_HEAD_TURN_MAX = 430      # ...and at most (a spiral turns more, so it stays a different spell)
ARROW_HEAD_CONSISTENCY = 0.85   # was 0.75
ARROW_HEAD_MIN_SIZE = 0.15     # head size compared to the stick's length (smallest)...
ARROW_HEAD_MAX_SIZE = 1.0      # ...and (biggest)
ARROW_CORNERS = 2              # sharp corners the stroke needs (the tip of the stick counts as one)
ARROW_CORNER_WINDOW = 3        # samples looked at on each side of a corner
ARROW_CORNER_ANGLE = 70         # was 60

# --- Shockwave spell (draw a jagged ring to blast everything around the cat) ---
SHOCKWAVE_DAMAGE = 2           # damage to every enemy the wave touches (once each)
SHOCKWAVE_RADIUS = round(INK_AREA_RADIUS * 1.5)   # px, how far the wave reaches (1.6 = 60% bigger than the ink area)
SHOCKWAVE_TIME = 0.2           # seconds the ring takes to expand (was 0.5)
SHOCKWAVE_FADE_TIME = 0.35     # seconds the wave takes to vanish after it has fully expanded
SHOCKWAVE_SPIN = 0           # degrees per second the ring turns (negative = the other way)
SHOCKWAVE_FILL_ALPHA = 110     # 0-255, how strong the fill is at the ring (it fades to nothing towards the middle)
SHOCKWAVE_FILL_FALLOFF = 2   # how fast the fill fades towards the middle (higher = the middle stays clear for longer)
# recognition of the drawing: an upside-down V (a "^") with an optional little hook at each foot
SHOCKWAVE_CORNERS = 3          # sharp corners it needs in total (the tip counts as one, each hook adds more; set to 1 to accept a plain ^)
SHOCKWAVE_CORNER_WINDOW = 3    # samples looked at on each side of a corner
SHOCKWAVE_CORNER_ANGLE = 40    # degrees of turning that count as a sharp corner
SHOCKWAVE_APEX_MIN = 30        # the angle at the tip of the ^ must be between these (degrees)
SHOCKWAVE_APEX_MAX = 120
SHOCKWAVE_LEG_RATIO = 0.2      # each leg must be at least this fraction of the whole stroke
SHOCKWAVE_LEG_BALANCE = 0.5    # the shorter leg must be at least this fraction of the longer one
SHOCKWAVE_LEG_STRAIGHTNESS = 0.12  # how wobbly the legs may be (higher = more forgiving)
SHOCKWAVE_APEX_RANGE = (0.25, 0.75)  # the tip must be this far along the stroke (fraction of its length)
SHOCKWAVE_TILT = 35            # degrees the ^ may be turned and still count
SHOCKWAVE_ANY_ROTATION = False # True = it may point in any direction (a "v", "<" or ">" counts too)

# --- Lightning Step spell (draw a lightning bolt: bar right, diagonal down-left, bar right, diagonal down-left) ---
LIGHTNING_TIME = 5.0           # seconds the boost lasts (casting it again while active does nothing: no stacking)
LIGHTNING_ACCEL_MULT = 1.6     # acceleration multiplier while active
LIGHTNING_SPEED_MULT = 1.6     # top speed multiplier while active
LIGHTNING_SPARK_COLORS = [(150, 205, 255), (235, 245, 255), (255, 240, 150)]
# recognition of the drawing (no mirror, no tilt: the segment directions must match closely)
LIGHTNING_ANGLES = (0, 216, 0, 241)   # direction of each of the 4 segments, degrees (0 = right, 90 = up)
LIGHTNING_ALLOW_REVERSE = True        # True = it may also be drawn starting from the bottom
LIGHTNING_ANGLE_TOL = 25              # degrees each segment may be off (lower = stricter)
LIGHTNING_CORNER_WINDOW = 3           # samples looked at on each side of a corner
LIGHTNING_CORNER_ANGLE = 60           # degrees of turning that count as a sharp corner
LIGHTNING_SEG_MIN = 0.10              # each segment must be at least this fraction of the whole stroke
LIGHTNING_STRAIGHTNESS = 0.20         # how wobbly each segment may be (higher = more forgiving)

# --- Shield spell (draw a "U": gives extra hearts under the health bar, each one absorbs one hit) ---
SHIELD_FILE = "shieldspell.png"   # the spell sprite, also used for the little shield hearts
SHIELD_HEARTS = 3                 # extra hits it absorbs (casting again only refills it, no stacking)
SHIELD_ICON_SIZE = sc(30)         # px, how tall each shield heart is (hearts are HEART_SIZE, so this is smaller)
SHIELD_GAP = sc(8)                # px between shield hearts
SHIELD_TOP_GAP = sc(6)            # px between the hearts and the shield row
# recognition of the drawing (a U, any size, either direction)
SHIELD_MIN_ASPECT = 0.4           # width / height of the drawing must be between these
SHIELD_MAX_ASPECT = 2.5
SHIELD_BOTTOM_RANGE = (0.25, 0.75)  # the lowest point must be this far along the stroke
SHIELD_END_HEIGHT = 0.45          # both ends must be in the top part of the drawing (fraction of its height)
SHIELD_MIN_GAP = 0.3              # the two ends must be at least this far apart (fraction of its width)
SHIELD_MIN_TURN = 140             # total turning in degrees (a U turns about 180)
SHIELD_MAX_TURN = 270             # (more than this is a spiral / loop)
SHIELD_CONSISTENCY = 0.8          # how much of the turning must go the same way

# --- Waves ---
WAVE_SPAWN_MARGIN = 60         # px past the screen edge (beyond the enemy's own size) where enemies appear
WAVE_SPAWN_DELAY = 0.3         # seconds the puff plays before the enemy pops out (it can't act or be hit meanwhile)
WAVE_TIME = 30.0               # seconds per wave; the next one spawns when it runs out, beaten or not
WAVE_SLIMES_BASE = 3           # slimes in wave 1
WAVE_SLIMES_STEP = 1           # extra slimes in every following wave
WAVE_SLIMES_MAX = 6           # most slimes a single wave can have
WAVE_STATUES_AFTER = 4        # statues can appear once this many waves have passed (first ones in wave 6)
WAVE_STATUE_STEP = 5           # one more statue every this many waves
WAVE_MAX_ALIVE = 80            # no new enemies spawn while this many are alive (stops the screen from flooding)
WAVE_SHOW_COUNTDOWN = False    # False = shows the total time survived, True = shows the time left in the current wave
WAVE_TIMER_FONT_SIZE = 26      # size of the timer digits
WAVE_TIMER_GAP = 10            # px between the hearts and the timer

# --- Shape recognition (advanced) ---------------------------------------------
N_SAMPLES = 64        # points the stroke is resampled to
CORNER_WINDOW = 6     # how many samples to look back/forward for a turn
CORNER_ANGLE = 55     # degrees of turning needed to count as a corner
CLOSED_RATIO = 0.20   # start/end gap smaller than 20% of the path = closed
MIN_SIZE = sc(60)         # pixels; drawings whose bounding box is smaller are gibberish

# =============================================================================
# END CONFIG
# =============================================================================

pygame.init()

# SCALED keeps the game at WIDTH x HEIGHT and stretches it to the screen (mouse position is mapped for us)
screen = pygame.display.set_mode((WIDTH, HEIGHT),
                                 pygame.SCALED | (pygame.FULLSCREEN if START_FULLSCREEN else 0))
pygame.display.set_caption(CAPTION)
clock = pygame.time.Clock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Camera: the world is infinite, the screen is a window onto it ---------------
cam = pygame.math.Vector2(0, 0)        # top-left corner of the view in world coordinates (whole pixels)
_cam_f = pygame.math.Vector2(0, 0)     # the smooth, fractional version of it


def view(x, y):
    """World position -> screen position."""
    return (round(x - cam.x), round(y - cam.y))


def update_camera(dt):
    target = player_pos - pygame.math.Vector2(WIDTH / 2, HEIGHT / 2)    # puts the cat in the middle
    if CAMERA_SMOOTHING > 0:
        _cam_f.update(_cam_f + (target - _cam_f) * min(1.0, CAMERA_SMOOTHING * dt))
    else:
        _cam_f.update(target)
    cam.update(round(_cam_f.x), round(_cam_f.y))

# ---------------------------------------------------------------------------
# SHAPE RECOGNITION
# Works on the raw mouse points of ONE stroke (press -> release).
# Steps: remove duplicates -> decide open/closed -> resample evenly ->
# smooth -> find corners (sharp turns) -> classify.
# ---------------------------------------------------------------------------
def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _resample(pts, n, closed):
    """Return n points spaced evenly along the path."""
    if closed:
        pts = pts + [pts[0]]
    cum = [0.0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + _dist(pts[i - 1], pts[i]))
    total = cum[-1]
    step = total / (n if closed else n - 1)
    out, j = [], 0
    for i in range(n):
        target = i * step
        while j < len(cum) - 2 and cum[j + 1] < target:
            j += 1
        seg = cum[j + 1] - cum[j]
        t = (target - cum[j]) / seg if seg > 0 else 0.0
        t = max(0.0, min(1.0, t))
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t,
                    pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t))
    return out


def _smooth(pts, closed, w=2):
    """Moving average to remove hand jitter."""
    n = len(pts)
    out = []
    for i in range(n):
        xs = ys = 0.0
        for d in range(-w, w + 1):
            idx = (i + d) % n if closed else max(0, min(n - 1, i + d))
            xs += pts[idx][0]
            ys += pts[idx][1]
        out.append((xs / (2 * w + 1), ys / (2 * w + 1)))
    return out


def _find_corners(pts, closed):
    """Indices of points where the path turns sharply."""
    n, k = len(pts), CORNER_WINDOW
    idx_range = range(n) if closed else range(k, n - k)
    angles = {}
    for i in idx_range:
        a = (pts[i][0] - pts[(i - k) % n][0], pts[i][1] - pts[(i - k) % n][1])
        b = (pts[(i + k) % n][0] - pts[i][0], pts[(i + k) % n][1] - pts[i][1])
        la, lb = math.hypot(*a), math.hypot(*b)
        if la == 0 or lb == 0:
            continue
        c = max(-1.0, min(1.0, (a[0] * b[0] + a[1] * b[1]) / (la * lb)))
        angles[i] = math.degrees(math.acos(c))

    candidates = sorted((i for i, a in angles.items() if a >= CORNER_ANGLE),
                        key=lambda i: -angles[i])
    corners = []
    for i in candidates:  # keep only the strongest corner in each neighbourhood
        too_close = False
        for j in corners:
            d = abs(i - j)
            if closed:
                d = min(d, n - d)
            if d <= k:
                too_close = True
                break
        if not too_close:
            corners.append(i)
    return sorted(corners)


def _pca(pts):
    """Centre, eigenvalues and main axis of the point cloud."""
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - cx) ** 2 for p in pts) / n
    syy = sum((p[1] - cy) ** 2 for p in pts) / n
    sxy = sum((p[0] - cx) * (p[1] - cy) for p in pts) / n
    half_tr = (sxx + syy) / 2
    disc = math.sqrt(max(0.0, half_tr ** 2 - (sxx * syy - sxy ** 2)))
    l1, l2 = half_tr + disc, max(half_tr - disc, 1e-9)
    if abs(sxy) > 1e-9:
        vx, vy = l1 - syy, sxy
    else:
        vx, vy = (1.0, 0.0) if sxx >= syy else (0.0, 1.0)
    norm = math.hypot(vx, vy) or 1.0
    return (cx, cy), l1, l2, (vx / norm, vy / norm)


def _ellipse_fit_error(pts, centre, l1, l2, axis):
    """Stretch the points so an ellipse becomes a circle, then measure how
    much the radius varies (0 = perfect ellipse/circle)."""
    vx, vy = axis
    radii = []
    for x, y in pts:
        dx, dy = x - centre[0], y - centre[1]
        u = (dx * vx + dy * vy) / math.sqrt(l1)
        v = (-dx * vy + dy * vx) / math.sqrt(l2)
        radii.append(math.hypot(u, v))
    mean = sum(radii) / len(radii)
    var = sum((r - mean) ** 2 for r in radii) / len(radii)
    return math.sqrt(var) / mean if mean else 1.0


DIRECTIONS = ["right", "up-right", "up", "up-left", "left", "down-left", "down", "down-right"]


def _direction_name(angle):
    """angle in degrees, 0 = right, 90 = up (screen y is flipped by the caller)."""
    return DIRECTIONS[int(round(angle / 45.0)) % 8]


def _vec_angle(dx, dy):
    """Angle of a screen vector, counted counter-clockwise with 'up' = 90."""
    return math.degrees(math.atan2(-dy, dx)) % 360


def _line_orientation(dx, dy):
    a = _vec_angle(dx, dy) % 180  # a line has no direction, only a tilt
    if a <= 15 or a >= 165:
        return "Horizontal"
    if 75 <= a <= 105:
        return "Vertical"
    if a < 90:
        return f"Diagonal, rising to the right ({a:.0f}\u00b0)"
    return f"Diagonal, falling to the right ({180 - a:.0f}\u00b0)"


def _square_orientation(q):
    """Tilt of the square: mean edge angle folded into -45..45 degrees."""
    sx = sy = 0.0
    for i in range(4):
        a = math.radians(_vec_angle(q[(i + 1) % 4][0] - q[i][0], q[(i + 1) % 4][1] - q[i][1]))
        sx += math.cos(4 * a)
        sy += math.sin(4 * a)
    tilt = math.degrees(math.atan2(sy, sx)) / 4  # -45..45, positive = counter-clockwise
    if abs(tilt) <= 8:
        return "Upright (sides horizontal/vertical)"
    if abs(tilt) >= 37:
        return "Diamond (rotated 45\u00b0)"
    way = "counter-clockwise" if tilt > 0 else "clockwise"
    return f"Rotated {abs(tilt):.0f}\u00b0 {way}"


def _triangle_orientation(q):
    """Direction the 'tip' of the triangle points to.
    - Clearly isosceles triangle: the tip is the apex (the vertex between the two equal sides).
    - Roughly equilateral: the tip is the corner that points closest to up/down/left/right."""
    cx = sum(p[0] for p in q) / 3
    cy = sum(p[1] for p in q) / 3
    side = [_dist(q[i], q[(i + 1) % 3]) for i in range(3)]
    mean_side = sum(side) / 3
    # diff[i] = how unequal the two sides meeting at vertex i are
    diff = [abs(side[i - 1] - side[i]) / mean_side for i in range(3)]
    order = sorted(range(3), key=lambda i: diff[i])
    if diff[order[0]] < 0.12 and diff[order[1]] - diff[order[0]] > 0.15:
        tip = order[0]
    else:
        def off_cardinal(i):
            ang = _vec_angle(q[i][0] - cx, q[i][1] - cy)
            return abs(((ang - 90 * round(ang / 90)) + 180) % 360 - 180)
        tip = min(range(3), key=off_cardinal)

    ang = _vec_angle(q[tip][0] - cx, q[tip][1] - cy)
    idx = int(round(ang / 45.0)) % 8
    delta = ((ang - idx * 45) + 180) % 360 - 180  # + = counter-clockwise
    text = "Pointing " + DIRECTIONS[idx]
    if abs(delta) > 8:
        text += f", tilted {abs(delta):.0f}\u00b0 {'counter-clockwise' if delta > 0 else 'clockwise'}"
    return text


def _curve_orientation(s):
    """Which way the curve bulges (away from the straight line start -> end)."""
    chord = _dist(s[0], s[-1])
    mx, my = (s[0][0] + s[-1][0]) / 2, (s[0][1] + s[-1][1]) / 2
    if chord < 1e-6:
        return "Unclear"
    dx, dy = s[-1][0] - s[0][0], s[-1][1] - s[0][1]
    far = max(s, key=lambda p: abs(dx * (p[1] - s[0][1]) - dy * (p[0] - s[0][0])))
    return "Bulging " + _direction_name(_vec_angle(far[0] - mx, far[1] - my))


def _classify_quad(s, corners):
    q = [s[i] for i in corners]
    angles = []
    for i in range(4):
        a, b, c = q[i - 1], q[i], q[(i + 1) % 4]
        v1 = (a[0] - b[0], a[1] - b[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        cosv = (v1[0] * v2[0] + v1[1] * v2[1]) / ((math.hypot(*v1) * math.hypot(*v2)) or 1)
        angles.append(math.degrees(math.acos(max(-1.0, min(1.0, cosv)))))
    if not all(abs(a - 90) <= 25 for a in angles):
        return GIBBERISH
    sides = [_dist(q[i], q[(i + 1) % 4]) for i in range(4)]
    w, h = (sides[0] + sides[2]) / 2, (sides[1] + sides[3]) / 2
    if min(w, h) / max(w, h) < 0.7:      # a clearly long rectangle is not a square
        return GIBBERISH
    return ("Square", _square_orientation(q))


def _classify_closed(s, corners):
    centre, l1, l2, axis = _pca(s)
    aspect = math.sqrt(l1 / l2)
    if aspect > 6:                       # drawn back and forth on itself
        return ("Line", _line_orientation(axis[0], axis[1]))
    n = len(corners)
    if n <= 2:  # tight ends of an ellipse can look like corners, so test the fit first
        if _ellipse_fit_error(s, centre, l1, l2, axis) <= 0.22 and aspect < 1.4:
            return ("Circle", None)
        return GIBBERISH
    if n == 3:
        return ("Triangle", _triangle_orientation([s[i] for i in corners]))
    if n == 4:
        return _classify_quad(s, corners)
    return GIBBERISH


def _classify_open(s, corners):
    chord = _dist(s[0], s[-1])
    if chord > 1e-6:
        dx, dy = s[-1][0] - s[0][0], s[-1][1] - s[0][1]
        dev = max(abs(dx * (p[1] - s[0][1]) - dy * (p[0] - s[0][0])) / chord for p in s)
        if dev / chord < 0.07:
            return ("Line", _line_orientation(dx, dy))
    n = len(corners)
    if n == 0:
        return ("Curve", _curve_orientation(s))
    if n >= 2:
        _, _, _, axis = _pca(s)
        return ("Zigzag", _line_orientation(axis[0], axis[1]))
    return GIBBERISH


# --- The slash spell: a diagonal line + a semicircle that leaves the tip of the line and
# curves back to the line's centre. Two ways to pass:
#   1) the shape check (_slash_shape_match): proportions only, any size / position / order / mirror
#   2) the old traced centre line of the claw sprite (x, y points), size and position don't matter,
#      a small tilt is allowed, and it can be drawn from either end.
SLASH_TEMPLATE = [
    (69, 304), (95, 297), (120, 288), (144, 276), (167, 263), (190, 249), (213, 233), (234, 216),
    (253, 195), (269, 173), (283, 150), (297, 127), (311, 104), (323, 81), (330, 63), (332, 62),
    (335, 80), (341, 105), (347, 131), (350, 159), (351, 187), (351, 216), (351, 244), (348, 272),
    (338, 297), (321, 318), (299, 333), (275, 343), (248, 347), (221, 343), (197, 332), (179, 314),
    (169, 291),
]
SLASH_POINTS = 64     # points the stroke and the template are compared with


def _normalize_path(pts):
    """Centre a path and scale it so its longest side is 1."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    size = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    return [((x - cx) / size, (y - cy) / size) for x, y in pts]


def _rotate_path(pts, degrees):
    c, s_ = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return [(x * c - y * s_, x * s_ + y * c) for x, y in pts]


_slash_forward = _normalize_path(_resample(SLASH_TEMPLATE, SLASH_POINTS, False))
_slash_backward = _slash_forward[::-1]


def _slash_score(pts):
    """How far (0 = identical, as a fraction of the drawing's size) the stroke is from the slash shape."""
    cand = _normalize_path(_smooth(_resample(pts, SLASH_POINTS, False), False, w=1))
    best = 1e9
    angle = -SLASH_TILT
    while angle <= SLASH_TILT + 1e-9:
        rotated = _rotate_path(cand, angle)
        for template in (_slash_forward, _slash_backward):
            d = sum(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(rotated, template)) / SLASH_POINTS
            best = min(best, d)
        angle += 5
    return best


def _perp_devs(seg):
    """Chord length of a segment and each point's signed distance from that chord."""
    a, b = seg[0], seg[-1]
    chord = _dist(a, b)
    if chord < 1e-6:
        return chord, []
    dx, dy = b[0] - a[0], b[1] - a[1]
    return chord, [(dx * (p[1] - a[1]) - dy * (p[0] - a[0])) / chord for p in seg]


def _path_len(seg):
    return sum(_dist(seg[i - 1], seg[i]) for i in range(1, len(seg)))


def _check_slash_parts(L, C):
    """L = the line, C = the curve; both start at the tip where they meet."""
    lc, ldev = _perp_devs(L)
    if lc < 1e-6:
        return False
    # 1) the line is fairly straight (the first points near the tip are rounded by smoothing, so skip them)
    if max(abs(d) for d in ldev[2:]) / lc > SLASH_LINE_STRAIGHTNESS:
        return False
    # 2) the line is diagonal
    a = _vec_angle(L[-1][0] - L[0][0], L[-1][1] - L[0][1]) % 180
    if not (SLASH_DIAG_MIN <= min(a, 180 - a) <= SLASH_DIAG_MAX):
        return False
    if not SLASH_ALLOW_MIRROR and a >= 90:
        return False
    # 3) the curve ends near the center of the line
    mid = ((L[0][0] + L[-1][0]) / 2, (L[0][1] + L[-1][1]) / 2)
    if _dist(C[-1], mid) > SLASH_END_TOLERANCE * lc:
        return False
    # 4) the curve is a real bend to ONE side, roughly semicircle-sized
    cc, cdev = _perp_devs(C)
    if cc < 0.2 * lc:
        return False
    pos, neg = max(max(cdev), 0), max(-min(cdev), 0)
    big, small = max(pos, neg), min(pos, neg)
    if not (SLASH_CURVE_MIN <= big / cc <= SLASH_CURVE_MAX) or small > 0.3 * big:
        return False
    if _path_len(C) / cc > 2.4:          # no spirals / scribbles
        return False
    return True


def _slash_shape_match(pts):
    """Try every point of the stroke as the tip; the line may be drawn first or second."""
    s = _smooth(_resample(pts, SLASH_POINTS, False), False, w=1)
    n = len(s)
    for i in range(int(n * 0.1), int(n * 0.9) + 1):
        before, after = s[i::-1], s[i:]            # both start at the tip
        if len(before) < 5 or len(after) < 5:
            continue
        if _check_slash_parts(before, after) or _check_slash_parts(after, before):
            return True
    return False

def _signed_turns(s):
    """Turning angle in degrees at every point of a path (+ one way, - the other)."""
    turns, prev = [], None
    for i in range(1, len(s)):
        v = (s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1])
        if math.hypot(*v) < 1e-9:
            continue
        if prev is not None:
            cross = prev[0] * v[1] - prev[1] * v[0]
            dot = prev[0] * v[0] + prev[1] * v[1]
            turns.append(math.degrees(math.atan2(cross, dot)))
        prev = v
    return turns


def _chain_shape_match(pts):
    """A long diagonal S: two hooks that curl in OPPOSITE directions."""
    s = _smooth(_resample(pts, N_SAMPLES, False), False, w=2)
    _, l1, l2, axis = _pca(s)
    if math.sqrt(l1 / l2) < CHAIN_MIN_ASPECT:
        return False
    a = _vec_angle(axis[0], axis[1]) % 180
    if not (CHAIN_DIAG_MIN <= min(a, 180 - a) <= CHAIN_DIAG_MAX):
        return False
    if not CHAIN_ALLOW_MIRROR and a >= 90:
        return False
    turns = _signed_turns(s)
    n = len(turns)
    if n < 10:
        return False
    pre = [0.0]
    for t in turns:
        pre.append(pre[-1] + t)
    for k in range(n // 5, n * 4 // 5 + 1):          # try every split point between the two hooks
        first, second = pre[k], pre[n] - pre[k]
        if first * second < 0 and min(abs(first), abs(second)) >= CHAIN_HOOK_TURN:
            a_total = sum(abs(t) for t in turns[:k])
            b_total = sum(abs(t) for t in turns[k:])
            if a_total > 0 and b_total > 0 and \
               abs(first) / a_total >= CHAIN_HOOK_CONSISTENCY and \
               abs(second) / b_total >= CHAIN_HOOK_CONSISTENCY:
                return True
    return False

def _ink_area_shape_match(pts):
    """A spiral: the stroke keeps turning the same way for 1.5+ turns and ends near the middle."""
    s = _smooth(_resample(pts, N_SAMPLES, False), False, w=2)
    turns = _signed_turns(s)
    if len(turns) < 10:
        return False
    net = sum(turns)
    total = sum(abs(t) for t in turns)
    if total == 0 or abs(net) < INK_AREA_MIN_TURN or abs(net) / total < INK_AREA_CONSISTENCY:
        return False
    if not INK_AREA_ALLOW_MIRROR and net < 0:
        return False
    xs, ys = [p[0] for p in s], [p[1] for p in s]
    size = max(max(xs) - min(xs), max(ys) - min(ys))
    centre = ((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2)
    return _dist(s[-1], centre) <= INK_AREA_END_TOLERANCE * size

def _sharp_corners(s, k, angle):
    """Indices where the path turns by at least `angle` degrees (looking k samples back and forward)."""
    n = len(s)
    found = {}
    for i in range(k, n - k):
        a = (s[i][0] - s[i - k][0], s[i][1] - s[i - k][1])
        b = (s[i + k][0] - s[i][0], s[i + k][1] - s[i][1])
        la, lb = math.hypot(*a), math.hypot(*b)
        if la == 0 or lb == 0:
            continue
        c = max(-1.0, min(1.0, (a[0] * b[0] + a[1] * b[1]) / (la * lb)))
        t = math.degrees(math.acos(c))
        if t >= angle:
            found[i] = t
    corners = []
    for i in sorted(found, key=lambda i: -found[i]):       # strongest first, one corner per neighbourhood
        if all(abs(i - j) > k for j in corners):
            corners.append(i)
    return sorted(corners)


def _arrow_try(s):
    """s = the smoothed stroke in drawing order: a straight stick first, then the angular head."""
    corners = _sharp_corners(s, ARROW_CORNER_WINDOW, ARROW_CORNER_ANGLE)
    if len(corners) < ARROW_CORNERS:
        return False
    tip = corners[0]                                       # where the stick ends and the head starts
    total = _path_len(s)
    shaft_len = _path_len(s[:tip + 1])
    if total < 1e-6 or shaft_len < ARROW_SHAFT_RATIO * total:
        return False
    # the stick is straight (the last points are rounded by the smoothing, so skip them)
    chord, devs = _perp_devs(s[:max(3, tip - 2)])
    if chord < 1e-6 or max(abs(d) for d in devs) / chord > ARROW_SHAFT_STRAIGHTNESS:
        return False
    # the head turns one way, by a sensible total amount
    head = s[max(0, tip - CORNER_WINDOW):]
    turns = _signed_turns(head)
    if not turns:
        return False
    net, whole = sum(turns), sum(abs(t) for t in turns)
    if not (ARROW_HEAD_TURN_MIN <= abs(net) <= ARROW_HEAD_TURN_MAX) or abs(net) / whole < ARROW_HEAD_CONSISTENCY:
        return False
    # the head is a sensible size compared to the stick
    xs, ys = [p[0] for p in head], [p[1] for p in head]
    size = max(max(xs) - min(xs), max(ys) - min(ys))
    return ARROW_HEAD_MIN_SIZE * shaft_len <= size <= ARROW_HEAD_MAX_SIZE * shaft_len


def _arrow_shape_match(pts):
    """A stick with an angular head, drawn stick-first or head-first, any size and rotation."""
    s = _smooth(_resample(pts, N_SAMPLES, False), False, w=2)
    return _arrow_try(s) or _arrow_try(s[::-1])

def _shockwave_shape_match(pts):
    """An upside-down V (a "^"): two straight legs meeting at a sharp tip, the legs may end in little hooks."""
    s = _smooth(_resample(pts, N_SAMPLES, False), False, w=2)
    corners = _sharp_corners(s, SHOCKWAVE_CORNER_WINDOW, SHOCKWAVE_CORNER_ANGLE)
    if len(corners) < SHOCKWAVE_CORNERS:
        return False
    chord, devs = _perp_devs(s)                          # distance of every point from the line joining the two ends
    total = _path_len(s)
    if chord < 1e-6 or total < 1e-6:
        return False
    apex = max(corners, key=lambda i: abs(devs[i]))     # the tip = the corner farthest from that line
    along = _path_len(s[:apex + 1]) / total
    if not (SHOCKWAVE_APEX_RANGE[0] <= along <= SHOCKWAVE_APEX_RANGE[1]):
        return False

    # each leg runs from the tip to the next corner (the start of a hook) or to the end of the stroke
    start = max([c for c in corners if c < apex], default=0)
    end = min([c for c in corners if c > apex], default=len(s) - 1)
    legs = (s[start:apex + 1][::-1], s[apex:end + 1])    # both start at the tip
    lens = []
    for leg in legs:
        length = _path_len(leg)
        c, d = _perp_devs(leg)
        if c < 1e-6 or length < SHOCKWAVE_LEG_RATIO * total:
            return False
        if len(d) > 6 and max(abs(x) for x in d[2:-2]) / c > SHOCKWAVE_LEG_STRAIGHTNESS:
            return False                                 # the ends of the leg are skipped: smoothing rounds them
        lens.append(length)
    if min(lens) < SHOCKWAVE_LEG_BALANCE * max(lens):
        return False

    # the angle between the legs at the tip
    u = []
    for leg in legs:
        dx, dy = leg[-1][0] - leg[0][0], leg[-1][1] - leg[0][1]
        n = math.hypot(dx, dy)
        u.append((dx / n, dy / n))
    cosv = max(-1.0, min(1.0, u[0][0] * u[1][0] + u[0][1] * u[1][1]))
    if not (SHOCKWAVE_APEX_MIN <= math.degrees(math.acos(cosv)) <= SHOCKWAVE_APEX_MAX):
        return False

    # the tip points up (the legs open downwards), give or take SHOCKWAVE_TILT degrees
    if not SHOCKWAVE_ANY_ROTATION:
        bx, by = u[0][0] + u[1][0], u[0][1] + u[1][1]
        if by <= 0 or math.degrees(math.atan2(abs(bx), by)) > SHOCKWAVE_TILT:
            return False
    return True

def _angle_diff(a, b):
    return abs((a - b + 180) % 360 - 180)


def _lightning_try(s, angles):
    """s = smoothed stroke in drawing order. 3 sharp corners -> 4 straight segments in fixed directions."""
    corners = _sharp_corners(s, LIGHTNING_CORNER_WINDOW, LIGHTNING_CORNER_ANGLE)
    if len(corners) < 3:
        return False
    k = LIGHTNING_CORNER_WINDOW

    def turn(i):
        a = (s[i][0] - s[i - k][0], s[i][1] - s[i - k][1])
        b = (s[i + k][0] - s[i][0], s[i + k][1] - s[i][1])
        la, lb = math.hypot(*a), math.hypot(*b)
        if la == 0 or lb == 0:
            return 0
        return math.acos(max(-1.0, min(1.0, (a[0] * b[0] + a[1] * b[1]) / (la * lb))))

    corners = sorted(sorted(corners, key=lambda i: -turn(i))[:3])   # the 3 strongest corners
    cuts = [0] + corners + [len(s) - 1]
    total = _path_len(s)
    if total < 1e-6:
        return False
    for j in range(4):
        seg = s[cuts[j]:cuts[j + 1] + 1]
        if len(seg) < 3 or _path_len(seg) < LIGHTNING_SEG_MIN * total:
            return False
        chord, devs = _perp_devs(seg)
        if chord < 1e-6:
            return False
        if len(devs) > 6 and max(abs(d) for d in devs[2:-2]) / chord > LIGHTNING_STRAIGHTNESS:
            return False
        ang = _vec_angle(seg[-1][0] - seg[0][0], seg[-1][1] - seg[0][1])
        if _angle_diff(ang, angles[j]) > LIGHTNING_ANGLE_TOL:
            return False
    return True


def _lightning_shape_match(pts):
    """A lightning bolt, upright, never mirrored and never tilted."""
    s = _smooth(_resample(pts, N_SAMPLES, False), False, w=2)
    if _lightning_try(s, LIGHTNING_ANGLES):
        return True
    if LIGHTNING_ALLOW_REVERSE:      # drawn from the bottom: same shape, segments in reverse order and direction
        rev = tuple((a + 180) % 360 for a in reversed(LIGHTNING_ANGLES))
        return _lightning_try(s[::-1], LIGHTNING_ANGLES) or _lightning_try(s, rev)
    return False

def _shield_shape_match(pts):
    """A "U": goes down, curves at the bottom and comes back up. Any size, drawn in either direction."""
    s = _smooth(_resample(pts, N_SAMPLES, False), False, w=2)
    xs, ys = [p[0] for p in s], [p[1] for p in s]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    if w < 1e-6 or h < 1e-6:
        return False
    if not (SHIELD_MIN_ASPECT <= w / h <= SHIELD_MAX_ASPECT):
        return False
    total = _path_len(s)
    if total < 1e-6:
        return False
    bottom = max(range(len(s)), key=lambda i: s[i][1])                  # lowest point of the stroke
    along = _path_len(s[:bottom + 1]) / total
    if not (SHIELD_BOTTOM_RANGE[0] <= along <= SHIELD_BOTTOM_RANGE[1]):
        return False
    limit = min(ys) + SHIELD_END_HEIGHT * h                              # both ends must be up high
    if s[0][1] > limit or s[-1][1] > limit:
        return False
    if abs(s[0][0] - s[-1][0]) < SHIELD_MIN_GAP * w:                     # arms apart, not a "|" or a hook
        return False
    turns = _signed_turns(s)
    if len(turns) < 10:
        return False
    net, whole = sum(turns), sum(abs(t) for t in turns)
    if whole == 0 or not (SHIELD_MIN_TURN <= abs(net) <= SHIELD_MAX_TURN):
        return False
    return abs(net) / whole >= SHIELD_CONSISTENCY

SLASH_SPELL = ("Slash Spell", None)
GIBBERISH = ("Gibberish", None)
CHAIN_SPELL = ("Chain Spell", None)
INK_AREA_SPELL = ("Ink Area Spell", None)
ARROW_SPELL = ("Arrow Spell", None)
SHOCKWAVE_SPELL = ("Shockwave Spell", None)
LIGHTNING_SPELL = ("Lightning Step", None)
SHIELD_SPELL = ("Shield Spell", None)          # add next to the other spell tuples
SPELL_NAMES = (SLASH_SPELL[0], CHAIN_SPELL[0], INK_AREA_SPELL[0], ARROW_SPELL[0], SHOCKWAVE_SPELL[0],
               LIGHTNING_SPELL[0], SHIELD_SPELL[0])

def recognize_shape(raw_points):
    """Return (shape name, orientation text or None) for one stroke.
    Possible names: Slash Spell, Circle, Square, Triangle, Line, Curve, Zigzag, Gibberish."""
    pts = [raw_points[0]]
    for p in raw_points[1:]:
        if _dist(p, pts[-1]) > 0.5:
            pts.append(p)
    if len(pts) < 2:
        return GIBBERISH

    # Too small to be a deliberate shape
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    if math.hypot(max(xs) - min(xs), max(ys) - min(ys)) < MIN_SIZE:
        return GIBBERISH

    # The slash spell is checked first, it is a special shape
    if _slash_shape_match(pts) or (SLASH_USE_TEMPLATE and _slash_score(pts) <= SLASH_MATCH_THRESHOLD):
        return SLASH_SPELL
    if _chain_shape_match(pts):
        return CHAIN_SPELL
    if _arrow_shape_match(pts):
        return ARROW_SPELL
    if _shockwave_shape_match(pts):
        return SHOCKWAVE_SPELL
    if _ink_area_shape_match(pts):
        return INK_AREA_SPELL
    if _lightning_shape_match(pts):
        return LIGHTNING_SPELL
    if _shield_shape_match(pts):
        return SHIELD_SPELL

    # Measure the path length on a smoothed copy so hand jitter doesn't inflate it
    rough = _smooth(_resample(pts, N_SAMPLES * 2, False), False, w=3)
    smooth_length = sum(_dist(rough[i - 1], rough[i]) for i in range(1, len(rough)))
    closed = _dist(pts[0], pts[-1]) < CLOSED_RATIO * smooth_length
    s = _smooth(_resample(pts, N_SAMPLES, closed), closed)
    corners = _find_corners(s, closed)
    return _classify_closed(s, corners) if closed else _classify_open(s, corners)


# ---------------------------------------------------------------------------
# END SHAPE RECOGNITION
# ---------------------------------------------------------------------------


def load(name):
    path = os.path.join(BASE_DIR, "assets", name)
    return pygame.image.load(path).convert_alpha()


def scale_sprite(img, factor):
    w, h = img.get_size()
    return pygame.transform.smoothscale(img, (max(1, round(w * factor)), max(1, round(h * factor))))

def draw_shadow_ellipse(rect, alpha=None):
    """A see-through shadow ellipse (pygame.draw alone can't blend, so it is drawn on its own surface first)."""
    rect = pygame.Rect(rect)
    surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (*SHADOW_COLOR, SHADOW_ALPHA if alpha is None else alpha), surf.get_rect())
    screen.blit(surf, view(rect.x, rect.y))


# --- Brush sprites ----------------------------------------------------------
outline_img = scale_sprite(load("outline.png"), BRUSH_SCALE)
base_colour_img = scale_sprite(load("colour.png"), BRUSH_SCALE)
glow_img = scale_sprite(load("glow.png"), BRUSH_SCALE)


def tint(img, colour):
    """Copy of `img` painted in a single colour, keeping its transparency."""
    img = img.copy()
    img.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)  # RGB -> black, alpha kept
    img.fill((*colour, 0), special_flags=pygame.BLEND_RGBA_ADD)     # add colour, alpha untouched
    return img


colour_img = tint(base_colour_img, INK_COLOR)         # the final ink
bright_img = tint(base_colour_img, INK_START_COLOR)   # fresh ink, fades out over time

# --- Floor: endless tiles + rare decorations, built chunk by chunk -------------------
FLOOR_SEED = random.randrange(1 << 30)     # a new floor every run, but a chunk always looks the same when you come back
floor_base = None
floor_decors = []
_floor_chunks = {}


def _load_floor_sprites():
    global floor_base, floor_decors
    folder = os.path.join(BASE_DIR, "assets", TILES_FOLDER)
    try:
        names = sorted(os.listdir(folder))
    except FileNotFoundError:
        return
    prefix = TILE_BASE_NAME.lower()
    files = [n for n in names if n.lower().endswith(".png") and n.lower().startswith(prefix)]
    base_file = next((n for n in files if n.lower() == prefix + ".png"), None)
    if base_file is None:
        return                                          # no dirt.png: plain colour

    def load_tile(name):
        return pygame.image.load(os.path.join(folder, name)).convert_alpha()

    base = load_tile(base_file)
    factor = TILE_SIZE / base.get_width()               # one scale for all, so sizes stay in proportion
    floor_base = scale_sprite(base, factor)
    floor_decors = [scale_sprite(load_tile(n), factor) for n in files if n != base_file]


_load_floor_sprites()
TW, TH = floor_base.get_size() if floor_base is not None else (TILE_SIZE, TILE_SIZE)
CHUNK_W, CHUNK_H = CHUNK_TILES * TW, CHUNK_TILES * TH


def floor_chunk(cx, cy):
    """One square piece of floor, made the first time it is needed and then remembered."""
    key = (cx, cy)
    if key not in _floor_chunks:
        if len(_floor_chunks) > 80:
            _floor_chunks.clear()                       # keeps memory small when you travel far
        surf = pygame.Surface((CHUNK_W, CHUNK_H)).convert()
        surf.fill(BG_COLOR)                             # fallback if no tiles are found
        if floor_base is not None:
            rng = random.Random(f"{FLOOR_SEED}:{cx}:{cy}")   # same chunk -> same decorations every time
            for ty in range(CHUNK_TILES):
                for tx in range(CHUNK_TILES):
                    surf.blit(floor_base, (tx * TW, ty * TH))
            for ty in range(CHUNK_TILES):               # decorations on top, in a second pass
                for tx in range(CHUNK_TILES):
                    if floor_decors and rng.random() < TILE_DECOR_CHANCE:
                        d = rng.choice(floor_decors)
                        if TILE_DECOR_FLIP and rng.random() < 0.5:
                            d = pygame.transform.flip(d, True, False)
                        surf.blit(d, d.get_rect(center=(tx * TW + TW // 2, ty * TH + TH // 2)))
        _floor_chunks[key] = surf
    return _floor_chunks[key]


def draw_floor():
    x0, x1 = int(cam.x // CHUNK_W), int((cam.x + WIDTH) // CHUNK_W)
    y0, y1 = int(cam.y // CHUNK_H), int((cam.y + HEIGHT) // CHUNK_H)
    for cy in range(y0, y1 + 1):
        for cx in range(x0, x1 + 1):
            screen.blit(floor_chunk(cx, cy), view(cx * CHUNK_W, cy * CHUNK_H))

# --- Target sprite: the whole sprite takes the ink colour, grey areas come out darker ---
def recolor_target(img, ink, white_level=None):
    """Paint every pixel in `ink`, scaled by its brightness: white = plain ink colour,
    grey = a darker version of it. Transparency is kept."""
    white = white_level or TARGET_WHITE_LEVEL
    img = img.copy()
    for x in range(img.get_width()):
        for y in range(img.get_height()):
            r, g, b, a = img.get_at((x, y))
            if a == 0:
                continue
            brightness = min(1.0, ((r + g + b) / 3) / white)   # 1 = white, 0 = black
            shade = 1 - TARGET_SHADE_STRENGTH * (1 - brightness)
            img.set_at((x, y), (round(ink[0] * shade), round(ink[1] * shade),
                                round(ink[2] * shade), a))
    return img


def brightest(img):
    """Brightness (0-255) of the brightest visible pixel, so a sprite's own white becomes the plain ink colour."""
    best = 1.0
    for x in range(img.get_width()):
        for y in range(img.get_height()):
            r, g, b, a = img.get_at((x, y))
            if a > 0:
                best = max(best, (r + g + b) / 3)
    return best


# --- Notebook ---------------------------------------------------------------
notebook_img = load(NOTEBOOK_FILE)
area_img = load(NOTEBOOK_AREA_FILE)
if area_img.get_size() != notebook_img.get_size():
    area_img = pygame.transform.scale(area_img, notebook_img.get_size())

# Page sprite: a copy of notebook.png with only the page left, so it shares the notebook's canvas
try:
    raw_page_img = load(PAGE_FILE)
    if raw_page_img.get_size() != notebook_img.get_size():
        raw_page_img = pygame.transform.smoothscale(raw_page_img, notebook_img.get_size())
except (FileNotFoundError, pygame.error):
    raw_page_img = None

# Crop away the empty (transparent) margins so only the visible notebook is used
content = notebook_img.get_bounding_rect(min_alpha=10)
notebook_img = notebook_img.subsurface(content).copy()
area_img = area_img.subsurface(content).copy()
if raw_page_img is not None:
    raw_page_img = raw_page_img.subsurface(content).copy()   # same crop, so the page lines up

# Scale both to the same, smaller size
nb_scale = min(HEIGHT * NOTEBOOK_HEIGHT_FRACTION / content.height,
               WIDTH * NOTEBOOK_MAX_W_FRACTION / content.width)
nb_size = (max(1, round(content.width * nb_scale)),
           max(1, round(content.height * nb_scale)))
notebook_img = pygame.transform.smoothscale(notebook_img, nb_size)
area_img = pygame.transform.scale(area_img, nb_size)  # no smoothing, keeps the red pure

# Top-left corner, leaving a padding around the visible notebook
notebook_rect = notebook_img.get_rect(
    topleft=(NOTEBOOK_PADDING, NOTEBOOK_PADDING))

# Mask of the red pixels = where drawing is allowed
area_mask = pygame.mask.from_threshold(area_img, (255, 0, 0, 255), (100, 100, 100, 255))

# Full-window alpha stencil: opaque inside the red area, transparent elsewhere
clip_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
clip_surface.fill((255, 255, 255, 0))
clip_surface.blit(
    area_mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(255, 255, 255, 0)),
    notebook_rect.topleft,
    special_flags=pygame.BLEND_RGBA_MAX,
)
screen_rect = screen.get_rect()

# Page sprite: cropped and scaled exactly like the notebook, so its page matches the notebook's page
if raw_page_img is not None:
    page_img = pygame.transform.smoothscale(raw_page_img, nb_size)
else:
    # no page.png found: use a plain paper-coloured rectangle instead
    page_img = pygame.Surface(nb_size, pygame.SRCALPHA)
    page_img.fill((252, 250, 243))
    pygame.draw.rect(page_img, (200, 195, 180), page_img.get_rect(), 2)


# --- Ink bar: a holder with a red window, and a shaded bar that slides inside that window ---
def trim(img):
    """Crop away the empty (transparent) margins of a sprite."""
    return img.subsurface(img.get_bounding_rect(min_alpha=10)).copy()


def fit_height(img, height):
    return scale_sprite(img, height / img.get_height())


_RED = (255, 0, 0, 255)
_RED_TOLERANCE = (100, 100, 100, 255)

_holder_raw = trim(load("inkbarholder.png"))
# Make the red pixels transparent so the bar can be seen through them
_red_full = pygame.mask.from_threshold(_holder_raw, _RED, _RED_TOLERANCE)
_cut = _red_full.to_surface(setcolor=(0, 0, 0, 0), unsetcolor=(255, 255, 255, 255))
_holder_clean = _holder_raw.copy()
_holder_clean.blit(_cut, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

_holder_h = max(1, round(notebook_rect.height * INKBAR_HEIGHT_RATIO))
_holder_w = max(1, round(_holder_raw.get_width() * _holder_h / _holder_raw.get_height()))
holder_img = pygame.transform.smoothscale(_holder_clean, (_holder_w, _holder_h))

# Mask of the window (no smoothing keeps the red pure), and the box around it
_bar_mask = pygame.mask.from_threshold(
    pygame.transform.scale(_holder_raw, (_holder_w, _holder_h)), _RED, _RED_TOLERANCE)
_rects = _bar_mask.get_bounding_rects()
if _rects:
    _biggest = max(r.width * r.height for r in _rects)
    _rects = [r for r in _rects if r.width * r.height >= 0.2 * _biggest]   # ignore stray pixels
    bar_area = _rects[0].unionall(_rects[1:])
else:
    bar_area = holder_img.get_rect()                                       # no red found: use it all
bar_stencil = _bar_mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(255, 255, 255, 0))

# The bar fills the window and gets the same colouring as the target (ink colour, darker greys)
bar_img = trim(load("inkbar.png"))
bar_img = pygame.transform.smoothscale(bar_img, bar_area.size)
if INKBAR_TINT:
    bar_img = recolor_target(bar_img, INK_COLOR, brightest(bar_img))
bar_layer = pygame.Surface(holder_img.get_size(), pygame.SRCALPHA)

# Right of the notebook, top edges lined up
holder_rect = holder_img.get_rect(topleft=(notebook_rect.right + INKBAR_GAP, notebook_rect.top))
hud_rect = notebook_rect.union(holder_rect)    # slimes don't start under the notebook and the ink bar

# --- Ink level and reload animation -------------------------------------------
ink = 1.0                  # 1 = full, 0 = empty
ink_shown = 1.0            # what the bar displays (follows `ink` smoothly)
reloading = False
reload_t = 0.0
reload_side = 1.0          # side of the cat the inker is on (1 = right, -1 = left); follows the way the cat faces
reload_flags = set()       # one-time events already triggered
reload_dips_done = 0
reload_start_ink = 1.0
puffs = []

inker_img = fit_height(trim(load("inker.png")), INKER_HEIGHT)      # top faces up
if INKER_TINT:
    inker_img = recolor_target(inker_img, INK_COLOR, brightest(inker_img))   # whites = ink colour, greys = darker
pencil_img = fit_height(trim(load("pencil.png")), PENCIL_HEIGHT)   # point faces down

# Timeline of the reload (seconds): inker pops in -> pencil pops in -> twirl -> dips -> both puff away
T_INKER = RELOAD_POP_TIME
T_PENCIL = T_INKER + RELOAD_POP_TIME
T_TWIRL = T_PENCIL + RELOAD_TWIRL_TIME
T_DIPS = T_TWIRL + RELOAD_DIPS * RELOAD_DIP_TIME
T_END = T_DIPS + RELOAD_OUT_TIME


def clamp01(x):
    return max(0.0, min(1.0, x))


def ease_out_back(x):
    """0 -> 1 with a little overshoot, makes things 'pop'."""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_in_out(x):
    return x * x * (3 - 2 * x)


def has_ink():
    return ink > 0 and not reloading


def spend_ink(pixels):
    """Drawing `pixels` of line uses up ink."""
    global ink
    ink = max(0.0, ink - pixels / INK_DRAW_LENGTH)


def spawn_puff(pos):
    for _ in range(PUFF_COUNT):
        a = random.uniform(0, math.tau)
        speed = random.uniform(30, 110) * UI_SCALE
        puffs.append({"pos": pygame.math.Vector2(pos),
                      "vel": pygame.math.Vector2(math.cos(a), math.sin(a)) * speed,
                      "r": sc(random.uniform(5, 11)),
                      "age": 0.0,
                      "life": random.uniform(0.35, 0.55)})


def update_puffs(dt):
    for p in puffs:
        p["age"] += dt
        p["pos"] += p["vel"] * dt
        p["vel"] *= max(0.0, 1 - 4 * dt)
    puffs[:] = [p for p in puffs if p["age"] < p["life"]]


def draw_puffs():
    for p in puffs:
        k = p["age"] / p["life"]
        r = max(1, round(p["r"] * (1 + k)))
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*PUFF_COLOR, round(200 * (1 - k))), (r, r), r)
        vx, vy = view(p["pos"].x, p["pos"].y)
        screen.blit(surf, (vx - r, vy - r))


def reload_positions():
    """Centre of the inker (standing in front of the cat) and the pencil's resting centre above it."""
    foot_y = player_pos.y + PLAYER_RADIUS
    ix = player_pos.x + reload_side * RELOAD_DISTANCE
    iy = foot_y - RELOAD_LIFT - inker_img.get_height() / 2
    inker_top = iy - inker_img.get_height() / 2
    py = inker_top - RELOAD_HOVER - pencil_img.get_height() / 2
    return (ix, iy), (ix, py)


def start_reload():
    global reloading, reload_t, reload_side, reload_dips_done, reload_start_ink
    if reloading or ink >= 0.999:
        return
    reloading = True
    reload_t = 0.0
    reload_side = 1.0 if player_look_right else -1.0
    reload_flags.clear()
    reload_dips_done = 0
    reload_start_ink = ink


def update_reload(dt):
    global reloading, reload_t, reload_dips_done, ink, reload_side
    if not reloading:
        return
    reload_t += dt
    # always stay in front of the cat: slide to whichever side it is facing now
    target_side = 1.0 if player_look_right else -1.0
    reload_side += (target_side - reload_side) * min(1.0, RELOAD_SIDE_SPEED * dt)
    (ix, iy), (px, py) = reload_positions()
    if "inker" not in reload_flags:
        reload_flags.add("inker")
        spawn_puff((ix, iy))
    if reload_t >= T_INKER and "pencil" not in reload_flags:
        reload_flags.add("pencil")
        spawn_puff((px, py))
    if reload_t >= T_TWIRL:
        # every time the pencil reaches the bottom of a dip, the ink goes up a little
        done = min(RELOAD_DIPS, int((reload_t - T_TWIRL) / RELOAD_DIP_TIME + 0.5))
        if done > reload_dips_done:
            reload_dips_done = done
            ink = reload_start_ink + (1.0 - reload_start_ink) * done / RELOAD_DIPS
    if reload_t >= T_DIPS and "out" not in reload_flags:
        reload_flags.add("out")
        spawn_puff((ix, iy))
        spawn_puff((px, py))
    if reload_t >= T_END:
        reloading = False
        ink = 1.0


def draw_reload():
    if not reloading:
        return
    t = reload_t
    (ix, iy), (px, py) = reload_positions()

    s_inker = ease_out_back(clamp01(t / RELOAD_POP_TIME))
    s_pencil = ease_out_back(clamp01((t - T_INKER) / RELOAD_POP_TIME)) if t >= T_INKER else 0.0
    if t >= T_DIPS:                                      # shrink away at the end
        k = 1 - clamp01((t - T_DIPS) / RELOAD_OUT_TIME) ** 2
        s_inker *= k
        s_pencil *= k

    angle = PENCIL_ANGLE_OFFSET
    if T_PENCIL <= t < T_TWIRL:                          # twirl
        angle += 360 * ease_in_out((t - T_PENCIL) / RELOAD_TWIRL_TIME)
    if T_TWIRL <= t < T_DIPS:                            # dips: down into the inker and back up
        frac = ((t - T_TWIRL) / RELOAD_DIP_TIME) % 1.0
        py += (RELOAD_HOVER + inker_img.get_height() * RELOAD_DIP_DEPTH) * math.sin(math.pi * frac)

    # the pencil is always drawn BEFORE the inker, so it stays behind it (the inker hides the dipped part)
    if s_pencil > 0.02:
        img = pygame.transform.rotozoom(pencil_img, angle, s_pencil)
        screen.blit(img, img.get_rect(center=view(px, py)))
    if s_inker > 0.02:
        img = pygame.transform.rotozoom(inker_img, 0, s_inker)
        screen.blit(img, img.get_rect(center=view(ix, iy)))


def draw_ink_bar(dt):
    """The bar slides down inside the holder's window as the ink runs out."""
    global ink_shown
    ink_shown += (ink - ink_shown) * min(1.0, INKBAR_SMOOTHING * dt)
    if abs(ink - ink_shown) < 0.002:
        ink_shown = ink
    bar_layer.fill((0, 0, 0, 0))
    bar_layer.blit(bar_img, (bar_area.x, bar_area.y + round((1 - ink_shown) * bar_area.height)))
    bar_layer.blit(bar_stencil, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)   # crop to the window
    bar_layer.blit(holder_img, (0, 0))                                          # the holder goes over the bar
    bar_layer.set_alpha(round(255 * hud_alpha_bar))                             # see-through when something is under it
    screen.blit(bar_layer, holder_rect.topleft)


def inside_area(pos):
    x, y = pos[0] - notebook_rect.x, pos[1] - notebook_rect.y
    return 0 <= x < nb_size[0] and 0 <= y < nb_size[1] and bool(area_mask.get_at((x, y)))

def segment_leaves_area(a, b):
    """True if any point on the straight line a -> b is outside the drawable (red) area.
    Checked along the whole line so a fast mouse jump can't skip over the edge."""
    steps = max(1, int(_dist(a, b) / max(1, SPACING)))
    for i in range(steps + 1):
        t = i / steps
        if not inside_area((round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t))):
            return True
    return False

# Separate transparent layers so the order is always: outline < colour < glow
outline_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
colour_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
glow_positions = []  # one glow per stroke, sitting on the stroke's last point

# Fresh ink: every stamp is remembered with its birth time and drawn in the bright colour,
# fading out over INK_FADE_TIME to reveal the real ink colour underneath.
fresh_stamps = deque()   # (position, time in seconds), oldest first
fresh_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
fresh_prev_box = None    # area of fresh_layer used in the previous frame
fresh_zone = notebook_rect.inflate(colour_img.get_width() * 2, colour_img.get_height() * 2)

# Distance between stamps (smaller = smoother line)
SPACING = max(1, min(colour_img.get_width(), colour_img.get_height()) * STAMP_SPACING)


result = None  # (shape name, orientation)


# --- Top-down character (independent from the notebook) -------------------
# Move with WASD or the arrow keys, 8 directions, with acceleration and friction.
player_pos = pygame.math.Vector2(WIDTH / 2, HEIGHT / 2)  # middle of the window
player_vel = pygame.math.Vector2(0, 0)
player_facing = pygame.math.Vector2(0, 1)  # looking down at the start
player_look_right = True                   # the cat is flipped when walking left
walk_timer = 0.0                           # seconds spent walking, drives the step animation

# Cat sprites: cat.png (standing) and catwalking.png (moving)
cat_idle_img = load("cat.png")
cat_walk_img = load("catwalking.png")
_cat_scale = CAT_HEIGHT / cat_idle_img.get_height()  # same scale for both so the size matches
cat_idle_img = scale_sprite(cat_idle_img, _cat_scale)
cat_walk_img = scale_sprite(cat_walk_img, _cat_scale)
try:
    cat_dead_img = scale_sprite(load(CAT_DEAD_FILE), _cat_scale)   # same scale as the other cat sprites
except (FileNotFoundError, pygame.error):
    cat_dead_img = cat_idle_img


def update_player(dt):
    global player_pos, player_vel, player_facing, player_look_right, walk_timer
    keys = pygame.key.get_pressed()
    direction = pygame.math.Vector2(
        (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
        (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP]),
    )
    if player_hp <= 0:
        direction = pygame.math.Vector2(0, 0)   # dead: no control (friction still slows the cat down)
    if direction.length_squared() > 0:
        direction = direction.normalize()   # diagonals are not faster
        player_facing = direction
        if direction.x != 0:
            player_look_right = direction.x > 0
        player_vel += direction * PLAYER_ACCEL * (LIGHTNING_ACCEL_MULT if lightning_left > 0 else 1.0) * dt

    player_vel -= player_vel * min(1.0, PLAYER_FRICTION * dt)  # friction
    max_speed = PLAYER_MAX_SPEED * (LIGHTNING_SPEED_MULT if lightning_left > 0 else 1.0)
    if player_vel.length() > max_speed:
        player_vel.scale_to_length(max_speed)
    elif player_vel.length() < 2 and direction.length_squared() == 0:
        player_vel.update(0, 0)             # stop completely instead of drifting forever

    player_pos += player_vel * dt

    if player_vel.length() > WALK_SPEED_THRESHOLD:
        walk_timer += dt          # keeps counting while walking
    else:
        walk_timer = 0.0          # standing still: the next walk starts with a fresh step

def draw_player():
    x, y = int(player_pos.x), int(player_pos.y)
    shadow_h = max(14, round(PLAYER_RADIUS * 0.6))
    shadow_w = PLAYER_RADIUS * 2
    shadow_y = y + PLAYER_RADIUS - shadow_h // 2
    if player_hp <= 0:                                                                       # dead: the cat lies down, so its shadow is wider and higher
        new_w = round(shadow_w * DEAD_SHADOW_SCALE)
        new_h = round(shadow_h * DEAD_SHADOW_SCALE)
        shadow_y = y + PLAYER_RADIUS - new_h // 2 - DEAD_SHADOW_LIFT
        x -= (new_w - shadow_w) // 2                                                         # keep it centred on the cat
        shadow_w, shadow_h = new_w, new_h
    draw_shadow_ellipse((x - PLAYER_RADIUS, shadow_y, shadow_w, shadow_h))                   # shadow

    if player_hp <= 0:
        img = cat_dead_img                                                                 # dead
    elif player_vel.length() > WALK_SPEED_THRESHOLD:
        # walking: alternate between catwalking.png and cat.png
        img = cat_walk_img if int(walk_timer / WALK_FRAME_TIME) % 2 == 0 else cat_idle_img
    else:
        img = cat_idle_img                                                                 # standing still
    if player_look_right != CAT_FACES_RIGHT:
        img = pygame.transform.flip(img, True, False)                                      # face left/right
    if player_hp > 0 and player_invuln > 0 and int(player_invuln * 14) % 2 == 0:
        return                                                                             # blinks after a hit
    # the cat's feet sit at the bottom of the collision circle
    screen.blit(img, img.get_rect(midbottom=view(x, y + PLAYER_RADIUS)))                                                                # blinks after a hit


def stamp(img, layer, pos):
    layer.blit(img, img.get_rect(center=(int(pos[0]), int(pos[1]))))


def stamp_pair(pos):
    stamp(outline_img, outline_layer, pos)
    stamp(colour_img, colour_layer, pos)
    if fresh_zone.collidepoint(pos):    # only near the notebook, the rest gets clipped away anyway
        fresh_stamps.append((pos, pygame.time.get_ticks() / 1000))


def stamp_line(start, end):
    """Place stamps evenly from start to end so fast mouse moves leave no gaps."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    dist = math.hypot(dx, dy)
    steps = max(1, int(dist / SPACING))
    for i in range(1, steps + 1):
        t = i / steps
        stamp_pair((start[0] + dx * t, start[1] + dy * t))


def clip_to_area(rect):
    """Erase anything painted outside the red area inside `rect`."""
    rect = rect.clip(screen_rect)
    if rect.width == 0 or rect.height == 0:
        return
    stencil = clip_surface.subsurface(rect)
    for layer in (outline_layer, colour_layer):
        layer.subsurface(rect).blit(stencil, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)


def paint(start, end):
    """Stamp the sprites from start to end, keeping only what lands on the red area."""
    stamp_line(start, end)
    box = pygame.Rect(min(start[0], end[0]), min(start[1], end[1]),
                      abs(end[0] - start[0]), abs(end[1] - start[1]))
    pad_w = max(outline_img.get_width(), colour_img.get_width())
    pad_h = max(outline_img.get_height(), colour_img.get_height())
    clip_to_area(box.inflate(pad_w * 2, pad_h * 2))


def draw_fresh_ink(target):
    """Draw the bright stamps on top of the real ink (into `target`, a surface the size of the notebook),
    fading them out with age."""
    global fresh_prev_box
    now = pygame.time.get_ticks() / 1000
    while fresh_stamps and now - fresh_stamps[0][1] >= INK_FADE_TIME:
        fresh_stamps.popleft()                       # fully faded, the real ink is all that is left

    box = None
    if fresh_stamps:
        w, h = bright_img.get_size()
        xs = [p[0] for p, _ in fresh_stamps]
        ys = [p[1] for p, _ in fresh_stamps]
        box = pygame.Rect(min(xs) - w, min(ys) - h,
                          max(xs) - min(xs) + 2 * w, max(ys) - min(ys) + 2 * h).clip(screen_rect)

    # wipe the area used last frame and this frame
    wipe = [r for r in (fresh_prev_box, box) if r is not None]
    if wipe:
        area = wipe[0].unionall(wipe[1:]) if len(wipe) > 1 else wipe[0]
        if area.width > 0 and area.height > 0:
            fresh_layer.subsurface(area).fill((0, 0, 0, 0))

    if box is not None and box.width > 0 and box.height > 0:
        for pos, born in fresh_stamps:
            age = (now - born) / INK_FADE_TIME       # 0 = brand new, 1 = faded
            bright_img.set_alpha(round(255 * (1 - age)))
            fresh_layer.blit(bright_img, bright_img.get_rect(center=(int(pos[0]), int(pos[1]))))
        # keep only what lands on the red area
        fresh_layer.subsurface(box).blit(clip_surface.subsurface(box), (0, 0),
                                         special_flags=pygame.BLEND_RGBA_MULT)
        target.blit(fresh_layer, (box.x - notebook_rect.x, box.y - notebook_rect.y), area=box)
    fresh_prev_box = box


# --- Falling pages ----------------------------------------------------------
class FallingPage:
    def __init__(self, surf, center):
        self.surf = surf
        self.pos = pygame.math.Vector2(center)
        self.vel = pygame.math.Vector2(0, 0)
        self.age = 0.0
        self.angle = 0.0
        self.spin = PAGE_SPIN * random.uniform(0.7, 1.0)   # positive = counter-clockwise
        self.radius = math.hypot(*surf.get_size()) / 2   # biggest reach once rotated


falling_pages = []


def snapshot_page():
    """The page with the drawing on it, as one picture."""
    page = page_img.copy()
    page.blit(outline_layer, (0, 0), area=notebook_rect)
    page.blit(colour_layer, (0, 0), area=notebook_rect)
    page.blit(fresh_layer, (0, 0), area=notebook_rect)
    for gp in glow_positions:
        page.blit(glow_img, glow_img.get_rect(center=(gp[0] - notebook_rect.x,
                                                      gp[1] - notebook_rect.y)))
    return page


def drop_page():
    """Lift the page (with the drawing on it) off the notebook and let it fall."""
    falling_pages.append(FallingPage(snapshot_page(), notebook_rect.center))


def clear_drawing():
    global glow_index
    outline_layer.fill((0, 0, 0, 0))
    colour_layer.fill((0, 0, 0, 0))
    fresh_stamps.clear()
    glow_positions.clear()
    glow_index = None


def update_pages(dt):
    for p in falling_pages:
        p.age += dt
        p.vel.y += PAGE_GRAVITY * dt             # falls faster and faster
        p.vel.x -= PAGE_CURVE * p.age * dt       # the sideways pull grows with time -> a curve to the left
        p.pos += p.vel * dt
        p.angle += p.spin * dt
    falling_pages[:] = [p for p in falling_pages
                        if p.pos.y - p.radius < HEIGHT and p.pos.x + p.radius > 0]


def draw_pages():
    for p in falling_pages:
        img = pygame.transform.rotate(p.surf, p.angle)
        screen.blit(img, img.get_rect(center=(round(p.pos.x), round(p.pos.y))))


# --- Spell page: turns bright purple, then crumbles into particles ---------------
spell_pages = []
spell_particles = []


class SpellPage:
    def __init__(self, surf, topleft):
        self.surf = surf
        self.topleft = topleft
        self.mask = pygame.mask.from_surface(surf, 40)
        self.age = 0.0
        self.cut = surf.get_height()     # rows below this line are already gone
        self.owed = 0.0                  # fractional particles still to spawn

    def update(self, dt):
        self.age += dt
        p = clamp01((self.age - SPELL_PURPLE_TIME) / SPELL_DISSOLVE_TIME)
        new_cut = round(self.surf.get_height() * (1 - ease_in_out(p)))
        if new_cut < self.cut:
            self.emit(new_cut, self.cut)
            self.cut = new_cut

    def emit(self, top, bottom):
        """Turn the rows between top and bottom into particles."""
        self.owed += SPELL_PARTICLES * (bottom - top) / self.surf.get_height()
        n = int(self.owed)
        self.owed -= n
        for _ in range(n):
            for _try in range(8):                      # find a spot where the page really is
                x, y = random.randrange(self.surf.get_width()), random.randrange(top, bottom)
                if self.mask.get_at((x, y)):
                    break
            else:
                continue
            spell_particles.append({
                "pos": pygame.math.Vector2(self.topleft[0] + x, self.topleft[1] + y),
                "vel": pygame.math.Vector2(random.uniform(-40, 40), random.uniform(-170, -40)) * UI_SCALE,
                "size": sc(random.uniform(2.5, 6.5)),
                "color": random.choice(SPELL_PARTICLE_COLORS),
                "age": 0.0,
                "life": random.uniform(0.6, 1.2),
                "phase": random.uniform(0, math.tau),
            })

    def draw(self, alpha):
        k = ease_in_out(clamp01(self.age / SPELL_PURPLE_TIME))
        img = self.surf.copy()
        mult = [round(255 + (c - 255) * k) for c in SPELL_PAGE_COLOR]
        glow = [round(c * k) for c in SPELL_PAGE_GLOW]
        img.fill((*mult, 255), special_flags=pygame.BLEND_RGBA_MULT)   # paper -> purple, ink stays dark
        img.fill((*glow, 0), special_flags=pygame.BLEND_RGBA_ADD)
        img.set_alpha(round(255 * alpha))
        screen.blit(img, self.topleft, area=pygame.Rect(0, 0, img.get_width(), self.cut))


def vanish_page():
    """A spell worked: the page turns purple and crumbles away, and the drawing is cleared for you."""
    spell_pages.append(SpellPage(snapshot_page(), notebook_rect.topleft))
    clear_drawing()


def update_spell_effects(dt):
    for sp in spell_pages:
        sp.update(dt)
    spell_pages[:] = [sp for sp in spell_pages if sp.cut > 0]
    for p in spell_particles:
        p["age"] += dt
        p["pos"] += p["vel"] * dt
        p["vel"] *= max(0.0, 1 - 1.5 * dt)
        p["vel"].x += math.sin(p["age"] * 9 + p["phase"]) * sc(120) * dt   # little drifting wobble
    spell_particles[:] = [p for p in spell_particles if p["age"] < p["life"]]


def draw_spell_effects(alpha):
    for sp in spell_pages:
        sp.draw(alpha)
    for p in spell_particles:
        r = max(1, round(p["size"] * (1 - p["age"] / p["life"])))       # shrink as they fade
        pygame.draw.circle(screen, p["color"], (round(p["pos"].x), round(p["pos"].y)), r)


drawing = False
last_pos = None
stroke_points = []
stroke_outside = False      # did this stroke put ink outside the page?
fizzle_time = 0.0           # how long the "ink outside" message stays
glow_index = None


# --- Slime sprites (normal + charging), scaled to the slime's size --------------
SLIME_HEIGHT = CAT_HEIGHT * min(SLIME_SIZE, 1.0)       # big, but never taller than the cat
slime_img = slime_charging_img = None
try:
    _slime_raw = trim(load(SLIME_FILE))
    _slime_scale = SLIME_HEIGHT / _slime_raw.get_height()
    slime_img = scale_sprite(_slime_raw, _slime_scale)
    try:
        # same scale as the normal sprite, so a squashed charging pose stays squashed
        slime_charging_img = scale_sprite(trim(load(SLIME_CHARGING_FILE)), _slime_scale)
    except (FileNotFoundError, pygame.error):
        slime_charging_img = slime_img
except (FileNotFoundError, pygame.error):
    pass                                               # no sprite found: slimes are drawn as plain balls

if slime_img is not None:
    SLIME_RADIUS = round((slime_img.get_width() + slime_img.get_height()) / 4 * SLIME_HITBOX_SCALE)
else:
    SLIME_RADIUS = round(SLIME_HEIGHT / 2)

# --- Statue sprites -------------------------------------------------------------
STATUE_HEIGHT = CAT_HEIGHT * min(STATUE_SIZE, 1.0)
statue_img = statue_charging_img = None
try:
    _statue_raw = trim(load(STATUE_FILE))
    _statue_scale = STATUE_HEIGHT / _statue_raw.get_height()
    statue_img = scale_sprite(_statue_raw, _statue_scale)
    try:
        statue_charging_img = scale_sprite(trim(load(STATUE_CHARGING_FILE)), _statue_scale)
    except (FileNotFoundError, pygame.error):
        statue_charging_img = statue_img
except (FileNotFoundError, pygame.error):
    pass

if statue_img is not None:
    STATUE_RADIUS = round((statue_img.get_width() + statue_img.get_height()) / 4 * STATUE_HITBOX_SCALE)
else:
    STATUE_RADIUS = round(STATUE_HEIGHT / 2)

# --- Target sprite: shrink it to the biggest size it is ever drawn at (circle fully grown),
# recolor it once, then rotozoom it to the right size every frame.
_target_max = round(2 * (max(SLIME_RADIUS, STATUE_RADIUS) + TARGET_RING_GAP) * (1 + TARGET_BOB_FRACTION))
target_img = load(TARGET_FILE)
target_img = scale_sprite(target_img, _target_max / max(target_img.get_size()))
target_img = recolor_target(target_img, INK_COLOR)


def squashed(img, amount):
    """The sprite pressed flat: 1 = fully squashed, 0 = normal, below 0 = stretched tall.
    It gets a bit wider when it gets lower. The bottom stays where it is when drawn with midbottom."""
    if abs(amount) < 0.005:
        return img
    w = max(1, round(img.get_width() * (1 + SLIME_SQUASH * amount * 0.5)))
    h = max(1, round(img.get_height() * (1 - SLIME_SQUASH * amount)))
    return pygame.transform.smoothscale(img, (w, h))


slime_sprite_cache = {}


def slime_sprites(scale):
    """(normal, charging) slime sprites at a size relative to the big slime (cached)."""
    key = round(scale, 3)
    if key not in slime_sprite_cache:
        if slime_img is None:
            slime_sprite_cache[key] = (None, None)
        elif key == 1:
            slime_sprite_cache[key] = (slime_img, slime_charging_img)
        else:
            slime_sprite_cache[key] = (scale_sprite(slime_img, scale), scale_sprite(slime_charging_img, scale))
    return slime_sprite_cache[key]


def flashed(img):
    """A brighter copy of a sprite, used for the hit flash."""
    img = img.copy()
    img.fill((140, 140, 140, 0), special_flags=pygame.BLEND_RGB_ADD)
    return img


# --- Enemies ------------------------------------------------------------------
class Enemy:
    """Base enemy: a circle you can push around. Other kinds of enemies can build on this."""

    def __init__(self, pos, radius, mass, damage=0):
        self.collidable = True       # False while flying (no collisions, no touch damage)
        self.spawn_t = 0.0           # > 0 while it is still hidden in its spawn puff
        self.shadow_scale = 1.0      # shadow size multiplier
        self.invulnerable = False    # True while flying
        self.target_offset = 0       # px the target ring is lowered (0 = centred on the enemy)
        self.pos = pos
        self.vel = pygame.math.Vector2(0, 0)
        self.radius = radius
        self.mass = mass
        self.damage = damage                          # health points taken from the cat on a hit
        self.friction = ENEMY_FRICTION                # how quickly it slows down
        self.health = 1
        self.flash = 0.0                              # seconds of hit flash left
        self.base_mass = mass                         # normal mass (a locked enemy is much heavier)
        self.lock_time = 0.0                          # seconds left locked by the chain spell
        self.chains = []                              # built when the chain spell hits
        self.ring_radius = radius + TARGET_RING_GAP   # bigger enemy -> bigger target circle
        # how far the target circle reaches from the centre when fully grown (keeps things on screen)
        self.reach = self.ring_radius * (1 + TARGET_BOB_FRACTION)

    def update_ai(self, dt):
        pass

    def draw_ground(self):
        self.draw_shadow()

    def on_death(self):
        """Enemies that appear when this one dies (none by default)."""
        return []

    def rect(self):
        """Area of the screen the enemy covers."""
        r = round(self.radius)
        return pygame.Rect(round(self.pos.x) - r, round(self.pos.y) - r, r * 2, r * 2)

    def draw_shadow(self, scale=None, alpha=None):
        """The floor shadow. The centre stays in the same place whatever the size,
        so the statue's landing telegraph ends exactly on the normal shadow."""
        x, y, r = int(self.pos.x), int(self.pos.y), self.radius
        k = self.shadow_scale if scale is None else scale
        base_h = max(6, round(r * 0.6))
        w = max(2, round(r * 2 * k))
        h = max(2, round(base_h * k))
        cy = y + round(r * 0.65) + base_h // 2
        draw_shadow_ellipse((x - w // 2, cy - h // 2, w, h), alpha)

    def draw(self):
        x, y = view(self.pos.x, self.pos.y)
        r = self.radius
        outline = max(2, round(r * 0.1))
        pygame.draw.circle(screen, (45, 45, 55), (x, y), r + outline)                      # outline
        pygame.draw.circle(screen, (125, 130, 145), (x, y), r)                             # body
        pygame.draw.circle(screen, (180, 185, 198),
                           (x - round(r * 0.33), y - round(r * 0.36)), max(3, round(r * 0.3)))  # shine


class Slime(Enemy):
    """Rests for a long time, squashes down and charges, pushes itself towards the cat,
    then skids past with friction before resting again. A big slime splits into smaller
    ones when it dies; the smaller ones just die."""

    def __init__(self, pos, scale=1.0, health=SLIME_HEALTH, splits=True):
        radius = max(1, round(SLIME_RADIUS * scale))
        super().__init__(pos, radius, PLAYER_MASS * SLIME_MASS * scale ** 2, SLIME_DAMAGE)
        self.scale = scale
        self.target_offset = SLIME_TARGET_OFFSET * scale
        self.shadow_scale = SLIME_SHADOW_SCALE
        self.health = health
        self.splits = splits
        self.img, self.charging_img = slime_sprites(scale)
        self.state = "rest"                 # rest -> charge -> crawl -> slide -> rest ...
        self.state_time = 0.0               # seconds spent in the current state
        self.rest_for = random.uniform(*SLIME_REST_TIME)
        self.crawl_dir = pygame.math.Vector2(0, 0)
        self.crawl_peak = 0.0               # speed it reaches at the end of the push

    def set_state(self, state):
        self.state = state
        self.state_time = 0.0
        self.friction = SLIME_SLIDE_FRICTION if state == "slide" else ENEMY_FRICTION
        if state == "rest":
            self.rest_for = random.uniform(*SLIME_REST_TIME)

    def start_crawl(self):
        to_cat = player_pos - self.pos
        dist = to_cat.length()
        self.crawl_dir = to_cat / dist if dist > 1e-3 else pygame.math.Vector2(0, 0)
        distance = min(SLIME_CRAWL_DISTANCE, dist)          # don't aim past the cat
        # the push speeds up along a quarter sine wave; this peak makes the push cover `distance`
        self.crawl_peak = distance * math.pi / (2 * SLIME_CRAWL_TIME)
        self.set_state("crawl")

    def update_ai(self, dt):
        self.state_time += dt
        if self.state == "rest":
            if self.state_time >= self.rest_for:
                self.set_state("charge")
        elif self.state == "charge":
            if self.state_time >= SLIME_CHARGE_TIME:
                self.start_crawl()
        elif self.state == "crawl":                          # pushing itself forward, speeding up
            k = self.state_time / SLIME_CRAWL_TIME
            if k >= 1:
                self.set_state("slide")
                self.vel = self.crawl_dir * self.crawl_peak  # lets go at full speed, friction does the rest
            else:
                self.vel = self.crawl_dir * self.crawl_peak * math.sin(math.pi / 2 * k)
        else:                                                # slide: skids past its aim and slows down
            if self.vel.length() < sc(12) or self.state_time > 4.0:
                self.set_state("rest")

    def on_death(self):
        """A big slime splits into smaller ones that fly apart."""
        if not self.splits:
            return []
        babies = []
        for i in range(SLIME_SPLIT_COUNT):
            angle = math.tau * i / SLIME_SPLIT_COUNT        # two babies: one flies left, one right
            direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))
            baby = Slime(self.pos + direction * round(SLIME_RADIUS * SLIME_SPLIT_SIZE),
                         SLIME_SPLIT_SIZE, SLIME_SPLIT_HEALTH, splits=False)
            baby.vel = direction * SLIME_SPLIT_SPEED
            babies.append(baby)
        return babies

    def rect(self):
        if self.img is None:
            return super().rect()
        return self.img.get_rect(midbottom=(round(self.pos.x), round(self.pos.y) + self.radius))

    def draw(self):
        if self.img is None:
            super().draw()                                   # no sprite: plain ball
            return
        x, y = view(self.pos.x, self.pos.y)
        r = self.radius
        shake = 0.0
        if self.state == "charge":
            if self.state_time < SLIME_SQUASH_TIME:
                # 1) squash down
                img = squashed(self.img, ease_in_out(self.state_time / SLIME_SQUASH_TIME))
            else:
                # 2) hold the squash in the charging pose, trembling more and more
                img = squashed(self.charging_img, SLIME_HOLD_SQUASH)   # the squash is kept
                held = (self.state_time - SLIME_SQUASH_TIME) / max(1e-6, SLIME_CHARGE_TIME - SLIME_SQUASH_TIME)
                shake = math.sin(self.state_time * 55) * SLIME_CHARGE_SHAKE * min(1.0, held)
        elif self.state == "crawl" and self.state_time < SLIME_SPRING_TIME:
            # the squash is released only now: springs up, overshooting into a little stretch
            img = squashed(self.img, SLIME_HOLD_SQUASH * (1 - ease_out_back(self.state_time / SLIME_SPRING_TIME)))
        else:
            img = self.img
        if self.flash > 0:
            img = flashed(img)                               # white flash when hit
        # the slime sits on the ground: its bottom lines up with the bottom of the collision circle
        screen.blit(img, img.get_rect(midbottom=(round(x + shake), y + r)))

class Statue(Enemy):
    """Rests, shakes while fading into its charging sprite, flies off the top of the screen,
    hovers, then drops onto the cat. A shadow on the floor telegraphs where it lands
    (big + faint -> small + dark)."""

    AIR_STATES = ("rise", "hover", "fall")

    def __init__(self, pos):
        super().__init__(pos, STATUE_RADIUS, PLAYER_MASS * STATUE_MASS, 0)   # only hurts with the slam
        self.health = STATUE_HEALTH
        self.img, self.charging_img = statue_img, statue_charging_img
        sprite_h = self.img.get_height() if self.img else STATUE_HEIGHT
        self.air_height = sprite_h + HEIGHT          # how far up it must go to be fully off screen
        self.air_offset = 0.0                        # <= 0, how far above the ground it is
        self.state = "rest"
        self.state_time = 0.0
        self.rest_for = random.uniform(*STATUE_REST_TIME)

    def set_state(self, state):
        self.state = state
        self.state_time = 0.0
        if state in ("rest", "charge", "land"):      # also what the chain spell does: yanks it to the ground
            self.air_offset = 0.0
            self.collidable = True
            self.invulnerable = False
        else:
            self.collidable = False
            self.invulnerable = True
        if state == "rest":
            self.rest_for = random.uniform(*STATUE_REST_TIME)

    def track(self, dt):
        """The statue (and its shadow) snaps straight onto the cat, no lag."""
        self.pos.update(player_pos)

    def air_progress(self):
        total = STATUE_RISE_TIME + STATUE_HOVER_TIME + STATUE_FALL_TIME
        done = {"rise": 0.0, "hover": STATUE_RISE_TIME,
                "fall": STATUE_RISE_TIME + STATUE_HOVER_TIME}[self.state] + self.state_time
        return clamp01(done / total)

    def land(self):
        self.set_state("land")
        for i in range(4):
            a = math.tau * i / 4
            spawn_puff((self.pos.x + math.cos(a) * self.radius,
                        self.pos.y + self.radius + math.sin(a) * self.radius * 0.3))
        away = player_pos - self.pos
        if away.length() <= PLAYER_RADIUS + self.radius + sc(4):    # the cat is under it
            hurt_player(STATUE_SLAM_DAMAGE)
            if away.length_squared() > 0:
                player_vel.update(player_vel + away.normalize() * STATUE_KNOCKBACK)

    def update_ai(self, dt):
        self.state_time += dt
        t = self.state_time
        if self.state == "rest":
            if t >= self.rest_for:
                self.set_state("charge")
        elif self.state == "charge":
            if t >= STATUE_CHARGE_TIME:
                self.set_state("rise")
        elif self.state == "rise":
            k = clamp01(t / STATUE_RISE_TIME)
            self.air_offset = -self.air_height * k                 # shoots straight up, fast
            if k >= 1:
                self.set_state("hover")
                self.track(dt)                                      # teleports onto the cat, shadow included
        elif self.state == "hover":
            self.air_offset = -self.air_height
            if t < STATUE_HOVER_TIME - STATUE_LOCK_TIME:
                self.track(dt)                                      # then the spot is locked
            if t >= STATUE_HOVER_TIME:
                self.set_state("fall")
        elif self.state == "fall":
            k = clamp01(t / STATUE_FALL_TIME)
            self.air_offset = -self.air_height * (1 - k * k)       # speeds up as it drops
            if k >= 1:
                self.land()
        elif self.state == "land":
            if t >= STATUE_LAND_TIME:
                self.set_state("rest")

    def rect(self):
        if not self.collidable:
            return pygame.Rect(0, 0, 0, 0)
        if self.img is None:
            return super().rect()
        return self.img.get_rect(midbottom=(round(self.pos.x), round(self.pos.y) + self.radius))

    def draw_ground(self):
        if self.state in self.AIR_STATES:
            p = self.air_progress()
            scale = STATUE_SHADOW_START_SCALE + (1.0 - STATUE_SHADOW_START_SCALE) * p
            alpha = round(STATUE_SHADOW_START_ALPHA + (SHADOW_ALPHA - STATUE_SHADOW_START_ALPHA) * p)
            self.draw_shadow(scale, alpha)       # same shape as the normal shadow, just bigger and fainter
        else:
            self.draw_shadow()

    def draw(self):
        if self.img is None:
            if self.state not in self.AIR_STATES:
                super().draw()                               # no sprite: plain ball
            return
        if self.state == "hover":
            return                                           # off screen
        x, y = view(self.pos.x, self.pos.y)
        r = self.radius
        img, shake_x, shake_y, blend = self.img, 0.0, 0.0, 0.0
        if self.state == "charge":
            k = clamp01(self.state_time / STATUE_CHARGE_TIME)
            blend = k                                        # idle fades into the charging sprite
            amp = STATUE_SHAKE * (0.3 + 0.7 * k)             # shakes harder as it charges
            shake_x = math.sin(self.state_time * 70) * amp
            shake_y = math.sin(self.state_time * 93) * amp * 0.4
        elif self.state == "land":
            img = squashed(self.img, STATUE_LAND_SQUASH * (1 - clamp01(self.state_time / STATUE_LAND_SQUASH_TIME)))
        pos = (round(x + shake_x), round(y + r + self.air_offset + shake_y))
        flashing = self.flash > 0
        screen.blit(flashed(img) if flashing else img, img.get_rect(midbottom=pos))
        if blend > 0:
            top = flashed(self.charging_img) if flashing else self.charging_img
            top.set_alpha(round(255 * blend))
            screen.blit(top, top.get_rect(midbottom=pos))
            top.set_alpha(255)


def spawn_enemies():
    """Enemies at random spots that keep clear of the cat, the notebook and ink bar,
    the window edges (so the target circle fits) and each other."""
    reach = max(Slime(pygame.math.Vector2()).reach, Statue(pygame.math.Vector2()).reach)
    margin = int(reach) + 4
    avoid_hud = hud_rect.inflate(int(reach) * 2, int(reach) * 2)

    placed = []
    for kind in [Slime] * ENEMY_COUNT + [Statue] * STATUE_COUNT:
        for _try in range(3000):
            pos = pygame.math.Vector2(random.randint(margin, WIDTH - margin),
                                      random.randint(margin, HEIGHT - margin))
            if avoid_hud.collidepoint(pos.x, pos.y):
                continue
            if pos.distance_to(player_pos) < reach + PLAYER_RADIUS + SLIME_SPAWN_DISTANCE:
                continue
            if any(pos.distance_to(o.pos) < reach + o.reach for o in placed):
                continue
            placed.append(kind(pos))
            break
    return placed


enemies = []


# --- Health: hearts, two health points each (full = 2, half = 1, empty = 0) ----
# Hearts are filled from the first to the last, so damage always empties the LAST heart first.
player_hp = HEART_COUNT * 2
player_invuln = 0.0                       # seconds left in which the cat can't be hurt
shield_hits = 0                           # extra hits the shield can still absorb


def _fallback_heart(size, fill):
    """A simple drawn heart, used when the heart sprites are not found."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pts = []
    for i in range(48):
        t = i / 48 * math.tau
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((size / 2 + x * size / 36, size / 2 - y * size / 36 + size * 0.04))
    pygame.draw.polygon(surf, fill, pts)
    pygame.draw.polygon(surf, (60, 20, 30), pts, max(2, size // 16))
    return surf


def recolor_lighter(img, ink, white_level, strength):
    """The opposite of recolor_target: white = the plain ink colour, and the greyer an area is,
    the LIGHTER the ink colour becomes there. Transparency is kept."""
    img = img.copy()
    for x in range(img.get_width()):
        for y in range(img.get_height()):
            r, g, b, a = img.get_at((x, y))
            if a == 0:
                continue
            brightness = min(1.0, ((r + g + b) / 3) / white_level)   # 1 = white, 0 = black
            lift = strength * (1 - brightness)                       # 0 = plain ink colour, 1 = white
            img.set_at((x, y), (round(ink[0] + (255 - ink[0]) * lift),
                                round(ink[1] + (255 - ink[1]) * lift),
                                round(ink[2] + (255 - ink[2]) * lift), a))
    return img


try:
    _hearts_raw = [trim(load(f)) for f in (HEART_EMPTY_FILE, HEART_HALF_FILE, HEART_FULL_FILE)]
    _heart_scale = HEART_SIZE / max(h.get_height() for h in _hearts_raw)      # one scale for all three
    # [empty, half, full]; the empty heart is drawn smaller
    heart_imgs = [scale_sprite(h, _heart_scale * (HEART_EMPTY_SCALE if i == 0 else 1.0))
                  for i, h in enumerate(_hearts_raw)]
    if HEART_TINT:
        _heart_white = max(brightest(h) for h in heart_imgs)                  # the sprites' own white = the plain ink colour
        heart_imgs = [recolor_lighter(h, INK_COLOR, _heart_white, HEART_LIGHTEN) for h in heart_imgs]
except (FileNotFoundError, pygame.error):
    _empty = _fallback_heart(HEART_SIZE, (90, 80, 85))
    _full = _fallback_heart(HEART_SIZE, (225, 55, 70))
    _half = _empty.copy()
    _half.blit(_full, (0, 0), area=pygame.Rect(0, 0, HEART_SIZE // 2, HEART_SIZE))
    heart_imgs = [scale_sprite(_empty, HEART_EMPTY_SCALE), _half, _full]

_heart_w = max(h.get_width() for h in heart_imgs)
_heart_h = max(h.get_height() for h in heart_imgs)
_heart_rows = -(-HEART_COUNT // HEART_COLUMNS)
# Centred on the top border (but never over the ink bar)
hearts_rect = pygame.Rect(0, notebook_rect.top,
                          HEART_COLUMNS * _heart_w + (HEART_COLUMNS - 1) * HEART_GAP,
                          _heart_rows * _heart_h + (_heart_rows - 1) * HEART_GAP)
hearts_rect.centerx = WIDTH // 2
hearts_rect.left = max(hearts_rect.left, holder_rect.right + sc(24))
hearts_surface = pygame.Surface(hearts_rect.size, pygame.SRCALPHA)

try:
    _shield_raw = trim(load(SHIELD_FILE))
    shield_img = scale_sprite(_shield_raw, SHIELD_ICON_SIZE / _shield_raw.get_height())
except (FileNotFoundError, pygame.error):
    shield_img = _fallback_heart(SHIELD_ICON_SIZE, (90, 40, 170))
SHIELD_ROW_H = shield_img.get_height() + SHIELD_TOP_GAP    # space reserved under the hearts


def draw_shield_hearts(alpha):
    """The extra hearts: a small row of spell sprites right under the hearts. One disappears per hit."""
    if shield_hits <= 0:
        return
    w = shield_img.get_width()
    x = hearts_rect.centerx - (shield_hits * w + (shield_hits - 1) * SHIELD_GAP) // 2
    y = hearts_rect.bottom + SHIELD_TOP_GAP
    shield_img.set_alpha(round(255 * alpha))
    for i in range(shield_hits):
        screen.blit(shield_img, (x + i * (w + SHIELD_GAP), y))

def hurt_player(points):
    """Take health points away (ignored while the cat is still blinking from the last hit).
    The shield absorbs a whole hit, whatever its damage, before any heart is touched."""
    global player_hp, player_invuln, shield_hits
    if player_invuln > 0 or player_hp <= 0:
        return
    if shield_hits > 0:
        shield_hits -= 1
        player_invuln = PLAYER_INVULN_TIME
        return
    player_hp = max(0, player_hp - points)
    player_invuln = PLAYER_INVULN_TIME


def update_health(dt):
    global player_invuln
    player_invuln = max(0.0, player_invuln - dt)


def draw_hearts(alpha):
    hearts_surface.fill((0, 0, 0, 0))
    for i in range(HEART_COUNT):
        row, col = divmod(i, HEART_COLUMNS)
        stage = max(0, min(2, player_hp - 2 * i))        # 0 = empty, 1 = half, 2 = full
        img = heart_imgs[stage]
        centre = (col * (_heart_w + HEART_GAP) + _heart_w // 2,
                  row * (_heart_h + HEART_GAP) + _heart_h // 2)
        hearts_surface.blit(img, img.get_rect(center=centre))
    hearts_surface.set_alpha(round(255 * alpha))
    screen.blit(hearts_surface, hearts_rect.topleft)


# --- Collision physics (player <-> enemies, enemy <-> enemy) ----------------
def collide(pa, va, ra, ma, pb, vb, rb, mb):
    """Separate two overlapping circles and exchange momentum (changes the vectors in place)."""
    delta = pb - pa
    dist = delta.length()
    min_dist = ra + rb
    if dist >= min_dist:
        return
    normal = delta / dist if dist > 0 else pygame.math.Vector2(1, 0)
    overlap = min_dist - dist
    total = ma + mb
    pa.update(pa - normal * overlap * (mb / total))   # the lighter one moves more
    pb.update(pb + normal * overlap * (ma / total))
    rel = (vb - va).dot(normal)
    if rel < 0:                                       # only if they are moving into each other
        j = -(1 + RESTITUTION) * rel / (1 / ma + 1 / mb)
        va.update(va - normal * (j / ma))
        vb.update(vb + normal * (j / mb))


def push_out_of_rect(e, rect):
    """Keep an enemy from being pushed onto the notebook."""
    cx = max(rect.left, min(e.pos.x, rect.right))
    cy = max(rect.top, min(e.pos.y, rect.bottom))
    d = pygame.math.Vector2(e.pos.x - cx, e.pos.y - cy)
    dist = d.length()
    if dist >= e.radius:
        return
    if dist == 0:                                     # centre is inside the rect
        e.pos.y = rect.top - e.radius
        e.vel.y = min(0, e.vel.y)
        return
    n = d / dist
    e.pos.update(e.pos + n * (e.radius - dist))
    vn = e.vel.dot(n)
    if vn < 0:
        e.vel.update(e.vel - n * vn)


def update_enemies(dt):
    for e in enemies:
        if e.spawn_t > 0:                # still in its spawn puff
            e.spawn_t -= dt
            if e.spawn_t <= 0:
                e.collidable = True
                e.invulnerable = False
                spawn_puff((e.pos.x, e.pos.y + e.radius))    # second puff as it pops out
            continue
        e.flash = max(0.0, e.flash - dt)
        if e.lock_time > 0:              # chained: can't move and can't act
            e.lock_time -= dt
            e.vel.update(0, 0)
            if e.lock_time <= 0:
                unlock_enemy(e)
        else:
            e.update_ai(dt * enemy_time_scale(e))    # slowed inside an ink area
    for e in enemies:
        if e.spawn_t > 0:
            continue
        edt = dt * enemy_time_scale(e)
        e.pos += e.vel * edt
        e.vel -= e.vel * min(1.0, e.friction * edt)
        if e.vel.length() < 2:
            e.vel.update(0, 0)

    # player <-> enemies
    for e in enemies:
        if not e.collidable:
            continue
        collide(player_pos, player_vel, PLAYER_RADIUS, PLAYER_MASS,
                e.pos, e.vel, e.radius, e.mass)
        if e.damage and player_pos.distance_to(e.pos) <= PLAYER_RADIUS + e.radius + sc(4):
            hurt_player(e.damage)

    # enemy <-> enemy
    for i in range(len(enemies)):
        for j in range(i + 1, len(enemies)):
            a, b = enemies[i], enemies[j]
            if not (a.collidable and b.collidable):
                continue
            collide(a.pos, a.vel, a.radius, a.mass, b.pos, b.vel, b.radius, b.mass)

def pick_target(current=None):
    """Random enemy among the ones near the player; if all the others are too far,
    the closest one wins. Never picks the enemy that is already targeted."""
    others = [i for i in range(len(enemies)) if i != current]
    if not others:
        return current
    near = [i for i in others if enemies[i].pos.distance_to(player_pos) <= TARGET_RANGE]
    if near:
        return random.choice(near)
    return min(others, key=lambda i: enemies[i].pos.distance_to(player_pos))


target_index = pick_target() if enemies else None
target_angle = 0.0
target_bob_time = 0.0


# --- Hurting enemies (the slash spell) ----------------------------------------
popups = []                                   # floating damage numbers


def add_popup(e, amount):
    surf = font.render(str(math.ceil(amount)), True, (210, 45, 45))
    rect = e.rect()
    popups.append({"surf": surf, "pos": pygame.math.Vector2(rect.centerx, rect.top), "age": 0.0})


def update_popups(dt):
    for p in popups:
        p["age"] += dt
        p["pos"].y -= sc(70) * dt             # rises while it fades
    popups[:] = [p for p in popups if p["age"] < 0.9]


def draw_popups():
    for p in popups:
        p["surf"].set_alpha(round(255 * (1 - p["age"] / 0.9)))
        screen.blit(p["surf"], p["surf"].get_rect(center=view(p["pos"].x, p["pos"].y)))


def damage_enemy(e, amount):
    """Hurt an enemy. When its health runs out it is removed, and it may split into smaller ones."""
    global target_index, kills
    if e not in enemies:
        return
    if e.invulnerable:
        return
    e.health -= amount
    e.flash = HIT_FLASH_TIME
    add_popup(e, amount)
    if e.health > 0:
        return

    idx = enemies.index(e)
    was_target = (idx == target_index)
    enemies.pop(idx)
    kills += 1
    if target_index is not None and idx < target_index:
        target_index -= 1                     # the list shifted down
    babies = e.on_death()
    enemies.extend(babies)
    spawn_puff(e.pos)                         # puff of smoke where it died
    drop_exp(e)                               # leaves exp on the ground                   # puff of smoke where it died
    if was_target:                            # keep the target on one of the new slimes, if any
        if babies:
            target_index = len(enemies) - len(babies)
        elif enemies:
            target_index = pick_target(None)
        else:
            target_index = None


def recolor_red(img, colour):
    """The red area of a sprite takes `colour`; everything else keeps its own colours.
    Half-red pixels (soft edges) get a half-and-half mix. Transparency is kept."""
    img = img.copy()
    for x in range(img.get_width()):
        for y in range(img.get_height()):
            r, g, b, a = img.get_at((x, y))
            if a == 0 or r == 0:
                continue
            amount = (r - max(g, b)) / r                   # 1 = pure red, 0 = not red at all
            if amount <= 0.02:
                continue
            img.set_at((x, y), (round(r * (1 - amount) + colour[0] * amount),
                                round(g * (1 - amount) + colour[1] * amount),
                                round(b * (1 - amount) + colour[2] * amount), a))
    return img


# built once, at the biggest size it is ever drawn at, then only shrunk
slash_base = None
try:
    _slash_raw = trim(load(SLASH_FILE))
    _slash_h = max(1, round(_slash_raw.get_height() * SLASH_LENGTH / _slash_raw.get_width()))
    slash_base = pygame.transform.smoothscale(_slash_raw, (round(SLASH_LENGTH * SLASH_STRETCH), _slash_h))
    slash_base = recolor_red(slash_base, SLASH_COLOR)
except (FileNotFoundError, pygame.error):
    pass                                                   # no sprite: the slash just hurts, without the animation


class SlashEffect:
    def __init__(self, enemy):
        self.enemy = enemy
        self.pos = pygame.math.Vector2(enemy.pos)
        self.reach = enemy.radius + SLASH_REACH
        self.angle = random.uniform(0, math.tau)           # random direction of the line (0 = right, clockwise)
        self.age = 0.0
        self.hit = False


slash_effects = []


def cast_slash():
    """The slash spell hits the enemy that is targeted right now."""
    if target_index is None or target_index >= len(enemies):
        return
    e = enemies[target_index]
    if slash_base is not None and not e.invulnerable:
        slash_effects.append(SlashEffect(e))               # the damage lands when the swipe crosses the centre
    else:
        damage_enemy(e, SLASH_DAMAGE)


def update_slashes(dt):
    for s in slash_effects:
        s.age += dt
        if s.enemy in enemies:
            s.pos.update(s.enemy.pos)                      # follows the enemy while it is alive
        if not s.hit and s.age >= SLASH_TIME / 2:
            s.hit = True
            damage_enemy(s.enemy, SLASH_DAMAGE)
    slash_effects[:] = [s for s in slash_effects if s.age < SLASH_TIME]


def draw_slashes():
    for s in slash_effects:
        u = clamp01(s.age / SLASH_TIME)                    # 0 = start of the line, 1 = end of it
        direction = pygame.math.Vector2(math.cos(s.angle), math.sin(s.angle))
        if not SLASH_FACES_RIGHT:
            direction = -direction
        centre = s.pos + direction * s.reach * (2 * u - 1)
        stretch = 1 + (SLASH_STRETCH - 1) * math.sin(math.pi * u)      # longest in the middle, normal at both ends
        img = pygame.transform.smoothscale(slash_base, (max(1, round(SLASH_LENGTH * stretch)), slash_base.get_height()))
        img = pygame.transform.rotozoom(img, -math.degrees(s.angle), 1)
        screen.blit(img, img.get_rect(center=view(centre.x, centre.y))) 



# --- Chain sprites ------------------------------------------------------------
try:
    _chain_raw = load(CHAIN_FILE)
    _chain_scale = CHAIN_HEIGHT / _chain_raw.get_height()
    chain_img = scale_sprite(_chain_raw, _chain_scale)
    try:
        chain_end_img = scale_sprite(load(CHAIN_END_FILE), _chain_scale)   # same scale, so the pieces match
    except (FileNotFoundError, pygame.error):
        chain_end_img = chain_img
except (FileNotFoundError, pygame.error):
    # no sprites found: simple grey links instead
    chain_img = pygame.Surface((CHAIN_HEIGHT * 2, CHAIN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(chain_img, (150, 150, 160), chain_img.get_rect().inflate(-4, -4),
                        max(2, CHAIN_HEIGHT // 6))
    chain_end_img = pygame.Surface((CHAIN_HEIGHT, CHAIN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(chain_end_img, (90, 90, 100), (CHAIN_HEIGHT // 2, CHAIN_HEIGHT // 2), CHAIN_HEIGHT // 2)
    
if CHAIN_TINT:
    # one shared white level, so the chain and the end piece get exactly the same colouring
    _chain_white = max(brightest(chain_img), brightest(chain_end_img))
    _chain_same = chain_end_img is chain_img          # (no end sprite found: it is the same picture)
    chain_img = recolor_target(chain_img, INK_COLOR, _chain_white)
    chain_end_img = chain_img if _chain_same else recolor_target(chain_end_img, INK_COLOR, _chain_white)


def chain_strip(length):
    """A horizontal chain `length` px long: the end piece on the left, links going right."""
    length = max(1, round(length))
    h = max(chain_img.get_height(), chain_end_img.get_height())
    strip = pygame.Surface((length, h), pygame.SRCALPHA)
    strip.blit(chain_end_img, (0, (h - chain_end_img.get_height()) // 2))
    step = max(1, chain_img.get_width() - CHAIN_LINK_OVERLAP)
    x = chain_end_img.get_width() - CHAIN_LINK_OVERLAP
    while x < length:                                  # whatever sticks out past `length` is cut off
        strip.blit(chain_img, (x, (h - chain_img.get_height()) // 2))
        x += step
    return strip


def build_chains(e):
    """The 4 chains of an enemy, as (picture, centre, floor end), all relative to the enemy's centre."""
    chains = []
    for deg in CHAIN_ANGLES:
        d = pygame.math.Vector2(math.cos(math.radians(deg)), math.sin(math.radians(deg)))
        anchor = d * (e.radius + CHAIN_REACH)          # where the end piece lies on the floor
        attach = d * (e.radius * CHAIN_ATTACH)         # where the chain meets the enemy
        along = attach - anchor
        length = along.length()
        along = along / length
        img = pygame.transform.rotozoom(chain_strip(length), -math.degrees(math.atan2(along.y, along.x)), 1)
        chains.append((img, anchor + along * (length / 2), anchor))
    return chains


def lock_enemy(e):
    """Chain an enemy to the floor so it can't move for CHAIN_TIME seconds."""
    was_locked = e.lock_time > 0
    e.lock_time = CHAIN_TIME
    e.vel.update(0, 0)
    e.mass = e.base_mass * CHAIN_MASS_MULT
    if hasattr(e, "set_state"):
        e.set_state("rest")                            # cancels a charge / crawl in progress
    if not was_locked:                                 # casting again only refreshes the timer
        e.chains = build_chains(e)
        for _img, _centre, anchor in e.chains:
            spawn_puff(e.pos + anchor)


def unlock_enemy(e):
    e.lock_time = 0.0
    e.mass = e.base_mass
    for _img, _centre, anchor in e.chains:
        spawn_puff(e.pos + anchor)
    e.chains = []


def draw_chains(e, front):
    """front=False draws the two upper chains (behind the enemy), front=True the two lower ones (over it)."""
    if e.lock_time <= 0 or not e.chains:
        return
    if e.lock_time < CHAIN_WARN_TIME and int(e.lock_time * 12) % 2 == 0:
        return                                         # blinks just before the chains break
    for img, centre, anchor in e.chains:
        if (anchor.y > 0) != front:                    # lower chains (floor end below the enemy's centre) are the front ones
            continue
        screen.blit(img, img.get_rect(center=view(e.pos.x + centre.x, e.pos.y + centre.y)))


def cast_chain():
    """The chain spell locks the targeted enemy (or all enemies) in place."""
    if CHAIN_ALL_ENEMIES:
        for e in enemies:
            lock_enemy(e)
    elif target_index is not None and target_index < len(enemies):
        lock_enemy(enemies[target_index])

# --- Ink area spell ----------------------------------------------------------
class InkArea:
    def __init__(self, center):
        self.pos = pygame.math.Vector2(center)
        self.age = 0.0
        self.angle = 0.0                 # how far the ring has turned (added up every frame, so speed changes are smooth)

    def spin_speed(self):
        """Degrees per second: slow at first, speeding up before the end."""
        start = INK_AREA_TIME - INK_AREA_SHRINK_TIME - INK_AREA_WARN_TIME
        k = ease_in_out(clamp01((self.age - start) / INK_AREA_WARN_TIME))
        return INK_AREA_SPIN * (1 + (INK_AREA_SPIN_BOOST - 1) * k)

    def radius(self):
        """Grows when cast, then shrinks to nothing at the end (the slowing area follows it)."""
        pop = max(0.0, ease_out_back(clamp01(self.age / INK_AREA_POP_TIME)))
        shrink = 1 - ease_in_out(clamp01((self.age - (INK_AREA_TIME - INK_AREA_SHRINK_TIME)) / INK_AREA_SHRINK_TIME))
        return INK_AREA_RADIUS * pop * shrink


ink_areas = []


def cast_ink_area():
    """Leaves a slowing zone at the cat's feet. It stays there and needs no target."""
    ink_areas.append(InkArea((player_pos.x, player_pos.y + PLAYER_RADIUS)))
    if len(ink_areas) > INK_AREA_MAX:
        ink_areas.pop(0)
    spawn_puff(ink_areas[-1].pos)


def update_ink_areas(dt):
    for a in ink_areas:
        a.age += dt
        a.angle += a.spin_speed() * dt
    ink_areas[:] = [a for a in ink_areas if a.age < INK_AREA_TIME]


def enemy_time_scale(e):
    """INK_AREA_SLOW if the enemy's feet are inside any zone, otherwise 1 (zones don't stack)."""
    foot = e.pos + pygame.math.Vector2(0, e.radius)
    for a in ink_areas:
        if foot.distance_to(a.pos) <= a.radius():
            return INK_AREA_SLOW
    return 1.0

def build_ink_ring():
    """The ring tile bent around a full circle (built once). The ring's centre line sits exactly on
    the zone's edge, half of it inside and half outside. The tile runs along the perimeter, and its
    length is adjusted a tiny bit so a whole number of tiles fits and the ends connect."""
    try:
        tile = load(INK_AREA_RING_FILE)
    except (FileNotFoundError, pygame.error):
        return None                                   # no sprite: the plain outline is used instead
    ss = max(1, INK_AREA_RING_QUALITY)
    half = (INK_AREA_RING_HEIGHT + 1) // 2            # half of the ring's thickness
    R = INK_AREA_RADIUS * ss                          # the centre line of the ring = the edge of the zone
    hh = half * ss
    h = 2 * hh
    outer, inner = R + hh, R - hh
    size = 2 * outer
    tile = tint(tile, INK_AREA_OUTLINE_COLOR)         # the white becomes the outline colour

    # a straight strip made of a whole number of tiles
    circ = math.tau * R
    natural_w = tile.get_width() * h / tile.get_height()
    n = INK_AREA_RING_TILES if INK_AREA_RING_TILES > 0 else max(1, round(circ / natural_w))
    tile_w = max(1, round(circ / n))
    tile = pygame.transform.smoothscale(tile, (tile_w, h))
    strip = pygame.Surface((n * tile_w, h), pygame.SRCALPHA)
    for i in range(n):
        strip.blit(tile, (i * tile_w, 0))
    sw = strip.get_width()

    # bend it: every pixel of the ring looks up where it sits on the strip
    out = pygame.Surface((size, size), pygame.SRCALPHA)
    out.fill((*INK_AREA_OUTLINE_COLOR, 0))            # same colour while transparent, so shrinking leaves no dark fringe
    for y in range(size):
        dy = y + 0.5 - outer
        if abs(dy) >= outer:
            continue
        x_out = math.sqrt(outer * outer - dy * dy)
        x_in = math.sqrt(inner * inner - dy * dy) if abs(dy) < inner else 0.0
        for x in range(max(0, math.ceil(outer - x_out)), min(size, math.floor(outer + x_out) + 1)):
            dx = x + 0.5 - outer
            if abs(dx) < x_in:
                continue                              # inside the hole of the ring
            d = math.hypot(dx, dy)
            if d >= outer or d < inner:
                continue
            u = (math.atan2(dy, dx) % math.tau) / math.tau * sw          # angle -> position along the strip
            v = (outer - d) if INK_AREA_RING_TOP_OUT else (d - inner)     # distance from the edge -> row of the strip
            out.set_at((x, y), strip.get_at((int(u) % sw, min(h - 1, int(v)))))
    if ss > 1:
        out = pygame.transform.smoothscale(out, (size // ss, size // ss))
    return out


ink_ring_img = build_ink_ring()

def draw_ink_areas():
    for a in ink_areas:
        r = round(a.radius())
        if r < 2:
            continue
        centre = view(a.pos.x, a.pos.y)
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*INK_COLOR, INK_AREA_FILL_ALPHA), (r, r), r)                        # see-through fill
        if ink_ring_img is None:
            pygame.draw.circle(surf, (*INK_AREA_OUTLINE_COLOR, 255), (r, r), r, INK_AREA_OUTLINE_WIDTH)   # fallback outline
        screen.blit(surf, surf.get_rect(center=centre))
        if ink_ring_img is not None:
            # the ring spins, and the same call resizes it while the zone pops in and shrinks away
            img = pygame.transform.rotozoom(ink_ring_img, a.angle, r / INK_AREA_RADIUS)
            screen.blit(img, img.get_rect(center=centre))

# --- Shockwave spell -------------------------------------------------------------
def build_shockwave_fill():
    """A disc in the ink colour that is strongest at the edge and fades to nothing in the middle (built once)."""
    R = SHOCKWAVE_RADIUS
    surf = pygame.Surface((R * 2, R * 2), pygame.SRCALPHA)
    surf.fill((*INK_COLOR, 0))                         # same colour while transparent, so shrinking leaves no dark fringe
    for r in range(R, 0, -1):                          # big circles first; each smaller one overwrites the middle with a fainter colour
        k = (r / R) ** SHOCKWAVE_FILL_FALLOFF
        pygame.draw.circle(surf, (*INK_COLOR, round(SHOCKWAVE_FILL_ALPHA * k)), (R, R), r)
    return surf


shockwave_fill_img = build_shockwave_fill()

def build_shockwave_image():
    """Fill + ring merged into one picture at the wave's full size (built once)."""
    img = shockwave_fill_img.copy()
    if ink_ring_img is not None:
        k = SHOCKWAVE_RADIUS / INK_AREA_RADIUS            # the ring is drawn bigger than in the ink area
        ring = pygame.transform.smoothscale(
            ink_ring_img, (round(ink_ring_img.get_width() * k), round(ink_ring_img.get_height() * k)))
        img.blit(ring, ring.get_rect(center=img.get_rect().center))
    return img


shockwave_img = build_shockwave_image()

class Shockwave:
    def __init__(self, center):
        self.pos = pygame.math.Vector2(center)
        self.age = 0.0
        self.pending = list(enemies)                   # only enemies that exist right now get hit

    def radius(self):
        t = clamp01(self.age / SHOCKWAVE_TIME)
        return SHOCKWAVE_RADIUS * (1 - (1 - t) ** 3)   # shoots out fast, then slows down

    def alpha(self):
        return clamp01(1 - (self.age - SHOCKWAVE_TIME) / SHOCKWAVE_FADE_TIME)


shockwaves = []


def cast_shockwave():
    """A wave of ink rolls out from the cat's feet and hurts everything it reaches."""
    shockwaves.append(Shockwave((player_pos.x, player_pos.y + PLAYER_RADIUS)))

# --- Lightning Step spell ---------------------------------------------------------
lightning_left = 0.0           # seconds of boost left
step_sparks = []


def cast_lightning():
    """Boosts the cat's movement. Can't be stacked: returns False (and does nothing) while it is active."""
    global lightning_left
    if lightning_left > 0:
        return False
    lightning_left = LIGHTNING_TIME
    spawn_puff((player_pos.x, player_pos.y + PLAYER_RADIUS))
    return True

def update_lightning(dt):
    global lightning_left
    lightning_left = max(0.0, lightning_left - dt)
    if lightning_left > 0 and player_vel.length() > WALK_SPEED_THRESHOLD:
        for _ in range(2):                                   # sparks behind the cat's feet
            step_sparks.append({
                "pos": pygame.math.Vector2(player_pos.x + random.uniform(-0.5, 0.5) * PLAYER_RADIUS,
                                           player_pos.y + PLAYER_RADIUS - random.uniform(0, sc(10))),
                "vel": pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 0.2)) * sc(60),
                "size": sc(random.uniform(2, 5)),
                "color": random.choice(LIGHTNING_SPARK_COLORS),
                "age": 0.0, "life": random.uniform(0.2, 0.4)})
    for p in step_sparks:
        p["age"] += dt
        p["pos"] += p["vel"] * dt
    step_sparks[:] = [p for p in step_sparks if p["age"] < p["life"]]


def draw_lightning():
    for p in step_sparks:
        r = max(1, round(p["size"] * (1 - p["age"] / p["life"])))
        pygame.draw.circle(screen, p["color"], view(p["pos"].x, p["pos"].y), r)

def cast_shield():
    """Fills the shield up to SHIELD_HEARTS. Returns False (and does nothing) if it is already full."""
    global shield_hits
    if shield_hits >= SHIELD_HEARTS:
        return False
    shield_hits = SHIELD_HEARTS
    spawn_puff((player_pos.x, player_pos.y + PLAYER_RADIUS))
    return True

def update_shockwaves(dt):
    for w in shockwaves:
        w.pos.update(player_pos.x, player_pos.y + PLAYER_RADIUS)   # the wave moves with the cat's feet
        w.age += dt
        r = w.radius()
        for e in list(w.pending):
            if e not in enemies:
                w.pending.remove(e)
                continue
            foot = e.pos + pygame.math.Vector2(0, e.radius)       # same floor level as the ink area
            if foot.distance_to(w.pos) <= r:                      # the ring has reached it
                w.pending.remove(e)
                damage_enemy(e, SHOCKWAVE_DAMAGE)
    shockwaves[:] = [w for w in shockwaves if w.age < SHOCKWAVE_TIME + SHOCKWAVE_FADE_TIME]


def draw_shockwaves():
    for w in shockwaves:
        r = round(w.radius())
        if r < 2:
            continue
        # one rotate + resize for fill and ring together (the fill is round, so turning it changes nothing)
        img = pygame.transform.rotozoom(shockwave_img, w.age * SHOCKWAVE_SPIN, r / SHOCKWAVE_RADIUS)
        img.set_alpha(round(255 * w.alpha()))
        screen.blit(img, img.get_rect(center=view(w.pos.x, w.pos.y)))

# --- Arrow spell ---------------------------------------------------------------
try:
    _arrow_raw = trim(load(ARROW_FILE))
    _arrow_k = ARROW_HEIGHT / _arrow_raw.get_height()
    arrow_img = pygame.transform.smoothscale(
        _arrow_raw, (max(1, round(_arrow_raw.get_width() * _arrow_k)),      # the width follows the size...
                     max(1, round(ARROW_HEIGHT * ARROW_STRETCH))))          # ...only the length is stretched
    arrow_img = recolor_red(arrow_img, ARROW_COLOR)                         # red area -> ink colour (same function as the slash)
except (FileNotFoundError, pygame.error):
    # no sprite found: a simple grey arrow instead
    _arrow_len = max(4, round(ARROW_HEIGHT * ARROW_STRETCH))
    arrow_img = pygame.Surface((max(4, ARROW_HEIGHT // 4), _arrow_len), pygame.SRCALPHA)
    _aw = arrow_img.get_width()
    pygame.draw.line(arrow_img, (70, 70, 80), (_aw // 2, 0), (_aw // 2, _arrow_len), max(2, _aw // 5))
    pygame.draw.polygon(arrow_img, (70, 70, 80), [(_aw // 2, 0), (0, _arrow_len // 3), (_aw, _arrow_len // 3)])


class Arrow:
    def __init__(self, target):
        self.target = target
        self.pos = pygame.math.Vector2(player_pos)         # the TIP of the arrow
        d = target.pos - player_pos
        self.dir = d.normalize() if d.length() > 1e-3 else pygame.math.Vector2(0, -1)
        self.age = 0.0
        self.pierced = set()                               # enemies it already went through
        self.done = False


arrows = []


def cast_arrow():
    """Sends an arrow at the enemy that is targeted right now."""
    if target_index is not None and target_index < len(enemies):
        arrows.append(Arrow(enemies[target_index]))


def update_arrows(dt):
    for a in arrows:
        a.age += dt
        dist = ARROW_SPEED * dt
        steps = max(1, math.ceil(dist / sc(12)))           # small steps, so a fast arrow can't jump over an enemy
        for _ in range(steps):
            if a.target in enemies:                        # steers at its target
                to = a.target.pos - a.pos
                if to.length() > 1e-3:
                    a.dir = to.normalize()
            a.pos += a.dir * (dist / steps)
            for e in list(enemies):
                if a.pos.distance_to(e.pos) > e.radius + ARROW_RADIUS:
                    continue
                if e is a.target:                          # reached its target: the arrow ends here
                    damage_enemy(e, ARROW_HIT_DAMAGE)
                    spawn_puff(a.pos)
                    a.done = True
                    break
                if e.collidable and not e.invulnerable and e not in a.pierced:
                    a.pierced.add(e)                       # every enemy is only pierced once
                    damage_enemy(e, ARROW_PIERCE_DAMAGE)
            if a.done:
                break
        if a.age >= ARROW_LIFETIME:
            a.done = True
    arrows[:] = [a for a in arrows if not a.done]


def draw_arrows():
    for a in arrows:
        img = pygame.transform.rotozoom(arrow_img, _vec_angle(a.dir.x, a.dir.y) - 90, 1)   # the sprite points up
        centre = a.pos - a.dir * (arrow_img.get_height() / 2)                               # the tip leads, the tail trails
        screen.blit(img, img.get_rect(center=view(centre.x, centre.y)))

def draw_enemies():
    for e in enemies:
        if e.spawn_t <= 0:
            e.draw_ground()                              # floor shadows / landing telegraph, under everything
    target = enemies[target_index] if target_index is not None and target_index < len(enemies) else None
    for e in sorted(enemies, key=lambda en: en.pos.y):
        if e.spawn_t > 0:
            continue
        draw_chains(e, front=False)
        if e is target:
            draw_target(e)                               # the ring sits behind the enemy
        e.draw()
        draw_chains(e, front=True)

def draw_target(e):
    """One ring, drawn behind the targeted enemy."""
    pulse = 1 + math.sin(target_bob_time * TARGET_BOB_SPEED) * TARGET_BOB_FRACTION
    diameter = 2 * e.ring_radius * pulse
    scale = diameter / max(target_img.get_size())
    img = pygame.transform.rotozoom(target_img, -target_angle, scale)   # spin + resize in one go
    screen.blit(img, img.get_rect(center=view(e.pos.x, e.pos.y + e.target_offset)))


# --- Notebook + ink bar: drawn on top of everything, see-through when something is under them ---
hud_surface = pygame.Surface(notebook_rect.size, pygame.SRCALPHA)   # the notebook and its ink are put together here
hud_alpha_notebook = 1.0
hud_alpha_bar = 1.0
hud_alpha_hearts = 1.0


def thing_rects():
    """Screen areas of everything that can end up under the notebook or the ink bar."""
    rects = [cat_idle_img.get_rect(midbottom=(round(player_pos.x), round(player_pos.y) + PLAYER_RADIUS))]
    rects += [e.rect() for e in enemies]
    if target_index is not None:                                    # the target circle counts too
        e = enemies[target_index]
        reach = round(e.reach)
        rects.append(pygame.Rect(round(e.pos.x) - reach, round(e.pos.y) - reach, reach * 2, reach * 2))
    if reloading:                                                   # and the inker + pencil
        (ix, iy), (px, py) = reload_positions()
        rects.append(inker_img.get_rect(center=(round(ix), round(iy))))
        side = max(pencil_img.get_size())
        rects.append(pygame.Rect(round(px) - side // 2, round(py) - side // 2, side, side))
    return [r.move(-round(cam.x), -round(cam.y)) for r in rects]

def update_hud_fade(dt):
    """Fade the notebook, the ink bar, the hearts and the exp bar out while something is under them."""
    global hud_alpha_notebook, hud_alpha_bar, hud_alpha_hearts, hud_alpha_xp
    rects = thing_rects()
    under_notebook = any(r.colliderect(notebook_rect) for r in rects)
    under_bar = any(r.colliderect(holder_rect) for r in rects)
    under_hearts = any(r.colliderect(hearts_rect) for r in rects)
    under_xp = any(r.colliderect(xp_rect) for r in rects)
    k = min(1.0, HUD_FADE_SPEED * dt)
    hud_alpha_notebook += ((HUD_FADE_ALPHA if under_notebook else 1.0) - hud_alpha_notebook) * k
    hud_alpha_bar += ((HUD_FADE_ALPHA if under_bar else 1.0) - hud_alpha_bar) * k
    hud_alpha_hearts += ((HUD_FADE_ALPHA if under_hearts else 1.0) - hud_alpha_hearts) * k
    hud_alpha_xp += ((HUD_FADE_ALPHA if under_xp else 1.0) - hud_alpha_xp) * k


def draw_notebook(alpha):
    """Notebook, ink and glows are put together on their own surface, then drawn with one alpha."""
    hud_surface.fill((0, 0, 0, 0))
    hud_surface.blit(notebook_img, (0, 0))
    hud_surface.blit(outline_layer, (0, 0), area=notebook_rect)     # bottom
    hud_surface.blit(colour_layer, (0, 0), area=notebook_rect)      # middle
    draw_fresh_ink(hud_surface)                                     # bright ink fading into the colour layer
    for gp in glow_positions:                                       # top (the surface edges keep glows inside)
        hud_surface.blit(glow_img, glow_img.get_rect(center=(gp[0] - notebook_rect.x, gp[1] - notebook_rect.y)))
    hud_surface.set_alpha(round(255 * alpha))
    screen.blit(hud_surface, notebook_rect.topleft)

# =============================================================================
# INTRO ANIMATIONS (logo zooms in, shockwave, text slides in, VHS look)
# =============================================================================
INTRO_K = HEIGHT / 600                    # the intro was designed for 800x600, this keeps the same look
INTRO_FONT_PATH = os.path.join(BASE_DIR, "assets", "Daydream DEMO.otf")   # falls back to default font if missing


MAGIC_COLORS = [(150, 205, 255), (235, 245, 255), (190, 165, 255), (110, 180, 255)]
MAGIC_BG_TOP = (8, 10, 28)
MAGIC_BG_BOTTOM = (30, 18, 64)
MAGIC_AMBIENT_SPARKLES = 70


class MagicEffect:
    """Gradient background, a soft glow, and twinkling star sparkles."""

    def __init__(self, width, height):
        self.width, self.height = width, height
        self.sparkles = []

        # vertical gradient (built tiny, then stretched)
        strip = pygame.Surface((2, 64))
        for y in range(64):
            k = y / 63
            col = tuple(round(MAGIC_BG_TOP[i] + (MAGIC_BG_BOTTOM[i] - MAGIC_BG_TOP[i]) * k) for i in range(3))
            strip.set_at((0, y), col)
            strip.set_at((1, y), col)
        self.background = pygame.transform.smoothscale(strip, (width, height))

        for _ in range(MAGIC_AMBIENT_SPARKLES):
            self.spawn(random_y=True)

    def spawn(self, random_y=False):
        life = random.uniform(3.0, 6.0)
        self.sparkles.append({
            "pos": pygame.math.Vector2(random.uniform(0, self.width),
                                       random.uniform(0, self.height) if random_y else self.height + 10),
            "vel": pygame.math.Vector2(random.uniform(-8, 8), -random.uniform(15, 50)) * INTRO_K,
            "size": random.uniform(2, 6) * INTRO_K,
            "color": random.choice(MAGIC_COLORS),
            "phase": random.uniform(0, math.tau),
            "speed": random.uniform(3, 7),
            "life": life,
            "age": random.uniform(0, life) if random_y else 0.0,
            "burst": False,
        })

    def burst(self, center, count=60):
        """A ring of sparkles flying outwards."""
        for _ in range(count):
            a = random.uniform(0, math.tau)
            speed = random.uniform(80, 420) * INTRO_K
            self.sparkles.append({
                "pos": pygame.math.Vector2(center),
                "vel": pygame.math.Vector2(math.cos(a), math.sin(a)) * speed,
                "size": random.uniform(3, 8) * INTRO_K,
                "color": random.choice(MAGIC_COLORS),
                "phase": random.uniform(0, math.tau),
                "speed": random.uniform(8, 14),
                "life": random.uniform(0.8, 1.6),
                "age": 0.0,
                "burst": True,
            })

    def update(self, dt):
        for s in self.sparkles:
            s["age"] += dt
            s["pos"] += s["vel"] * dt
            s["pos"].x += math.sin(s["age"] * 1.5 + s["phase"]) * 10 * INTRO_K * dt   # gentle sway
            if s["burst"]:
                s["vel"] *= max(0.0, 1 - 2.5 * dt)                                      # burst slows down
        self.sparkles = [s for s in self.sparkles if s["age"] < s["life"]]
        while sum(1 for s in self.sparkles if not s["burst"]) < MAGIC_AMBIENT_SPARKLES:
            self.spawn()

    def draw(self, surface):
        for s in self.sparkles:
            fade = math.sin(math.pi * s["age"] / s["life"])                 # fades in and out
            twinkle = 0.65 + 0.35 * math.sin(s["age"] * s["speed"] + s["phase"])
            b = max(0.0, fade * twinkle)
            if b <= 0.02:
                continue
            col = tuple(round(c * b) for c in s["color"])
            x, y, size = s["pos"].x, s["pos"].y, s["size"]
            if size < 3:
                pygame.draw.circle(surface, col, (round(x), round(y)), max(1, round(size / 2)))
            else:
                t = size * 0.2
                pygame.draw.polygon(surface, col, [
                    (x, y - size), (x + t, y - t), (x + size, y), (x + t, y + t),
                    (x, y + size), (x - t, y + t), (x - size, y), (x - t, y - t)])
                pygame.draw.circle(surface, tuple(c // 3 for c in col), (round(x), round(y)), max(1, round(size * 0.5)))

    def apply(self, surface):
        self.frame += 1
        result = surface.copy()
        if self.frame % 2 == 0:                                   # red channel shifted sideways
            red = pygame.Surface((self.width, self.height))
            red.blit(surface, (-self.color_shift, 0))
            red.fill((255, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
            result.blit(red, (self.color_shift, 0), special_flags=pygame.BLEND_RGB_ADD)
        result.blit(self.scanlines, (0, 0))
        result.blit(self.noise_patches[(self.frame // 3) % len(self.noise_patches)], (0, 0))
        return result


def _intro_font(size):
    try:
        return pygame.font.Font(INTRO_FONT_PATH, size)
    except (FileNotFoundError, pygame.error):
        return pygame.font.Font(None, size)

# =============================================================================
# LEVELS, EXP ORBS AND THE EXP BAR
# =============================================================================
level = 1
exp_points = 0
xp_shown = 0.0                 # what the bar displays (follows the real value smoothly)
hud_alpha_xp = 1.0

# --- Spell choices -------------------------------------------------------------
SPELL_SKIP_REFUND = 0.2        # skipping a choice gives back this fraction of the exp that level needed
ALL_SPELLS = list(SPELL_NAMES)
DAMAGE_SPELLS = [SLASH_SPELL[0], ARROW_SPELL[0], SHOCKWAVE_SPELL[0]]   # offered in the very first choice
UNKNOWN_SPELL = ("Unknown Spell", None)
known_spells = set()
kills = 0
pending_choice_refunds = []    # one entry per level-up still waiting for a spell choice

def exp_needed():
    return EXP_BASE_NEEDED + (level - 1) * EXP_NEEDED_STEP


def render_outlined(fnt, label, colour, outline_colour, o):
    """Text with a round solid outline."""
    body = fnt.render(label, True, colour)
    edge = fnt.render(label, True, outline_colour)
    surf = pygame.Surface((body.get_width() + 2 * o, body.get_height() + 2 * o), pygame.SRCALPHA)
    for dx in range(-o, o + 1):
        for dy in range(-o, o + 1):
            if dx * dx + dy * dy <= o * o + 1:
                surf.blit(edge, (o + dx, o + dy))
    surf.blit(body, (o, o))
    return surf


# --- Orb sprite ---
try:
    _exp_raw = trim(load(EXP_FILE))
    exp_img = scale_sprite(_exp_raw, EXP_HEIGHT / _exp_raw.get_height())
except (FileNotFoundError, pygame.error):
    exp_img = pygame.Surface((EXP_HEIGHT, EXP_HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(exp_img, INK_START_COLOR, (EXP_HEIGHT // 2, EXP_HEIGHT // 2), EXP_HEIGHT // 2)
    pygame.draw.circle(exp_img, INK_COLOR, (EXP_HEIGHT // 2, EXP_HEIGHT // 2), EXP_HEIGHT // 2, max(2, EXP_HEIGHT // 8))

exp_orbs = []


class ExpOrb:
    def __init__(self, ground_pos):
        self.pos = pygame.math.Vector2(ground_pos)           # the spot on the ground under the orb
        a = random.uniform(0, math.tau)
        self.vel = pygame.math.Vector2(math.cos(a), math.sin(a)) * random.uniform(0.4, 1.0) * EXP_POP_SPEED
        self.age = 0.0
        self.phase = random.uniform(0, math.tau)
        self.magnet = False
        self.speed = EXP_MAGNET_START


def drop_exp(e):
    """Called when an enemy dies: it leaves exp orbs on the ground where it stood."""
    for _ in range(EXP_PER_ENEMY):
        exp_orbs.append(ExpOrb(e.pos + pygame.math.Vector2(0, e.radius)))


def gain_exp(amount):
    global level, exp_points, xp_shown
    exp_points += amount
    while exp_points >= exp_needed():
        needed = exp_needed()
        exp_points -= needed
        level += 1
        xp_shown = 0.0                                       # the bar starts over for the new level
        spawn_puff((player_pos.x, player_pos.y + PLAYER_RADIUS))
        if any(s not in known_spells for s in ALL_SPELLS):   # something left to learn: queue a choice
            pending_choice_refunds.append(max(1, round(needed * SPELL_SKIP_REFUND)))


def update_exp(dt):
    feet = pygame.math.Vector2(player_pos.x, player_pos.y + PLAYER_RADIUS)
    for o in exp_orbs:
        o.age += dt
        to = feet - o.pos
        dist = to.length()
        if not o.magnet and o.age >= EXP_MAGNET_DELAY and dist <= EXP_MAGNET_RANGE:
            o.magnet = True                                  # once it starts flying it never stops
        if o.magnet:
            o.speed = min(EXP_MAGNET_MAX, o.speed + EXP_MAGNET_ACCEL * dt)
            if dist > 1e-3:
                o.pos += to / dist * min(dist, o.speed * dt)
        else:
            o.pos += o.vel * dt
            o.vel -= o.vel * min(1.0, EXP_POP_FRICTION * dt)
    for o in exp_orbs[:]:
        if o.magnet and feet.distance_to(o.pos) <= EXP_PICKUP_RADIUS:
            exp_orbs.remove(o)
            gain_exp(EXP_VALUE)


def draw_exp():
    for o in exp_orbs:
        k = (math.sin(o.age * EXP_BOB_SPEED + o.phase) + 1) / 2       # 0..1
        lift = EXP_HOVER + EXP_BOB_HEIGHT * k
        w = max(4, round(exp_img.get_width() * (0.9 - 0.3 * k)))      # the shadow shrinks when the orb is high
        draw_shadow_ellipse((round(o.pos.x) - w // 2, round(o.pos.y) - max(2, w // 6), w, max(3, w // 3)))
        screen.blit(exp_img, exp_img.get_rect(midbottom=view(o.pos.x, o.pos.y - lift)))


# --- Exp bar: copies of the inkbar sprite side by side across the whole screen, flush with the bottom edge ---
_xp_tile = trim(load("inkbar.png"))
if XPBAR_ROTATE:
    _xp_tile = pygame.transform.rotate(_xp_tile, XPBAR_ROTATE)
if XPBAR_SCALE != 1.0:
    _xp_tile = scale_sprite(_xp_tile, XPBAR_SCALE * UI_SCALE)    # same width and height factor, so no stretching
if INKBAR_TINT:
    _xp_tile = recolor_target(_xp_tile, INK_COLOR, brightest(_xp_tile))   # same colouring as the ink bar

XP_H = _xp_tile.get_height()
xp_strip = pygame.Surface((WIDTH, XP_H), pygame.SRCALPHA)
for _x in range(0, WIDTH, max(1, _xp_tile.get_width())):         # copies, cut off at the screen edge
    xp_strip.blit(_xp_tile, (_x, 0))
xp_strip_dim = xp_strip.copy()
xp_strip_dim.set_alpha(XPBAR_EMPTY_ALPHA)
xp_layer = pygame.Surface((WIDTH, XP_H), pygame.SRCALPHA)
xp_rect = pygame.Rect(0, HEIGHT - XP_H, WIDTH, XP_H)             # flush with the bottom border

xp_font = _intro_font(sc(XPBAR_FONT_SIZE))
xp_text_cache = {}


def xp_text(label):
    if label not in xp_text_cache:
        if len(xp_text_cache) > 60:
            xp_text_cache.clear()
        xp_text_cache[label] = render_outlined(xp_font, label, (255, 255, 255), MENU_TEXT_OUTLINE_COLOR, max(1, sc(2)))
    return xp_text_cache[label]


def draw_xp_bar(dt, alpha):
    """Only the bar (track + fill). The text is drawn separately by draw_xp_text, after everything else."""
    global xp_shown
    xp_shown += (exp_points / exp_needed() - xp_shown) * min(1.0, INKBAR_SMOOTHING * dt)
    filled = round(WIDTH * clamp01(xp_shown))
    xp_layer.fill((0, 0, 0, 0))
    xp_layer.blit(xp_strip_dim, (0, 0))
    if filled > 0:
        xp_layer.blit(xp_strip, (0, 0), area=pygame.Rect(0, 0, filled, XP_H))
    xp_layer.set_alpha(round(255 * alpha))
    screen.blit(xp_layer, xp_rect.topleft)


def draw_xp_text(alpha):
    """"lvN" and "N remaining" side by side in the middle of the bar, always on top of it."""
    level_surf = xp_text(f"lv{level}")
    left_surf = xp_text(f"{exp_needed() - exp_points} {tr('remaining')}")
    gap = sc(XPBAR_TEXT_GAP)
    x = WIDTH // 2 - (level_surf.get_width() + gap + left_surf.get_width()) // 2
    for surf in (level_surf, left_surf):
        surf.set_alpha(round(255 * alpha))
        screen.blit(surf, surf.get_rect(midleft=(x, xp_rect.centery)))
        x += surf.get_width() + gap

spell_label_font = _intro_font(sc(SPELL_LABEL_SIZE))
font = _intro_font(sc(44))
small_font = _intro_font(sc(28))

MAGIC_FORM_COLOR = (150, 205, 255)   # the logo starts out tinted like this, then settles to its real colours
MAGIC_FORM_PARTICLES = 500           # particles that fly in to build the logo


class LogoForm:
    """The page-vanish effect played backwards: particles fly in and the logo
    appears from the top down, then the bright tint fades to normal."""

    LEAD = 0.5   # seconds particles fly before the row they build is revealed

    def __init__(self, logo, topleft, build_time, tint_time):
        self.logo = logo
        self.topleft = topleft
        self.mask = pygame.mask.from_surface(logo, 40)
        self.build_time = build_time
        self.tint_time = tint_time
        self.age = 0.0
        self.cut = 0              # rows above this line are already visible
        self.emitted = 0          # rows that already have particles on the way
        self.owed = 0.0
        self.particles = []

    @property
    def built(self):
        return self.age >= self.build_time

    def update(self, dt):
        self.age += dt
        h = self.logo.get_height()
        self.cut = round(h * ease_in_out(clamp01(self.age / self.build_time)))
        ahead = round(h * ease_in_out(clamp01((self.age + self.LEAD) / self.build_time)))
        if ahead > self.emitted:
            self.emit(self.emitted, ahead)
            self.emitted = ahead
        for p in self.particles:
            p["age"] += dt
        self.particles = [p for p in self.particles if p["age"] < p["life"]]

    def emit(self, top, bottom):
        h = self.logo.get_height()
        self.owed += MAGIC_FORM_PARTICLES * (bottom - top) / h
        n = int(self.owed)
        self.owed -= n
        for _ in range(n):
            for _try in range(8):                          # find a spot where the logo really is
                x = random.randrange(self.logo.get_width())
                y = random.randrange(top, max(top + 1, bottom))
                if y < h and self.mask.get_at((x, y)):
                    break
            else:
                continue
            end = pygame.math.Vector2(self.topleft[0] + x, self.topleft[1] + y)
            start = end + pygame.math.Vector2(random.uniform(-40, 40), -random.uniform(40, 170)) * INTRO_K
            self.particles.append({
                "start": start, "end": end,
                "size": random.uniform(3, 7) * INTRO_K,
                "color": random.choice(MAGIC_COLORS),
                "age": 0.0,
                "life": random.uniform(self.LEAD * 0.8, self.LEAD),
            })

    def draw(self, surface):
        if self.cut > 0:
            ti = clamp01((self.age - self.build_time) / self.tint_time)
            k = 1 - ease_in_out(ti)                       # 1 = bright blue, 0 = normal colours
            if k > 0.01:
                img = self.logo.copy()
                mult = [round(255 + (c - 255) * k) for c in MAGIC_FORM_COLOR]
                img.fill((*mult, 255), special_flags=pygame.BLEND_RGBA_MULT)
                img.fill((round(15 * k), round(15 * k), round(10 * k), 0), special_flags=pygame.BLEND_RGBA_ADD)
            else:
                img = self.logo
            surface.blit(img, self.topleft, area=pygame.Rect(0, 0, img.get_width(), self.cut))
        for p in self.particles:
            k = p["age"] / p["life"]
            pos = p["start"] + (p["end"] - p["start"]) * ease_in_out(k)
            r = max(1, round(p["size"] * (0.4 + 0.6 * k)))   # grow as they arrive
            pygame.draw.circle(surface, p["color"], (round(pos.x), round(pos.y)), r)

def _ease_out(x):
    return 1 - (1 - x) ** 3


def run_logo_intro(logo_file, final_size, text, text_size, text_offset, fallback_text):
    """The logo builds itself out of flying particles, a thin ring ripples out, the text fades in.
    Any key / click skips it. Returns False if the window was closed."""
    fx = MagicEffect(WIDTH, HEIGHT)
    surface = pygame.Surface((WIDTH, HEIGHT))
    wave = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    fade_surf = pygame.Surface((WIDTH, HEIGHT))
    fade_surf.fill((0, 0, 0))
    intro_clock = pygame.time.Clock()

    try:
        original_logo = load(logo_file)
    except (FileNotFoundError, pygame.error):
        original_logo = None

    final_w = final_h = round(final_size * INTRO_K)
    text_font = _intro_font(round(text_size * INTRO_K))
    text_surf = text_font.render(text, True, (255, 255, 255))

    build_time = 0.9         # seconds the logo takes to build itself
    tint_time = 0.45         # seconds the bright tint takes to fade away
    text_delay = 1300        # ms before the text starts to appear
    text_fade = 600          # ms the text takes to appear
    total = 3200             # ms the whole intro lasts
    fade_in, fade_out = 300, 400

    center = (WIDTH // 2, HEIGHT // 2)
    form = None
    if original_logo:
        logo = pygame.transform.smoothscale(original_logo, (final_w, final_h))
        form = LogoForm(logo, logo.get_rect(center=center).topleft, build_time, tint_time)
    fallback = text_font.render(fallback_text, True, (170, 215, 255))

    shock_width = max(2, round(5 * INTRO_K))
    shock_max_radius = 520 * INTRO_K
    shock_speed = 700 * INTRO_K          # px per second
    ring_start = build_time * 1000       # the ring leaves the logo once it is built

    start = last = pygame.time.get_ticks()
    while True:
        now = pygame.time.get_ticks()
        elapsed = now - start
        dt = (now - last) / 1000
        last = now
        if elapsed >= total:
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return True         # skip

        fx.update(dt)
        surface.blit(fx.background, (0, 0))

        # thin ring
        wave.fill((0, 0, 0, 0))
        if elapsed >= ring_start:
            radius = shock_speed * (elapsed - ring_start) / 1000
            if 0 < radius < shock_max_radius:
                a = 255 * (1 - radius / shock_max_radius)
                pygame.draw.circle(wave, (220, 240, 255, round(a)), center, int(radius), shock_width)
                surface.blit(wave, (0, 0))

        # logo
        if form:
            form.update(dt)
            form.draw(surface)
        else:
            fallback.set_alpha(round(255 * clamp01(elapsed / (build_time * 1000))))
            surface.blit(fallback, fallback.get_rect(center=(center[0], center[1] - round(50 * INTRO_K))))

        # text: fades in while rising a little
        if elapsed >= text_delay:
            p = _ease_out(clamp01((elapsed - text_delay) / text_fade))
            ty = HEIGHT // 2 - final_h // 2 + round(text_offset * INTRO_K) + round((1 - p) * 20 * INTRO_K)
            text_surf.set_alpha(round(255 * p))
            surface.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, ty))

        fx.draw(surface)    # sparkles on top of everything

        # fade from / to black
        black = max(1 - elapsed / fade_in, (elapsed - (total - fade_out)) / fade_out, 0.0)
        if black > 0:
            fade_surf.set_alpha(round(255 * min(1.0, black)))
            surface.blit(fade_surf, (0, 0))

        screen.blit(surface, (0, 0))
        pygame.display.flip()
        intro_clock.tick(60)
    return True


def play_intros():
    if not run_logo_intro("coffi.png", 400, "COFFITIME STUDIOS", 36, 430, "COFFITIME STUDIOS"):
        return False
    return run_logo_intro("logo-python.png", 360, "MADE WITH PYTHON", 36, 410, "MADE WITH PYTHON")


# =============================================================================

# =============================================================================
# START MENU
# =============================================================================
MENU_TEXT_OUTLINE_COLOR = (43, 16, 85)   # #2b1055
MENU_TEXT_OUTLINE = 4                    # px thickness of the outline
MENU_BUTTON_HOVER = 1.06     # how much bigger a button sprite gets when the mouse is over it
MENU_FALL_STAGGER = 0.15     # seconds between each piece starting to fall (logo first, then the buttons)
MENU_BUTTONS_LIFT = 40       # px the buttons are moved up (raise it to move them higher)
MENU_LOGO_WIDTH = 0.5       # max logo width as a fraction of the screen width
MENU_LOGO_HEIGHT = 0.65      # max logo height as a fraction of the screen height
MENU_SLIDE_TIME = 1.0        # seconds the cat takes to slide in from the left
MENU_PANEL_SHIFT = 60        # px the menu panel is moved to the left of the right half's centre
MENU_FALL_DELAY = 0.15       # pause after the cat is centred, before the menu drops
MENU_FALL_TIME = 0.9         # seconds the menu takes to fall (it bounces at the end)
MENU_PULSE_TIME = 0.30       # seconds of the size up / size down when the cat is clicked
MENU_PULSE_SIZE = 0.05       # how much bigger the cat gets at the peak (0.05 = 5%)
MENU_EYES_SHUT_TIME = 0.45   # seconds the eyes stay shut after a click
MENU_BLINK_INTERVAL = (2.0, 5.0)   # random seconds between blinks
MENU_BLINK_TIME = 0.15       # seconds one blink lasts
MENU_MAD_CLICKS = 6          # this many clicks on the cat...
MENU_MAD_WINDOW = 2.0        # ...within this many seconds makes it mad
MENU_MAD_TIME = 3.0          # seconds the cat stays mad
MENU_MAD_SHAKE = 4           # px the mad cat trembles
MENU_SLEEP_IDLE = 12.0       # seconds without any input before the cat falls asleep
MENU_ZED_INTERVAL = 0.8      # seconds between "Z" particles while asleep
MENU_ZED_LIFE = (3.2, 4.2)   # seconds a Z lives
MENU_ZED_SPEED = 90          # px/s the Zs float upwards
MENU_ZED_SWAY = 40           # px the Zs swing left and right
MENU_ZED_SWAY_SPEED = 2.4    # how fast they swing (radians per second)
MENU_ZED_SIZE = 40           # base size of a Z
MENU_MAD_OFFSET = 12         # px the mad sprite is shifted to the left (instant, no animation)

LANGUAGE_FILE = os.path.join(BASE_DIR, "language.txt")   # remembers the choice between runs
LANGUAGE = "en"                                          # "en" or "es"
try:
    with open(LANGUAGE_FILE, encoding="utf-8") as _f:
        if _f.read().strip() == "es":
            LANGUAGE = "es"
except OSError:
    pass

# English text -> Spanish text. Anything not listed here is shown as it is.
TEXTS_ES = {
    "START": "JUGAR",
    "CONFIG": "AJUSTES",
    "QUIT GAME": "SALIR",
    "FULLSCREEN": "PANTALLA COMPLETA",
    "LANGUAGE": "IDIOMA",
    "BACK": "VOLVER",
    "Slash Spell": "Hechizo de Tajo",
    "Chain Spell": "Hechizo de Cadenas",
    "Ink Area Spell": "Hechizo de Zona de Tinta",
    "Arrow Spell": "Hechizo de Flecha",
    "Shockwave Spell": "Hechizo de Onda de Choque",
    "remaining": "restantes",
    "Gibberish": "Garabato"
}


def tr(text):
    """The text in the current language."""
    return TEXTS_ES.get(text, text) if LANGUAGE == "es" else text


def toggle_language():
    global LANGUAGE
    LANGUAGE = "es" if LANGUAGE == "en" else "en"
    try:
        with open(LANGUAGE_FILE, "w", encoding="utf-8") as f:
            f.write(LANGUAGE)
    except OSError:
        pass

def run_start_menu():
    """Cat slides in, the menu falls in the right half. Returns "start" or "quit"."""
    menu_clock = pygame.time.Clock()

    def load_full(name):
        img = load(name)
        if img.get_size() != (WIDTH, HEIGHT):
            img = pygame.transform.smoothscale(img, (WIDTH, HEIGHT))
        return img

    try:
        cat_open = load_full("catintro.png")
        cat_shut = load_full("catintroeyesshut.png")
        cat_mask = pygame.mask.from_surface(cat_open, 40)    # only non-transparent pixels count
    except (FileNotFoundError, pygame.error):
        cat_open = cat_shut = cat_mask = None
    try:
        cat_mad = load_full("catintromad.png")
    except (FileNotFoundError, pygame.error):
        cat_mad = cat_open

    title_font = _intro_font(round(22 * INTRO_K))
    button_font = _intro_font(round(24 * INTRO_K))

    panel_cx = round(WIDTH * 0.75) - sc(MENU_PANEL_SHIFT)    # centre line of the logo and the buttons
    btn_w, btn_h = round(WIDTH * 0.24), round(HEIGHT * 0.10)
    btn_gap = round(HEIGHT * 0.04)

    button_imgs = {}

    def load_button_imgs():
        """Loads start_es.png etc. in Spanish and falls back to start.png if there is no Spanish one."""
        button_imgs.clear()
        for _action in ("start", "config", "quit"):
            for _name in (f"{_action}_{LANGUAGE}.png", f"{_action}.png"):
                try:
                    _raw = trim(load(_name))
                    _k = min(btn_h / _raw.get_height(), btn_w / _raw.get_width())
                    button_imgs[_action] = scale_sprite(_raw, _k)
                    break
                except (FileNotFoundError, pygame.error):
                    continue

    load_button_imgs()
    for _action in ("start", "config", "quit", "fullscreen", "back"):
        try:
            _raw = trim(load(f"{_action}.png"))              # trim: transparent margins don't count
            _k = min(btn_h / _raw.get_height(), btn_w / _raw.get_width())
            button_imgs[_action] = scale_sprite(_raw, _k)
        except (FileNotFoundError, pygame.error):
            pass                                             # no sprite: the drawn rectangle is used

    try:
        _logo_raw = load("animagic.png")
        _k = min(WIDTH * MENU_LOGO_WIDTH / _logo_raw.get_width(), HEIGHT * MENU_LOGO_HEIGHT / _logo_raw.get_height())
        logo_img = scale_sprite(_logo_raw, _k)
    except (FileNotFoundError, pygame.error):
        logo_img = title_font.render("ANIMAGIC", True, INK_COLOR)
    logo_top_final = round(HEIGHT * 0.06)
    buttons_top_final = logo_top_final + logo_img.get_height() + round(HEIGHT * 0.04) - sc(MENU_BUTTONS_LIFT)   

    mode = "main"
    t = 0.0
    pulse_t = None                                       # time since the cat was clicked
    blink_wait = random.uniform(*MENU_BLINK_INTERVAL)
    blink_left = 0.0

    click_times = []                                     # recent clicks on the cat (for getting mad)
    mad_left = 0.0                                       # seconds of madness left
    idle_t = 0.0                                         # seconds since the last input
    asleep = False
    zed_timer = 0.0
    zeds = []

    def make_zed(px):
        font_z = _intro_font(px)
        body = font_z.render("Z", True, INK_START_COLOR)
        edge = font_z.render("Z", True, INK_COLOR)
        o = max(2, px // 10)
        surf = pygame.Surface((body.get_width() + 2 * o, body.get_height() + 2 * o), pygame.SRCALPHA)
        for dx, dy in ((-o, 0), (o, 0), (0, -o), (0, o), (-o, -o), (o, o), (-o, o), (o, -o)):
            surf.blit(edge, (o + dx, o + dy))            # dark outline
        surf.blit(body, (o, o))
        return surf

    def spawn_zed():
        px = round(MENU_ZED_SIZE * INTRO_K * random.uniform(0.7, 1.3))
        zeds.append({"surf": make_zed(px), "age": 0.0, "life": random.uniform(*MENU_ZED_LIFE),
                     "phase": random.uniform(0, math.tau),
                     "x0": WIDTH * 0.25 + random.uniform(-10, 10) * INTRO_K,   # centre of the left half
                     "y0": HEIGHT / 2})

    def outlined_text(label):
        """White text with a solid outline."""
        o = sc(MENU_TEXT_OUTLINE)
        body = button_font.render(label, True, (255, 255, 255))
        edge = button_font.render(label, True, MENU_TEXT_OUTLINE_COLOR)
        surf = pygame.Surface((body.get_width() + 2 * o, body.get_height() + 2 * o), pygame.SRCALPHA)
        for dx in range(-o, o + 1):
            for dy in range(-o, o + 1):
                if dx * dx + dy * dy <= o * o + 1:       # a round outline, not a square one
                    surf.blit(edge, (o + dx, o + dy))
        surf.blit(body, (o, o))
        return surf

    text_cache = {}

    def buttons_for(mode_name):
        if mode_name == "main":
            return [(tr("START"), "start"), (tr("CONFIG"), "config"), (tr("QUIT GAME"), "quit")]
        lang_name = "ENGLISH" if LANGUAGE == "en" else "ESPANOL"
        return [(tr("FULLSCREEN"), "fullscreen"),
                (f"{tr('LANGUAGE')} {lang_name}", "language"),
                (tr("BACK"), "back")]
    
    def fall_top(final_top, h, index):
        """Top of a piece that glides down from above the screen and settles smoothly on its final spot."""
        p = clamp01((t - MENU_SLIDE_TIME - MENU_FALL_DELAY - index * MENU_FALL_STAGGER) / MENU_FALL_TIME)
        return round(final_top - (final_top + h) * (1 - _ease_out(p)))

    def button_rects(mode_name):
        rects = []
        for i, (label, action) in enumerate(buttons_for(mode_name)):
            top = fall_top(buttons_top_final + i * (btn_h + btn_gap), btn_h, i + 1)
            if mode_name == "main" and action in button_imgs:
                w = button_imgs[action].get_width()
            elif mode_name == "config":
                if label not in text_cache:
                    text_cache[label] = outlined_text(label)
                w = text_cache[label].get_width()
            else:
                w = btn_w
            rects.append((pygame.Rect(panel_cx - w // 2, top, w, btn_h), label, action))
        return rects

    while True:
        dt_m = min(menu_clock.tick(60) / 1000, MAX_FRAME_TIME)
        t += dt_m

        cat_ready = t >= MENU_SLIDE_TIME
        menu_ready = t >= MENU_SLIDE_TIME + MENU_FALL_DELAY + MENU_FALL_TIME + 3 * MENU_FALL_STAGGER
        rects = button_rects(mode)
        mode_of_rects = mode                                 # the mode these rects (and labels) belong to
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                idle_t = 0.0                             # any input counts as being active
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and mode == "config":
                mode = "main"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_button = False
                if menu_ready:
                    for rect, _label, action in rects:
                        if rect.collidepoint(event.pos):
                            clicked_button = True
                            if action == "start":
                                return "start"
                            elif action == "quit":
                                return "quit"
                            elif action == "config":
                                mode = "config"
                            elif action == "back":
                                mode = "main"
                            elif action == "fullscreen":
                                pygame.display.toggle_fullscreen()
                            elif action == "language":
                                toggle_language()
                                load_button_imgs()
                            break
                # clicking a non-transparent pixel of the cat
                if not clicked_button and cat_ready and cat_mask is not None:
                    x, y = event.pos
                    if 0 <= x < WIDTH and 0 <= y < HEIGHT and cat_mask.get_at((x, y)):
                        if asleep:                       # a click wakes the cat up
                            asleep = False
                            click_times.clear()
                            pulse_t = 0.0
                        elif mad_left <= 0:
                            if pulse_t is None or pulse_t >= MENU_PULSE_TIME:
                                pulse_t = 0.0
                            click_times.append(t)        # too many fast clicks make it mad
                            click_times[:] = [c for c in click_times if t - c <= MENU_MAD_WINDOW]
                            if len(click_times) >= MENU_MAD_CLICKS:
                                mad_left = MENU_MAD_TIME
                                click_times.clear()
                                pulse_t = None

        # --- cat state: click pulse, blinking, mad, sleep ---
        if pulse_t is not None:
            pulse_t += dt_m
            if pulse_t >= MENU_EYES_SHUT_TIME:
                pulse_t = None
        if blink_left > 0:
            blink_left -= dt_m
        else:
            blink_wait -= dt_m
            if blink_wait <= 0:
                blink_left = MENU_BLINK_TIME
                blink_wait = random.uniform(*MENU_BLINK_INTERVAL)
        if mad_left > 0:
            mad_left -= dt_m
            idle_t = 0.0                                 # being mad is not being idle
        idle_t += dt_m
        if not asleep and mad_left <= 0 and menu_ready and idle_t >= MENU_SLEEP_IDLE:
            asleep = True
            zed_timer = 0.0                              # first Z comes right away

        # --- zzz particles ---
        if asleep:
            zed_timer -= dt_m
            if zed_timer <= 0:
                spawn_zed()
                zed_timer = MENU_ZED_INTERVAL
        for z in zeds:
            z["age"] += dt_m
        zeds[:] = [z for z in zeds if z["age"] < z["life"]]

        # --- draw ---
        draw_floor()
        if cat_open is not None:
            offset_x = round(-WIDTH * (1 - _ease_out(clamp01(t / MENU_SLIDE_TIME))))
            if asleep:
                img = cat_shut                           # stays shut until clicked
            elif mad_left > 0:
                img = cat_mad
                offset_x += -sc(MENU_MAD_OFFSET) + round(math.sin(t * 70) * sc(MENU_MAD_SHAKE))
            elif blink_left > 0 or pulse_t is not None:
                img = cat_shut
            else:
                img = cat_open
            if pulse_t is not None and pulse_t < MENU_PULSE_TIME:
                k = 1 + MENU_PULSE_SIZE * math.sin(math.pi * pulse_t / MENU_PULSE_TIME)
                img = pygame.transform.smoothscale(img, (round(WIDTH * k), round(HEIGHT * k)))
            screen.blit(img, img.get_rect(center=(WIDTH // 2 + offset_x, HEIGHT // 2)))

        for z in zeds:
            age, life = z["age"], z["life"]
            sway = MENU_ZED_SWAY * INTRO_K * (0.4 + 0.6 * min(1.0, age))      # swings wider as it rises
            wave = age * MENU_ZED_SWAY_SPEED + z["phase"]
            x = z["x0"] + math.sin(wave) * sway                                # zigzag like a leaf, but going up
            y = z["y0"] - MENU_ZED_SPEED * INTRO_K * age
            alpha = clamp01(age / 0.4) * clamp01((life - age) / (life * 0.4))  # fades in, then out
            tilt = math.cos(wave) * 20                                         # leans into the swing
            zimg = pygame.transform.rotozoom(z["surf"], tilt, 0.6 + 0.6 * age / life)
            zimg.set_alpha(round(255 * alpha))
            screen.blit(zimg, zimg.get_rect(center=(round(x), round(y))))

        logo_top = fall_top(logo_top_final, logo_img.get_height(), 0)
        screen.blit(logo_img, logo_img.get_rect(midtop=(panel_cx, logo_top)))
        for rect, label, action in rects:
            hover = menu_ready and rect.collidepoint(mouse)
            if mode_of_rects == "config":
                if label not in text_cache:
                    text_cache[label] = outlined_text(label)
                img = text_cache[label]                      # plain outlined text, no background
            else:
                img = button_imgs.get(action)
            if img is not None:
                if hover:
                    img = pygame.transform.smoothscale(
                        img, (round(img.get_width() * MENU_BUTTON_HOVER), round(img.get_height() * MENU_BUTTON_HOVER)))
                screen.blit(img, img.get_rect(center=rect.center))
            else:
                pygame.draw.rect(screen, INK_START_COLOR if hover else INK_COLOR, rect, border_radius=sc(14))
                text = button_font.render(label, True, (255, 255, 255))
                screen.blit(text, text.get_rect(center=rect.center))

        pygame.display.flip()

if "--menu" not in sys.argv and not play_intros():
    pygame.quit()
    raise SystemExit

if run_start_menu() == "quit":
    pygame.quit()
    raise SystemExit

# =============================================================================
# WAVES AND THE TIMER
# =============================================================================
wave = 0
wave_left = 0.0                 # 0 at the start, so wave 1 spawns on the first frame
game_time = 0.0                 # total seconds survived

_WAVE_REACH = max(Slime(pygame.math.Vector2()).reach, Statue(pygame.math.Vector2()).reach)


def spawn_wave():
    """Spawns this wave's enemies just outside the screen, each one with a puff."""
    global target_index
    slimes = min(WAVE_SLIMES_BASE + (wave - 1) * WAVE_SLIMES_STEP, WAVE_SLIMES_MAX)
    statues = 0
    if wave > WAVE_STATUES_AFTER:
        statues = (wave - WAVE_STATUES_AFTER - 1) // WAVE_STATUE_STEP + 1

    for kind in [Slime] * slimes + [Statue] * statues:
        if len(enemies) >= WAVE_MAX_ALIVE:
            break
        e = kind(pygame.math.Vector2())
        m = e.radius + sc(WAVE_SPAWN_MARGIN)
        for _try in range(100):
            side = random.randrange(4)                       # 0 top, 1 bottom, 2 left, 3 right
            if side < 2:
                x = random.uniform(cam.x - m, cam.x + WIDTH + m)
                y = cam.y - m if side == 0 else cam.y + HEIGHT + m
            else:
                y = random.uniform(cam.y - m, cam.y + HEIGHT + m)
                x = cam.x - m if side == 2 else cam.x + WIDTH + m
            pos = pygame.math.Vector2(x, y)
            if all(pos.distance_to(o.pos) >= e.radius + o.radius for o in enemies):
                break
        e.pos.update(pos)
        e.spawn_t = WAVE_SPAWN_DELAY                         # hidden, no collisions, can't be hurt
        e.collidable = False
        e.invulnerable = True
        spawn_puff((pos.x, pos.y + e.radius))
        enemies.append(e)
    if target_index is None and enemies:
        target_index = pick_target(None)


def update_waves(dt):
    global wave, wave_left, game_time
    game_time += dt
    wave_left -= dt
    if wave_left <= 0:
        wave += 1
        wave_left += WAVE_TIME                               # keeps the rhythm exact, no drift
        spawn_wave()


# --- Timer: digits drawn one by one, the two dots of the colon are drawn by hand ---
timer_font = _intro_font(sc(WAVE_TIMER_FONT_SIZE))
timer_digits = [render_outlined(timer_font, str(d), (255, 255, 255), MENU_TEXT_OUTLINE_COLOR, max(1, sc(3)))
                for d in range(10)]
TIMER_CELL_W = max(d.get_width() for d in timer_digits)      # same width for every digit, so nothing jitters
TIMER_H = max(d.get_height() for d in timer_digits)
TIMER_DOT_R = max(2, sc(4))
TIMER_DOT_OUT = max(1, sc(2))
TIMER_DOTS_W = TIMER_DOT_R * 2 + TIMER_DOT_OUT * 2 + sc(10)
TIMER_W = TIMER_CELL_W * 4 + TIMER_DOTS_W


def draw_wave_timer():
    """MM:SS under the hearts."""
    seconds = math.ceil(wave_left) if WAVE_SHOW_COUNTDOWN else int(game_time)
    seconds = max(0, seconds)
    minutes, secs = min(99, seconds // 60), seconds % 60
    digits = [minutes // 10, minutes % 10, secs // 10, secs % 10]

    left = hearts_rect.centerx - TIMER_W // 2
    top = hearts_rect.bottom + sc(WAVE_TIMER_GAP) + SHIELD_ROW_H
    x = left
    for i, d in enumerate(digits):
        if i == 2:                                           # the two dots between minutes and seconds
            cx = x + TIMER_DOTS_W // 2
            for cy in (top + round(TIMER_H * 0.38), top + round(TIMER_H * 0.68)):
                pygame.draw.circle(screen, MENU_TEXT_OUTLINE_COLOR, (cx, cy), TIMER_DOT_R + TIMER_DOT_OUT)
                pygame.draw.circle(screen, (255, 255, 255), (cx, cy), TIMER_DOT_R)
            x += TIMER_DOTS_W
        img = timer_digits[d]
        screen.blit(img, img.get_rect(midtop=(x + TIMER_CELL_W // 2, top)))
        x += TIMER_CELL_W

# =============================================================================
# TUTORIAL + COUNTDOWN   (paste right ABOVE the line:  dt = 1 / FPS)
# =============================================================================
SHOW_TUTORIAL = True           # False = no tutorial
SHOW_STATUE_TUTORIAL = True    # False = no tutorial when the first statue appears
COUNTDOWN_SECONDS = 3          # countdown before the run starts (0 = none)
TUTORIAL_DARKNESS = 190        # 0-255, how dark the screen gets behind the tutorial
TUTORIAL_PANEL_COLOR = (24, 16, 48)

TEXTS_ES.update({
    "NEXT": "SIGUIENTE", "SKIP": "SALTAR", "FINISH": "TERMINAR",
    "NEW WAVE": "NUEVA OLEADA", "GET READY": "PREPARATE",
})

TUT_TITLE_FONT = _intro_font(sc(38))
TUT_BODY_FONT = _intro_font(sc(26))
TUT_BTN_FONT = _intro_font(sc(28))
TUT_KEY_FONT = _intro_font(sc(26))

_tut_texts = {}
_tut_cache = {}


def tut_lang(d):
    return d["es"] if LANGUAGE == "es" else d["en"]


def tut_text(label, fnt, colour=(255, 255, 255), o=None):
    o = max(1, sc(3)) if o is None else o
    key = (label, id(fnt), colour, o)
    if key not in _tut_texts:
        _tut_texts[key] = render_outlined(fnt, label, colour, MENU_TEXT_OUTLINE_COLOR, o)
    return _tut_texts[key]


def tut_wrap(fnt, text, max_w):
    lines, cur = [], ""
    for word in text.split():
        test = f"{cur} {word}".strip()
        if cur and fnt.size(test)[0] > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines

def tut_fit(surf, max_w):
    """Shrinks a text picture (keeping its proportions) if it is wider than max_w."""
    if surf.get_width() <= max_w:
        return surf
    k = max_w / surf.get_width()
    return pygame.transform.smoothscale(surf, (max(1, round(surf.get_width() * k)), max(1, round(surf.get_height() * k))))

# --- small drawing helpers (scenes draw straight onto the screen, inside a clip) ---
def tut_ground(r):
    return r.y + round(r.h * 0.78)


def tut_floor(r, ox=0, oy=0):
    ox, oy = int(ox), int(oy)
    for cy in range(oy // CHUNK_H, (oy + r.h) // CHUNK_H + 1):
        for cx in range(ox // CHUNK_W, (ox + r.w) // CHUNK_W + 1):
            screen.blit(floor_chunk(cx, cy), (r.x + cx * CHUNK_W - ox, r.y + cy * CHUNK_H - oy))


def tut_shadow_oval(cx, cy, w, h, alpha=None):
    surf = pygame.Surface((max(2, w), max(2, h)), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (*SHADOW_COLOR, SHADOW_ALPHA if alpha is None else alpha), surf.get_rect())
    screen.blit(surf, (round(cx) - surf.get_width() // 2, round(cy) - surf.get_height() // 2))


def tut_ground_shadow(x, feet, r, k=1.0, alpha=None):
    """Same shape and position as Enemy.draw_shadow."""
    base_h = max(6, round(r * 0.6))
    cy = feet - r + round(r * 0.65) + base_h // 2
    tut_shadow_oval(x, cy, round(r * 2 * k), round(base_h * k), alpha)


def tut_cat(x, feet, left=False, walking=False, t=0.0, visible=True):
    shadow_h = max(14, round(PLAYER_RADIUS * 0.6))
    tut_shadow_oval(x, feet, PLAYER_RADIUS * 2, shadow_h)
    if not visible:
        return
    img = cat_walk_img if (walking and int(t / WALK_FRAME_TIME) % 2 == 0) else cat_idle_img
    if (not left) != CAT_FACES_RIGHT:
        img = pygame.transform.flip(img, True, False)
    screen.blit(img, img.get_rect(midbottom=(round(x), round(feet))))


def tut_slime(x, feet, scale=1.0, squash=0.0, charging=False, shake=0.0, flash=False):
    r = max(1, round(SLIME_RADIUS * scale))
    tut_ground_shadow(x, feet, r, SLIME_SHADOW_SCALE)
    base, charge = slime_sprites(scale)
    if base is None:
        pygame.draw.circle(screen, (125, 130, 145), (round(x), round(feet - r)), r)
        return
    img = squashed(charge if charging else base, squash)
    if flash:
        img = flashed(img)
    screen.blit(img, img.get_rect(midbottom=(round(x + shake), round(feet))))


def tut_statue(x, feet, off=0.0, squash=0.0, blend=0.0, shake=(0.0, 0.0)):
    if statue_img is None:
        pygame.draw.circle(screen, (125, 130, 145), (round(x + shake[0]), round(feet + off - STATUE_RADIUS)), STATUE_RADIUS)
        return
    pos = (round(x + shake[0]), round(feet + off + shake[1]))
    img = squashed(statue_img, squash)
    screen.blit(img, img.get_rect(midbottom=pos))
    if blend > 0:
        statue_charging_img.set_alpha(round(255 * blend))
        screen.blit(statue_charging_img, statue_charging_img.get_rect(midbottom=pos))
        statue_charging_img.set_alpha(255)


def tut_charge_pose(c, total):
    """(squash, use charging sprite, shake) for a slime that has been charging for c seconds."""
    if c < SLIME_SQUASH_TIME:
        return ease_in_out(c / SLIME_SQUASH_TIME), False, 0.0
    held = clamp01((c - SLIME_SQUASH_TIME) / max(1e-6, total - SLIME_SQUASH_TIME))
    return SLIME_HOLD_SQUASH, True, math.sin(c * 55) * SLIME_CHARGE_SHAKE * held


def tut_puff(x, y, age, life=0.5):
    if not (0 <= age < life):
        return
    k = age / life
    for i in range(PUFF_COUNT):
        a = math.tau * i / PUFF_COUNT + 0.4
        d = sc(70) * (1 - (1 - k) ** 2)
        rad = max(1, round(sc(8 + (i % 3) * 2) * (1 + k)))
        surf = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*PUFF_COLOR, round(200 * (1 - k))), (rad, rad), rad)
        screen.blit(surf, (round(x + math.cos(a) * d) - rad, round(y + math.sin(a) * d) - rad))


def tut_popup(label, x, y, age, life=0.9, colour=(210, 45, 45)):
    if 0 <= age < life:
        s = font.render(label, True, colour)
        s.set_alpha(round(255 * (1 - age / life)))
        screen.blit(s, s.get_rect(center=(round(x), round(y - sc(70) * age))))


def tut_key(label, centre, pressed=False, size=None):
    s = size or sc(50)
    depth = sc(5)
    rect = pygame.Rect(0, 0, s, s)
    rect.center = centre
    base = rect.move(0, depth)
    pygame.draw.rect(screen, (60, 60, 90), base, border_radius=sc(9))
    top = base if pressed else rect
    pygame.draw.rect(screen, INK_START_COLOR if pressed else (225, 230, 245), top, border_radius=sc(9))
    pygame.draw.rect(screen, INK_COLOR, top, max(2, sc(3)), border_radius=sc(9))
    txt = TUT_KEY_FONT.render(label, True, INK_COLOR)
    screen.blit(txt, txt.get_rect(center=top.center))


def tut_wasd(cx, cy, down):
    s, g = sc(50), sc(6)
    for label, (col, row) in (("W", (0, -1)), ("A", (-1, 0)), ("S", (0, 0)), ("D", (1, 0))):
        tut_key(label, (cx + col * (s + g), cy + row * (s + g)), pressed=label in down)


def tut_mouse(centre, left_down):
    w, h = sc(44), sc(66)
    rect = pygame.Rect(0, 0, w, h)
    rect.center = centre
    pygame.draw.rect(screen, (225, 230, 245), rect, border_radius=w // 2)
    if left_down:
        pygame.draw.rect(screen, INK_START_COLOR, pygame.Rect(rect.left, rect.top, w // 2, h // 2),
                         border_top_left_radius=w // 2)
    pygame.draw.rect(screen, INK_COLOR, rect, max(2, sc(3)), border_radius=w // 2)
    pygame.draw.line(screen, INK_COLOR, (rect.centerx, rect.top), (rect.centerx, rect.top + h // 2), max(2, sc(2)))
    pygame.draw.line(screen, INK_COLOR, (rect.left, rect.top + h // 2), (rect.right, rect.top + h // 2), max(2, sc(2)))


def tut_cursor(x, y):
    pts = [(x + px * UI_SCALE, y + py * UI_SCALE)
           for px, py in ((0, 0), (0, 22), (6, 17), (11, 28), (16, 26), (11, 15), (18, 15))]
    pygame.draw.polygon(screen, (255, 255, 255), pts)
    pygame.draw.polygon(screen, (20, 20, 30), pts, max(1, sc(2)))


def tut_target_ring(cx, cy, t, pop=1.0):
    pulse = 1 + math.sin(t * TARGET_BOB_SPEED) * TARGET_BOB_FRACTION
    scale = 2 * (SLIME_RADIUS + TARGET_RING_GAP) * pulse * pop / max(target_img.get_size())
    if scale <= 0.01:
        return
    img = pygame.transform.rotozoom(target_img, -(t * TARGET_SPIN_SPEED) % 360, scale)
    screen.blit(img, img.get_rect(center=(round(cx), round(cy))))


def tut_hearts_row(r, stages):
    n = len(stages)
    x = r.centerx - (n * _heart_w + (n - 1) * HEART_GAP) // 2
    y = r.y + sc(18)
    for i, st in enumerate(stages):
        img = heart_imgs[st]
        screen.blit(img, img.get_rect(center=(x + i * (_heart_w + HEART_GAP) + _heart_w // 2, y + _heart_h // 2)))


def tut_timer(cx, top, seconds):
    minutes, secs = min(99, seconds // 60), seconds % 60
    x = cx - TIMER_W // 2
    for i, d in enumerate([minutes // 10, minutes % 10, secs // 10, secs % 10]):
        if i == 2:
            dx = x + TIMER_DOTS_W // 2
            for dy in (top + round(TIMER_H * 0.38), top + round(TIMER_H * 0.68)):
                pygame.draw.circle(screen, MENU_TEXT_OUTLINE_COLOR, (dx, dy), TIMER_DOT_R + TIMER_DOT_OUT)
                pygame.draw.circle(screen, (255, 255, 255), (dx, dy), TIMER_DOT_R)
            x += TIMER_DOTS_W
        img = timer_digits[d]
        screen.blit(img, img.get_rect(midtop=(x + TIMER_CELL_W // 2, top)))
        x += TIMER_CELL_W


def tut_xp_bar(r, fill, remaining):
    y = r.bottom - XP_H
    screen.blit(xp_strip_dim, (r.x, y), area=pygame.Rect(0, 0, r.w, XP_H))
    f = round(r.w * clamp01(fill))
    if f > 0:
        screen.blit(xp_strip, (r.x, y), area=pygame.Rect(0, 0, f, XP_H))
    a, b = xp_text("lv1"), xp_text(f"{remaining} {tr('remaining')}")
    gap = sc(XPBAR_TEXT_GAP)
    x = r.centerx - (a.get_width() + gap + b.get_width()) // 2
    for s in (a, b):
        screen.blit(s, s.get_rect(midleft=(x, y + XP_H // 2)))
        x += s.get_width() + gap


def tut_button(rect, label, hover, fnt=None):
    pygame.draw.rect(screen, INK_START_COLOR if hover else INK_COLOR, rect, border_radius=sc(14))
    pygame.draw.rect(screen, MENU_TEXT_OUTLINE_COLOR, rect, max(2, sc(3)), border_radius=sc(14))
    s = tut_fit(tut_text(label, fnt or TUT_BTN_FONT, o=max(1, sc(2))), rect.width - sc(20))
    screen.blit(s, s.get_rect(center=rect.center))

# =============================================================================
# SPELL CHOICE SCREEN
# =============================================================================
# Optional icon files in the assets folder (if one is missing, a sprite already used in the game stands in for it)
SPELL_ICON_FILES = {
    "Slash Spell": "slashspell.png",
    "Chain Spell": "chainspell.png",
    "Ink Area Spell": "inkareaspell.png",
    "Arrow Spell": "arrowspell.png",
    "Shockwave Spell": "shockwavespell.png",
    "Lightning Step": "speedspell.png",     # optional: a fallback bolt is drawn if the file is missing
    "Shield Spell": "shieldspell.png",
}
SPELL_FORMAT = dict(slash=SLASH_DAMAGE, chain=CHAIN_TIME, area=INK_AREA_TIME,
                    arrow_hit=ARROW_HIT_DAMAGE, pierce=ARROW_PIERCE_DAMAGE, wave=SHOCKWAVE_DAMAGE,
                    light=LIGHTNING_TIME, shield=SHIELD_HEARTS)
SPELL_INFO = {
    "Slash Spell": {
        "en": "Deals {slash:g} damage to your target. Draw a diagonal line, then a semicircle from its tip back to its middle.",
        "es": "Hace {slash:g} de dano al objetivo. Dibuja una linea diagonal y luego un semicirculo desde su punta hasta su centro."},
    "Chain Spell": {
        "en": "Locks your target in chains for {chain:g} seconds so it cannot move. Draw a long diagonal S.",
        "es": "Encadena al objetivo durante {chain:g} segundos y no podra moverse. Dibuja una S diagonal larga."},
    "Ink Area Spell": {
        "en": "Leaves a zone on the floor that slows enemies for {area:g} seconds. Draw a spiral.",
        "es": "Deja una zona en el suelo que ralentiza a los enemigos durante {area:g} segundos. Dibuja una espiral."},
    "Arrow Spell": {
        "en": "Fires an arrow at your target for {arrow_hit:g} damage. It also pierces enemies on the way for {pierce:g} damage. Draw a 4, a stick with an angular head.",
        "es": "Lanza una flecha al objetivo que hace {arrow_hit:g} de dano. Tambien atraviesa a los enemigos del camino y les hace {pierce:g} de dano. Dibuja un 4, un palo con una cabeza angular."},
    "Shockwave Spell": {
        "en": "Blasts every enemy around you for {wave:g} damage. Draw an upside down V, like a roof.",
        "es": "Golpea a todos los enemigos a tu alrededor y les hace {wave:g} de dano. Dibuja una V invertida, como un techo."},
    "Lightning Step": {
        "en": "Makes you much faster for {light:g} seconds. It cannot be stacked. Draw a lightning bolt: a bar, a diagonal, another bar and a diagonal, no tilt and no mirror.",
        "es": "Te hace mucho mas rapido durante {light:g} segundos. No se puede acumular. Dibuja una barra, una diagonal, otra barra y otra diagonal, sin inclinar y sin espejo."},
    "Shield Spell": {
        "en": "Gives you {shield:g} extra hearts under your health bar. Each one absorbs a hit and then disappears. Draw a U.",
        "es": "Te da {shield:g} corazones extra bajo tu barra de vida. Cada uno absorbe un golpe y luego desaparece. Dibuja una U."},
}
TEXTS_ES.update({
    "Unknown Spell": "Hechizo desconocido",
    "Lightning Step": "Paso Relampago",
    "CHOOSE YOUR FIRST SPELL": "ELIGE TU PRIMER HECHIZO",
    "CHOOSE YOUR SECOND SPELL": "ELIGE TU SEGUNDO HECHIZO",
    "LEVEL UP, CHOOSE A SPELL": "SUBISTE DE NIVEL, ELIGE UN HECHIZO",
    "NEW SPELLS": "NUEVOS HECHIZOS",
    "Shield Spell": "Hechizo de Escudo",
})

_spell_icon_cache = {}


def _spell_icon_source(name):
    f = SPELL_ICON_FILES.get(name)
    if f:
        try:
            return trim(load(f))
        except (FileNotFoundError, pygame.error):
            pass
    if name == SLASH_SPELL[0] and slash_base is not None:
        return pygame.transform.rotozoom(slash_base, 35, 1)
    if name == ARROW_SPELL[0]:
        return arrow_img
    if name == CHAIN_SPELL[0]:
        return chain_img
    if name == INK_AREA_SPELL[0] and ink_ring_img is not None:
        return ink_ring_img
    if name == SHOCKWAVE_SPELL[0]:
        if ink_ring_img is None:
            return shockwave_fill_img
        out = pygame.Surface(ink_ring_img.get_size(), pygame.SRCALPHA)
        out.blit(pygame.transform.smoothscale(shockwave_fill_img, out.get_size()), (0, 0))
        out.blit(ink_ring_img, (0, 0))
        return out
    surf = pygame.Surface((100, 100), pygame.SRCALPHA)       # last resort: a circle with the first letter
    pygame.draw.circle(surf, INK_START_COLOR, (50, 50), 48)
    pygame.draw.circle(surf, INK_COLOR, (50, 50), 48, 5)
    letter = TUT_TITLE_FONT.render(name[0], True, (255, 255, 255))
    surf.blit(letter, letter.get_rect(center=(50, 50)))
    return surf


def spell_icon(name, max_w, max_h):
    key = (name, max_w, max_h)
    if key not in _spell_icon_cache:
        src = _spell_icon_source(name)
        k = min(max_w / src.get_width(), max_h / src.get_height(), 3.0)
        _spell_icon_cache[key] = scale_sprite(src, k)
    return _spell_icon_cache[key]

# =============================================================================
# THE FAKE GAMEPLAY SCENES.  Each one gets (t, r): t = seconds into the loop, r = its rectangle.
# =============================================================================
def tut_scene_move(t, r):
    u = (t % 6.0) / 3.0
    p = ease_in_out(u if u < 1 else 2 - u)
    right = u < 1
    moving = 0.04 < p < 0.96
    tut_floor(r, p * r.w * 0.5, 0)
    tut_cat(r.centerx, tut_ground(r), left=not right, walking=moving, t=t)
    tut_wasd(r.x + sc(110), r.y + sc(95), ({"D"} if right else {"A"}) if moving else set())


def tut_scene_slimes(t, r):
    tut_floor(r)
    fy = tut_ground(r)
    tut_cat(r.x + r.w * 0.82, fy, left=True)
    x0, D = r.x + r.w * 0.16, r.w * 0.40
    xs = x0 + D
    if t < 4.4:
        x, squash, charging, shake = x0, 0.0, False, 0.0
        if 1.0 <= t < 2.0:
            squash, charging, shake = tut_charge_pose(t - 1.0, 1.0)
        elif 2.0 <= t < 2.3:
            squash = SLIME_HOLD_SQUASH * (1 - ease_out_back(min(1.0, (t - 2.0) / SLIME_SPRING_TIME)))
            x = x0 + D * 0.5 * math.sin(math.pi / 2 * (t - 2.0) / 0.3)
        elif t >= 2.3:
            q = clamp01((t - 2.3) / 1.1)
            x = x0 + D * (0.5 + 0.5 * (1 - (1 - q) ** 3))
        tut_slime(x, fy, squash=squash, charging=charging, shake=shake, flash=t >= 4.25)
    else:
        tau = t - 4.4
        tut_puff(xs, fy - SLIME_RADIUS, tau)
        for sgn in (-1, 1):
            tut_slime(xs + sgn * sc(150) * (1 - math.exp(-3.5 * tau)), fy, scale=SLIME_SPLIT_SIZE)
    tut_popup("5", xs, fy - SLIME_RADIUS * 2, t - 4.25)

def tut_scene_health(t, r):
    tut_floor(r)
    fy = tut_ground(r)
    th = 1.8
    cat0 = r.x + r.w * 0.60
    contact = cat0 - (PLAYER_RADIUS + SLIME_RADIUS) * 0.9
    x0 = r.x + r.w * 0.14
    x, squash, charging, shake = x0, 0.0, False, 0.0
    if 0.8 <= t < 1.5:
        squash, charging, shake = tut_charge_pose(t - 0.8, 0.7)
    elif 1.5 <= t < th:
        squash = SLIME_HOLD_SQUASH * (1 - ease_out_back(min(1.0, (t - 1.5) / SLIME_SPRING_TIME)))
        x = x0 + (contact - x0) * math.sin(math.pi / 2 * (t - 1.5) / (th - 1.5))
    elif t >= th:
        x = contact - sc(80) * (1 - (1 - clamp01((t - th) / 0.6)) ** 3)
    tut_slime(x, fy, squash=squash, charging=charging, shake=shake)
    kb = sc(60) * _ease_out(clamp01((t - th) / 0.4)) if t >= th else 0.0
    left_inv = th + PLAYER_INVULN_TIME - t
    visible = not (t >= th and left_inv > 0 and int(left_inv * 14) % 2 == 0)
    tut_cat(cat0 + kb, fy, left=True, visible=visible)
    tut_popup("1", cat0 + kb, fy - CAT_HEIGHT, t - th)
    tut_hearts_row(r, [2, 2, 2, 2, 2, 2 if t < th else 1])


def tut_ink_assets():
    if not _tut_cache:
        rects = area_mask.get_bounding_rects()
        _tut_cache["box"] = rects[0].unionall(rects[1:]) if rects else pygame.Rect(0, 0, *nb_size)
        _tut_cache["stencil"] = area_mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(255, 255, 255, 0))
        _tut_cache["outline"] = pygame.Surface(nb_size, pygame.SRCALPHA)
        _tut_cache["colour"] = pygame.Surface(nb_size, pygame.SRCALPHA)
        _tut_cache["bar"] = pygame.Surface(holder_img.get_size(), pygame.SRCALPHA)
    return _tut_cache


def tut_stroke_pt(box, s):
    """A neutral wavy line across the page (just to show how drawing works)."""
    return (box.x + box.w * (0.10 + 0.80 * s),
            box.centery + box.h * 0.28 * math.sin(s * math.tau * 2.0 + 0.6))


def tut_scene_ink(t, r):
    tut_floor(r)
    A = tut_ink_assets()
    nb_w, nb_h = nb_size
    hw, hh = holder_img.get_size()
    total_w = nb_w + INKBAR_GAP + hw
    nx = r.x + sc(110) + max(0, (r.w - sc(110) - total_w - sc(110)) // 2)
    ny = r.centery - nb_h // 2
    draw_t = clamp01((t - 0.5) / 2.8)
    ink_v = 1 - 0.55 * draw_t if t < 4.0 else 0.45 + 0.55 * ease_in_out(clamp01((t - 4.0) / 1.0))

    outline, colour = A["outline"], A["colour"]
    outline.fill((0, 0, 0, 0))
    colour.fill((0, 0, 0, 0))
    tip = tut_stroke_pt(A["box"], 0.0)
    if t >= 0.5:
        N = 220
        for i in range(int(draw_t * N) + 1):
            tip = tut_stroke_pt(A["box"], i / N)
            stamp(outline_img, outline, tip)
            stamp(colour_img, colour, tip)
        for lay in (outline, colour):
            lay.blit(A["stencil"], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    screen.blit(notebook_img, (nx, ny))
    screen.blit(outline, (nx, ny))
    screen.blit(colour, (nx, ny))
    if t >= 0.5:
        screen.blit(glow_img, glow_img.get_rect(center=(round(nx + tip[0]), round(ny + tip[1]))))
    if 0.2 <= t < 3.6:
        tut_cursor(nx + tip[0], ny + tip[1])
    tut_mouse((nx - sc(55), r.centery), 0.5 <= t < 3.3)

    bl = A["bar"]
    bl.fill((0, 0, 0, 0))
    bl.blit(bar_img, (bar_area.x, bar_area.y + round((1 - ink_v) * bar_area.height)))
    bl.blit(bar_stencil, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    bl.blit(holder_img, (0, 0))
    hx = nx + nb_w + INKBAR_GAP
    screen.blit(bl, (hx, ny))
    tut_key("R", (hx + hw + sc(60), r.centery), pressed=4.0 <= t < 4.5)


def tut_scene_target(t, r):
    tut_floor(r)
    tut_cat(r.x + r.w * 0.12, r.y + round(r.h * 0.80), left=False)
    spots = [(0.38, 0.46), (0.62, 0.80), (0.86, 0.52)]
    cur, ph = int(t / 1.5) % 3, t % 1.5
    for i in sorted(range(3), key=lambda i: spots[i][1]):
        x, feet = r.x + r.w * spots[i][0], r.y + round(r.h * spots[i][1])
        if i == cur:
            tut_target_ring(x, feet - SLIME_RADIUS + SLIME_TARGET_OFFSET, t, ease_out_back(clamp01(ph / 0.25)))
        tut_slime(x, feet)
    tut_key("Q", (r.x + sc(60), r.y + sc(60)), pressed=(t >= 1.5 and ph < 0.2))


def tut_scene_exp(t, r):
    tut_floor(r)
    fy = r.y + round(r.h * 0.66)
    cat_x, sx = r.x + r.w * 0.28, r.x + r.w * 0.58
    tut_cat(cat_x, fy, left=False)
    if t < 1.0:
        tut_slime(sx, fy, flash=t >= 0.7)
    else:
        tut_puff(sx, fy - SLIME_RADIUS, t - 1.0)
    tut_popup("5", sx, fy - SLIME_RADIUS * 2, t - 0.7)

    fill, remaining = 2 / EXP_BASE_NEEDED, EXP_BASE_NEEDED - 2
    age = t - 1.0
    if age >= 0:
        o0 = pygame.math.Vector2(sx, fy)
        start = o0 + pygame.math.Vector2(-sc(90), sc(12)) * (1 - math.exp(-5 * min(age, 0.8)))
        q = clamp01((age - 0.8) / 0.7)
        if q < 1:                                      # tossed out, bobs, then gets pulled to the cat
            pos = start.lerp(pygame.math.Vector2(cat_x, fy), q * q)
            k = (math.sin(age * EXP_BOB_SPEED) + 1) / 2
            w = max(4, round(exp_img.get_width() * (0.9 - 0.3 * k)))
            tut_shadow_oval(pos.x, pos.y, w, max(3, w // 3))
            screen.blit(exp_img, exp_img.get_rect(midbottom=(round(pos.x), round(pos.y - EXP_HOVER - EXP_BOB_HEIGHT * k))))
        fill = (2 + ease_in_out(clamp01((age - 1.5) / 0.4))) / EXP_BASE_NEEDED
        if age >= 1.5:
            remaining -= 1
    if t >= 5.0:                                       # a new wave arrives
        tut_puff(r.x + r.w * 0.88, fy - SLIME_RADIUS, t - 5.0)
    if t >= 5.3:
        tut_slime(r.x + r.w * 0.88, fy)
    if 5.0 <= t < 7.5:
        s = tut_fit(tut_text(tr("NEW WAVE"), TUT_BODY_FONT), r.w - sc(20))
        s.set_alpha(round(255 * clamp01(min((t - 5.0) / 0.3, (7.5 - t) / 0.5))))
        screen.blit(s, s.get_rect(center=(r.centerx, r.y + sc(70))))
    tut_timer(r.right - TIMER_W // 2 - sc(30), r.y + sc(20), 15 + int(t))
    tut_xp_bar(r, fill, remaining)

def tut_scene_choice(t, r):
    tut_floor(r)
    opts = ["Slash Spell", "Arrow Spell", "Chain Spell"]
    gap = sc(14)
    cw = (r.w - 4 * gap) // 3
    ch = round(r.h * 0.62)
    top = r.y + sc(16)
    cur = int(t / 1.5) % 3
    pygame.draw.rect(screen, TUTORIAL_PANEL_COLOR, pygame.Rect(r.x + sc(6), r.y + sc(6), r.w - sc(12), r.h - sc(12)),
                     border_radius=sc(16))
    for i, o in enumerate(opts):
        rect = pygame.Rect(r.x + gap + i * (cw + gap), top, cw, ch)
        hover = i == cur
        pygame.draw.rect(screen, (46, 34, 92) if hover else (32, 24, 64), rect, border_radius=sc(12))
        pygame.draw.rect(screen, INK_START_COLOR if hover else (90, 85, 130), rect, sc(3), border_radius=sc(12))
        icon = spell_icon(o, cw - sc(20), round(ch * 0.5))
        screen.blit(icon, icon.get_rect(center=(rect.centerx, rect.top + sc(12) + round(ch * 0.25))))
        name = tut_fit(tut_text(tr(o), TUT_KEY_FONT, o=max(1, sc(2))), cw - sc(10))
        screen.blit(name, name.get_rect(midbottom=(rect.centerx, rect.bottom - sc(10))))
        if hover:
            tut_cursor(rect.centerx + sc(20), rect.centery + sc(20))
    skip_r = pygame.Rect(0, 0, sc(300), sc(44))
    skip_r.midbottom = (r.centerx, r.bottom - sc(14))
    tut_button(skip_r, f"{tr('SKIP')}, 1 EXP", False, TUT_KEY_FONT)


# =============================================================================
# THE SLIDES  (text in English + Spanish; no accents/n-tilde because the font may not have them)
# =============================================================================
SLIDES = [
    {"title": {"en": "MOVE", "es": "MOVERSE"}, "period": 6.0, "scene": tut_scene_move,
     "text": {"en": "Use WASD or the arrow keys to move your cat. You speed up gradually and slide a little when you let go, so plan your steps.",
              "es": "Usa WASD o las flechas para mover al gato. Aceleras poco a poco y te deslizas un poco al soltar, asi que planea tus pasos."}},
    {"title": {"en": "SLIMES", "es": "SLIMES"}, "period": 9.0, "scene": tut_scene_slimes,
     "text": {"en": "Slimes rest, then squash down and lunge at you. Hit a big one and it bursts into two smaller slimes.",
              "es": "Los slimes descansan, luego se aplastan y se lanzan hacia ti. Si golpeas a uno grande, se divide en dos slimes mas pequenos."}},
    {"title": {"en": "HEALTH", "es": "VIDA"}, "period": 6.0, "scene": tut_scene_health,
     "text": {"en": "Each heart holds 2 health points. Touching an enemy takes some away, and then you blink and cannot be hurt for a moment. Keep an eye on your hearts.",
              "es": "Cada corazon tiene 2 puntos de vida. Tocar a un enemigo te quita algunos, y luego parpadeas y no te pueden hacer dano por un momento. Vigila tus corazones."}},
    {"title": {"en": "NOTEBOOK AND INK", "es": "CUADERNO Y TINTA"}, "period": 7.0, "scene": tut_scene_ink,
     "text": {"en": "Hold the left mouse button and draw on the notebook page. Drawing uses up ink, and ink outside the page ruins your drawing. Press R to refill the ink and C to clear the page. What you draw matters, and you will discover the rest as you play.",
              "es": "Manten pulsado el boton izquierdo del raton y dibuja en la pagina del cuaderno. Dibujar gasta tinta, y la tinta fuera de la pagina arruina el dibujo. Pulsa R para rellenar la tinta y C para limpiar la pagina. Lo que dibujas importa, y el resto lo iras descubriendo."}},
    {"title": {"en": "TARGETING", "es": "OBJETIVO"}, "period": 6.0, "scene": tut_scene_target,
     "text": {"en": "One enemy always has a ring around it, and that is your target. Press Q to jump the ring to another enemy.",
              "es": "Un enemigo siempre tiene un anillo alrededor, y ese es tu objetivo. Pulsa Q para pasar el anillo a otro enemigo."}},
    {"title": {"en": "LEVELS AND WAVES", "es": "NIVELES Y OLEADAS"}, "period": 9.0, "scene": tut_scene_exp,
     "text": {"en": "Defeated enemies drop exp orbs. Walk close and they fly to you and fill the bar at the bottom. A new wave arrives every {t} seconds, beaten or not, and the clock shows how long you have survived.",
              "es": "Los enemigos derrotados sueltan orbes de exp. Acercate y volaran hacia ti y llenaran la barra de abajo. Cada {t} segundos llega una nueva oleada, hayas ganado o no, y el reloj muestra cuanto has sobrevivido."}},
    {"title": {"en": "NEW SPELLS", "es": "NUEVOS HECHIZOS"}, "period": 6.0, "scene": tut_scene_choice,
     "text": {"en": "You start by choosing two spells. Every time you level up you can choose a new one from up to three you do not know yet. Drawing a spell you have not learned does nothing. You can skip a choice to get some of the exp back.",
              "es": "Empiezas eligiendo dos hechizos. Cada vez que subes de nivel puedes elegir uno nuevo entre hasta tres que aun no conoces. Dibujar un hechizo que no has aprendido no hace nada. Puedes saltar una eleccion para recuperar parte de la exp."}},
]


# =============================================================================
# THE TUTORIAL ITSELF
# =============================================================================

def tut_scene_statue(t, r):
    """Uses the statue's real timings: shake, fly up, shadow tracks the cat and locks, drop, stuck."""
    tut_floor(r)
    fy = tut_ground(r)
    t_rise = STATUE_REST_TIME[0] + STATUE_CHARGE_TIME
    t_hover = t_rise + STATUE_RISE_TIME
    t_fall = t_hover + STATUE_HOVER_TIME
    t_lock = t_fall - STATUE_LOCK_TIME
    t_land = t_fall + STATUE_FALL_TIME
    air = fy - r.y + STATUE_HEIGHT + sc(10)               # far enough up to be off the scene

    cx0, xmin = r.x + r.w * 0.55, r.x + r.w * 0.10
    run_from = t_rise - 0.3                                # the cat starts running when the statue starts to shake hard

    def cat_x(tt):
        return max(xmin, cx0 - PLAYER_MAX_SPEED * max(0.0, tt - run_from))

    sx, lx = r.x + r.w * 0.85, cat_x(t_lock)               # where the statue rests / where it lands

    # shadow on the floor
    if t < t_rise:
        tut_ground_shadow(sx, fy, STATUE_RADIUS)
    elif t < t_land:
        p = clamp01((t - t_rise) / (STATUE_RISE_TIME + STATUE_HOVER_TIME + STATUE_FALL_TIME))
        k = STATUE_SHADOW_START_SCALE + (1.0 - STATUE_SHADOW_START_SCALE) * p
        a = round(STATUE_SHADOW_START_ALPHA + (SHADOW_ALPHA - STATUE_SHADOW_START_ALPHA) * p)
        x = sx if t < t_hover else (cat_x(t) if t < t_lock else lx)
        tut_ground_shadow(x, fy, STATUE_RADIUS, k, a)
    else:
        tut_ground_shadow(lx, fy, STATUE_RADIUS)

    # the statue
    if t < t_rise:
        c = t - STATUE_REST_TIME[0]
        k = clamp01(c / STATUE_CHARGE_TIME)
        amp = STATUE_SHAKE * (0.3 + 0.7 * k)
        shake = (math.sin(c * 70) * amp, math.sin(c * 93) * amp * 0.4) if c > 0 else (0.0, 0.0)
        tut_statue(sx, fy, blend=k, shake=shake)
    elif t < t_hover:
        tut_statue(sx, fy, off=-air * clamp01((t - t_rise) / STATUE_RISE_TIME))
    elif t < t_fall:
        pass                                               # off screen
    elif t < t_land:
        k = (t - t_fall) / STATUE_FALL_TIME
        tut_statue(lx, fy, off=-air * (1 - k * k))
    else:
        squash = STATUE_LAND_SQUASH * (1 - clamp01((t - t_land) / STATUE_LAND_SQUASH_TIME))
        tut_statue(lx, fy, squash=squash)
        tut_puff(lx, fy - sc(10), t - t_land)
        tut_popup("5", lx, fy - STATUE_HEIGHT, t - (t_land + 0.3))    # the cat hits it while it is stuck

    cx = cat_x(t)
    tut_cat(cx, fy, left=t >= run_from, walking=t >= run_from and cx > xmin + 1, t=t)


STATUE_SLIDES = [
    {"title": {"en": "STATUES", "es": "ESTATUAS"}, "period": 7.0, "scene": tut_scene_statue,
     "text": {"en": "Statues rest, shake, then fly off the screen. A shadow follows you on the floor and locks onto the spot where the statue will land. Get out of the shadow before it drops, or the slam hurts you and knocks you back. After landing, the statue is stuck for a moment, which is your chance to hit it. It cannot be hurt while it is in the air.",
              "es": "Las estatuas descansan, tiemblan y luego salen volando de la pantalla. Una sombra te sigue por el suelo y se fija en el punto donde caera la estatua. Sal de la sombra antes de que caiga, o el golpe te hara dano y te empujara. Despues de caer, la estatua se queda atascada un momento, y esa es tu oportunidad para golpearla. No se le puede hacer dano mientras esta en el aire."}},
]

def tut_draw_world(step):
    """The real game world + HUD, no enemy logic (the tutorial updates it when needed)."""
    draw_floor()
    draw_enemies()
    draw_player()
    draw_reload()
    draw_puffs()
    draw_popups()
    update_hud_fade(step)
    draw_notebook(hud_alpha_notebook)
    draw_pages()
    draw_ink_bar(step)
    draw_hearts(hud_alpha_hearts)
    draw_wave_timer()
    draw_xp_bar(step, hud_alpha_xp)
    draw_xp_text(hud_alpha_xp)

def tut_reset_world():
    """Puts everything back to a clean start for the real run."""
    global target_index, drawing, last_pos, stroke_outside, result
    global player_hp, player_invuln, ink, ink_shown, reloading, reload_t
    shield_hits = 0
    enemies.clear()
    target_index = None
    clear_drawing()
    falling_pages.clear()
    puffs.clear()
    popups.clear()
    reload_flags.clear()
    reloading, reload_t, ink, ink_shown = False, 0.0, 1.0, 1.0
    player_hp, player_invuln = HEART_COUNT * 2, 0.0
    player_pos.update(WIDTH / 2, HEIGHT / 2)
    player_vel.update(0, 0)
    _cam_f.update(0, 0)
    cam.update(0, 0)
    drawing, last_pos, stroke_outside, result = False, None, False, None


def run_tutorial(slides=None, reset=True):
    """Returns False if the window was closed."""
    slides = slides or SLIDES
    last = len(slides) - 1
    pad = sc(24)
    panel = pygame.Rect(0, 0, round(WIDTH * 0.64), round(HEIGHT * 0.82))
    panel.center = (WIDTH // 2, HEIGHT // 2)
    scene_r = pygame.Rect(panel.left + pad, panel.top + pad + TUT_TITLE_FONT.get_height() + sc(10),
                          panel.width - 2 * pad, round(panel.height * 0.5))
    btn_w, btn_h = sc(230), sc(58)
    btn_y = panel.bottom - pad - btn_h
    back_r = pygame.Rect(panel.left + pad, btn_y, btn_w, btn_h)
    next_r = pygame.Rect(panel.right - pad - btn_w, btn_y, btn_w, btn_h)
    skip_r = pygame.Rect(panel.right - pad - sc(170), panel.top + pad, sc(170), sc(42))
    title_max_w = panel.width - 3 * pad - skip_r.width
    text_top = scene_r.bottom + pad
    text_bottom = btn_y - sc(10)                      # the text must end above the buttons

    body_fonts = {}

    def fit_body(text):
        """Biggest font size at which the wrapped text fits inside the panel."""
        size = sc(26)
        while True:
            if size not in body_fonts:
                body_fonts[size] = _intro_font(size)
            f = body_fonts[size]
            lines = tut_wrap(f, text, panel.width - 2 * pad)
            if len(lines) * (f.get_height() + sc(4)) <= text_bottom - text_top or size <= 8:
                return f, lines
            size -= 1

    dim = pygame.Surface((WIDTH, HEIGHT))
    dim.fill((0, 0, 14))
    fade = pygame.Surface(scene_r.size)
    fade.fill((0, 0, 0))
    backdrop = None if reset else screen.copy()     # in the middle of a run, the frozen game is the background

    idx, slide_t = 0, 0.0
    dark = pop = 0.0
    finished = False
    text_cache = {}

    def go(new_idx):
        nonlocal idx, slide_t
        idx = new_idx
        slide_t = 0.0

    while not finished:
        step = min(clock.tick(60) / 1000, MAX_FRAME_TIME)
        mouse = pygame.mouse.get_pos()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()
                elif ev.key in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE) and pop >= 1.0:
                    if idx == last:
                        finished = True
                    else:
                        go(idx + 1)
                elif ev.key == pygame.K_LEFT and idx > 0:
                    go(idx - 1)
                elif ev.key == pygame.K_ESCAPE:
                    finished = True
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and pop >= 1.0:
                if next_r.collidepoint(ev.pos):
                    if idx == last:
                        finished = True
                    else:
                        go(idx + 1)
                elif back_r.collidepoint(ev.pos) and idx > 0:
                    go(idx - 1)
                elif skip_r.collidepoint(ev.pos):
                    finished = True

        if backdrop is not None:
            screen.blit(backdrop, (0, 0))
        else:
            tut_draw_world(0.0)

        dark += max(-step / 0.5, min(step / 0.5, 1.0 - dark))      # the screen gets darker
        dim.set_alpha(round(TUTORIAL_DARKNESS * dark))
        screen.blit(dim, (0, 0))

        if dark > 0.6:
            pop = min(1.0, pop + step / 0.45)
        if pop >= 1.0:
            slide_t += step

        if 0 < pop < 1:                                 # the empty panel grows
            k = ease_out_back(pop)
            if k > 0.02:
                rr = pygame.Rect(0, 0, max(2, round(panel.w * k)), max(2, round(panel.h * k)))
                rr.center = panel.center
                pygame.draw.rect(screen, TUTORIAL_PANEL_COLOR, rr, border_radius=sc(22))
                pygame.draw.rect(screen, INK_START_COLOR, rr, sc(4), border_radius=sc(22))
        elif pop >= 1.0:
            slide = slides[idx]
            pygame.draw.rect(screen, TUTORIAL_PANEL_COLOR, panel, border_radius=sc(22))
            pygame.draw.rect(screen, INK_START_COLOR, panel, sc(4), border_radius=sc(22))
            title = tut_fit(tut_text(tut_lang(slide["title"]), TUT_TITLE_FONT), title_max_w)
            screen.blit(title, title.get_rect(topleft=(panel.left + pad, panel.top + pad)))

            phase = slide_t % slide["period"]           # the scene loops until you press next
            screen.set_clip(scene_r)
            slide["scene"](phase, scene_r)
            f = max(1 - phase / 0.3, (phase - (slide["period"] - 0.3)) / 0.3, 0.0)
            if f > 0:
                fade.set_alpha(round(255 * min(1.0, f)))
                screen.blit(fade, scene_r.topleft)
            screen.set_clip(None)
            pygame.draw.rect(screen, INK_START_COLOR, scene_r, sc(3))

            key = (idx, LANGUAGE)
            if key not in text_cache:
                text_cache[key] = fit_body(tut_lang(slide["text"]).replace("{t}", str(int(WAVE_TIME))))
            body_font, lines = text_cache[key]
            y = text_top
            for line in lines:
                s = body_font.render(line, True, (235, 240, 255))
                screen.blit(s, s.get_rect(midtop=(panel.centerx, y)))
                y += s.get_height() + sc(4)

            if idx > 0:
                tut_button(back_r, tr("BACK"), back_r.collidepoint(mouse))
            tut_button(next_r, tr("FINISH") if idx == last else tr("NEXT"), next_r.collidepoint(mouse))
            tut_button(skip_r, tr("SKIP"), skip_r.collidepoint(mouse), TUT_BODY_FONT)
            for i in range(len(slides)):                # page dots
                cx = panel.centerx + round((i - (len(slides) - 1) / 2) * sc(26))
                pygame.draw.circle(screen, INK_START_COLOR if i == idx else (90, 85, 130), (cx, back_r.centery),
                                   sc(8) if i == idx else sc(5))

        pygame.display.flip()

    if reset:
        tut_reset_world()
    return True


def run_countdown():
    """3, 2, 1 over the (still) game, then the run starts. Returns False if the window was closed."""
    big = _intro_font(round(170 * INTRO_K))
    cache = {}
    total = float(COUNTDOWN_SECONDS)
    dim = pygame.Surface((WIDTH, HEIGHT))
    dim.fill((0, 0, 14))
    dim.set_alpha(90)
    t = 0.0
    while t < total:
        step = min(clock.tick(60) / 1000, MAX_FRAME_TIME)
        t += step
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_f:
                pygame.display.toggle_fullscreen()
        tut_draw_world(0.0)
        screen.blit(dim, (0, 0))
        n = max(1, math.ceil(total - t))
        p = t % 1.0
        if n not in cache:
            cache[n] = render_outlined(big, str(n), (255, 255, 255), MENU_TEXT_OUTLINE_COLOR, sc(6))
        img = pygame.transform.rotozoom(cache[n], 0, 1.5 - 0.5 * _ease_out(p))
        img.set_alpha(round(255 * (1 - clamp01((p - 0.7) / 0.3))))
        screen.blit(img, img.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        label = tut_fit(tut_text(tr("GET READY"), TUT_TITLE_FONT), WIDTH - sc(48))
        screen.blit(label, label.get_rect(midbottom=(WIDTH // 2, HEIGHT // 2 - round(150 * INTRO_K))))
        pygame.display.flip()
    return True

if SHOW_TUTORIAL and not run_tutorial():
    pygame.quit()
    raise SystemExit
if COUNTDOWN_SECONDS > 0 and not run_countdown():
    pygame.quit()
    raise SystemExit

def run_spell_choice(options, title, refund):
    """Shows the options as cards. Returns the chosen spell name, None if skipped, or "quit" if the window was closed."""
    backdrop = screen.copy()
    dim = pygame.Surface((WIDTH, HEIGHT))
    dim.fill((0, 0, 14))
    pad, gap = sc(24), sc(20)
    panel = pygame.Rect(0, 0, round(WIDTH * 0.72), round(HEIGHT * 0.78))
    panel.center = (WIDTH // 2, HEIGHT // 2)
    skip_r = pygame.Rect(0, 0, sc(420), sc(58))
    skip_r.midbottom = (panel.centerx, panel.bottom - pad)
    cards_top = panel.top + pad + TUT_TITLE_FONT.get_height() + sc(16)
    cards_h = skip_r.top - sc(16) - cards_top
    card_w = (panel.width - 2 * pad - 2 * gap) // 3          # always sized for 3, so 1 or 2 cards stay centred
    n = len(options)
    x0 = panel.centerx - (n * card_w + (n - 1) * gap) // 2
    cards = [pygame.Rect(x0 + i * (card_w + gap), cards_top, card_w, cards_h) for i in range(n)]

    inner = card_w - 2 * sc(16)
    icon_h = round(cards_h * 0.36)
    icons = [spell_icon(o, inner, icon_h) for o in options]
    names = [tut_fit(tut_text(tr(o), TUT_BTN_FONT, o=max(1, sc(2))), inner) for o in options]
    texts = [tut_lang(SPELL_INFO[o]).format(**SPELL_FORMAT) for o in options]
    desc_top = cards_top + sc(16) + icon_h + sc(10) + max(s.get_height() for s in names) + sc(10)
    desc_room = cards_top + cards_h - sc(14) - desc_top

    size = sc(24)                                            # biggest font at which every description fits its card
    while True:
        f = _intro_font(size)
        wrapped = [tut_wrap(f, t, inner) for t in texts]
        if size <= 8 or all(len(w) * (f.get_height() + sc(3)) <= desc_room for w in wrapped):
            break
        size -= 1

    skip_label = f"{tr('SKIP')}, {refund} EXP"
    pop = 0.0
    while True:
        step = min(clock.tick(60) / 1000, MAX_FRAME_TIME)
        pop = min(1.0, pop + step / 0.35)
        ready = pop >= 1.0
        mouse = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()
                elif ready and pygame.K_1 <= ev.key < pygame.K_1 + n:
                    return options[ev.key - pygame.K_1]
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and ready:
                if skip_r.collidepoint(ev.pos):
                    return None
                for rect, o in zip(cards, options):
                    if rect.collidepoint(ev.pos):
                        return o

        screen.blit(backdrop, (0, 0))
        dim.set_alpha(190)
        screen.blit(dim, (0, 0))
        k = ease_out_back(pop)
        rr = pygame.Rect(0, 0, max(2, round(panel.w * k)), max(2, round(panel.h * k)))
        rr.center = panel.center
        pygame.draw.rect(screen, TUTORIAL_PANEL_COLOR, rr, border_radius=sc(22))
        pygame.draw.rect(screen, INK_START_COLOR, rr, sc(4), border_radius=sc(22))
        if ready:
            t_surf = tut_fit(tut_text(tr(title), TUT_TITLE_FONT), panel.width - 2 * pad)
            screen.blit(t_surf, t_surf.get_rect(midtop=(panel.centerx, panel.top + pad)))
            for i, rect in enumerate(cards):
                hover = rect.collidepoint(mouse)
                pygame.draw.rect(screen, (46, 34, 92) if hover else (32, 24, 64), rect, border_radius=sc(16))
                pygame.draw.rect(screen, INK_START_COLOR if hover else (90, 85, 130), rect, sc(3), border_radius=sc(16))
                screen.blit(icons[i], icons[i].get_rect(center=(rect.centerx, rect.top + sc(16) + icon_h // 2)))
                ny = rect.top + sc(16) + icon_h + sc(10)
                screen.blit(names[i], names[i].get_rect(midtop=(rect.centerx, ny)))
                y = desc_top
                for line in wrapped[i]:
                    s = f.render(line, True, (235, 240, 255))
                    screen.blit(s, s.get_rect(midtop=(rect.centerx, y)))
                    y += s.get_height() + sc(3)
            tut_button(skip_r, skip_label, skip_r.collidepoint(mouse), TUT_BODY_FONT)
        pygame.display.flip()


def offer_spell_choice(pool, title, refund):
    """Offers up to 3 random spells from `pool`. Returns False if the window was closed."""
    options = random.sample(pool, min(3, len(pool)))
    res = run_spell_choice(options, title, refund)
    if res == "quit":
        return False
    if res is None:
        gain_exp(refund)                  # skipped: the exp comes back
    else:
        known_spells.add(res)
    return True


# --- the two starting choices (after the tutorial and the countdown) ---
_start_refund = max(1, round(EXP_BASE_NEEDED * SPELL_SKIP_REFUND))
tut_draw_world(0.0)
if not offer_spell_choice(DAMAGE_SPELLS, "CHOOSE YOUR FIRST SPELL", _start_refund):
    pygame.quit()
    raise SystemExit
tut_draw_world(0.0)
if not offer_spell_choice([s for s in ALL_SPELLS if s not in known_spells], "CHOOSE YOUR SECOND SPELL", _start_refund):
    pygame.quit()
    raise SystemExit

# =============================================================================
# DEATH SCREEN
# =============================================================================
TEXTS_ES.update({
    "YOU DIED": "HAS MUERTO",
    "TIME SURVIVED": "TIEMPO SOBREVIVIDO",
    "LEVEL REACHED": "NIVEL ALCANZADO",
    "KILLS": "ENEMIGOS DERROTADOS",
    "SPELLS": "HECHIZOS",
})
DEATH_ICON_SIZE = sc(80)       # px, size of each spell icon
DEATH_ICON_GAP = sc(14)        # px between the icons


def run_death_screen():
    """The cat slides in, then the results drop in on the right. Returns when the player leaves."""
    try:
        cat = load("catintro.png")
        if cat.get_size() != (WIDTH, HEIGHT):
            cat = pygame.transform.smoothscale(cat, (WIDTH, HEIGHT))
    except (FileNotFoundError, pygame.error):
        cat = None

    big = _intro_font(sc(60))
    panel_cx = round(WIDTH * 0.75) - sc(MENU_PANEL_SHIFT)
    max_w = round(WIDTH * 0.42)
    seconds = int(game_time)
    spells = [s for s in ALL_SPELLS if s in known_spells]
    btn = pygame.Rect(0, 0, sc(300), sc(58))
    btn.center = (panel_cx, round(HEIGHT * 0.93))

    t = 0.0
    while True:
        step = min(clock.tick(60) / 1000, MAX_FRAME_TIME)
        t += step
        p = clamp01((t - MENU_SLIDE_TIME - MENU_FALL_DELAY) / MENU_FALL_TIME)
        ready = p >= 1.0
        mouse = pygame.mouse.get_pos()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()
                elif ready and ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    return
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and ready:
                if btn.collidepoint(ev.pos):
                    return

        draw_floor()
        if cat is not None:
            offset_x = round(-WIDTH * (1 - _ease_out(clamp01(t / MENU_SLIDE_TIME))))
            screen.blit(cat, cat.get_rect(center=(WIDTH // 2 + offset_x, HEIGHT // 2)))

        if p > 0:
            dy = round(-HEIGHT * (1 - _ease_out(p)))             # the panel drops in from above

            title = tut_fit(tut_text(tr("YOU DIED"), big, o=max(1, sc(4))), max_w)
            screen.blit(title, title.get_rect(midtop=(panel_cx, round(HEIGHT * 0.08) + dy)))

            stats = (("TIME SURVIVED", None), ("LEVEL REACHED", level), ("KILLS", kills))
            for i, (label, value) in enumerate(stats):
                y = round(HEIGHT * (0.26 + 0.16 * i)) + dy
                lab = tut_fit(tut_text(tr(label), TUT_BODY_FONT), max_w)
                screen.blit(lab, lab.get_rect(midtop=(panel_cx, y)))
                top = y + lab.get_height() + sc(6)
                if value is None:
                    tut_timer(panel_cx, top, seconds)
                else:
                    val = tut_text(str(value), timer_font, o=max(1, sc(3)))
                    screen.blit(val, val.get_rect(midtop=(panel_cx, top)))

            y = round(HEIGHT * 0.74) + dy
            lab = tut_fit(tut_text(tr("SPELLS"), TUT_BODY_FONT), max_w)
            screen.blit(lab, lab.get_rect(midtop=(panel_cx, y)))
            if spells:
                cell = DEATH_ICON_SIZE + DEATH_ICON_GAP
                x0 = panel_cx - (len(spells) * cell - DEATH_ICON_GAP) // 2
                cy = y + lab.get_height() + sc(10) + DEATH_ICON_SIZE // 2
                for i, name in enumerate(spells):
                    icon = spell_icon(name, DEATH_ICON_SIZE, DEATH_ICON_SIZE)
                    screen.blit(icon, icon.get_rect(center=(x0 + i * cell + DEATH_ICON_SIZE // 2, cy)))

            if ready:
                tut_button(btn, tr("QUIT GAME"), btn.collidepoint(mouse), TUT_BODY_FONT)

        pygame.display.flip()

# =============================================================================
# PAUSE MENU
# =============================================================================
TEXTS_ES.update({
    "PAUSED": "PAUSA",
    "RESUME": "CONTINUAR",
    "EXIT TO MAIN MENU": "MENU PRINCIPAL",
    "GIVE UP": "RENDIRSE",
})


def return_to_main_menu():
    """Resets the run and shows the start menu again, all inside the same window.
    Returns False if the window was closed."""
    global wave, wave_left, game_time, level, exp_points, xp_shown, kills
    global death_timer, fizzle_time, walk_timer, player_look_right, lightning_left
    global hud_alpha_notebook, hud_alpha_bar, hud_alpha_hearts, hud_alpha_xp

    # everything from the old run goes away
    tut_reset_world()                    # enemies, ink, hp, player position, camera, pages, puffs...
    exp_orbs.clear()
    ink_areas.clear()
    shockwaves.clear()
    arrows.clear()
    slash_effects.clear()
    spell_pages.clear()
    spell_particles.clear()
    known_spells.clear()
    pending_choice_refunds.clear()
    wave, wave_left, game_time = 0, 0.0, 0.0
    level, exp_points, xp_shown, kills = 1, 0, 0.0, 0
    death_timer, fizzle_time, walk_timer = 0.0, 0.0, 0.0
    player_look_right = True
    hud_alpha_notebook = hud_alpha_bar = hud_alpha_hearts = hud_alpha_xp = 1.0

    # the same sequence as when the game first starts
    if run_start_menu() == "quit":
        return False
    tut_reset_world()                    # the menu may have changed nothing, but this keeps the start clean
    if SHOW_TUTORIAL and not run_tutorial():
        return False
    if COUNTDOWN_SECONDS > 0 and not run_countdown():
        return False
    refund = max(1, round(EXP_BASE_NEEDED * SPELL_SKIP_REFUND))
    tut_draw_world(0.0)
    if not offer_spell_choice(DAMAGE_SPELLS, "CHOOSE YOUR FIRST SPELL", refund):
        return False
    tut_draw_world(0.0)
    if not offer_spell_choice([s for s in ALL_SPELLS if s not in known_spells], "CHOOSE YOUR SECOND SPELL", refund):
        return False
    return True


def run_pause_menu():
    """Same look as the start menu (cat slides in, menu falls in on the right) but with text buttons.
    Returns "resume", "give_up", "menu" or "quit" (window closed)."""
    backdrop = screen.copy()
    dim = pygame.Surface((WIDTH, HEIGHT))
    dim.fill((0, 0, 14))
    dim.set_alpha(150)
    menu_clock = pygame.time.Clock()

    def load_full(name):
        img = load(name)
        if img.get_size() != (WIDTH, HEIGHT):
            img = pygame.transform.smoothscale(img, (WIDTH, HEIGHT))
        return img

    try:
        cat_open = load_full("catintro.png")
        cat_shut = load_full("catintroeyesshut.png")
    except (FileNotFoundError, pygame.error):
        cat_open = cat_shut = None

    title_font = _intro_font(round(44 * INTRO_K))
    button_font = _intro_font(round(24 * INTRO_K))
    panel_cx = round(WIDTH * 0.75) - sc(MENU_PANEL_SHIFT)
    btn_h = round(HEIGHT * 0.08)
    btn_gap = round(HEIGHT * 0.035)
    title_top_final = round(HEIGHT * 0.10)
    buttons_top_final = round(HEIGHT * 0.30)

    text_cache = {}

    def outlined(label, fnt, o):
        key = (label, id(fnt))
        if key not in text_cache:
            text_cache[key] = render_outlined(fnt, label, (255, 255, 255), MENU_TEXT_OUTLINE_COLOR, o)
        return text_cache[key]

    def buttons_for(mode_name):
        if mode_name == "main":
            return [(tr("RESUME"), "resume"), (tr("CONFIG"), "config"),
                    (tr("EXIT TO MAIN MENU"), "menu"), (tr("GIVE UP"), "give_up")]
        lang_name = "ENGLISH" if LANGUAGE == "en" else "ESPANOL"
        return [(tr("FULLSCREEN"), "fullscreen"),
                (f"{tr('LANGUAGE')} {lang_name}", "language"),
                (tr("BACK"), "back")]

    t = 0.0
    mode = "main"
    blink_wait = random.uniform(*MENU_BLINK_INTERVAL)
    blink_left = 0.0

    def fall_top(final_top, h, index):
        p = clamp01((t - MENU_SLIDE_TIME - MENU_FALL_DELAY - index * MENU_FALL_STAGGER) / MENU_FALL_TIME)
        return round(final_top - (final_top + h) * (1 - _ease_out(p)))

    while True:
        dt_m = min(menu_clock.tick(60) / 1000, MAX_FRAME_TIME)
        t += dt_m
        ready = t >= MENU_SLIDE_TIME + MENU_FALL_DELAY + MENU_FALL_TIME + 4 * MENU_FALL_STAGGER
        mouse = pygame.mouse.get_pos()

        rects = []
        for i, (label, action) in enumerate(buttons_for(mode)):
            w = outlined(label, button_font, sc(MENU_TEXT_OUTLINE)).get_width()
            top = fall_top(buttons_top_final + i * (btn_h + btn_gap), btn_h, i + 1)
            rects.append((pygame.Rect(panel_cx - w // 2, top, w, btn_h), label, action))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN and ready:
                if event.key == pygame.K_ESCAPE:
                    if mode == "config":
                        mode = "main"
                    else:
                        return "resume"
                elif event.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and ready:
                for rect, _label, action in rects:
                    if rect.collidepoint(event.pos):
                        if action == "resume":
                            return "resume"
                        elif action == "menu":
                            return "menu"
                        elif action == "give_up":
                            return "give_up"
                        elif action == "config":
                            mode = "config"
                        elif action == "back":
                            mode = "main"
                        elif action == "fullscreen":
                            pygame.display.toggle_fullscreen()
                        elif action == "language":
                            toggle_language()
                        break

        if blink_left > 0:
            blink_left -= dt_m
        else:
            blink_wait -= dt_m
            if blink_wait <= 0:
                blink_left = MENU_BLINK_TIME
                blink_wait = random.uniform(*MENU_BLINK_INTERVAL)

        # --- draw ---
        screen.blit(backdrop, (0, 0))
        screen.blit(dim, (0, 0))
        if cat_open is not None:
            offset_x = round(-WIDTH * (1 - _ease_out(clamp01(t / MENU_SLIDE_TIME))))
            img = cat_shut if blink_left > 0 else cat_open
            screen.blit(img, img.get_rect(center=(WIDTH // 2 + offset_x, HEIGHT // 2)))

        title = outlined(tr("PAUSED"), title_font, sc(MENU_TEXT_OUTLINE))
        screen.blit(title, title.get_rect(midtop=(panel_cx, fall_top(title_top_final, title.get_height(), 0))))

        for rect, label, action in rects:
            img = outlined(label, button_font, sc(MENU_TEXT_OUTLINE))
            if ready and rect.collidepoint(mouse):
                img = pygame.transform.smoothscale(
                    img, (round(img.get_width() * MENU_BUTTON_HOVER), round(img.get_height() * MENU_BUTTON_HOVER)))
            screen.blit(img, img.get_rect(center=rect.center))

        pygame.display.flip()

death_timer = 0.0               # counts up once the cat is dead
statue_tutorial_done = False

running = True
while running:
    dt = clock.tick(FPS) / 1000          # real seconds since the last frame (and caps the game at FPS)
    for event in pygame.event.get():
        if player_hp <= 0 and event.type != pygame.QUIT:
            continue                                # the cat is dead: no more input

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:  # clear canvas
                if glow_positions:       # something was drawn: the page falls with it
                    drop_page()
                outline_layer.fill((0, 0, 0, 0))
                colour_layer.fill((0, 0, 0, 0))
                fresh_stamps.clear()
                glow_positions.clear()
                glow_index = None
                result = None
            elif event.key == pygame.K_f:  # switch between fullscreen and window
                pygame.display.toggle_fullscreen()
            elif event.key == pygame.K_r:  # reload the ink
                start_reload()
            elif event.key == pygame.K_ESCAPE:
                _res = run_pause_menu()
                if _res == "quit":
                    running = False
                elif _res == "give_up":
                    player_hp = 0                    # the death check at the end of the frame takes over
                elif _res == "menu":
                    if not return_to_main_menu():
                        running = False
                drawing, last_pos, stroke_points = False, None, []   # don't carry a half-drawn stroke over
            elif event.key == pygame.K_q and enemies:
                target_index = pick_target(target_index)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not spell_pages:
            drawing = True
            last_pos = event.pos
            stroke_points = []
            stroke_outside = False
            glow_index = None
            if has_ink():
                paint(event.pos, event.pos)
                if inside_area(event.pos):
                    spend_ink(SPACING)
                    stroke_points.append(event.pos)
                    glow_positions.append(event.pos)
                    glow_index = len(glow_positions) - 1
                else:
                    stroke_outside = True

        elif event.type == pygame.MOUSEMOTION and drawing:
            if has_ink():
                if segment_leaves_area(last_pos, event.pos):
                    stroke_outside = True
                paint(last_pos, event.pos)
                if inside_area(event.pos):
                    spend_ink(_dist(last_pos, event.pos))
                    stroke_points.append(event.pos)
                    if glow_index is None:
                        glow_positions.append(event.pos)
                        glow_index = len(glow_positions) - 1
                    else:
                        glow_positions[glow_index] = event.pos
            last_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and drawing:
            drawing = False
            if stroke_points:
                result = recognize_shape(stroke_points)
                if result[0] in SPELL_NAMES and stroke_outside:
                    result = GIBBERISH                  # ink outside the page: the spell fizzles
                    fizzle_time = SPELL_FIZZLE_TIME
                if result[0] in SPELL_NAMES and result[0] not in known_spells:
                    result = UNKNOWN_SPELL              # not learned yet: nothing is cast, the page stays
                print("Shape drawn:", result[0], "|", result[1] or "-")
                if result[0] in known_spells:           # only learned spells are ever cast
                    if result[0] == SLASH_SPELL[0]:
                        cast_slash()
                        vanish_page()
                    elif result[0] == CHAIN_SPELL[0]:
                        cast_chain()
                        vanish_page()
                    elif result[0] == INK_AREA_SPELL[0]:
                        cast_ink_area()
                        vanish_page()
                    elif result[0] == ARROW_SPELL[0]:
                        cast_arrow()
                        vanish_page()
                    elif result[0] == SHOCKWAVE_SPELL[0]:
                        cast_shockwave()
                        vanish_page()
                    elif result[0] == LIGHTNING_SPELL[0]:
                        if cast_lightning():        # already active: nothing happens and the page stays
                            vanish_page()
                    elif result[0] == SHIELD_SPELL[0]:
                        if cast_shield():           # already full: nothing happens and the page stays
                            vanish_page()

    step = min(dt, MAX_FRAME_TIME)
    update_player(step)
    update_lightning(step)
    update_enemies(step)
    update_shockwaves(step)
    update_arrows(step)
    update_slashes(step)
    update_ink_areas(step)
    update_pages(step)
    update_reload(step)
    update_puffs(step)
    update_popups(step)
    update_health(step)
    update_waves(step)                  # add this line
    update_exp(step)                    # add this line with the other updates
    update_spell_effects(step)
    update_camera(step)
    fizzle_time = max(0.0, fizzle_time - step)
    target_angle = (target_angle + TARGET_SPIN_SPEED * step) % 360
    target_bob_time += step

    draw_floor()
    draw_ink_areas()
    draw_shockwaves()                   # on the floor, under shadows and enemies
    draw_enemies()
    draw_player()
    draw_exp()                          # add this line: orbs are drawn above the cat so they are never hidden
    draw_arrows()                     # above the enemies and the cat
    draw_slashes()                      # above the enemies and the cat
    draw_reload()                       # inker + pencil next to the cat
    draw_puffs()
    draw_popups()                       # floating damage numbers

    # The notebook and the ink bar are drawn on top of everything, and fade out while something is under them
    update_hud_fade(step)
    draw_notebook(hud_alpha_notebook)
    draw_pages()                        # cleared pages falling off the notebook (above it)
    draw_spell_effects(hud_alpha_notebook)   # purple page + particles
    draw_ink_bar(step)                  # ink bar right of the notebook
    draw_hearts(hud_alpha_hearts)
    draw_shield_hearts(hud_alpha_hearts)
    draw_wave_timer()                   # add this line
    draw_xp_bar(step, hud_alpha_xp)     # add this line: exp bar on the bottom border

    # Spell label: only the spell's name, below the notebook (nothing for gibberish or plain shapes)
    # Result label under the notebook: the spell's name, or "Gibberish" for anything that isn't a spell.
    # If the text is wider than the notebook, it continues on a new line.
    if result:
        shown = result[0] if (result[0] in SPELL_NAMES or result[0] == UNKNOWN_SPELL[0]) else GIBBERISH[0]
        max_w = notebook_rect.width - sc(8)                       # a little margin on both sides
        lines, current = [], ""
        for word in tr(shown).split():
            test = f"{current} {word}".strip()
            if current and spell_label_font.size(test)[0] > max_w:
                lines.append(current)                             # it doesn't fit: start a new line
                current = word
            else:
                current = test
        lines.append(current)
        y = notebook_rect.bottom + sc(12)
        for line in lines:
            label = spell_label_font.render(line, True, TEXT_COLOR)
            if label.get_width() > max_w:                         # a single word that is too long: shrink it
                k = max_w / label.get_width()
                label = pygame.transform.smoothscale(label, (max_w, max(1, round(label.get_height() * k))))
            screen.blit(label, label.get_rect(midtop=(notebook_rect.centerx, y)))
            y += label.get_height() + sc(2)

    draw_xp_text(hud_alpha_xp)          # the exp text goes on top of everything

    pygame.display.flip()

    if player_hp <= 0:                               # the cat died: the game keeps playing for a moment
        death_timer += step
        if death_timer >= DEATH_ANIM_TIME:
            run_death_screen()
            running = False
    elif pending_choice_refunds:                     # a level-up is waiting for its spell choice
        _left = [s for s in ALL_SPELLS if s not in known_spells]
        if not _left:
            pending_choice_refunds.clear()
        else:
            if not offer_spell_choice(_left, "LEVEL UP, CHOOSE A SPELL", pending_choice_refunds.pop(0)):
                running = False
            drawing, last_pos, stroke_points = False, None, []
    elif (SHOW_STATUE_TUTORIAL and not statue_tutorial_done
          and any(isinstance(e, Statue) and e.spawn_t <= 0 for e in enemies)):
        statue_tutorial_done = True
        if not run_tutorial(STATUE_SLIDES, reset=False):
            running = False
        drawing, last_pos, stroke_points = False, None, []
    

pygame.quit()