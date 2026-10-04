# -*- coding: utf-8 -*-
"""
图片优化脚本（和各政府网）

做的事：
  1. 把 assets/images 下过大的 PNG/JPG 压到合理尺寸；
  2. 生成同名 .webp 兄弟文件（<picture> 优先走 WebP，原图兜底）；
  3. 原图备份到 assets/images/.originals/（以点开头，Jekyll 默认不发布）；
  4. 输出 _data/image_variants.yml，供 _includes/img.html 读取宽高，避免布局抖动。

可重复运行：若 .originals 里已有备份，则以备份为源重新处理，不会二次压缩。

不处理：视频（Kuanian2026.mp4）、已生成的 .webp、.originals/。

用法：python tools/optimize-images.py
"""

import os
import sys
from collections import deque

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(ROOT, "assets", "images")
ORIGINALS_DIR = os.path.join(IMAGES_DIR, ".originals")
DATA_FILE = os.path.join(ROOT, "_data", "image_variants.yml")

IMAGE_EXTS = (".png", ".jpg", ".jpeg")
WEBP_QUALITY = 82
JPEG_QUALITY = 82

# 单张图片的最大边长（等比缩放）。默认 1600；超宽头图 2400；logo 只保留显示所需高度。
MAX_WIDTH = 1600
MAX_WIDTH_WIDE = 2400
MAX_LOGO_HEIGHT = 240
WIDE_KEYWORDS = ("costum_cover",)


def target_size(name, width, height):
    """按文件名规则返回缩放后的 (w, h)。"""
    lower = name.lower()
    if "logo" in lower:
        if height > MAX_LOGO_HEIGHT:
            ratio = MAX_LOGO_HEIGHT / float(height)
            return max(1, int(round(width * ratio))), MAX_LOGO_HEIGHT
        return width, height
    max_w = MAX_WIDTH_WIDE if any(k in lower for k in WIDE_KEYWORDS) else MAX_WIDTH
    if width > max_w:
        ratio = max_w / float(width)
        return max_w, max(1, int(round(height * ratio)))
    return width, height


def backup_path(rel):
    return os.path.join(ORIGINALS_DIR, rel)


def collect_images():
    for dirpath, dirnames, filenames in os.walk(IMAGES_DIR):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in IMAGE_EXTS:
                full = os.path.join(dirpath, fname)
                yield full, os.path.relpath(full, IMAGES_DIR)


def strip_background(im, tol=40):
    """把与四角同色的「外部背景」按连通区域抠掉，保留图形内部的白色区域。

    适用于白底 logo：让 logo 能放到深色页脚等任意背景上。
    """
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    bg_r = sum(c[0] for c in corners) / 4.0
    bg_g = sum(c[1] for c in corners) / 4.0
    bg_b = sum(c[2] for c in corners) / 4.0

    def is_bg(p):
        return (abs(p[0] - bg_r) <= tol and
                abs(p[1] - bg_g) <= tol and
                abs(p[2] - bg_b) <= tol)

    visited = bytearray(w * h)
    queue = deque()

    def visit(x, y):
        i = y * w + x
        if not visited[i] and is_bg(px[x, y]):
            visited[i] = 1
            queue.append((x, y))

    for x in range(w):
        visit(x, 0)
        visit(x, h - 1)
    for y in range(h):
        visit(0, y)
        visit(w - 1, y)

    while queue:
        x, y = queue.popleft()
        r, g, b, _ = px[x, y]
        px[x, y] = (r, g, b, 0)
        if x > 0:
            visit(x - 1, y)
        if x + 1 < w:
            visit(x + 1, y)
        if y > 0:
            visit(x, y - 1)
        if y + 1 < h:
            visit(x, y + 1)

    return im


def process(full, rel):
    name = os.path.basename(rel)
    backup = backup_path(rel)

    # 以备份为源（若有），保证脚本可重复运行
    if os.path.exists(backup):
        source = backup
    else:
        source = full
        bdir = os.path.dirname(backup)
        if not os.path.isdir(bdir):
            os.makedirs(bdir)
        with open(source, "rb") as src, open(backup, "wb") as dst:
            dst.write(src.read())

    with Image.open(source) as im:
        im.load()
        # 白底 logo 抠成透明底（原图本就没有透明通道时才处理）
        if "logo" in name.lower():
            alpha_used = "A" in im.getbands() and im.getchannel("A").getextrema()[0] < 255
            if not alpha_used:
                im = strip_background(im)
        new_w, new_h = target_size(name, im.width, im.height)
        work = im
        if (new_w, new_h) != im.size:
            work = im.resize((new_w, new_h), Image.LANCZOS)

        ext = os.path.splitext(full)[1].lower()
        if ext == ".png":
            if work.mode not in ("RGB", "RGBA"):
                work = work.convert("RGBA")
            work.save(full, "PNG", optimize=True)
        else:
            if work.mode != "RGB":
                work = work.convert("RGB")
            work.save(full, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)

        # 若重编码后反而更大，则回退为原图，避免「越优化越大」
        if os.path.getsize(full) >= os.path.getsize(backup):
            with open(backup, "rb") as src, open(full, "wb") as dst:
                dst.write(src.read())

        webp = os.path.splitext(full)[0] + ".webp"
        if work.mode not in ("RGB", "RGBA"):
            work = work.convert("RGBA")
        work.save(webp, "WEBP", quality=WEBP_QUALITY, method=6)

    return name, new_w, new_h


def main():
    entries = []
    before = after = 0
    for full, rel in sorted(collect_images()):
        old_size = os.path.getsize(full)
        try:
            name, w, h = process(full, rel)
        except Exception as exc:  # noqa: BLE001
            print("跳过 %s：%s" % (rel, exc))
            continue
        new_size = os.path.getsize(full)
        webp_size = os.path.getsize(os.path.splitext(full)[0] + ".webp")
        before += old_size
        after += new_size + webp_size
        entries.append((rel, w, h))
        print(
            "%-32s %4dx%-5d  %6.0fKB -> %5.0fKB (webp %5.0fKB)"
            % (name, w, h, old_size / 1024.0, new_size / 1024.0, webp_size / 1024.0)
        )

    # 生成尺寸表，供 Liquid 读取
    lines = [
        "# 由 tools/optimize-images.py 自动生成，请勿手改。",
        "# 键为图片在站内的路径，值含宽高与是否存在 WebP 版本。",
    ]
    for rel, w, h in entries:
        key = "/assets/images/" + rel.replace(os.sep, "/")
        lines.append('"%s":' % key)
        lines.append("  width: %d" % w)
        lines.append("  height: %d" % h)
        lines.append("  webp: true")
    with open(DATA_FILE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")

    print("-" * 64)
    print("合计：%.0fKB -> %.0fKB（含 WebP）" % (before / 1024.0, after / 1024.0))
    print("尺寸表：%s" % os.path.relpath(DATA_FILE, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
