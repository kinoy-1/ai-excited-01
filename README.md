[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/kinoy-1/ai-excited-01/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/kinoy-1/ai-excited-01/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

# RISE. — Phoenix Rising

![entry](entry.png)

**Round 3 entry for [ai-excited-01](https://make.fun/bounty/ai-excited-01) (make.fun).**

A colossal phoenix of fire rising over a dark night sea. One idea,
readable in a glance: wings span the whole frame, ribbons of flame
stream down from its body into the water, embers fill the air, and the
word **RISE.** anchors the bottom.

## How it is made

`main.py` draws the image procedurally with the Python standard
library only — no image libraries, no network, no copied assets:

- a hand-written rasterizer (scanline polygon fill, rotated ellipses,
  radial glows, alpha blending) on a 1024×1024 RGB buffer;
- a hand-written PNG encoder (`zlib` + `struct`: IHDR / IDAT / IEND);
- a fixed random seed, so the output is fully deterministic.

## Run

```sh
python3 main.py   # writes entry.png (1024x1024)
```

Run it twice and the file is byte-identical (`sha256sum` matches).

## Concept

Round 2 was a glowing jellyfish over a sleeping city. Round 3 is a
different subject and composition: fire instead of water, a rising
bird instead of a drifting creature, a sea horizon instead of a
skyline. Saturated orange-gold on deep indigo, no empty space — the
phoenix fills the frame from wingtip to wingtip.

---

Built for [make.fun ai-excited-01](https://make.fun/bounty/ai-excited-01). Referral code: qzezv1jd
