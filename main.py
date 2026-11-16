#!/usr/bin/env python3
"""ai-excited-01 — "The Jellyfish That Ate the Skyline".

A colossal bioluminescent jellyfish descends over a sleeping city at night:
one huge glowing bell, a curtain of tentacles, a beam of light falling on
the rooftops, and a tiny aeroplane for scale. Procedural, standard library
only, fully deterministic (same bytes every run). Writes
$MAKEFUN_OUTPUT_DIR/entry.png, 1024x1024.
"""
import binascii
import math
import os
import random
import struct
import zlib

W = 1024
H = 1024
SEED = 20261117
rng = random.Random(SEED)

buf = bytearray(W * H * 3)


def set_px(x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = r
        buf[i + 1] = g
        buf[i + 2] = b


def blend_px(x, y, r, g, b, a):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        ia = 1.0 - a
        buf[i] = int(buf[i] * ia + r * a)
        buf[i + 1] = int(buf[i + 1] * ia + g * a)
        buf[i + 2] = int(buf[i + 2] * ia + b * a)


def add_px(x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        v = buf[i] + r
        buf[i] = 255 if v > 255 else v
        v = buf[i + 1] + g
        buf[i + 1] = 255 if v > 255 else v
        v = buf[i + 2] + b
        buf[i + 2] = 255 if v > 255 else v


def lerp3(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


def disc(cx, cy, r, color, alpha=1.0):
    r = int(r)
    if r <= 0:
        return
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        dy = y - cy
        dx = int((r * r - dy * dy) ** 0.5)
        x0 = max(0, cx - dx)
        x1 = min(W - 1, cx + dx)
        for x in range(x0, x1 + 1):
            if alpha >= 1.0:
                set_px(x, y, *color)
            else:
                blend_px(x, y, *color, alpha)


def hline(x0, x1, y, color, alpha=1.0):
    if not (0 <= y < H):
        return
    for x in range(max(0, x0), min(W, x1 + 1)):
        if alpha >= 1.0:
            set_px(x, y, *color)
        else:
            blend_px(x, y, *color, alpha)


def rect(x0, y0, x1, y1, color, alpha=1.0):
    for y in range(max(0, y0), min(H, y1 + 1)):
        hline(x0, x1, y, color, alpha)


# ------------------------------------------------------------------- PNG out
def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += buf[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", comp) + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ------------------------------------------------------------------- sky
TOP = (8, 5, 36)       # deep indigo
MID = (30, 14, 84)     # violet
HOR = (14, 66, 92)     # teal at the horizon
for y in range(H):
    t = y / 1023.0
    if t < 0.6:
        c = lerp3(TOP, MID, t / 0.6)
    else:
        c = lerp3(MID, HOR, (t - 0.6) / 0.4)
    buf[y * W * 3:(y + 1) * W * 3] = bytes(c) * W

# stars
for _ in range(320):
    x = rng.randint(0, W - 1)
    y = rng.randint(0, 700)
    b = rng.randint(120, 255)
    if rng.random() < 0.7:
        set_px(x, y, b, b, min(255, b + 20))
    else:
        disc(x, y, 1, (b, b, min(255, b + 20)))
# a few bright cross sparkles
for _ in range(14):
    x = rng.randint(20, W - 20)
    y = rng.randint(20, 500)
    b = rng.randint(200, 255)
    hline(x - 4, x + 4, y, (b, b, 255), alpha=0.9)
    for dy in range(-4, 5):
        set_px(x, y + dy, b, b, 255)

# soft clouds: overlapping translucent discs in horizontal bands
for (cy0, n, col, a) in [(150, 9, (70, 55, 130), 0.10),
                         (260, 8, (55, 45, 115), 0.09),
                         (90, 7, (85, 60, 140), 0.08)]:
    cx = rng.randint(0, 200)
    for _ in range(n):
        disc(cx, cy0 + rng.randint(-8, 8), rng.randint(28, 60), col, alpha=a)
        cx += rng.randint(55, 110)

# ------------------------------------------------------------------- halo
def radial_glow(cx, cy, r, color, peak):
    """Soft additive halo, tight loop over the bounding box."""
    r2 = r * r
    x0 = max(0, cx - r)
    x1 = min(W - 1, cx + r)
    y0 = max(0, cy - r)
    y1 = min(H - 1, cy + r)
    cr, cg, cb = color
    for y in range(y0, y1 + 1):
        dy = y - cy
        base = (y * W) * 3
        for x in range(x0, x1 + 1):
            dx = x - cx
            d2 = dx * dx + dy * dy
            if d2 >= r2:
                continue
            d = (d2 ** 0.5) / r
            a = peak * (1.0 - d) * (1.0 - d)
            if a <= 0.004:
                continue
            i = base + x * 3
            ia = 1.0 - a
            buf[i] = int(buf[i] * ia + cr * a)
            buf[i + 1] = int(buf[i + 1] * ia + cg * a)
            buf[i + 2] = int(buf[i + 2] * ia + cb * a)


DCX, DCY, DRX, DRY = 512, 390, 335, 255
radial_glow(DCX, DCY, 430, (90, 160, 255), 0.34)
radial_glow(DCX, DCY - 40, 300, (190, 110, 255), 0.22)

# ------------------------------------------------------------------- the bell
CORE = (240, 255, 255)
MIDC = (110, 225, 255)
RIMC = (205, 95, 255)
for y in range(DCY - DRY, DCY + DRY + 1):
    ny = (y - DCY) / DRY
    span = DRX * (1.0 - ny * ny) ** 0.5
    x0 = int(DCX - span)
    x1 = int(DCX + span)
    top = 1.0 - (y - (DCY - DRY)) / (2.0 * DRY)  # 1 at the top of the bell
    base = (y * W) * 3
    for x in range(max(0, x0), min(W - 1, x1 + 1)):
        nx = (x - DCX) / DRX
        d = (nx * nx + ny * ny) ** 0.5
        if d < 0.45:
            c = lerp3(CORE, MIDC, d / 0.45)
        else:
            c = lerp3(MIDC, RIMC, (d - 0.45) / 0.55)
        lift = 0.20 * top * (1.0 - d)
        i = base + x * 3
        buf[i] = min(255, int(c[0] + 46 * lift))
        buf[i + 1] = min(255, int(c[1] + 30 * lift))
        buf[i + 2] = min(255, int(c[2] + 10 * lift))

# fine radial striations inside the bell (subtle, sunburst texture)
for k in range(72):
    ang = k * math.pi / 36.0
    ca, sa = math.cos(ang), math.sin(ang)
    for rr in range(55, 320, 4):
        x = int(DCX + rr * ca * (DRX / 335.0))
        y = int(DCY + rr * sa * (DRY / 255.0) * 0.92)
        blend_px(x, y, 120, 80, 220, 0.11)
        blend_px(x + 1, y, 120, 80, 220, 0.08)

# (no gonads: any pair of dots inside the bell reads as a face by
# accident, so the bell stays clean — its core glow is the heart)

# bright rim: a glowing arc along the top edge of the bell
for k in range(0, 181, 2):
    ang = math.pi * (1.0 + k / 180.0)  # top half, left to right
    x = int(DCX + DRX * math.cos(ang))
    y = int(DCY + DRY * math.sin(ang))
    add_px(x, y, 60, 70, 90)
    add_px(x, y + 1, 40, 50, 70)
    if k % 6 == 0:
        disc(x, y, 2, (220, 250, 255), alpha=0.8)

# scalloped lower margin: soft beads along the bottom edge, kept subtle
for k in range(8, 173, 9):
    ang = math.pi * k / 180.0  # bottom half
    x = int(DCX + DRX * math.cos(ang))
    y = int(DCY + DRY * math.sin(ang))
    disc(x, y, 8, (170, 70, 230), alpha=0.5)
    disc(x, y - 3, 4, (230, 130, 255), alpha=0.45)

# ------------------------------------------------------------------- tentacles
def tentacle(x0, y0, length, amp, period, phase, r0, r1, col_top, col_bot,
             alpha=0.9, frill=0.0):
    steps = int(length / 3)
    for i in range(steps + 1):
        t = i / steps
        y = y0 + t * length
        x = x0 + amp * math.sin(phase + (y - y0) / period * 2 * math.pi) * t
        r = r0 + (r1 - r0) * t
        if frill:
            r *= 1.0 + frill * math.sin(i / 2.2)
        c = lerp3(col_top, col_bot, t)
        disc(int(x), int(y), max(1, int(r)), c, alpha * (1.0 - 0.55 * t))


CYAN_T, CYAN_B = (105, 225, 255), (60, 130, 255)
MAG_T, MAG_B = (255, 120, 220), (175, 60, 255)
# thin curtain tentacles from the bell margin
starts = []
for k in range(16):
    fx = -0.92 + 1.84 * k / 15.0
    sx = int(DCX + DRX * fx)
    sy = int(DCY + DRY * (1.0 - fx * fx) ** 0.5 * 0.96)
    starts.append((sx, sy))
for k, (sx, sy) in enumerate(starts):
    if k % 2 == 0:
        ct, cb = CYAN_T, CYAN_B
    else:
        ct, cb = MAG_T, MAG_B
    tentacle(sx, sy, rng.randint(230, 380), rng.randint(12, 30),
             rng.randint(120, 200), rng.uniform(0, 6.28),
             rng.randint(4, 6), 1, ct, cb)
# glowing beads strung along some tentacles
for k in (1, 4, 7, 10, 13):
    sx, sy = starts[k]
    for d in range(60, 300, 46):
        y = sy + d
        x = int(sx + 18 * math.sin(d / 55.0 + k))
        disc(x, y, 3, (220, 255, 255), alpha=0.95)
        add_px(x, y, 30, 40, 50)
# four thick frilly oral arms in the centre
for k, ox in enumerate((-90, -30, 30, 90)):
    tentacle(DCX + ox, DCY + 200, rng.randint(260, 330),
             rng.randint(10, 18), rng.randint(140, 190),
             rng.uniform(0, 6.28), 12, 3,
             (255, 150, 205), (230, 80, 200), alpha=0.92, frill=0.35)

# ------------------------------------------------------------------- light beam
# a soft cone of light falling from the bell onto the rooftops
for y in range(640, 940):
    t = (y - 640) / 300.0
    cx = DCX
    half = 90 + 130 * t
    a = 0.10 * (1.0 - t * 0.6)
    hline(int(cx - half), int(cx + half), y, (190, 240, 255), alpha=a)
    hline(int(cx - half * 0.45), int(cx + half * 0.45), y,
          (220, 250, 255), alpha=a * 1.1)
# pool of light on the rooftops
for rr in range(200, 0, -6):
    disc(DCX, 935, rr, (170, 220, 255), alpha=0.06)

# ------------------------------------------------------------------- city
# dark skyline silhouettes along the bottom edge, lit windows, neon roofs
bx = 0
while bx < W:
    if rng.random() < 0.55:
        bw = rng.randint(18, 48)
        bh = rng.randint(30, 112)
        if rng.random() < 0.08:
            bh = rng.randint(130, 175)  # a tower
        by = H - bh
        rect(bx, by, bx + bw, H - 1, (7, 9, 26))
        if rng.random() < 0.35:
            neon = rng.choice([(0, 255, 240), (255, 60, 200),
                               (255, 210, 60)])
            hline(bx, bx + bw, by, neon, alpha=0.9)
        for wy in range(by + 8, H - 6, 10):
            for wx in range(bx + 4, bx + bw - 3, 9):
                if rng.random() < 0.45:
                    wc = rng.choice([(255, 210, 120), (140, 230, 255),
                                     (255, 150, 220)])
                    rect(wx, wy, wx + 3, wy + 4, wc, alpha=0.95)
        if bh >= 130:  # aircraft-warning beacon on tall towers
            disc(bx + bw // 2, by - 3, 3, (255, 60, 60))
            add_px(bx + bw // 2, by - 3, 60, 20, 20)
        bx += bw + rng.randint(0, 6)
    else:
        bx += rng.randint(6, 20)

# ------------------------------------------------------------------- scale cues
# a tiny aeroplane crossing the sky beside the bell
AX, AY = 845, 285
rect(AX - 14, AY - 1, AX + 14, AY + 1, (12, 12, 30))
rect(AX - 3, AY - 7, AX + 3, AY + 7, (12, 12, 30))
set_px(AX + 12, AY, 255, 255, 255)
set_px(AX - 12, AY, 255, 60, 60)
# faint contrail behind it
for i in range(1, 90, 2):
    blend_px(AX - 16 - i, AY + i // 22, 220, 230, 255, 0.10 * (1 - i / 90.0))
# a few tiny birds
for (bxx, byy) in [(180, 210), (210, 235), (150, 250), (700, 180)]:
    for d in range(0, 6):
        set_px(bxx - d, byy - d // 2, 200, 210, 255)
        set_px(bxx + d, byy - d // 2, 200, 210, 255)

# ------------------------------------------------------------------- LOOK UP.
FONT = {
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    'O': ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    'K': ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    'U': ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    'P': ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    '.': ["00000", "00000", "00000", "00000", "00000", "00000", "00100"],
    ' ': ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}
SCALE = 7
OX, OY = 48, 48
word = "LOOK UP."
cw = 5 * SCALE + SCALE
for ci, ch in enumerate(word):
    glyph = FONT[ch]
    for gy, row in enumerate(glyph):
        for gx, bit in enumerate(row):
            if bit != '1':
                continue
            px = OX + ci * cw + gx * SCALE
            py = OY + gy * SCALE
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2),
                           (-2, -2), (2, -2), (-2, 2), (2, 2)):
                rect(px + ox, py + oy, px + ox + SCALE - 1,
                     py + oy + SCALE - 1, (12, 10, 50))
            rect(px, py, px + SCALE - 1, py + SCALE - 1, (205, 250, 255))

# ------------------------------------------------------------------- vignette
colf = [1.0 - 0.14 * ((x - 512) / 512.0) ** 2 for x in range(W)]
for y in range(H):
    rf = 1.0 - 0.14 * ((y - 512) / 512.0) ** 2
    base = (y * W) * 3
    for x in range(W):
        f = rf * colf[x]
        i = base + x * 3
        buf[i] = int(buf[i] * f)
        buf[i + 1] = int(buf[i + 1] * f)
        buf[i + 2] = int(buf[i + 2] * f)

# ------------------------------------------------------------------- run
if __name__ == "__main__":
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    size = write_png(os.path.join(outdir, "entry.png"))
    print(f"wrote entry.png ({size} bytes)")
