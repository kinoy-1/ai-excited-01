#!/usr/bin/env python3
"""ai-excited-01 round 3 — "RISE."
A colossal phoenix of fire rising over a dark night sea.
One idea, instantly readable: wings span the whole frame, tail ribbons
of flame stream down into the water, embers fill the air, and the word
RISE. anchors the bottom.

Pure Python stdlib only. Hand-written PNG encoder (zlib + struct).
Fixed seed -> fully deterministic: two runs produce identical bytes.
Run:  python3 main.py   (writes entry.png, 1024x1024)
"""
import math
import random
import struct
import zlib

W = H = 1024
SEED = 20261116

buf = bytearray(W * H * 3)


def lerp(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


def span(x0, x1, y, color):
    """Fill a horizontal run with a solid color (fast slice assign)."""
    x0 = max(0, int(x0))
    x1 = min(W - 1, int(x1))
    if x1 < x0 or y < 0 or y >= H:
        return
    i = (y * W + x0) * 3
    buf[i:i + (x1 - x0 + 1) * 3] = bytes(color) * (x1 - x0 + 1)


def span_alpha(x0, x1, y, color, a):
    x0 = max(0, int(x0))
    x1 = min(W - 1, int(x1))
    if x1 < x0 or y < 0 or y >= H or a <= 0:
        return
    for x in range(x0, x1 + 1):
        blend_px(x, y, color, a)


def blend_px(x, y, color, a):
    if a <= 0 or x < 0 or x >= W or y < 0 or y >= H:
        return
    i = (y * W + x) * 3
    inv = 255 - a
    buf[i] = (color[0] * a + buf[i] * inv) // 255
    buf[i + 1] = (color[1] * a + buf[i + 1] * inv) // 255
    buf[i + 2] = (color[2] * a + buf[i + 2] * inv) // 255


def fill_poly(pts, color):
    """Scanline polygon fill."""
    ys = [p[1] for p in pts]
    y0 = max(0, int(min(ys)))
    y1 = min(H - 1, int(max(ys)))
    n = len(pts)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x0, ya = pts[i]
            x1, yb = pts[(i + 1) % n]
            if (ya <= y < yb) or (yb <= y < ya):
                t = (y - ya) / (yb - ya)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            span(xs[k], xs[k + 1], y, color)


def ellipse_poly(cx, cy, rx, ry, rot_deg=0.0, n=30):
    rot = math.radians(rot_deg)
    cr, sr = math.cos(rot), math.sin(rot)
    pts = []
    for k in range(n):
        t = 2.0 * math.pi * k / n
        ex, ey = rx * math.cos(t), ry * math.sin(t)
        pts.append((cx + ex * cr - ey * sr, cy + ex * sr + ey * cr))
    return pts


def fill_ellipse(cx, cy, rx, ry, color, rot_deg=0.0):
    fill_poly(ellipse_poly(cx, cy, rx, ry, rot_deg), color)


def radial_glow(cx, cy, rx, ry, color, peak):
    """Soft radial glow: one clipped pass over the bounding box."""
    x0 = max(0, int(cx - rx))
    x1 = min(W - 1, int(cx + rx))
    y0 = max(0, int(cy - ry))
    y1 = min(H - 1, int(cy + ry))
    for y in range(y0, y1 + 1):
        dy = (y - cy) / ry
        dy2 = dy * dy
        for x in range(x0, x1 + 1):
            dx = (x - cx) / rx
            d2 = dx * dx + dy2
            if d2 < 1.0:
                blend_px(x, y, color, int(peak * (1.0 - d2)))


# ---------------------------------------------------------------- sky & sea

def draw_sky(rng):
    top = (7, 11, 36)
    mid = (20, 16, 66)
    low = (58, 24, 78)
    for y in range(0, 830):
        if y < 420:
            c = lerp(top, mid, y / 420.0)
        else:
            c = lerp(mid, low, (y - 420) / 410.0)
        span(0, W - 1, y, c)
    # stars, upper sky only
    for _ in range(170):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, 690)
        s = rng.random()
        if s < 0.6:
            col = (255, 255, 255)
        elif s < 0.85:
            col = (170, 200, 255)
        else:
            col = (255, 220, 160)
        a = rng.randint(80, 200)
        blend_px(x, y, col, a)
        if rng.random() < 0.12:
            blend_px(x + 1, y, col, a // 2)
            blend_px(x, y + 1, col, a // 2)


def draw_sea(rng):
    # soft transition from the warm sky down into the dark water
    for y in range(800, 870):
        span(0, W - 1, y, lerp((58, 24, 78), (6, 16, 38), (y - 800) / 70.0))
    for y in range(870, H):
        span(0, W - 1, y, lerp((6, 16, 38), (2, 6, 18), (y - 870) / 154.0))
    # wave strokes
    for _ in range(26):
        y = rng.randint(845, 1010)
        x = rng.randint(0, 800)
        ln = rng.randint(40, 190)
        col = (14, 42, 84) if rng.random() < 0.7 else (255, 138, 0)
        a = rng.randint(40, 120)
        for xx in range(x, min(W, x + ln)):
            blend_px(xx, y, col, a)
    # orange fire reflection under the phoenix
    for _ in range(260):
        x = int(rng.gauss(512, 60))
        y = rng.randint(835, 1010)
        blend_px(x, y, (255, 122, 0), rng.randint(30, 110))


# ---------------------------------------------------------------- phoenix

def ribbon(x0, phase, width, color):
    """One flowing tail ribbon: sine-swayed tapered strip, y 610 -> 1010."""
    left, right = [], []
    steps = 26
    for s in range(steps + 1):
        t = s / steps
        y = 610 + t * 285
        cx = x0 + 80 * math.sin(t * 2.4 + phase) * t
        w = width * (1.0 - 0.72 * t)
        left.append((cx - w, y))
        right.append((cx + w, y))
    fill_poly(left + right[::-1], color)


def wing(mirror):
    """One wing. mirror=False -> left wing; True -> right wing."""
    m = -1 if mirror else 1

    def X(x):
        return 512 + m * (x - 512)

    # base layer (deep red)
    base = [(440, 430), (310, 320), (180, 255), (95, 250),
            (150, 350), (260, 450), (430, 490)]
    fill_poly([(X(x), y) for x, y in base], (150, 18, 8))
    # mid layer (flame red)
    mid = [(445, 435), (330, 345), (220, 290), (150, 290),
           (210, 375), (300, 445), (435, 470)]
    fill_poly([(X(x), y) for x, y in mid], (222, 52, 0))
    # feather row along the trailing edge
    for i in range(7):
        t = i / 6.0
        fx = 190 + t * 250
        fy = 380 + t * 95 + (8 if i % 2 else 0)
        col = (255, 138, 0) if i % 2 == 0 else (255, 179, 0)
        fill_ellipse(X(fx), fy, 72, 20, col, rot_deg=m * -42)
    # long primary tips fanning out
    for i, (tx, ty, rot) in enumerate([(150, 260, -38),
                                       (110, 285, -52),
                                       (85, 320, -66)]):
        col = (255, 106, 0) if i % 2 == 0 else (255, 179, 0)
        fill_ellipse(X(tx), ty, 95, 17, col, rot_deg=m * rot)


def draw_body():
    # POLISH (round 3): the old body read as a flat oval "egg" because the
    # bright core sat dead-centre in concentric rings. Fix, same palette
    # and composition:
    #  1. bright core drops to the BELLY (low, small) — glowing belly,
    #     not a target centre;
    #  2. dark flank shading gives the torso roundness/depth;
    #  3. overlapping flank feathers + flame tufts scallop the outline
    #     so the silhouette is no longer a smooth oval;
    #  4. head slightly larger, two-tone beak, brow + cheek.
    # --- torso base: deep red shell
    fill_ellipse(512, 505, 96, 168, (150, 18, 8))
    # dark flank shading: roundness, edges darker than the centre
    fill_ellipse(436, 515, 20, 128, (96, 8, 4))
    fill_ellipse(588, 515, 20, 128, (96, 8, 4))
    # warm mid layers, sinking toward the belly
    fill_ellipse(512, 520, 70, 135, (222, 52, 0))
    fill_ellipse(512, 540, 50, 105, (255, 106, 0))
    # bright belly core (low) + cream heart
    fill_ellipse(512, 578, 32, 68, (255, 210, 63))
    fill_ellipse(512, 588, 15, 38, (255, 240, 160))
    # chest flame flickers: small gold tongues on the upper chest
    # (upward = flame licks; the dark chevrons read as a stray face)
    for cx, cy in [(486, 470), (538, 470), (512, 496)]:
        fill_poly([(cx - 10, cy + 10), (cx, cy - 12), (cx + 10, cy + 10)],
                  (255, 210, 63))
    # flank feathers: overlapping flame feathers sticking OUT past the
    # oval edge — breaks the silhouette on both sides (symmetric)
    for side in (-1, 1):
        for i, (fy, fr) in enumerate([(448, 42), (498, 50),
                                      (548, 55), (598, 48), (640, 38)]):
            fx = 512 + side * 78
            col = (255, 138, 0) if i % 2 == 0 else (255, 179, 0)
            fill_ellipse(fx, fy, 46, 15, col, rot_deg=side * fr)
    # flame tufts past the bottom edge, over the tail ribbons
    fill_poly([(470, 668), (462, 622), (484, 662)], (222, 52, 0))
    fill_poly([(512, 682), (502, 632), (524, 672)], (255, 138, 0))
    fill_poly([(554, 668), (544, 622), (562, 662)], (222, 52, 0))
    # dark collar at the neck base hides the neck/body seam
    fill_ellipse(512, 392, 58, 30, (150, 18, 8))
    # neck (tapered) + darker left edge for depth
    fill_poly([(490, 385), (534, 385), (545, 300), (505, 290)], (255, 138, 0))
    fill_poly([(500, 380), (528, 380), (534, 305), (510, 298)], (255, 179, 0))
    fill_poly([(490, 385), (498, 385), (505, 300), (498, 292)], (200, 40, 0))
    # head: slightly larger, rounder
    fill_ellipse(522, 260, 46, 37, (255, 179, 0))
    # cheek patch below the eye
    fill_ellipse(528, 278, 16, 10, (255, 150, 0))
    # beak, two-tone: gold upper + darker lower, pointing up-right
    fill_poly([(550, 246), (600, 256), (550, 268)], (255, 210, 63))
    fill_poly([(550, 268), (592, 264), (552, 278)], (200, 90, 0))
    # brow line above the eye (fierce, defined)
    fill_poly([(512, 244), (542, 238), (544, 246), (514, 252)], (150, 18, 8))
    # eye + glint
    fill_ellipse(532, 254, 7, 7, (26, 10, 0))
    blend_px(534, 252, (255, 255, 255), 220)
    # crest: three flame feathers (slightly longer)
    fill_poly([(505, 238), (490, 172), (515, 225)], (255, 106, 0))
    fill_poly([(522, 234), (520, 158), (542, 228)], (255, 179, 0))
    fill_poly([(538, 240), (558, 182), (558, 232)], (255, 210, 63))


def draw_embers(rng):
    for _ in range(240):
        x = rng.randint(60, 964)
        y = rng.randint(140, 960)
        r = rng.random()
        if r < 0.5:
            col = (255, 210, 63)
        elif r < 0.8:
            col = (255, 138, 0)
        else:
            col = (255, 45, 120)
        a = rng.randint(100, 220)
        s = 1 if rng.random() < 0.7 else 2
        for dx in range(s):
            for dy in range(s):
                blend_px(x + dx, y + dy, col, a)
        if rng.random() < 0.15:  # short falling streak
            for k in range(1, 5):
                blend_px(x, y + k, col, a // (k + 1))
    # a few big glowing embers
    for _ in range(6):
        x = rng.randint(150, 874)
        y = rng.randint(200, 850)
        radial_glow(x, y, 10, 10, (255, 150, 0), 120)


# ---------------------------------------------------------------- pixel text

FONT = {
    'R': ["01110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'I': ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    'S': ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    '.': ["00000", "00000", "00000", "00000", "00000", "00110", "00110"],
}


def draw_text(text, x0, y0, scale, color):
    x = x0
    for ch in text:
        glyph = FONT[ch]
        for ri, row in enumerate(glyph):
            for ci, bit in enumerate(row):
                if bit == '1':
                    for dy in range(scale):
                        span(x + ci * scale, x + (ci + 1) * scale - 1,
                             y0 + ri * scale + dy, color)
        x += 6 * scale


def draw_title():
    scale = 11
    width = 5 * 6 * scale - scale  # "RISE." = 5 glyphs
    x0 = 512 - width // 2
    y0 = 895
    # dark band behind the text so it reads over ribbons + sea
    for y in range(880, 986):
        span_alpha(320, 704, y, (2, 6, 16), 110)
    # outline (4 offsets) then gold face
    for ox, oy in [(-4, 0), (4, 0), (0, -4), (0, 4)]:
        draw_text("RISE.", x0 + ox, y0 + oy, scale, (20, 6, 2))
    draw_text("RISE.", x0, y0, scale, (255, 210, 63))


# ---------------------------------------------------------------- PNG writer

def write_png(path, w, h, data):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter: none
        raw += data[y * stride:(y + 1) * stride]
    compressed = zlib.compress(bytes(raw), 6)

    def chunk(typ, payload):
        out = struct.pack(">I", len(payload)) + typ + payload
        out += struct.pack(">I", zlib.crc32(typ + payload) & 0xFFFFFFFF)
        return out

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    rng = random.Random(SEED)
    draw_sky(rng)
    # warm horizon glow, then the sea over its lower half
    radial_glow(512, 800, 520, 240, (255, 90, 0), 85)
    draw_sea(rng)
    # big fire glow behind the phoenix
    radial_glow(512, 470, 430, 400, (255, 110, 0), 110)
    # tail ribbons (behind body): dark, mid, bright core per ribbon
    for x0, ph in [(400, 0.0), (445, 0.9), (480, 1.8), (512, 2.7),
                   (544, 3.6), (579, 4.5), (624, 5.4)]:
        ribbon(x0, ph, 26, (200, 40, 0))
        ribbon(x0, ph, 15, (255, 138, 0))
        ribbon(x0, ph, 7, (255, 210, 63))
    wing(False)
    wing(True)
    draw_body()
    draw_embers(rng)
    draw_title()
    write_png("entry.png", W, H, buf)
    print("wrote entry.png 1024x1024")


if __name__ == "__main__":
    main()
