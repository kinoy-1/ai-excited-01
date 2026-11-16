# The Koi That Swallowed the Moon

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/kinoy-1/ai-excited-01/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/kinoy-1/ai-excited-01/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

An entry for the [ai-excited-01](https://make.fun/bounty/ai-excited-01) competition on make.fun — "Make the AI judge excited."

![The Koi That Swallowed the Moon](entry.png)

## What the image is

A giant luminous koi fish, scales of molten gold and ember-orange with magenta
fins, leaps in a huge diagonal arc out of a dark indigo ocean — its head
touching a colossal full moon ringed in violet and gold aurora light. Below,
a tiny neon-lit coastal city glitters along the bottom edge while glowing
spray explodes where the koi burst out of the water. The sky is a deep
violet-to-teal gradient scattered with stars and aurora ribbons. A bold gold
**WOW!** crowns the top-left corner.

One clear focal point: the koi's head against the moon. The composition runs
on a strong diagonal from the dark wave at bottom-left to the moon and the
leaping koi at top-right, so the idea still reads at ~300px: big moon circle,
big koi arc, one word.

## How the program works

`main.py` draws the image entirely in code — nothing is downloaded or copied.
It uses only the Python standard library, so the grader needs to install
nothing:

- A `bytearray` holds the 1024×1024 RGB pixel buffer. Helper functions paint
  vertical/radial gradients, filled circles, triangles, thick tapered curves
  (the koi's body is a chain of ~150 overlapping circles along a cubic Bézier
  arc), translucent aurora sine bands, and seeded-random spray, stars and
  city lights.
- The **WOW!** lettering is drawn from a small hand-made 5×7 bitmap font,
  scaled up with a dark outline so it stays crisp.
- The PNG is written by hand: RGB scanlines (filter byte 0 per row) are
  compressed with `zlib`, and the IHDR / IDAT / IEND chunks are assembled
  with `struct` and `binascii.crc32`.
- The output is **deterministic**: a fixed seed (`random.Random(20261116)`)
  and no time or system randomness, so two runs produce byte-identical files.

## How to run it locally

```bash
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png` (1024×1024, ~137 KB). Running it twice into
two different output directories produces byte-identical files (verified
with `sha256sum`).

## Files

| File | Description |
| --- | --- |
| `main.py` | The generator — draws the image and writes the PNG |
| `entry.png` | The generated entry image (1024×1024) |
| `README.md` | This file |
| `LICENSE` | MIT license |
| `.makefun/owner.json` | Owner wallet for the make.fun entry |

## Competition

Built for [ai-excited-01](https://make.fun/bounty/ai-excited-01) on make.fun.
Referral code: `qzezv1jd`
