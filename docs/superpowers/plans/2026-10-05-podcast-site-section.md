# 和国播客 · 网站播客栏目（子项目 A）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 B 产出的音频/字幕/逐字稿接入 Jekyll 站点：注册 `podcasts` 集合、单集播放页（原生 `<audio>` + VTT）、栏目页、导航入口，以及标准播客 RSS 与封面。

**Architecture:** 集合与布局走主题既有机制（`archive`/`default` 布局、`documents-collection.html`、`_custom.scss`）；RSS 用自建 `podcast.xml`（GitHub Pages 白名单不允许第三方播客插件）；播客所需的机器可读元数据（`permalink` / `audio_bytes` / `header.og_image` / `episode`）由 `tools/podcast/build.py` 生成单集时写入 front matter，保持“生成器为唯一事实源”。

**Tech Stack:** Jekyll（Minimal Mistakes，本地覆盖主题）+ Liquid + SCSS；`tools/podcast` 为 Python 3.14 stdlib `unittest`；封面用 Pillow。

**Spec:** `docs/superpowers/specs/2026-10-05-podcast-site-section-design.md`

## Global Constraints

- 所有面向用户的内容与界面文案用中文。
- **不得新增 Jekyll 插件**（GitHub Pages 白名单只含 `jekyll-sitemap / jekyll-gist / jekyll-feed / jekyll-include-cache`）。
- 修改本地 `_layouts/`、`_includes/`、`_sass/`、`_data/`，不要改 Gem 主题。
- `_site/` 与 `.jekyll-cache/` 是生成产物，禁止编辑；验证=构建后检查 `_site/`。
- `_config.yml` 改动后需重新 `jekyll build`（serve 时需重启）。
- 单集路由固定为 `/podcast/`（栏目）与 `/podcast/<slug>/`（单集）。
- 播客**不设片尾/outro**；单集页不放评论、分享、作者卡。
- 播客 Python 测试命令：`python -m unittest discover -s tools/podcast/tests -t tools/podcast`。
- 本机控制台为 GBK；Python 脚本打印中文时用 `sys.stdout.reconfigure(errors="replace")`（`build.py` 已有 `_safe_stdout`）。测试用文件重定向取退出码。
- 封面为自产 `assets/images/podcast-cover.png`（1400×1400），须提交入库。

## Review Focus

计划外但很可能出问题的输入/边界（每条在其所属任务里有对应检查）:

1. **旧 md 缺 `audio_bytes`** → `<enclosure length>` 为空/错误、平台拒收。Task 5 检查：`length` == 实际 mp3 字节数。
2. **`related_post` 指向不存在的文章** → 页面应退化为显示该路径文本，而非空白或报错。Task 2 模板用 `| default: page.related_post` 兜底；检查正例渲染出原文标题。
3. **单集无 `episode` 字段** → 不得输出 `<itunes:episode>`，也不得显示“第 N 期”。Task 1 单测 `build_meta` 缺省不含该键；Task 5 模板用 `{% if ep.episode %}` 守卫。
4. **标题/摘要含 `&`、`<`、`>`** → RSS 必须转义，否则 XML 解析失败。Task 5 所有文本节点用 `xml_escape`；检查模板出现 `xml_escape` 且 `_site/podcast.xml` 可解析。
5. **`site.podcasts` 为空** → feed 仍须是合法 XML（空 channel）。Task 5 用 `xml.etree` 解析 `_site/podcast.xml` 验证。
6. **`hosts`/`guests` 为空数组** → 不显示空的“主持：/嘉宾：”标签。Task 2 模板用 `size > 0` 守卫；样片 `guests: []` 检查渲染结果不含“嘉宾：”。

---

### Task 1: 单集 front matter 增补（`episode` 字段 + `build_meta`）

**Files:**
- Modify: `tools/podcast/podcast_lib/config.py`
- Modify: `tools/podcast/build.py`
- Modify: `tools/podcast/scripts/hege-news-ep1.yml`
- Modify: `tools/podcast/tests/test_config.py`
- Modify: `tools/podcast/tests/test_build.py`
- Regenerate: `_podcasts/2026-10-05-hege-news-ep1.md`

**Interfaces:**
- Produces: `config.Episode.episode: int | None`（可选期号）。
- Produces: `build.build_meta(episode, audio_path, cover="/assets/images/podcast-cover.png") -> dict`，返回含 `permalink`、`audio_bytes`（`int`，来自 `audio_path.stat().st_size`）、`header.og_image`、以及（仅当 `episode.episode` 非 `None` 时）`episode` 的 front matter 字典。
- Consumes: `config.Episode`、`transcript.render_episode_md`（`front = dict(meta)` 后追加 `duration`/`transcript`，`yaml.safe_dump` 支持嵌套 dict）。

- [ ] **Step 1: 写失败的测试（config）**

在 `tools/podcast/tests/test_config.py` 的 `LoadEpisodeTest` 里追加：

```python
    def test_episode_optional(self):
        path = self._write(
            "title: 标题\ndate: 2026-10-05\n"
            "segments:\n  - role: anchor\n    text: '嗨'\n"
        )
        ep = config.load_episode(path, VOICES)
        self.assertIsNone(ep.episode)

    def test_parses_episode_number(self):
        path = self._write(
            "title: 标题\ndate: 2026-10-05\nepisode: 3\n"
            "segments:\n  - role: anchor\n    text: '嗨'\n"
        )
        ep = config.load_episode(path, VOICES)
        self.assertEqual(ep.episode, 3)

    def test_non_integer_episode_raises(self):
        path = self._write(
            "title: 标题\ndate: 2026-10-05\nepisode: abc\n"
            "segments:\n  - role: anchor\n    text: '嗨'\n"
        )
        with self.assertRaises(config.ConfigError):
            config.load_episode(path, VOICES)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: FAIL —— `AttributeError: 'Episode' object has no attribute 'episode'`

- [ ] **Step 3: 实现 config 的 `episode` 字段**

`tools/podcast/podcast_lib/config.py`：在 `Episode` 的 `intro: dict | None` 之后加一行：

```python
    episode: int | None
```

在 `load_episode` 里，`intro` 校验之后、`return Episode(` 之前加：

```python
    episode = data.get("episode")
    if episode is not None:
        if isinstance(episode, bool) or not isinstance(episode, int):
            raise ConfigError(f"{path} 的 episode 必须是整数")
```

在 `Episode(...)` 构造里，`intro=intro,` 之后加：

```python
        episode=episode,
```

- [ ] **Step 4: 运行 config 测试确认通过**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: PASS（新增 3 项 + 既有全绿）

- [ ] **Step 5: 写失败的测试（build_meta）**

在 `tools/podcast/tests/test_build.py` 末尾（`if __name__ == "__main__":` 之前）追加：

```python
class BuildMetaTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.audio = self.dir / "ep.mp3"
        self.audio.write_bytes(b"0123456789")

    def tearDown(self):
        self._tmp.cleanup()

    def _episode(self, **overrides):
        values = dict(
            slug="demo", title="标题", date="2026-10-05 09:00:00",
            episode_type="播报", excerpt="简介", publisher="和各政府网",
            related_post="/公告/x/", hosts=["云阳"], guests=[],
            segments=[], bed=[], cues=[], intro=None, episode=None,
        )
        values.update(overrides)
        return config.Episode(**values)

    def test_includes_podcast_fields(self):
        meta = build.build_meta(self._episode(), self.audio)
        self.assertEqual(meta["permalink"], "/podcast/demo/")
        self.assertEqual(meta["audio_bytes"], 10)
        self.assertEqual(meta["header"]["og_image"], "/assets/images/podcast-cover.png")
        self.assertNotIn("episode", meta)

    def test_episode_number_included_when_set(self):
        meta = build.build_meta(self._episode(episode=1), self.audio)
        self.assertEqual(meta["episode"], 1)
```

`test_build.py` 顶部需要 `from podcast_lib import config`（当前只 `importlib` 载入 build）。在 `SPEC.loader.exec_module(build)` 之后加：

```python
from podcast_lib import config  # noqa: E402
```

- [ ] **Step 6: 运行测试确认失败**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: FAIL —— `AttributeError: module 'build' has no attribute 'build_meta'`

- [ ] **Step 7: 实现 `build_meta` 并接入 `build_episode`**

`tools/podcast/build.py`：在 `COVER` 常量与 `build_meta` 函数：

在文件顶部路径常量附近加：

```python
COVER = "/assets/images/podcast-cover.png"
```

在 `resolve_intro` 之后加：

```python
def build_meta(episode, audio_path, cover=COVER):
    """构造单集 front matter（网站播客集合所需的机器可读字段）。"""
    audio_bytes = Path(audio_path).stat().st_size
    meta = {
        "title": episode.title,
        "excerpt": episode.excerpt,
        "date": episode.date,
        "episode_type": episode.episode_type,
        "audio": f"/assets/audio/podcast/{episode.slug}.mp3",
        "subtitles": f"/assets/audio/podcast/{episode.slug}.vtt",
        "permalink": f"/podcast/{episode.slug}/",
        "audio_bytes": audio_bytes,
        "header": {"og_image": cover},
        "hosts": episode.hosts,
        "guests": episode.guests,
        "related_post": episode.related_post,
        "publisher": episode.publisher,
    }
    if episode.episode is not None:
        meta["episode"] = episode.episode
    return meta
```

在 `build_episode` 中，把原来的 `meta = { ... }` 整块替换为：

```python
    meta = build_meta(episode, out_audio)
```

- [ ] **Step 8: 运行全部测试确认通过**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: PASS（全部）

- [ ] **Step 9: 给样片脚本加期号**

`tools/podcast/scripts/hege-news-ep1.yml`：在 `episode_type: 播报` 之后加一行：

```yaml
episode: 1
```

- [ ] **Step 10: 重新生成样片 md**

Run: `python tools/podcast/build.py hege-news-ep1`
Expected: 退出码 0；`_podcasts/2026-10-05-hege-news-ep1.md` 的 front matter 含 `permalink: /podcast/hege-news-ep1/`、`audio_bytes:`、`header:`（`og_image`）、`episode: 1`。

检查（PowerShell）：

```powershell
Select-String -Path "_podcasts\2026-10-05-hege-news-ep1.md" -Pattern "permalink|audio_bytes|og_image|episode:"
```

- [ ] **Step 11: 提交**

```bash
git add tools/podcast/podcast_lib/config.py tools/podcast/build.py \
        tools/podcast/scripts/hege-news-ep1.yml \
        tools/podcast/tests/test_config.py tools/podcast/tests/test_build.py \
        _podcasts/2026-10-05-hege-news-ep1.md
git commit -m "feat: 播客单集 front matter 增加 permalink/audio_bytes/og_image/期号"
```

---

### Task 2: 注册集合 + 单集播放页（可构建渲染）

**Files:**
- Modify: `_config.yml`
- Create: `_layouts/podcast.html`
- Create: `_includes/podcast-player.html`
- Modify: `_sass/minimal-mistakes/_custom.scss`

**Interfaces:**
- Consumes: 单集 md 的 front matter（`audio` / `subtitles` / `episode` / `episode_type` / `hosts` / `guests` / `duration` / `related_post`）。
- Produces: 布局名 `podcast`；include `podcast-player.html`；CSS 类 `.podcast-player` / `.podcast-meta` / `.podcast-related` / `.podcast-back`。

- [ ] **Step 1: 写失败的检查（页面尚未存在）**

Run: `bundle exec jekyll build` 之后：

```powershell
Test-Path "_site\podcast\hege-news-ep1\index.html"
```

Expected: `False`（集合未注册）

- [ ] **Step 2: 注册集合与默认值**

`_config.yml`：在 `plugins:` 段之前（例如 `# 归档` 注释之前）新增：

```yaml
# 播客集合（内容与播放页）
collections:
  podcasts:
    output: true
```

在 `defaults:` 列表里，`_posts` 条目之后追加：

```yaml
  # _podcasts
  - scope:
      path: ""
      type: podcasts
    values:
      layout: podcast
      author_profile: false
      comments: false
      share: false
      related: false
```

- [ ] **Step 3: 创建播放器 include**

`_includes/podcast-player.html`：

```html
{% if page.audio %}
<audio class="podcast-player" controls preload="metadata" src="{{ page.audio | relative_url }}">
  {% if page.subtitles %}<track kind="captions" src="{{ page.subtitles | relative_url }}" srclang="zh" label="中文" default>{% endif %}
  您的浏览器不支持音频播放，请
  <a href="{{ page.audio | relative_url }}">下载音频</a>。
</audio>
{% endif %}
```

- [ ] **Step 4: 创建单集布局**

`_layouts/podcast.html`：

```html
---
layout: default
classes: wide
---

<div id="main" role="main">
  <article class="page podcast-episode" itemscope itemtype="https://schema.org/CreativeWork"{% if page.locale %} lang="{{ page.locale }}"{% endif %}>
    {% if page.title %}<meta itemprop="headline" content="{{ page.title | replace: '|', '&#124;' | markdownify | strip_html | strip_newlines | escape_once }}">{% endif %}
    {% if page.excerpt %}<meta itemprop="description" content="{{ page.excerpt | markdownify | strip_html | strip_newlines | escape_once }}">{% endif %}
    {% if page.date %}<meta itemprop="datePublished" content="{{ page.date | date_to_xmlschema }}">{% endif %}

    <div class="page__inner-wrap">
      <p class="podcast-back"><a href="{{ '/podcast/' | relative_url }}">← 返回播客</a></p>
      <header>
        <h1 id="page-title" class="page__title" itemprop="headline">{{ page.title | markdownify | remove: "<p>" | remove: "</p>" }}</h1>
        <p class="podcast-meta">
          {%- if page.episode %}<span class="podcast-meta__item">第 {{ page.episode }} 期</span>{% endif -%}
          {%- if page.episode_type %}<span class="podcast-meta__item">{{ page.episode_type }}</span>{% endif -%}
          {%- if page.date %}<span class="podcast-meta__item">{{ page.date | date: site.date_format }}</span>{% endif -%}
          {%- if page.duration %}<span class="podcast-meta__item">时长 {{ page.duration }}</span>{% endif -%}
          {%- if page.hosts.size > 0 %}<span class="podcast-meta__item">主持：{{ page.hosts | join: "、" }}</span>{% endif -%}
          {%- if page.guests.size > 0 %}<span class="podcast-meta__item">嘉宾：{{ page.guests | join: "、" }}</span>{% endif -%}
        </p>
      </header>

      <section class="page__content" itemprop="text">
        {% include podcast-player.html %}
        {{ content }}
        {% if page.related_post %}
          {% assign related = site.posts | where: "url", page.related_post | first %}
          <p class="podcast-related">相关报道：<a href="{{ page.related_post | relative_url }}">{{ related.title | default: page.related_post }}</a></p>
        {% endif %}
      </section>
    </div>
  </article>
</div>
```

- [ ] **Step 5: 加样式**

`_sass/minimal-mistakes/_custom.scss` 末尾追加：

```scss
/* 播客：播放器与元信息
   ========================================================================== */

.podcast-player {
  display: block;
  width: 100%;
  margin: 0 0 1.25rem;
}

.podcast-meta {
  margin: 0.25rem 0 1rem;
  font-size: 0.85em;
  color: $hege-muted;
}

.podcast-meta__item {
  margin-right: 0.9em;
  white-space: nowrap;
}

.podcast-back {
  margin: 0 0 0.5rem;
  font-size: 0.85em;
}

.podcast-related {
  margin-top: 1.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid $hege-border;
  font-size: 0.9em;
}
```

- [ ] **Step 6: 构建**

Run: `bundle exec jekyll build`
Expected: 退出码 0，无 `Layout 'podcast' requested ... not found`。

- [ ] **Step 7: 检查渲染结果**

```powershell
$p = "_site\podcast\hege-news-ep1\index.html"
Test-Path $p
Select-String -Path $p -Pattern "<audio","kind=.captions",".vtt","相关报道","第 1 期" | ForEach-Object { $_.Line.Trim() }
```

Expected: 文件存在；含 `<audio`、`<track ... kind="captions"`、`.vtt`、`相关报道`（且链接文字为原文标题）、`第 1 期`；**不含**「嘉宾：」（样片 `guests: []`）。

- [ ] **Step 8: 检查 `related_post` 兜底（Review Focus 2）**

用文件编辑工具把 `_podcasts/2026-10-05-hege-news-ep1.md` 的 `related_post` 临时改为 `/不存在/`，重新构建并检查：

```powershell
bundle exec jekyll build
Select-String -Path "_site\podcast\hege-news-ep1\index.html" -Pattern "相关报道" | ForEach-Object { $_.Line.Trim() }
```

Expected: 构建成功；页面出现「相关报道：<a href="/不存在/">/不存在/</a>」，不报错、不空白。

还原（由生成器重写 md）：

```powershell
python tools/podcast/build.py hege-news-ep1
```

- [ ] **Step 9: 提交**

```bash
git add _config.yml _layouts/podcast.html _includes/podcast-player.html \
        _sass/minimal-mistakes/_custom.scss
git commit -m "feat: 注册 podcasts 集合并新增单集播放页与 VTT 字幕"
```

---

### Task 3: 栏目页 `/podcast/`

**Files:**
- Create: `_pages/podcast.md`

**Interfaces:**
- Consumes: 集合 `site.podcasts`；`_includes/documents-collection.html`（`collection` / `sort_by` / `sort_order` / `type`）。

- [ ] **Step 1: 写失败的检查**

Run: `bundle exec jekyll build` 之后：

```powershell
Test-Path "_site\podcast\index.html"
```

Expected: `False`

- [ ] **Step 2: 创建栏目页**

`_pages/podcast.md`：

```markdown
---
title: "播客"
layout: archive
permalink: /podcast/
author_profile: false
description: "和各中央广播与电视平台的音频节目：政府新闻播报与访谈。"
---

{% include documents-collection.html collection=podcasts sort_by=date sort_order=reverse type=list %}
```

- [ ] **Step 3: 构建**

Run: `bundle exec jekyll build`
Expected: 退出码 0。

- [ ] **Step 4: 检查列表**

```powershell
$p = "_site\podcast\index.html"
Test-Path $p
Select-String -Path $p -Pattern "/podcast/hege-news-ep1/","和国新闻","第 1 期" | ForEach-Object { $_.Line.Trim() }
```

Expected: 文件存在；含指向 `/podcast/hege-news-ep1/` 的链接与单集标题。

- [ ] **Step 5: 提交**

```bash
git add _pages/podcast.md
git commit -m "feat: 新增播客栏目页 /podcast/"
```

---

### Task 4: 播客封面生成器（TDD）

**Files:**
- Create: `tools/podcast/gen_cover.py`
- Create: `tools/podcast/tests/test_gen_cover.py`
- Created (generated): `assets/images/podcast-cover.png`

**Interfaces:**
- Produces: `gen_cover.build_cover(out=OUT, size=1400) -> Path`，生成 RGB 方形 PNG。
- Produces: 命令行 `python tools/podcast/gen_cover.py` → 写 `assets/images/podcast-cover.png`。

- [ ] **Step 1: 写失败的测试**

`tools/podcast/tests/test_gen_cover.py`：

```python
import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image

SPEC = importlib.util.spec_from_file_location(
    "gen_cover", Path(__file__).resolve().parents[1] / "gen_cover.py"
)
gen_cover = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen_cover)


class BuildCoverTest(unittest.TestCase):
    def test_square_rgb_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "cover.png"
            gen_cover.build_cover(out, size=1400)
            self.assertTrue(out.exists())
            with Image.open(out) as im:
                self.assertEqual(im.size, (1400, 1400))
                self.assertEqual(im.mode, "RGB")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: FAIL —— 无法载入 `gen_cover`（文件不存在）或 `AttributeError: module 'gen_cover' has no attribute 'build_cover'`

- [ ] **Step 3: 实现生成器**

`tools/podcast/gen_cover.py`：

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: PASS

- [ ] **Step 5: 生成封面**

Run: `python tools/podcast/gen_cover.py`
Expected: `OK ...\assets\images\podcast-cover.png (1400x1400)`

- [ ] **Step 6: 人工检查封面**

打开 `assets/images/podcast-cover.png`，确认：方形、方框与色带整齐、文字居中不溢出、无缺字（如字体缺失会退化为默认字体——若中文显示异常，改 `_font` 的字体名或安装微软雅黑后重跑）。

- [ ] **Step 7: 提交**

```bash
git add tools/podcast/gen_cover.py tools/podcast/tests/test_gen_cover.py \
        assets/images/podcast-cover.png
git commit -m "feat: 程序化生成播客方形封面（1400×1400）"
```

---

### Task 5: 播客 RSS `podcast.xml` + 发现链接

**Files:**
- Create: `podcast.xml`
- Modify: `_includes/head.html`

**Interfaces:**
- Consumes: `site.podcasts` 文档字段 `title` / `url` / `date` / `excerpt` / `audio` / `audio_bytes` / `duration` / `episode`；`site.url` / `site.title` / `site.description`。
- Produces: `/podcast.xml`（RSS 2.0 + iTunes + Atom 命名空间）。

- [ ] **Step 1: 写失败的检查**

Run: `bundle exec jekyll build` 之后：

```powershell
Test-Path "_site\podcast.xml"
```

Expected: `False`

- [ ] **Step 2: 创建 feed 模板**

`podcast.xml`（仓库根）：

```xml
---
layout: null
permalink: /podcast.xml
sitemap: false
---
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{{ site.title | xml_escape }} · 播客</title>
    <link>{{ '/' | absolute_url | xml_escape }}</link>
    <description>{{ site.description | xml_escape }}</description>
    <language>zh-cn</language>
    <itunes:author>和各中央广播与电视平台</itunes:author>
    <itunes:explicit>no</itunes:explicit>
    <itunes:category text="News" />
    <itunes:image href="{{ '/assets/images/podcast-cover.png' | absolute_url | xml_escape }}" />
    <atom:link href="{{ '/podcast.xml' | absolute_url | xml_escape }}" rel="self" type="application/rss+xml" />
    {% for ep in site.podcasts %}
    <item>
      <title>{{ ep.title | xml_escape }}</title>
      <link>{{ ep.url | absolute_url | xml_escape }}</link>
      <guid isPermaLink="true">{{ ep.url | absolute_url | xml_escape }}</guid>
      <pubDate>{{ ep.date | date_to_rfc822 }}</pubDate>
      <description>{{ ep.excerpt | xml_escape }}</description>
      <enclosure url="{{ ep.audio | absolute_url | xml_escape }}" length="{{ ep.audio_bytes }}" type="audio/mpeg" />
      <itunes:duration>{{ ep.duration | xml_escape }}</itunes:duration>
      <itunes:episodeType>full</itunes:episodeType>
      {% if ep.episode %}<itunes:episode>{{ ep.episode }}</itunes:episode>{% endif %}
      <itunes:image href="{{ '/assets/images/podcast-cover.png' | absolute_url | xml_escape }}" />
    </item>
    {% endfor %}
  </channel>
</rss>
```

- [ ] **Step 3: 在 `<head>` 加发现链接**

`_includes/head.html`：在 atom feed 的 `{% endunless %}`（第 7 行）之后加：

```html
<link rel="alternate" type="application/rss+xml" title="{{ site.title }} 播客" href="{{ '/podcast.xml' | relative_url }}">
```

- [ ] **Step 4: 构建**

Run: `bundle exec jekyll build`
Expected: 退出码 0。

- [ ] **Step 5: 用脚本校验 feed（含 Review Focus 1/4/5）**

把下面内容存成 `%TEMP%\check_feed.py` 再运行（或直接内联）：

```python
import os
import sys
import xml.etree.ElementTree as ET

root = ET.parse("_site/podcast.xml").getroot()
assert root.tag == "rss", root.tag
channel = root.find("channel")
assert channel is not None
items = channel.findall("item")
assert len(items) >= 1, "feed 应含至少一集"

mp3 = "assets/audio/podcast/hege-news-ep1.mp3"
enc = items[0].find("enclosure")
assert enc is not None, "缺 enclosure"
assert enc.get("type") == "audio/mpeg"
assert int(enc.get("length")) == os.path.getsize(mp3), (enc.get("length"), os.path.getsize(mp3))
assert enc.get("url").startswith("http"), enc.get("url")

ns = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
assert channel.find("itunes:image", ns) is not None
assert channel.find("itunes:category", ns).get("text") == "News"
assert items[0].find("itunes:duration", ns).text == "01:43"
assert items[0].find("itunes:episode", ns).text == "1"
print("feed OK:", enc.get("length"), "bytes;", len(items), "item(s)")
```

Run: `python -X utf8 <path>`（工作目录 = 仓库根）
Expected: `feed OK: <bytes> bytes; 1 item(s)`

> XML 转义检查（Review Focus 4）：确认模板中所有文本节点都经 `xml_escape`：

```powershell
Select-String -Path "podcast.xml" -Pattern "xml_escape" | Measure-Object | ForEach-Object { "xml_escape 出现 $($_.Count) 次" }
```

Expected: 出现次数 ≥ 8（title/description/link/guid/excerpt/enclosure/封面/self 等）。

- [ ] **Step 6: 检查 XML 转义（Review Focus 4）**

用文件编辑工具把 `_podcasts/2026-10-05-hege-news-ep1.md` 的 `excerpt` 临时改为含特殊字符，例如 `excerpt: A & B < C > D`，重新构建并解析：

```powershell
bundle exec jekyll build
python -X utf8 -c "import xml.etree.ElementTree as ET; r=ET.parse('_site/podcast.xml').getroot(); print('parsed OK', r.find('channel/item/description').text)"
```

Expected: 解析成功（不抛 `xml.etree.ElementTree.ParseError`），description 文本含 `A & B < C > D`。

还原（重写 md）：

```powershell
python tools/podcast/build.py hege-news-ep1
```

- [ ] **Step 7: 检查空集合仍是合法 XML（Review Focus 5）**

临时移走 `_podcasts` 目录，构建后解析 feed，应合法且 0 个 item；随后还原并重建：

```powershell
Rename-Item _podcasts _podcasts_bak
bundle exec jekyll build
python -X utf8 -c "import xml.etree.ElementTree as ET; c=ET.parse('_site/podcast.xml').getroot().find('channel'); print('parsed OK, items =', len(c.findall('item')))"
Rename-Item _podcasts_bak _podcasts
bundle exec jekyll build
```

Expected: 输出 `parsed OK, items = 0`；还原后构建成功。

- [ ] **Step 8: 检查 sitemap 不含 feed、含单集**

```powershell
Select-String -Path "_site\sitemap.xml" -Pattern "podcast.xml"
Select-String -Path "_site\sitemap.xml" -Pattern "/podcast/hege-news-ep1/"
```

Expected: 第一条无匹配（`sitemap: false` 生效）；第二条有匹配。

- [ ] **Step 9: 提交**

```bash
git add podcast.xml _includes/head.html
git commit -m "feat: 播客 RSS /podcast.xml 与 head 发现链接"
```

---

### Task 6: 导航入口

**Files:**
- Modify: `_data/navigation.yml`

- [ ] **Step 1: 写失败的检查**

Run: `bundle exec jekyll build` 之后：

```powershell
Select-String -Path "_site\index.html" -Pattern 'href="/podcast/"'
```

Expected: 无匹配

- [ ] **Step 2: 加导航项**

`_data/navigation.yml`：在「社论」与「意见建议」之间插入：

```yaml
  - title: "播客"
    url: /podcast/
```

改后 `main:` 顺序为：首页 / 要闻 / 新闻 / 公告 / 社论 / 播客 / 意见建议。

- [ ] **Step 3: 构建并检查**

Run: `bundle exec jekyll build`

```powershell
Select-String -Path "_site\index.html" -Pattern 'href="/podcast/"' | ForEach-Object { $_.Line.Trim() }
```

Expected: 有匹配（导航含「播客 → /podcast/」）。

- [ ] **Step 4: 提交**

```bash
git add _data/navigation.yml
git commit -m "feat: 主导航新增播客入口"
```

---

### Task 7: 文档更新与全量回归

**Files:**
- Modify: `docs/播客制作规范.md`
- Modify: `tools/podcast/README.md`

- [ ] **Step 1: 更新制作规范**

`docs/播客制作规范.md`「五、命名与发布」一节末尾追加：

```markdown
- 网站栏目：单集经 `_podcasts` 集合发布到 `/podcast/<slug>/`，栏目页 `/podcast/`；播客 RSS 为 `/podcast.xml`。
- 发布前确认单集 front matter 含 `permalink`、`audio_bytes`、`header.og_image`（由 `build.py` 生成）；`audio_bytes` 必须与音频字节一致，否则 RSS `enclosure` 不正确。
- 播客封面：`assets/images/podcast-cover.png`（1400×1400），由 `python tools/podcast/gen_cover.py` 生成。
- 网站不设片尾/outro。
```

- [ ] **Step 2: 更新 README**

`tools/podcast/README.md` 末尾追加：

```markdown
## 网站附产物

- 单集发布到 `/podcast/<slug>/`，栏目页 `/podcast/`，RSS `/podcast.xml`（见 `docs/播客制作规范.md`）。
- 生成播客封面：`python tools/podcast/gen_cover.py` → `assets/images/podcast-cover.png`。
```

- [ ] **Step 3: 全量回归构建**

Run: `bundle exec jekyll build`
Expected: 退出码 0。

逐项检查：

```powershell
Test-Path "_site\podcast\index.html"
Test-Path "_site\podcast\hege-news-ep1\index.html"
Test-Path "_site\podcast.xml"
Test-Path "_site\assets\audio\podcast\hege-news-ep1.mp3"
Test-Path "_site\assets\audio\podcast\hege-news-ep1.vtt"
Test-Path "_site\assets\images\podcast-cover.png"
Test-Path "_site\news\index.html"
Test-Path "_site\archive\index.html"
Test-Path "_site\feedback\index.html"
Test-Path "_site\feed.xml"
Select-String -Path "_site\assets\js\lunr\lunr-store.js" -Pattern "hege-news-ep1"
```

Expected: 全部 `True`；lunr store 含单集 URL（搜索索引包含播客逐字稿）。

- [ ] **Step 4: 播客 Python 测试回归**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: PASS（全部）

- [ ] **Step 5: 提交**

```bash
git add docs/播客制作规范.md tools/podcast/README.md
git commit -m "docs: 播客网站栏目与封面的发布说明"
```

---

## 完成后

- 与用户确认是否 `git push origin main`（会触发 `gh-pages` 部署）。
- 子项目 C（内容生产）另行 brainstorm → spec → plan。
