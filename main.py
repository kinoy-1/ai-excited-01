#!/usr/bin/env python3
"""ai-excited-01 — "The Koi That Swallowed the Moon".

Generates a 1024x1024 PNG procedurally (standard library only) and writes it
to $MAKEFUN_OUTPUT_DIR/entry.png. Fully deterministic: same bytes every run.
"""
import binascii
import os
import random
import struct
import zlib

W = 1024
H = 1024
SEED = 20261116

rng = random.Random(SEED)

# ---------------------------------------------------------------- pixel buffer
buf = bytearray(W * H * 3)


def idx(x, y):
    return (y * W + x) * 3


def set_px(x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = idx(x, y)
        buf[i] = r
        buf[i + 1] = g
        buf[i + 2] = b


def blend_px(x, y, r, g, b, a):
    """Alpha-blend a colour over the pixel (a in 0..1)."""
    if 0 <= x < W and 0 <= y < H:
        i = idx(x, y)
        ia = 1.0 - a
        buf[i] = int(buf[i] * ia + r * a)
        buf[i + 1] = int(buf[i + 1] * ia + g * a)
        buf[i + 2] = int(buf[i + 2] * ia + b * a)


def add_px(x, y, r, g, b):
    """Additive glow, clamped at 255."""
    if 0 <= x < W and 0 <= y < H:
        i = idx(x, y)
        buf[i] = min(255, buf[i] + r)
        buf[i + 1] = min(255, buf[i + 1] + g)
        buf[i + 2] = min(255, buf[i + 2] + b)


def lerp(c1, c2, t):
    return tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))


def disc(cx, cy, r, color, alpha=1.0):
    """Filled circle (integer centre/radius)."""
    r = int(r)
    if r <= 0:
        return
    for y in range(cy - r, cy + r + 1):
        dy = y - cy
        dx = int((r * r - dy * dy) ** 0.5)
        for x in range(cx - dx, cx + dx + 1):
            if alpha >= 1.0:
                set_px(x, y, *color)
            else:
                blend_px(x, y, *color, alpha)


def radial_disc(cx, cy, r, inner, outer):
    """Disc shaded by distance from centre (inner -> outer colour)."""
    r = int(r)
    for y in range(cy - r, cy + r + 1):
        dy = y - cy
        span = (r * r - dy * dy) ** 0.5
        dx = int(span)
        for x in range(cx - dx, cx + dx + 1):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / r
            set_px(x, y, *lerp(inner, outer, min(1.0, d)))


def hline(x0, x1, y, color, alpha=1.0):
    for x in range(max(0, x0), min(W, x1 + 1)):
        if alpha >= 1.0:
            set_px(x, y, *color)
        else:
            blend_px(x, y, *color, alpha)


def rect(x0, y0, x1, y1, color, alpha=1.0):
    for y in range(max(0, y0), min(H, y1 + 1)):
        hline(x0, x1, y, color, alpha)


def tri(p0, p1, p2, color, alpha=1.0):
    """Filled triangle via scanline interpolation."""
    pts = sorted([p0, p1, p2], key=lambda p: p[1])
    (ax, ay), (bx, by), (cx, cy) = pts
    if ay == cy:
        return
    for y in range(max(0, ay), min(H, cy + 1)):
        if y < by:
            t1 = (y - ay) / (by - ay) if by != ay else 0.0
            xa = ax + (bx - ax) * t1
        else:
            t1 = (y - by) / (cy - by) if cy != by else 0.0
            xa = bx + (cx - bx) * t1
        t2 = (y - ay) / (cy - ay)
        xb = ax + (cx - ax) * t2
        hline(int(min(xa, xb)), int(max(xa, xb)), y, color, alpha)


def bez(p0, p1, p2, p3, t):
    u = 1.0 - t
    x = (u ** 3 * p0[0] + 3 * u * u * t * p1[0]
         + 3 * u * t * t * p2[0] + t ** 3 * p3[0])
    y = (u ** 3 * p0[1] + 3 * u * u * t * p1[1]
         + 3 * u * t * t * p2[1] + t ** 3 * p3[1])
    return x, y


# ------------------------------------------------------------------- sky
TOP = (26, 8, 64)        # deep violet
MID = (58, 24, 110)      # violet
HOR = (14, 90, 110)      # teal at the horizon
for y in range(H):
    t = y / (H - 1)
    if t < 0.62:
        c = lerp(TOP, MID, t / 0.62)
    else:
        c = lerp(MID, HOR, (t - 0.62) / 0.38)
    for x in range(W):
        set_px(x, y, *c)

# stars
for _ in range(260):
    x = rng.randint(0, W - 1)
    y = rng.randint(0, 620)
    b = rng.randint(120, 255)
    s = rng.random()
    if s < 0.7:
        set_px(x, y, b, b, min(255, b + 20))
    else:
        disc(x, y, 1, (b, b, min(255, b + 20)))

# aurora ribbons (translucent sine bands, cyan / magenta / violet)
for (r, g, b), amp, base, per, _a in [
        ((64, 224, 208), 26, 300, 210, 0.55),
        ((216, 64, 220), 20, 210, 260, 0.5),
        ((140, 90, 255), 30, 120, 320, 0.45)]:
    import math
    for x in range(0, W, 2):
        yc = base + amp * math.sin(x / per)
        for dy in range(-26, 27):
            fall = 1.0 - abs(dy) / 27.0
            blend_px(x, int(yc) + dy, r, g, b, 0.16 * fall * fall)
            blend_px(x + 1, int(yc) + dy, r, g, b, 0.16 * fall * fall)

# ------------------------------------------------------------------- moon
import math
MOON = (758, 268)
MOON_R = 196
# violet-gold halo
for rr in range(MOON_R + 90, MOON_R, -2):
    a = 0.05 * (1.0 - (rr - MOON_R) / 90.0)
    disc(*MOON, rr, (150, 110, 255), alpha=a)
radial_disc(*MOON, MOON_R, (255, 246, 214), (255, 196, 90))
# craters: soft darker gold discs
for _ in range(14):
    a = rng.uniform(0, 2 * math.pi)
    d = rng.uniform(0, MOON_R * 0.72)
    cx = int(MOON[0] + d * math.cos(a))
    cy = int(MOON[1] + d * math.sin(a))
    cr = rng.randint(8, 26)
    disc(cx, cy, cr, (232, 168, 74), alpha=0.35)
# bright core glow (colours kept close to the moon body so no hard edge shows)
radial_disc(*MOON, int(MOON_R * 0.62), (255, 250, 230), (255, 208, 115))

# ------------------------------------------------------------------- ocean
# dark indigo sea from the horizon down, with a diagonal swell rising left
SEA_TOP = (10, 26, 78)
SEA_BOT = (4, 8, 34)
for y in range(760, H):
    t = (y - 760) / (H - 760)
    c = lerp(SEA_TOP, SEA_BOT, t)
    for x in range(W):
        set_px(x, y, *c)
# soft glow where sea meets sky (no hard horizon line)
for x in range(0, W, 3):
    for dy in range(-8, 9):
        fall = 1.0 - abs(dy) / 9.0
        blend_px(x, 760 + dy, 60, 120, 190, 0.10 * fall)
# gentle wave strokes across the sea
for wy in (800, 850, 905, 960):
    for x in range(0, W, 2):
        yy = wy + int(6 * math.sin(x / 47.0 + wy))
        blend_px(x, yy, 70, 170, 230, 0.16)
        blend_px(x, yy + 2, 70, 170, 230, 0.08)
for x in range(0, 560):
    wy = 800 - int(0.28 * x) + int(14 * math.sin(x / 55.0))
    for dy in range(0, 26):
        fall = 1.0 - dy / 26.0
        blend_px(x, wy + dy, 40, 140, 200, 0.20 * fall)
        blend_px(x, wy + dy + 3, 120, 220, 255, 0.10 * fall)
# moonlight path on the water
for y in range(770, H, 2):
    wdt = 26 + (y - 770) // 6
    cx = MOON[0]
    for x in range(cx - wdt, cx + wdt + 1):
        flick = 0.5 + 0.5 * math.sin(x / 9.0 + y / 23.0)
        blend_px(x, y, 255, 200, 110, 0.10 * flick)
        blend_px(x, y + 1, 255, 200, 110, 0.06 * flick)

# ------------------------------------------------------------------- city
# tiny neon-lit coastal city along the bottom edge
for bx in range(8, W - 30, 1):
    if rng.random() < 0.42:
        bw = rng.randint(14, 42)
        bh = rng.randint(18, 74)
        by = H - bh
        rect(bx, by, bx + bw, H - 1, (8, 10, 30))
        # roof neon strip
        neon = rng.choice([(0, 255, 240), (255, 60, 200), (255, 210, 60)])
        hline(bx, bx + bw, by, neon, alpha=0.9)
        # lit windows
        for wy in range(by + 6, H - 6, 9):
            for wx in range(bx + 4, bx + bw - 3, 8):
                if rng.random() < 0.5:
                    wc = rng.choice([(255, 220, 120), (150, 240, 255),
                                     (255, 150, 220)])
                    rect(wx, wy, wx + 3, wy + 4, wc, alpha=0.95)
        bx += bw

# ------------------------------------------------------------------- koi
# body arc: cubic bezier from tail (bottom-left) to head (against the moon).
# Control points bow the body well above the straight chord: a true leap.
P0 = (150, 830)   # tail tip
P1 = (280, 600)
P2 = (420, 330)
P3 = (700, 330)   # head, overlapping the moon's lower-left edge
GOLD = (255, 196, 60)
EMBER = (255, 110, 40)
BELLY = (255, 226, 150)
MAGENTA = (235, 40, 160)

# tail fin: broad layered fan of magenta triangles behind the tail tip
for k, ang in enumerate([-1.1, -0.55, 0.0, 0.55, 1.1]):
    L = 195 - abs(ang) * 60
    dx = math.cos(ang + math.pi) * L
    dy = math.sin(ang + math.pi) * L * 0.55
    tip = (int(P0[0] + dx), int(P0[1] + dy))
    side = (int(P0[0] - dy * 0.22), int(P0[1] + dx * 0.22))
    side2 = (int(P0[0] + dy * 0.22), int(P0[1] - dx * 0.22))
    col = lerp(MAGENTA, (255, 110, 200), k / 4.0)
    tri(side, side2, tip, col, alpha=0.92)

# body: chain of overlapping circles, radius tapering toward tail and head
# (dense chain so the body reads smooth, not ribbed)
N = 150
prev = None
for i in range(N + 1):
    t = i / N
    x, y = bez(P0, P1, P2, P3, t)
    # slim at tail (t=0) and head (t=1), fat in the middle: a real fish shape
    r = 16 + 62 * math.sin(math.pi * (0.08 + 0.84 * t))
    # colour: gold on the back, ember toward the belly
    top_c = lerp(GOLD, (255, 150, 30), t * 0.4)
    disc(int(x), int(y), int(r), top_c)
    disc(int(x), int(y + r * 0.42), int(r * 0.58), BELLY, alpha=0.30)
    prev = (x, y, r)

# dorsal fin along the top of the arc: small swept-back magenta ridge
for i in range(8, N - 20, 6):
    t = i / N
    x, y = bez(P0, P1, P2, P3, t)
    r = 16 + 62 * math.sin(math.pi * (0.08 + 0.84 * t))
    tri((int(x - 12), int(y - r + 6)), (int(x + 12), int(y - r + 6)),
        (int(x + 10), int(y - r - 22)), MAGENTA, alpha=0.9)

# scale hints: small arcs of darker gold along the body
for i in range(6, N - 4, 4):
    t = i / N
    x, y = bez(P0, P1, P2, P3, t)
    r = 16 + 62 * math.sin(math.pi * (0.08 + 0.84 * t))
    for a in range(0, 7):
        ang = math.pi * (0.15 + a / 6.0 * 0.7)
        sx = int(x + r * 0.62 * math.cos(ang))
        sy = int(y + r * 0.62 * math.sin(ang))
        set_px(sx, sy, 200, 120, 20)

# pectoral fin (magenta, sweeping down-back from mid-body)
mx, my = bez(P0, P1, P2, P3, 0.72)
tri((int(mx - 8), int(my + 20)), (int(mx + 22), int(my + 30)),
    (int(mx - 26), int(my + 100)), MAGENTA, alpha=0.92)
tri((int(mx - 8), int(my + 20)), (int(mx + 22), int(my + 30)),
    (int(mx + 4), int(my + 92)), (255, 110, 200), alpha=0.85)

# head: a distinct rounded head disc over the end of the body chain
hx, hy = P3
disc(int(hx + 4), int(hy + 2), 44, GOLD)
disc(int(hx + 4), int(hy + 16), 30, BELLY, alpha=0.4)
# snout shading toward the moon
disc(int(hx + 30), int(hy - 4), 18, (255, 214, 110))
# eye + mouth + gill
disc(int(hx - 6), int(hy - 14), 17, (255, 255, 255))
disc(int(hx - 4), int(hy - 14), 9, (10, 10, 30))
disc(int(hx - 1), int(hy - 17), 3, (255, 255, 255))
# gill curve
for a in range(0, 13):
    ang = math.pi * (0.1 + a / 12.0 * 0.8)
    gx = int(hx - 34 + 16 * math.cos(ang))
    gy = int(hy + 6 + 20 * math.sin(ang))
    set_px(gx, gy, 200, 80, 20)
    set_px(gx + 1, gy, 200, 80, 20)
# whiskers
for sgn in (1, -1):
    for k in range(1, 26):
        wx = int(hx + 30 + k * 2.4)
        wy = int(hy + 26 + sgn * k * 1.1 + 4 * math.sin(k / 4.0))
        blend_px(wx, wy, 255, 220, 140, 0.8)

# ------------------------------------------------------------------- spray
# glowing spray exploding where the koi burst out of the water
BX, BY = 210, 780
for _ in range(900):
    a = rng.uniform(-math.pi, 0.15)
    d = rng.uniform(0, 1) ** 0.6 * 260
    x = int(BX + d * math.cos(a))
    y = int(BY + d * math.sin(a) * 0.75)
    if y < 560:
        continue
    b = rng.randint(140, 255)
    col = rng.choice([(b, 240, 255), (255, 255, 255), (180, 220, 255)])
    r = 1 if rng.random() < 0.8 else 2
    disc(x, y, r, col)
    if rng.random() < 0.25:
        add_px(x, y, 40, 60, 60)
# big spray arcs
for _ in range(46):
    a = rng.uniform(-math.pi * 0.95, -math.pi * 0.05)
    d = rng.uniform(60, 300)
    x = int(BX + d * math.cos(a))
    y = int(BY + d * math.sin(a) * 0.8)
    disc(x, y, rng.randint(2, 4), (200, 245, 255), alpha=0.85)

# ------------------------------------------------------------------- WOW!
FONT = {
    'W': ["11111", "10001", "10001", "10101", "10101", "01010", "01010"],
    'O': ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    '!': ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
}
SCALE = 9
OX, OY = 52, 52
word = "WOW!"
cw = 5 * SCALE + SCALE  # char width incl. gap
for ci, ch in enumerate(word):
    glyph = FONT[ch]
    for gy, row in enumerate(glyph):
        for gx, bit in enumerate(row):
            if bit != '1':
                continue
            px = OX + ci * cw + gx * SCALE
            py = OY + gy * SCALE
            # dark outline: draw block offset in 8 directions first
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2),
                           (-2, -2), (2, -2), (-2, 2), (2, 2)):
                rect(px + ox, py + oy, px + ox + SCALE - 1,
                     py + oy + SCALE - 1, (20, 8, 60))
            rect(px, py, px + SCALE - 1, py + SCALE - 1, (255, 205, 60))

# ------------------------------------------------------------------- PNG out
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    c += struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)
    return c


def write_png(path):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += buf[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


if __name__ == "__main__":
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    size = write_png(os.path.join(outdir, "entry.png"))
    print(f"wrote entry.png ({size} bytes)")
