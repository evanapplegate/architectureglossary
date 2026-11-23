"""Draw the outlines from tools/regions.py on top of a photo, so you can check them before publishing.

    python3 tools/verify.py PHOTO_KEY OUT [X0 Y0 X1 Y1] [--only a,b,c] [--gamma G]

    PHOTO_KEY    a key of DATA in tools/regions.py, e.g. north (the picture is read from docs/img/<key>.jpg)
    OUT          where to write the check picture, e.g. /tmp/check.jpg
    X0 Y0 X1 Y1  crop to look at, in percent of the full photo (default: the whole photo)
    --only       comma-separated term keys to draw (default: all of them, which gets crowded)
    --gamma      below 1 brightens a dark photo, e.g. 0.45

Each term gets its own color and a label at the top-left of every shape. Fix the numbers in
tools/regions.py, run this again, repeat until the outlines hug the stone.

Needs Pillow:  python3 -m pip install pillow
"""
import argparse
import colorsys
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import regions  # noqa: E402

OUT_WIDTH = 1800


def load_font(size):
    for path in ("/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photo_key", choices=sorted(regions.DATA))
    ap.add_argument("out")
    ap.add_argument("box", nargs="*", type=float, default=[0, 0, 100, 100], metavar="X0 Y0 X1 Y1")
    ap.add_argument("--only", default="")
    ap.add_argument("--gamma", type=float, default=1)
    a = ap.parse_args()
    if len(a.box) != 4:
        ap.error("the crop needs exactly four numbers: X0 Y0 X1 Y1")
    x0, y0, x1, y1 = a.box
    only = [k for k in a.only.split(",") if k]

    im = Image.open(os.path.join(HERE, "..", "docs", "img", a.photo_key + ".jpg")).convert("RGB")
    if a.gamma != 1:
        im = im.point(lambda v: int(255 * ((v / 255) ** a.gamma)))
    W, H = im.size
    crop = im.crop((int(W * x0 / 100), int(H * y0 / 100), int(W * x1 / 100), int(H * y1 / 100)))
    crop = crop.resize((OUT_WIDTH, int(crop.size[1] * OUT_WIDTH / crop.size[0])), Image.LANCZOS)
    cw, ch = crop.size
    d = ImageDraw.Draw(crop, "RGBA")
    font = load_font(18)

    def to_px(p):
        return ((p[0] - x0) / (x1 - x0) * cw, (p[1] - y0) / (y1 - y0) * ch)

    data = regions.DATA[a.photo_key]
    for bad in [k for k in only if k not in data]:
        print(f"note: no '{bad}' on photo '{a.photo_key}'")
    names = list(data)
    for i, key in enumerate(names):
        if only and key not in only:
            continue
        r, g, b = [int(v * 255) for v in colorsys.hsv_to_rgb(i / len(names), 1, 1)]
        for shape in data[key]:
            if shape["t"] == "p":
                pts = [to_px(p) for p in shape["pts"]]
            else:
                (cx, cy), (rx, ry) = shape["c"], shape["r"]
                pts = [to_px((cx + rx * math.cos(t / 40 * 2 * math.pi), cy + ry * math.sin(t / 40 * 2 * math.pi))) for t in range(40)]
            d.polygon(pts, fill=(r, g, b, 40))
            d.line(pts + [pts[0]], fill=(r, g, b, 255), width=2)
            lx, ly = min(p[0] for p in pts), min(p[1] for p in pts)
            d.rectangle([lx, ly - 20, lx + len(key) * 10 + 4, ly], fill=(0, 0, 0, 180))
            d.text((lx + 2, ly - 19), key, fill=(r, g, b, 255), font=font)

    crop.save(a.out, quality=88)
    print("wrote", a.out, crop.size)


if __name__ == "__main__":
    main()
