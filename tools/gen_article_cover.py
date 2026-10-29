"""生成文章封面（自产，无第三方素材）。用法：

    python tools/gen_article_cover.py                 # 只给缺封面的文章生成
    python tools/gen_article_cover.py --force         # 强制重新生成（会改写 header.image）
    python tools/gen_article_cover.py --force --no-write   # 只出图，不动 front matter
    python tools/gen_article_cover.py --post 2026-07-04-capital-yikong

设计约束（来自站点排版）：
  - 文章页 header.image 是整幅铺满的宽图，1638x500；
  - 首页卡片 .gov-card__media 按 16:9 裁切（中央 889x500），
    因此所有文字必须落在安全区内，两侧留白可被裁掉。

版式：左侧竖向色标 + 栏目标签 + 大字标题（最多两行）
      右侧同色系渐变底的几何纹样 + 底边色带
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "assets" / "images" / "covers"

W, H = 1638, 500
SAFE_L, SAFE_R = (W - 889) // 2, (W + 889) // 2  # 16:9 安全区边界；374 .. 1263
TEXT_X = SAFE_L + 72               # 正文左边界 446
TEXT_W = (SAFE_R - TEXT_X) - 150   # 给右侧纹样留出空间

# 栏目配色：(深色底, 渐变偏色, 强调色, 纹样)
CATEGORY_THEME = {
    "要闻": ((11, 31, 58), (24, 52, 92), (196, 62, 50), "bands"),
    "新闻": ((11, 31, 58), (20, 46, 84), (200, 169, 106), "grid"),
    "公告": ((122, 22, 26), (168, 28, 28), (214, 182, 118), "seal"),
    "社论": ((74, 26, 30), (112, 40, 42), (200, 169, 106), "rule"),
    "维护": ((20, 48, 44), (34, 74, 66), (200, 169, 106), "grid"),
    "播客": ((16, 34, 62), (28, 54, 96), (196, 62, 50), "wave"),
    "文件": ((30, 38, 52), (48, 60, 78), (200, 169, 106), "rule"),
}
DEFAULT_MOTIF = "rule"

CREAM = (246, 242, 232)
MUTED_ON_DARK = (150, 162, 182)

NO_LINE_START = "，。、；：？！）》」』】…—·,.;:?!)]}"


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


def _measure(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap_title(draw, title, font, max_width):
    """按宽度折行；中文无空格逐字累加，带行首禁则。"""
    lines, cur = [], ""
    for ch in title:
        trial = cur + ch
        if _measure(draw, trial, font) <= max_width or not cur:
            cur = trial
        elif ch in NO_LINE_START:
            lines.append(trial)
            cur = ""
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def fit_title(draw, title, max_width, max_lines=2, hi=104, lo=30):
    """从大到小试字号，返回能在 max_lines 行内排下的最大字号。"""
    size = hi
    while size >= lo:
        font = _font(size)
        lines = wrap_title(draw, title, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
        size -= 2

    font = _font(lo)
    lines = wrap_title(draw, title, font, max_width)[:max_lines]
    last = lines[-1]
    while last and _measure(draw, last + "…", font) > max_width:
        last = last[:-1]
    lines[-1] = last + "…"
    return font, lines


def vertical_gradient(size, top, bottom):
    """自上而下的线性渐变底。"""
    w, h = size
    base = Image.new("RGB", (1, h))
    px = base.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return base.resize((w, h))


def draw_seal(draw, cx, cy, r, color):
    """公章样式：外圈实线 + 内圈细线 + 五角星 + 环绕刻线。
    庄重、无放射状装饰，与公告类文件的官方气质一致。
    """
    faint = tuple(int(c * 0.55 + 20) for c in color)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=6)
    draw.ellipse([cx - r + 16, cy - r + 16, cx + r - 16, cy + r - 16], outline=faint, width=2)

    # 五角星
    star_r = int(r * 0.30)
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = star_r if i % 2 == 0 else star_r * 0.42
        pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
    draw.polygon(pts, fill=color)

    # 环绕短刻线，代替文字环
    for k in range(28):
        a = k * 2 * math.pi / 28
        if k % 7 == 0:
            continue  # 留出呼吸的空档
        r1, r2 = r - 22, r - 34
        draw.line(
            [cx + math.cos(a) * r1, cy + math.sin(a) * r1, cx + math.cos(a) * r2, cy + math.sin(a) * r2],
            fill=faint, width=2,
        )


def draw_motif(draw, kind, x0, x1, accent, bg=None):
    """安全区内右半幅的几何纹样：强调色的低透明度变体，有层次但不抢标题。
    x0/x1 必须落在 16:9 安全区内，否则首页卡片裁切会露边。
    """
    faint = tuple(int(c * 0.34 + 26) for c in accent)
    mid = tuple(int(c * 0.62 + 12) for c in accent)
    hi = tuple(min(255, int(c * 0.92 + 8)) for c in accent)

    if kind == "grid":
        step = 30
        for gx in range(int(x0), int(x1) + step, step):
            draw.line([gx, 0, gx, H], fill=faint, width=1)
        for gy in range(0, H + step, step):
            draw.line([x0, gy, x1, gy], fill=faint, width=1)
        # 叠加几条重点斜线，打破棋盘感
        for k in range(3):
            off = 60 + k * 55
            draw.line([x0 + off, H, x0 + off + 190, 0], fill=mid, width=2)

    elif kind == "bands":
        for i in range(7):
            yy = H - 46 - i * 30
            x_start = x0 + 30 + i * 14
            draw.line([x_start, yy, x1 - 30, yy], fill=faint if i % 2 == 0 else mid, width=3)
        draw.polygon(
            [(x1 - 150, 0), (x1 - 60, 0), (x1 - 200, H), (x1 - 290, H)],
            fill=tuple(int(c * 0.42 + 18) for c in bg),
        )

    elif kind == "seal":
        # 公告：庄重的公章，放在右侧留白，不与标题重叠
        draw_seal(draw, SAFE_R - 170, H // 2, 96, mid)

    elif kind == "wave":
        for k in range(6):
            amp = 26 + k * 14
            pts = [
                (px, H // 2 + math.sin((px - x0) / 85.0 + k * 0.7) * amp)
                for px in range(int(x0), int(x1) + 1, 4)
            ]
            draw.line(pts, fill=mid if k % 2 == 0 else faint, width=2 if k % 2 else 3)

    else:  # rule
        cx = (x0 + x1) // 2 + 20
        draw.line([cx, 70, cx, H - 70], fill=mid, width=2)
        for dy in (70, H - 70):
            draw.line([cx - 110, dy, cx + 110, dy], fill=mid, width=2)
        for k in range(3):
            yy = 130 + k * 110
            draw.line([cx + 26, yy, x1 - 40, yy], fill=faint, width=2)


MONTHLY_THEME = ((14, 28, 46), (26, 46, 72), (200, 169, 106))  # 月刊：更深的靛蓝 + 香槟金


def draw_full_frame(draw, color, inset, width_outer=3, width_inner=1):
    """公文式双线边框：外粗内细。用于公告与月刊，强调正式感。"""
    draw.rectangle([inset, inset, W - inset, H - inset], outline=color, width=width_outer)
    gap = 12
    draw.rectangle(
        [inset + gap, inset + gap, W - inset - gap, H - inset - gap],
        outline=tuple(min(255, c) for c in color), width=width_inner,
    )


def build_monthly_cover(title, out, w=W, h=H):
    """《和各月刊》专用版式：刊名为主视觉，期号与副题分行，整体端庄排布。"""
    bg, bg2, accent = MONTHLY_THEME
    img = vertical_gradient((w, h), bg, bg2)
    draw = ImageDraw.Draw(img)

    draw_full_frame(draw, accent, 34, 3, 1)

    # 右侧装饰：细密斜线，克制
    x0, x1 = SAFE_L + 520, SAFE_R - 60
    for k in range(9):
        ox = x0 + k * 38
        draw.line([ox, 40, ox - 190, H - 40], fill=tuple(int(c * 0.34 + 20) for c in accent), width=1)

    heading = "和各月刊"
    sub = ""
    m = re.match(r"^《和各月刊》\s*(.*?)[:：]\s*(.+)$", title)
    if m:
        heading = m.group(1).strip() or heading
        sub = m.group(2).strip()

    x = TEXT_X
    # 刊名
    name_font = _font(30, bold=False)
    draw.text((x, 92), "和 各 月 刊", font=name_font, fill=accent)
    draw.line([x, 142, x + 120, 142], fill=accent, width=3)

    # 期号（大字）
    period_font = _font(72)
    draw.text((x, 168), heading, font=period_font, fill=CREAM)

    # 副题
    if sub:
        font, lines = fit_title(draw, sub, TEXT_W + 120, max_lines=1, hi=34, lo=22)
        draw.text((x, 274), lines[0], font=font, fill=CREAM)

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)
    return out


def build_cover(title, category, out, w=W, h=H, publisher=""):
    cat = (category or "").split(",")[0].strip() or "文件"
    if len(cat) > 6:
        cat = cat[:6]

    # 《和各月刊》用独立版式
    if (publisher or "").strip() == "和各月刊":
        return build_monthly_cover(title, out, w, h)

    key = cat if cat in CATEGORY_THEME else "文件"
    bg, bg2, accent, motif = CATEGORY_THEME[key]

    img = vertical_gradient((w, h), bg, bg2)
    draw = ImageDraw.Draw(img)

    # 右侧纹样区（安全区右半，裁切时仍可见主体）
    draw_motif(draw, motif, SAFE_L + 430, SAFE_R - 20, accent)

    # 公告：公文式双线边框，庄重
    if key == "公告":
        draw_full_frame(draw, tuple(int(c * 0.85 + 30) for c in accent), 28, 3, 1)

    # 左侧竖向色标：短红条压长金条，做出层次
    draw.rectangle([SAFE_L - 26, 0, SAFE_L - 18, h], fill=accent)
    draw.rectangle([SAFE_L - 8, 74, SAFE_L, h - 74], fill=CREAM)

    # 底边色带，收住画面
    draw.rectangle([0, h - 8, w, h], fill=accent)

    # 栏目标签
    cat_font = _font(26, bold=False)
    draw.text((TEXT_X, 86), cat, font=cat_font, fill=accent)
    label_w = _measure(draw, cat, cat_font)
    draw.line([TEXT_X, 132, TEXT_X + max(64, label_w + 28), 132], fill=accent, width=3)

    # 标题：大字优先；公告右留印章位，正文宽度回收，标题允许三行
    if key == "公告":
        max_w, max_lines = TEXT_W - 210, 3
    else:
        max_w, max_lines = TEXT_W, 2
    font, lines = fit_title(draw, title, max_w, max_lines=max_lines, hi=104, lo=30)
    line_h = int(font.size * 1.28)
    total = line_h * len(lines)
    ty = 150 + max(0, (250 - total) // 2)
    for line in lines:
        draw.text((TEXT_X, ty), line, font=font, fill=CREAM)
        ty += line_h

    # 站点标识
    site_font = _font(19, bold=False)
    draw.text((TEXT_X, h - 62), "和各共和国政府新闻发言网", font=site_font, fill=MUTED_ON_DARK)

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)
    return out


def _strip_comment(value):
    """去掉行尾注释（# ...），但保留引号内与无空格前缀的 #（如 C#）。"""
    if not value:
        return value
    if value[0] in "\"'":
        q = value[0]
        end = value.find(q, 1)
        return value[1:end] if end > 0 else value.strip(q)
    m = re.search(r"\s+#", value)
    if m:
        value = value[: m.start()]
    return value.strip()


def parse_frontmatter(text):
    """取出 front matter（不引入 yaml 依赖，只取需要的几个字段）。"""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}
    body = m.group(1)
    data = {}

    def get(key):
        mm = re.search(rf"(?m)^{key}:[ \t]*(.+?)[ \t]*\r?$", body)
        return _strip_comment(mm.group(1).strip()) if mm else None

    data["title"] = get("title")
    data["publisher"] = get("publisher")
    cats = get("categories")
    if cats:
        data["categories"] = [
            _strip_comment(c).strip('"').strip("'")
            for c in cats.strip("[]").split(",")
            if _strip_comment(c).strip('"').strip("'")
        ]
    else:
        data["categories"] = []
    img = re.search(r"(?m)^[ \t]+image:[ \t]*([^\s]+)", body)
    data["image"] = _strip_comment(img.group(1)) if img else None
    return data


def collect_posts():
    items = []
    for base in ("_posts", "_podcasts"):
        d = REPO / base
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            items.append((p, parse_frontmatter(p.read_text(encoding="utf-8"))))
    return items


def slug_for(post_path):
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", post_path.stem)


def set_frontmatter_image(post_path, image_path):
    """把 header.image 写回 front matter；值为空的 image: 行会被替换而不是追加。"""
    text = post_path.read_text(encoding="utf-8")
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)", text, re.S)
    head, body, tail = m.group(1), m.group(2), m.group(3)

    if re.search(r"(?m)^header:[ \t]*(#.*)?$", body):
        if re.search(r"(?m)^([ \t]+)image:[ \t]*\S*[ \t]*$", body):
            body = re.sub(
                r"(?m)^([ \t]+)image:[ \t]*\S*[ \t]*$",
                lambda mm: f"{mm.group(1)}image: {image_path}",
                body,
                count=1,
            )
        else:
            body = re.sub(
                r"(?m)^(header:[ \t]*(#.*)?)$",
                lambda mm: f"{mm.group(1)}\n  image: {image_path}",
                body,
                count=1,
            )
    else:
        body = body.rstrip() + f"\nheader:\n  image: {image_path}"

    post_path.write_text(head + body + tail + text[m.end():], encoding="utf-8")


def main(argv=None):
    _safe_stdout()
    ap = argparse.ArgumentParser(description="为文章生成封面并写入 header.image")
    ap.add_argument("--force", action="store_true", help="已有 header.image 的也重新生成")
    ap.add_argument("--post", help="只处理指定文章（可用文件名片段）")
    ap.add_argument("--no-write", action="store_true", help="只渲染 PNG，不改写 front matter")
    args = ap.parse_args(argv)

    made, skipped = 0, 0
    for post, fm in collect_posts():
        if args.post and args.post not in post.stem:
            continue
        if fm.get("image") and not args.force:
            skipped += 1
            continue
        title = fm.get("title") or slug_for(post)
        cats = fm.get("categories") or []
        # 集合本身也是栏目信息：_podcasts 下的文章统一按「播客」配色
        category = cats[0] if cats else ("播客" if post.parent.name == "_podcasts" else "")
        out = OUT_DIR / f"{slug_for(post)}.png"
        build_cover(title, category, out, publisher=fm.get("publisher") or "")
        if not args.no_write:
            set_frontmatter_image(post, "/" + out.relative_to(REPO).as_posix())
        print(f"OK  {post.name} -> {out.relative_to(REPO).as_posix()}")
        made += 1

    print(f"\n生成 {made} 张，跳过 {skipped} 篇（已有封面）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
