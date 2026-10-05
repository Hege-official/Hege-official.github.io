"""生成播客方形封面（自产，无第三方授权）。用法：python tools/podcast/gen_cover.py"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
OUT = REPO / "assets" / "images" / "podcast-cover.png"

SIZE = 1400
NAVY = (16, 33, 63)      # 藏青
GOLD = (198, 166, 100)   # 香槟金
RED = (166, 32, 38)      # 中国红
CREAM = (246, 242, 232)
MUTED = (206, 210, 220)


def _safe_stdout():
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass


def _font(size, bold=True):
    names = ("msyhbd.ttc", "msyh.ttc", "simhei.ttf", "simsun.ttc") if bold else ("msyh.ttc", "simhei.ttf")
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _centered(draw, text, font, y, fill, width):
    box = draw.textbbox((0, 0), text, font=font)
    draw.text(((width - (box[2] - box[0])) / 2 - box[0], y), text, font=font, fill=fill)


def build_cover(out=OUT, size=SIZE):
    img = Image.new("RGB", (size, size), NAVY)
    draw = ImageDraw.Draw(img)

    margin = int(size * 0.05)
    draw.rectangle([margin, margin, size - margin, size - margin], outline=GOLD, width=6)
    draw.rectangle([margin, margin, size - margin, margin + int(size * 0.11)], fill=RED)

    _centered(draw, "和各政府网", _font(int(size * 0.055)), margin + int(size * 0.03), CREAM, size)
    _centered(draw, "和国播客", _font(int(size * 0.16)), int(size * 0.34), CREAM, size)
    _centered(draw, "和各中央广播与电视平台", _font(int(size * 0.04), bold=False), int(size * 0.58), GOLD, size)
    draw.line([int(size * 0.30), int(size * 0.68), int(size * 0.70), int(size * 0.68)], fill=GOLD, width=3)
    _centered(draw, "hege-official.github.io", _font(int(size * 0.028), bold=False), int(size * 0.80), MUTED, size)

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def main():
    _safe_stdout()
    path = build_cover()
    print(f"OK {path} ({SIZE}x{SIZE})")


if __name__ == "__main__":
    main()
