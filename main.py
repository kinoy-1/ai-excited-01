#!/usr/bin/env python3
"""The Jellyfish That Ate the Skyline.

A colossal bioluminescent jellyfish drifts down over a sleeping city at
night: one huge glowing bell, a curtain of tentacles, a beam of light on
the rooftops, and a tiny aeroplane for scale.

Python 3.13, standard library only. Everything is drawn procedurally on a
1024x1024 pixel buffer and written out with a hand-rolled PNG encoder.
Fixed seed, fully deterministic: run it twice and the bytes are identical.

Usage:  python3 main.py   # writes entry.png next to this file, or to
                           # $MAKEFUN_OUTPUT_DIR/entry.png when that is set.
"""

import math
import os
import random
import struct
import zlib
from binascii import crc32

W, H = 1024, 1024
SEED = 20261116
rng = random.Random(SEED)


# ---------------------------------------------------------------- canvas
class Canvas:
    """A plain RGB pixel buffer with source-over blending helpers."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.rows = [bytearray(w * 3) for _ in range(h)]

    def put(self, x, y, rgb):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = x * 3
            row = self.rows[y]
            row[i] = rgb[0]
            row[i + 1] = rgb[1]
            row[i + 2] = rgb[2]

    def blend(self, x, y, rgb, alpha):
        """Blend rgb over the pixel at (x, y); alpha 0..1."""
        if 0 <= x < self.w and 0 <= y < self.h and alpha > 0.0:
            i = x * 3
            row = self.rows[y]
            if alpha >= 1.0:
                row[i] = rgb[0]
                row[i + 1] = rgb[1]
                row[i + 2] = rgb[2]
            else:
                ia = 1.0 - alpha
                row[i] = int(row[i] * ia + rgb[0] * alpha)
                row[i + 1] = int(row[i + 1] * ia + rgb[1] * alpha)
                row[i + 2] = int(row[i + 2] * ia + rgb[2] * alpha)

    def disc(self, cx, cy, r, rgb, alpha=1.0):
        """Filled circle, blended."""
        r = int(r)
        if r <= 0:
            return
        x0 = max(0, cx - r)
        x1 = min(self.w - 1, cx + r)
        y0 = max(0, cy - r)
        y1 = min(self.h - 1, cy + r)
        r2 = r * r
        for y in range(y0, y1 + 1):
            dy = y - cy
            dx = int(math.sqrt(max(0, r2 - dy * dy)))
            for x in range(max(x0, cx - dx), min(x1, cx + dx) + 1):
                self.blend(x, y, rgb, alpha)

    def rect(self, x, y, w, h, rgb, alpha=1.0):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                self.blend(xx, yy, rgb, alpha)

    def fill_row(self, y, rgb):
        """Paint one whole scanline a solid colour (fast path)."""
        self.rows[y][:] = bytes(rgb) * self.w


def lerp(a, b, t):
    return a + (b - a) * t


def lerp3(c0, c1, t):
    return (int(lerp(c0[0], c1[0], t)),
            int(lerp(c0[1], c1[1], t)),
            int(lerp(c0[2], c1[2], t)))


def lut_gradient(stops, size=256):
    """Build a lookup table of RGB triples from [(pos, rgb), ...] stops."""
    table = []
    for i in range(size):
        t = i / (size - 1)
        for j in range(len(stops) - 1):
            p0, c0 = stops[j]
            p1, c1 = stops[j + 1]
            if p0 <= t <= p1:
                f = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                table.append(lerp3(c0, c1, f))
                break
        else:
            table.append(stops[-1][1])
    return table


cv = Canvas(W, H)


# ---------------------------------------------------------------- night sky
def paint_sky():
    """Deep indigo at the top, a touch lighter and warmer near the horizon."""
    stops = [(0.0, (7, 9, 34)),
             (0.45, (13, 14, 48)),
             (0.75, (22, 20, 62)),
             (1.0, (33, 28, 76))]
    table = lut_gradient(stops, H)
    for y in range(H):
        cv.fill_row(y, table[y])


def paint_clouds():
    """Faint translucent discs in loose horizontal bands, barely there."""
    bands = [(70, 170), (180, 320), (330, 470)]
    for (y0, y1) in bands:
        for _ in range(5):
            cx = rng.randint(40, W - 40)
            cy = rng.randint(y0, y1)
            rx = rng.randint(60, 150)
            ry = rng.randint(18, 42)
            tone = rng.choice([(46, 42, 92), (58, 50, 104), (36, 34, 80)])
            a = rng.uniform(0.05, 0.11)
            for yy in range(max(0, cy - ry), min(H, cy + ry + 1)):
                dy = (yy - cy) / ry
                half = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
                for xx in range(max(0, cx - half), min(W, cx + half + 1)):
                    cv.blend(xx, yy, tone, a)


def paint_stars():
    """Pinprick stars, plus a handful of bright four-point sparkles."""
    for _ in range(260):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, 760)
        b = rng.randint(140, 255)
        warm = rng.random() < 0.25
        col = (b, int(b * 0.92), int(b * 0.78)) if warm else (int(b * 0.85), int(b * 0.9), b)
        cv.put(x, y, col)
        if rng.random() < 0.12:
            cv.put(x + 1, y, col)
    for _ in range(14):
        x = rng.randint(20, W - 20)
        y = rng.randint(20, 620)
        arm = rng.randint(4, 8)
        col = (225, 240, 255)
        for d in range(-arm, arm + 1):
            cv.blend(x + d, y, col, 0.85)
            cv.blend(x, y + d, col, 0.85)
        cv.put(x, y, (255, 255, 255))


# ---------------------------------------------------------------- the bell
BELL_CX, BELL_CY = 512, 352
BELL_RX, BELL_RY = 342, 232

BELL_STOPS = [(0.00, (238, 255, 255)),
              (0.22, (158, 236, 255)),
              (0.48, (122, 185, 252)),
              (0.72, (158, 128, 246)),
              (0.90, (196, 104, 238)),
              (1.00, (212, 96, 232))]


def paint_bell():
    """The giant glowing dome: radial gradient, sunburst striations,
    a bright rim along the top and a scalloped lower margin. A soft halo
    fades out just past the rim."""
    table = lut_gradient(BELL_STOPS, 256)
    glow = (150, 108, 240)
    cx, cy, rx, ry = BELL_CX, BELL_CY, BELL_RX, BELL_RY
    ext = 1.38  # halo reaches this far past the rim, in units of the radii
    y0 = max(0, int(cy - ry * ext))
    y1 = min(H - 1, int(cy + ry * ext))
    for y in range(y0, y1 + 1):
        dy = (y - cy) / ry
        dy2 = dy * dy
        if dy2 >= ext * ext:
            continue
        half = rx * math.sqrt(ext * ext - dy2)
        x0 = max(0, int(cx - half))
        x1 = min(W - 1, int(cx + half))
        for x in range(x0, x1 + 1):
            dx = (x - cx) / rx
            d2 = dx * dx + dy2
            if d2 > ext * ext:
                continue
            if d2 <= 1.0:
                d = math.sqrt(d2)
                col = table[min(255, int(d * 255))]
                # fine radial striations: a whisper of sunburst texture
                ang = math.atan2(dy, dx)
                shimmer = 1.0 + 0.012 * math.sin(ang * 64.0)
                r = min(255, int(col[0] * shimmer))
                g = min(255, int(col[1] * shimmer))
                b = min(255, int(col[2] * shimmer))
                cv.put(x, y, (r, g, b))
            else:
                # halo: soft purple glow fading with distance past the rim
                fade = (math.sqrt(d2) - 1.0) / (ext - 1.0)
                cv.blend(x, y, glow, 0.30 * (1.0 - fade) * (1.0 - fade))

    # bright rim: a glowing arc hugging the top edge of the dome
    for deg in range(-168, -12, 1):
        a = math.radians(deg)
        x = int(cx + rx * math.cos(a))
        y = int(cy + ry * math.sin(a) * 0.98)
        cv.disc(x, y, 2, (228, 246, 255), 0.6)
    # scalloped lower margin: soft beads along the bottom edge
    for deg in range(18, 163, 5):
        a = math.radians(deg)
        x = int(cx + rx * math.cos(a))
        y = int(cy + ry * math.sin(a) * 0.99)
        cv.disc(x, y, 4, (196, 150, 242), 0.3)


# ---------------------------------------------------------------- light beam
def paint_beam():
    """A soft cone of light falling from the bell onto the rooftops,
    plus the pool of light where it lands."""
    top_y, bot_y = 596, 908
    top_half, bot_half = 46, 196
    for y in range(top_y, bot_y + 1):
        t = (y - top_y) / (bot_y - top_y)
        half = top_half + (bot_half - top_half) * t
        alpha = 0.17 * (1.0 - t) + 0.03
        x0 = int(BELL_CX - half)
        x1 = int(BELL_CX + half)
        for x in range(max(0, x0), min(W, x1 + 1)):
            cv.blend(x, y, (176, 216, 255), alpha)
    # pool of light on the rooftops, fading softly toward its edges
    for yy in range(868, 930):
        dy = (yy - 898) / 34.0
        if abs(dy) >= 1.0:
            continue
        half = int(215 * math.sqrt(1.0 - dy * dy))
        for xx in range(max(0, BELL_CX - half), min(W, BELL_CX + half + 1)):
            dxn = (xx - BELL_CX) / 215.0
            fade = max(0.0, 1.0 - dy * dy) * max(0.0, 1.0 - dxn * dxn)
            cv.blend(xx, yy, (170, 205, 250), 0.12 * fade)


# ---------------------------------------------------------------- tentacles
def paint_tentacles():
    """A curtain of thin wavy tentacles hanging from the bell's margin,
    cyan and magenta, some strung with glowing beads."""
    cols = [(96, 226, 255), (255, 122, 224), (204, 132, 255), (120, 200, 255)]
    n = 17
    for i in range(n):
        # anchor along the bottom arc of the bell
        frac = i / (n - 1)
        ang = math.radians(lerp(22, 158, frac))
        x0 = int(BELL_CX + BELL_RX * math.cos(ang))
        y0 = int(BELL_CY + BELL_RY * math.sin(ang) * 0.99)
        length = rng.randint(170, 380)
        amp = rng.uniform(7, 20)
        waves = rng.uniform(2.0, 4.0)  # gentle S-curves, not tight zigzags
        phase = rng.uniform(0, 6.28)
        col = cols[i % len(cols)]
        bead = rng.random() < 0.55
        steps = length // 2
        for s in range(steps + 1):
            t = s / steps
            y = y0 + int(length * t)
            if y >= H:
                break
            x = int(x0 + amp * math.sin(t * waves * 6.28 + phase)
                    * (0.4 + 0.6 * t))
            r = lerp(2.6, 1.0, t)
            cv.disc(x, y, r, col, 0.92)
            if bead and s % 18 == 8:
                cv.disc(x, y, 3.0, (235, 250, 255), 0.7)


def paint_arms():
    """Four thick frilly oral arms in the centre, pink ribbons of
    overlapping discs whose radius pulses along their length."""
    centres = [428, 478, 530, 580]
    for k, x0 in enumerate(centres):
        length = rng.randint(235, 280)
        phase = rng.uniform(0, 6.28)
        drift = rng.uniform(-14, 14)
        y0 = 584
        steps = length // 3
        for s in range(steps + 1):
            t = s / steps
            y = y0 + int(length * t)
            x = int(x0 + drift * t + 9.0 * math.sin(t * 5.0 + phase))
            r = 6.5 + 5.0 * math.sin(t * 26.0 + phase)
            r = max(2.5, r)
            cv.disc(x, y, r, (238, 112, 186), 0.95)
            cv.disc(x, y, r * 0.55, (255, 168, 216), 0.95)


# ---------------------------------------------------------------- the city
def paint_city():
    """Dark skyline silhouettes along the bottom, lit windows, a few
    neon roof lines and one tall tower with a red beacon."""
    win_cols = [(122, 232, 255), (255, 150, 210), (255, 210, 120),
                (232, 236, 255), (140, 255, 220)]
    x = -6
    while x < W:
        w = rng.randint(26, 72)
        h = rng.randint(42, 148)
        top = H - h
        tone = rng.choice([(7, 8, 20), (10, 10, 26), (6, 7, 18)])
        cv.rect(x, top, w, h, tone)
        # lit windows on a loose grid
        for wy in range(top + 8, H - 8, 13):
            for wx in range(x + 5, x + w - 5, 10):
                if rng.random() < 0.42:
                    cv.rect(wx, wy, 3, 5, rng.choice(win_cols), 0.95)
        # neon roof line on some buildings
        if rng.random() < 0.22:
            cv.rect(x, top, w, 2, rng.choice([(90, 230, 255), (255, 110, 220)]), 0.9)
        # antenna on some buildings
        if rng.random() < 0.18:
            ax = x + w // 2
            cv.rect(ax, top - 14, 1, 14, (16, 16, 34))
            cv.put(ax, top - 15, (255, 70, 70))
        x += w + rng.randint(0, 8)
    # the tall tower, right of centre, with its red beacon
    tx, tw, th = 688, 34, 176
    cv.rect(tx, H - th, tw, th, (9, 9, 24))
    for wy in range(H - th + 10, H - 10, 13):
        for wx in range(tx + 6, tx + tw - 6, 10):
            if rng.random() < 0.5:
                cv.rect(wx, wy, 3, 5, rng.choice(win_cols), 0.95)
    cv.rect(tx + tw // 2 - 1, H - th - 18, 2, 18, (16, 16, 34))
    cv.disc(tx + tw // 2, H - th - 19, 3, (255, 64, 64), 1.0)


# ---------------------------------------------------------------- scale cues
def paint_plane():
    """A tiny aeroplane crossing the sky beside the bell, with a faint
    contrail trailing behind it."""
    px, py = 826, 298
    ink = (14, 14, 30)
    # fuselage and wings, drawn as short thick strokes of discs
    for d in range(-13, 14):
        cv.disc(px + d, py, 2, ink, 0.95)
    for d in range(-7, 8):
        cv.disc(px + 2 + d, py - 5 - abs(d) // 3, 1.6, ink, 0.95)
        cv.disc(px - 4 + d // 2, py + 4, 1.4, ink, 0.95)
    cv.disc(px - 13, py - 4, 2, ink, 0.95)  # tail fin
    cv.put(px + 12, py, (255, 80, 80))      # nose light
    cv.put(px - 2, py - 6, (255, 255, 255))  # wing light
    # contrail
    for d in range(0, 120, 3):
        cv.disc(px + 16 + d, py - 1 - d // 14, 1.6, (220, 230, 255),
                max(0.0, 0.22 - d * 0.0016))


def paint_birds():
    """A few tiny birds, just dark chevrons in the sky."""
    for (bx, by) in [(238, 176), (706, 148), (168, 418), (884, 178)]:
        for d in range(0, 6):
            cv.put(bx - d, by - d // 2, (18, 18, 38))
            cv.put(bx + d, by - d // 2, (18, 18, 38))


# ---------------------------------------------------------------- the words
GLYPHS = {
    "L": ("#....",
          "#....",
          "#....",
          "#....",
          "#....",
          "#....",
          "#####"),
    "O": (".###.",
          "#...#",
          "#...#",
          "#...#",
          "#...#",
          "#...#",
          ".###."),
    "K": ("#...#",
          "#..#.",
          "#.#..",
          "##...",
          "#.#..",
          "#..#.",
          "#...#"),
    "U": ("#...#",
          "#...#",
          "#...#",
          "#...#",
          "#...#",
          "#...#",
          ".###."),
    "P": ("####.",
          "#...#",
          "#...#",
          "####.",
          "#....",
          "#....",
          "#...."),
    ".": (".....",
          ".....",
          ".....",
          ".....",
          ".....",
          ".....",
          ".##.."),
    " ": (".....",
          ".....",
          ".....",
          ".....",
          ".....",
          ".....",
          "....."),
}


def paint_text():
    """LOOK UP. in a chunky 5x7 pixel font, pale cyan, top left."""
    text = "LOOK UP."
    scale = 6
    adv = 6 * scale
    x = 48
    y = 48
    col = (176, 236, 255)
    for ch in text:
        glyph = GLYPHS[ch]
        for gy, row in enumerate(glyph):
            for gx, cell in enumerate(row):
                if cell == "#":
                    cv.rect(x + gx * scale, y + gy * scale,
                            scale, scale, col)
        x += adv


# ---------------------------------------------------------------- vignette
def paint_vignette():
    """Gently darken the corners so the glow in the middle holds the eye."""
    fx = [1.0 - 0.30 * ((xx - 512) / 512.0) ** 2 for xx in range(W)]
    fy = [1.0 - 0.30 * ((yy - 512) / 512.0) ** 2 for yy in range(H)]
    for y in range(H):
        fyy = fy[y]
        row = cv.rows[y]
        for x in range(W):
            f = fx[x] * fyy
            if f < 0.999:
                i = x * 3
                row[i] = int(row[i] * f)
                row[i + 1] = int(row[i + 1] * f)
                row[i + 2] = int(row[i + 2] * f)


# ---------------------------------------------------------------- PNG out
def _chunk(kind, data):
    body = kind + data
    return (struct.pack(">I", len(data)) + body +
            struct.pack(">I", crc32(body) & 0xFFFFFFFF))


def write_png(path):
    """Truecolour PNG, 8 bit, one IDAT. Every scanline uses the Up filter,
    which suits the smooth vertical gradients in this image."""
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    prev = bytearray(W * 3)
    for y in range(H):
        row = cv.rows[y]
        raw.append(2)  # filter: Up
        for i in range(W * 3):
            raw.append((row[i] - prev[i]) & 0xFF)
        prev = row
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + _chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


# ---------------------------------------------------------------- run
def main():
    paint_sky()
    paint_clouds()
    paint_stars()
    paint_bell()
    paint_beam()
    paint_tentacles()
    paint_arms()
    paint_city()
    paint_plane()
    paint_birds()
    paint_text()
    paint_vignette()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.dirname(
        os.path.abspath(__file__))
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path)
    print(f"wrote {path} ({size} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
