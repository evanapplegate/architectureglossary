"""Draw a labelled percent grid over a photo (or a crop of it) so you can read off outline coordinates.

    python3 tools/grid.py PHOTO OUT [X0 Y0 X1 Y1] [--step N] [--gamma G]

    PHOTO        image to measure, e.g. docs/img/north.jpg
    OUT          where to write the gridded picture, e.g. /tmp/grid.jpg
    X0 Y0 X1 Y1  crop to look at, in percent of the full photo (default: 0 0 100 100)
    --step       spacing of the grid lines in percent (default: 5; use 1 or 2 on tight crops)
    --gamma      below 1 brightens a dark photo for reading, e.g. 0.45 (default: 1, no change)

The labels always show percent of the FULL photo, even on a crop, so numbers read off any crop can go
straight into tools/regions.py. Vertical lines are magenta with yellow labels along the top; horizontal
lines are cyan with labels down the left side.

Typical session: one full-frame grid at --step 5 to find things, then a crop per feature at --step 1.

Needs Pillow:  python3 -m pip install pillow
"""
import argparse
import math

from PIL import Image, ImageDraw, ImageFont

OUT_WIDTH = 1800  # every output is scaled to this width, so small crops come out magnified


def load_font(size):
    for path in ("/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def ticks(lo, hi, step):
    v = math.ceil(lo / step) * step
    while v <= hi + 1e-9:
        yield round(v, 4)
        v += step


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photo")
    ap.add_argument("out")
    ap.add_argument("box", nargs="*", type=float, default=[0, 0, 100, 100], metavar="X0 Y0 X1 Y1")
    ap.add_argument("--step", type=float, default=5)
    ap.add_argument("--gamma", type=float, default=1)
    a = ap.parse_args()
    if len(a.box) != 4:
        ap.error("the crop needs exactly four numbers: X0 Y0 X1 Y1")
    x0, y0, x1, y1 = a.box

    im = Image.open(a.photo).convert("RGB")
    if a.gamma != 1:
        im = im.point(lambda v: int(255 * ((v / 255) ** a.gamma)))
    W, H = im.size
    crop = im.crop((int(W * x0 / 100), int(H * y0 / 100), int(W * x1 / 100), int(H * y1 / 100)))
    scale = OUT_WIDTH / crop.size[0]
    crop = crop.resize((OUT_WIDTH, int(crop.size[1] * scale)), Image.LANCZOS)
    cw, ch = crop.size
    d = ImageDraw.Draw(crop, "RGBA")
    font = load_font(20)

    for gx in ticks(x0, x1, a.step):
        px = (gx - x0) / (x1 - x0) * cw
        d.line([(px, 0), (px, ch)], fill=(255, 0, 255, 150), width=1)
        label = f"{gx:g}"
        w = len(label) * 11
        d.rectangle([px - w / 2 - 2, 2, px + w / 2 + 2, 24], fill=(0, 0, 0, 170))
        d.text((px - w / 2, 3), label, fill=(255, 255, 0, 255), font=font)
    for gy in ticks(y0, y1, a.step):
        py = (gy - y0) / (y1 - y0) * ch
        d.line([(0, py), (cw, py)], fill=(0, 255, 255, 150), width=1)
        label = f"{gy:g}"
        d.rectangle([2, py - 11, 2 + len(label) * 12, py + 11], fill=(0, 0, 0, 170))
        d.text((3, py - 10), label, fill=(0, 255, 255, 255), font=font)

    crop.save(a.out, quality=88)
    print("wrote", a.out, crop.size)


if __name__ == "__main__":
    main()
