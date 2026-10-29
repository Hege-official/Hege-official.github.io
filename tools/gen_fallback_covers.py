"""生成按栏目区分的兜底封面 SVG（站点模板兜底用）。

没有 header.image 的文章由 _includes/cover_src.html 指向这些静态文件，
保证即使忘了跑 gen_article_cover.py，也不会出现空白占位。
配色与版式与 tools/gen_article_cover.py 保持一致。
用法：python tools/gen_fallback_covers.py
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "assets" / "images"

W, H = 1638, 500
SAFE_L, SAFE_R = (W - 889) // 2, (W + 889) // 2   # 374 .. 1263
TEXT_X = SAFE_L + 72                               # 446

# key -> (深色底, 渐变偏色, 强调色, 纹样, 栏目名)
PALETTE = {
    "news": ("#0b1f3a", "#142e54", "#c8a96a", "grid", "新闻"),
    "yaowen": ("#0b1f3a", "#18345c", "#c43e32", "bands", "要闻"),
    "gonggao": ("#7a161a", "#a81c1c", "#d6b676", "seal", "公告"),
    "shelun": ("#4a1a1e", "#70282a", "#c8a96a", "rule", "社论"),
    "weihu": ("#14302c", "#224a42", "#c8a96a", "grid", "维护"),
    "boke": ("#10223e", "#1c3660", "#c43e32", "wave", "播客"),
}


def motif(kind: str, accent: str) -> str:
    x0, x1 = SAFE_L + 430, SAFE_R - 20
    cx = (x0 + x1) // 2
    if kind == "grid":
        v = "".join(f'<line x1="{x0 + i * 30}" y1="0" x2="{x0 + i * 30}" y2="500"/>' for i in range(15))
        h = "".join(f'<line x1="{x0}" y1="{i * 30}" x2="{x1}" y2="{i * 30}"/>' for i in range(18))
        extra = "".join(
            f'<line x1="{x0 + 60 + k * 55}" y1="500" x2="{x0 + 250 + k * 55}" y2="0"/>' for k in range(3)
        )
        return (
            f'<g stroke="{accent}" opacity="0.24">{v}{h}</g>'
            f'<g stroke="{accent}" opacity="0.55">{extra}</g>'
        )
    if kind == "seal":
        cx, cy, r = SAFE_R - 170, 250, 96
        star = ""
        pts = []
        for i in range(10):
            import math as _m
            ang = -_m.pi / 2 + i * _m.pi / 5
            rad = r * 0.30 if i % 2 == 0 else r * 0.30 * 0.42
            pts.append(f"{cx + _m.cos(ang) * rad:.1f},{cy + _m.sin(ang) * rad:.1f}")
        star = f'<polygon points="{" ".join(pts)}" fill="{accent}" opacity="0.6"/>'
        return (
            f'<rect x="28" y="28" width="1582" height="444" fill="none" stroke="{accent}" stroke-width="3" opacity="0.55"/>'
            f'<rect x="40" y="40" width="1558" height="420" fill="none" stroke="{accent}" stroke-width="1" opacity="0.4"/>'
            f'<g fill="none" stroke="{accent}">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke-width="6" opacity="0.55"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r - 16}" stroke-width="2" opacity="0.35"/></g>'
            f"{star}"
        )
    if kind == "bands":
        lines = "".join(
            f'<line x1="{x0 + 30 + i * 14}" y1="{454 - i * 30}" x2="{x1 - 30}" y2="{454 - i * 30}"/>'
            for i in range(7)
        )
        return f'<g stroke="{accent}" stroke-width="3" opacity="0.3">{lines}</g>'
    if kind == "wave":
        waves = "".join(
            f'<path d="M{x0} 250 q42 -{26 + k * 14} 85 0 t85 0 t85 0 t85 0 t85 0 t85 0" stroke-width="2"/>'
            for k in range(6)
        )
        return f'<g fill="none" stroke="{accent}" opacity="0.35">{waves}</g>'
    lines = (
        f'<line x1="{cx + 20}" y1="70" x2="{cx + 20}" y2="430"/>'
        f'<line x1="{cx - 90}" y1="70" x2="{cx + 130}" y2="70"/>'
        f'<line x1="{cx - 90}" y1="430" x2="{cx + 130}" y2="430"/>'
    )
    return f'<g stroke="{accent}" stroke-width="2" opacity="0.4">{lines}</g>'


def build(key: str) -> str:
    bg, bg2, accent, kind, label = PALETTE[key]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1638 500" width="1638" height="500" role="img" aria-label="{label}栏目封面">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{bg}"/>
      <stop offset="1" stop-color="{bg2}"/>
    </linearGradient>
  </defs>
  <rect width="1638" height="500" fill="url(#g)"/>
  {motif(kind, accent)}
  <rect x="{SAFE_L - 26}" y="0" width="8" height="500" fill="{accent}"/>
  <rect x="{SAFE_L - 8}" y="74" width="8" height="352" fill="#f6f2e8"/>
  <rect x="0" y="492" width="1638" height="8" fill="{accent}"/>
  <text x="{TEXT_X}" y="112" font-family="Microsoft YaHei, SimHei, sans-serif" font-size="26" fill="{accent}">{label}</text>
  <line x1="{TEXT_X}" y1="132" x2="{TEXT_X + 92}" y2="132" stroke="{accent}" stroke-width="3"/>
  <text x="{TEXT_X}" y="420" font-family="Microsoft YaHei, SimHei, sans-serif" font-size="19" fill="#96a2b6">和各共和国政府新闻发言网</text>
</svg>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for key in PALETTE:
        path = OUT / f"fallback-{key}.svg"
        path.write_text(build(key), encoding="utf-8")
        print(f"OK  {path.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
