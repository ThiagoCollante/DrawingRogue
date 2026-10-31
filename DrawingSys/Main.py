import math
import os
import random
import pygame

pygame.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sprite Draw  |  Left click = draw  |  WASD/arrows = move  |  Q = next target  |  C = clear")
clock = pygame.time.Clock()

BG_COLOR = (245, 235, 215)  # beige
TEXT_COLOR = (40, 40, 60)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# SHAPE RECOGNITION
# Works on the raw mouse points of ONE stroke (press -> release).
# Steps: remove duplicates -> decide open/closed -> resample evenly ->
# smooth -> find corners (sharp turns) -> classify.
# ---------------------------------------------------------------------------
N_SAMPLES = 64        # points the stroke is resampled to
CORNER_WINDOW = 6     # how many samples to look back/forward for a turn
CORNER_ANGLE = 55     # degrees of turning needed to count as a corner
CLOSED_RATIO = 0.20   # start/end gap smaller than 20% of the path = closed
MIN_SIZE = 60         # pixels; drawings whose bounding box is smaller are gibberish


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


GIBBERISH = ("Gibberish", None)


def recognize_shape(raw_points):
    """Return (shape name, orientation text or None) for one stroke.
    Possible names: Circle, Square, Triangle, Line, Curve, Zigzag, Gibberish."""
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


outline_img = load("outline.png")
colour_img = load("colour.png")
glow_img = load("glow.png")

# Make the whole brush (outline, colour and glow) smaller
BRUSH_SCALE = 0.6   # 1.0 = original size


def scale_sprite(img, factor):
    w, h = img.get_size()
    return pygame.transform.smoothscale(img, (max(1, round(w * factor)), max(1, round(h * factor))))


outline_img = scale_sprite(outline_img, BRUSH_SCALE)
colour_img = scale_sprite(colour_img, BRUSH_SCALE)
glow_img = scale_sprite(glow_img, BRUSH_SCALE)

# Recolor the colour sprite to dark blue, keeping its transparency
DARK_BLUE = (15, 30, 110)
colour_img.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)  # RGB -> black, alpha kept
colour_img.fill((*DARK_BLUE, 0), special_flags=pygame.BLEND_RGBA_ADD)  # add blue, alpha untouched

# --- Target sprite: its white pixels take the colour of the ink -------------
TARGET_SIZE = 44  # px, the longest side of one target


def recolor_whites(img, ink):
    """Turn white pixels into `ink` (soft edges and grays are blended), keep everything else."""
    img = img.copy()
    for x in range(img.get_width()):
        for y in range(img.get_height()):
            r, g, b, a = img.get_at((x, y))
            if a == 0:
                continue
            # 0 below mid-gray, 1 for (near) white
            t = max(0.0, min(1.0, (min(r, g, b) - 128) / 72))
            img.set_at((x, y), (round(r + (ink[0] - r) * t),
                                round(g + (ink[1] - g) * t),
                                round(b + (ink[2] - b) * t), a))
    return img


target_img = load("target.png")
target_img = scale_sprite(target_img, TARGET_SIZE / max(target_img.get_size()))
target_img = recolor_whites(target_img, DARK_BLUE)

# --- Notebook (the "paper" you draw on) -----------------------------------
# notebook.png      -> the picture of the notebook
# notebook_area.png -> same picture, but the drawable zone is painted red
NOTEBOOK_FILE = "notebook.png"
NOTEBOOK_AREA_FILE = "notebook_area.png"
NOTEBOOK_HEIGHT_FRACTION = 0.35     # visible notebook height as a fraction of the window
NOTEBOOK_MAX_W_FRACTION = 0.5       # ...but never wider than this fraction of the window
NOTEBOOK_PADDING = 24               # gap (px) between the notebook and the window edges

notebook_img = load(NOTEBOOK_FILE)
area_img = load(NOTEBOOK_AREA_FILE)
if area_img.get_size() != notebook_img.get_size():
    area_img = pygame.transform.scale(area_img, notebook_img.get_size())

# Crop away the empty (transparent) margins so only the visible notebook is used
content = notebook_img.get_bounding_rect(min_alpha=10)
notebook_img = notebook_img.subsurface(content).copy()
area_img = area_img.subsurface(content).copy()

# Scale both to the same, smaller size
nb_scale = min(HEIGHT * NOTEBOOK_HEIGHT_FRACTION / content.height,
               WIDTH * NOTEBOOK_MAX_W_FRACTION / content.width)
nb_size = (max(1, round(content.width * nb_scale)),
           max(1, round(content.height * nb_scale)))
notebook_img = pygame.transform.smoothscale(notebook_img, nb_size)
area_img = pygame.transform.scale(area_img, nb_size)  # no smoothing, keeps the red pure

# Bottom-left corner, leaving a padding around the visible notebook
notebook_rect = notebook_img.get_rect(
    bottomleft=(NOTEBOOK_PADDING, HEIGHT - NOTEBOOK_PADDING))

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


def inside_area(pos):
    x, y = pos[0] - notebook_rect.x, pos[1] - notebook_rect.y
    return 0 <= x < nb_size[0] and 0 <= y < nb_size[1] and bool(area_mask.get_at((x, y)))


# Separate transparent layers so the order is always: outline < colour < glow
outline_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
colour_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
glow_positions = []  # one glow per stroke, sitting on the stroke's last point

# Distance between stamps (smaller = smoother line)
SPACING = max(1, min(colour_img.get_width(), colour_img.get_height()) * 0.2)

font = pygame.font.Font(None, 44)
small_font = pygame.font.Font(None, 28)
result = None  # (shape name, orientation)


# --- Top-down character (independent from the notebook) -------------------
# Move with WASD or the arrow keys, 8 directions, with acceleration and friction.
PLAYER_RADIUS = 24
PLAYER_ACCEL = 2400      # px/s^2 while a key is held
PLAYER_FRICTION = 8.0    # how quickly it slows down when you let go (higher = stops sooner)
PLAYER_MAX_SPEED = 320   # px/s

player_pos = pygame.math.Vector2(WIDTH / 2, HEIGHT / 2)  # middle of the window
player_vel = pygame.math.Vector2(0, 0)
player_facing = pygame.math.Vector2(0, 1)  # looking down at the start


def update_player(dt):
    global player_pos, player_vel, player_facing
    keys = pygame.key.get_pressed()
    direction = pygame.math.Vector2(
        (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
        (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP]),
    )
    if direction.length_squared() > 0:
        direction = direction.normalize()   # diagonals are not faster
        player_facing = direction
        player_vel += direction * PLAYER_ACCEL * dt

    player_vel -= player_vel * min(1.0, PLAYER_FRICTION * dt)  # friction
    if player_vel.length() > PLAYER_MAX_SPEED:
        player_vel.scale_to_length(PLAYER_MAX_SPEED)
    elif player_vel.length() < 2 and direction.length_squared() == 0:
        player_vel.update(0, 0)             # stop completely instead of drifting forever

    player_pos += player_vel * dt

    # Keep inside the window
    if player_pos.x < PLAYER_RADIUS or player_pos.x > WIDTH - PLAYER_RADIUS:
        player_pos.x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, player_pos.x))
        player_vel.x = 0
    if player_pos.y < PLAYER_RADIUS or player_pos.y > HEIGHT - PLAYER_RADIUS:
        player_pos.y = max(PLAYER_RADIUS, min(HEIGHT - PLAYER_RADIUS, player_pos.y))
        player_vel.y = 0


def draw_player():
    x, y = int(player_pos.x), int(player_pos.y)
    pygame.draw.ellipse(screen, (170, 155, 130),
                        (x - PLAYER_RADIUS, y + PLAYER_RADIUS - 8, PLAYER_RADIUS * 2, 14))  # shadow
    pygame.draw.circle(screen, (30, 30, 45), (x, y), PLAYER_RADIUS + 3)                      # outline
    pygame.draw.circle(screen, (225, 95, 60), (x, y), PLAYER_RADIUS)                         # body
    eye = player_pos + player_facing * (PLAYER_RADIUS * 0.55)                                # facing mark
    pygame.draw.circle(screen, (255, 245, 225), (int(eye.x), int(eye.y)), 8)
    pygame.draw.circle(screen, (30, 30, 45), (int(eye.x), int(eye.y)), 4)


def stamp(img, layer, pos):
    layer.blit(img, img.get_rect(center=(int(pos[0]), int(pos[1]))))


def stamp_pair(pos):
    stamp(outline_img, outline_layer, pos)
    stamp(colour_img, colour_layer, pos)


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


drawing = False
last_pos = None
stroke_points = []
glow_index = None

# --- Dummy enemies (balls that never move) ---------------------------------
ENEMY_COUNT = 6
ENEMY_MIN_RADIUS = 20
ENEMY_MAX_RADIUS = 46
TARGET_RING_GAP = 8          # target circle radius = enemy radius + this
TARGET_SPACING = 1.5         # arc length each target needs, as a fraction of TARGET_SIZE (higher = fewer targets)
TARGET_BOB_FRACTION = 0.15   # the circle expands/closes by this fraction of its radius
TARGET_BOB_SPEED = 3.0       # expand/close speed (radians per second)
TARGET_SPIN_SPEED = 120      # degrees per second
TARGET_RANGE = 350           # enemies closer than this to the player are "near"
TARGET_POINT_INWARD = True   # the sprite's tip faces the enemy (False = faces away)


class Enemy:
    def __init__(self, pos, radius):
        self.pos = pos
        self.radius = radius
        self.ring_radius = radius + TARGET_RING_GAP   # bigger enemy -> bigger target circle
        # ...and more targets on it, always spaced perfectly evenly
        fit = int(2 * math.pi * self.ring_radius / (TARGET_SIZE * TARGET_SPACING))
        self.target_count = max(3, min(10, fit))
        # how far the targets can reach from the centre (used to keep things on screen)
        self.reach = self.ring_radius * (1 + TARGET_BOB_FRACTION) + TARGET_SIZE // 2


def spawn_enemies():
    """Enemies of different sizes at random spots that keep clear of the player, the
    notebook, the window edges (so the target circle fits) and each other."""
    n = ENEMY_COUNT
    span = ENEMY_MAX_RADIUS - ENEMY_MIN_RADIUS
    radii = [ENEMY_MIN_RADIUS + span * i / max(1, n - 1) + random.randint(-3, 3) for i in range(n)]
    radii = sorted((max(ENEMY_MIN_RADIUS, min(ENEMY_MAX_RADIUS, round(r))) for r in radii), reverse=True)

    placed = []
    for r in radii:                                   # biggest first, they are hardest to fit
        probe = Enemy(pygame.math.Vector2(), r)
        margin = int(probe.reach) + 4
        avoid_notebook = notebook_rect.inflate(int(probe.reach) * 2, int(probe.reach) * 2)
        for _ in range(3000):
            pos = pygame.math.Vector2(random.randint(margin, WIDTH - margin),
                                      random.randint(margin, HEIGHT - margin))
            if avoid_notebook.collidepoint(pos.x, pos.y):
                continue
            if pos.distance_to(player_pos) < probe.reach + PLAYER_RADIUS + 40:
                continue
            if any(pos.distance_to(o.pos) < probe.reach + o.reach for o in placed):
                continue
            placed.append(Enemy(pos, r))
            break
    return placed


enemies = spawn_enemies()


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


def draw_enemies():
    for e in enemies:
        x, y, r = int(e.pos.x), int(e.pos.y), e.radius
        outline = max(2, round(r * 0.1))
        pygame.draw.ellipse(screen, (170, 155, 130),
                            (x - r, y + round(r * 0.65), r * 2, max(6, round(r * 0.6))))  # shadow
        pygame.draw.circle(screen, (45, 45, 55), (x, y), r + outline)                      # outline
        pygame.draw.circle(screen, (125, 130, 145), (x, y), r)                             # body
        pygame.draw.circle(screen, (180, 185, 198),
                           (x - round(r * 0.33), y - round(r * 0.36)), max(3, round(r * 0.3)))  # shine


def draw_targets():
    """Evenly spaced targets spinning around the targeted enemy while the circle
    expands and closes."""
    if target_index is None:
        return
    e = enemies[target_index]
    pulse = 1 + math.sin(target_bob_time * TARGET_BOB_SPEED) * TARGET_BOB_FRACTION
    ring = e.ring_radius * pulse
    for i in range(e.target_count):
        a = target_angle + i * 360 / e.target_count
        rad = math.radians(a)
        x = e.pos.x + ring * math.cos(rad)
        y = e.pos.y + ring * math.sin(rad)
        # target.png points UP; turn it so its tip faces the enemy (or away from it)
        rotation = (90 - a) if TARGET_POINT_INWARD else (270 - a)
        rotated = pygame.transform.rotate(target_img, rotation)
        screen.blit(rotated, rotated.get_rect(center=(round(x), round(y))))


dt = 1 / 120

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:  # clear canvas
                outline_layer.fill((0, 0, 0, 0))
                colour_layer.fill((0, 0, 0, 0))
                glow_positions.clear()
                glow_index = None
                result = None
            elif event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_q and enemies:
                target_index = pick_target(target_index)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            drawing = True
            last_pos = event.pos
            stroke_points = []
            glow_index = None
            paint(event.pos, event.pos)
            if inside_area(event.pos):          # only the red area counts
                stroke_points.append(event.pos)
                glow_positions.append(event.pos)  # glow for this stroke
                glow_index = len(glow_positions) - 1

        elif event.type == pygame.MOUSEMOTION and drawing:
            paint(last_pos, event.pos)
            last_pos = event.pos
            if inside_area(event.pos):
                stroke_points.append(event.pos)
                if glow_index is None:
                    glow_positions.append(event.pos)
                    glow_index = len(glow_positions) - 1
                else:
                    glow_positions[glow_index] = event.pos  # glow follows the latest point

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and drawing:
            drawing = False
            # glow stays on the last spot drawn before lifting the mouse
            if stroke_points:  # strokes made entirely outside the red area don't count
                result = recognize_shape(stroke_points)
                print("Shape drawn:", result[0], "|", result[1] or "-")

    update_player(min(dt, 0.05))
    target_angle = (target_angle + TARGET_SPIN_SPEED * min(dt, 0.05)) % 360
    target_bob_time += min(dt, 0.05)

    screen.fill(BG_COLOR)
    screen.blit(notebook_img, notebook_rect)  # the notebook sits under everything
    screen.blit(outline_layer, (0, 0))  # bottom
    screen.blit(colour_layer, (0, 0))   # middle
    screen.set_clip(notebook_rect)      # glows never spill outside the notebook
    for gp in glow_positions:           # top
        screen.blit(glow_img, glow_img.get_rect(center=gp))
    screen.set_clip(None)

    draw_enemies()
    draw_targets()
    draw_player()

    # Result label
    if result:
        screen.blit(font.render(f"You drew: {result[0]}", True, TEXT_COLOR), (20, 16))
        if result[1]:
            screen.blit(small_font.render(f"Orientation: {result[1]}", True, TEXT_COLOR), (20, 54))
    else:
        screen.blit(small_font.render("Draw a shape, then lift the mouse", True, TEXT_COLOR), (20, 20))

    pygame.display.flip()
    dt = clock.tick(120) / 1000

pygame.quit()