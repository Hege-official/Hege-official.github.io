# 和国播客 · 网站播客栏目（子项目 A）· 设计规格

- 日期：2026-10-05
- 状态：已通过对话设计评审，待用户审阅本规格
- 范围：把子项目 B 产出的音频/字幕/逐字稿接入网站：注册集合、栏目页、单集页与播放器、导航入口、标准播客 RSS 与封面
- 上游：`docs/superpowers/specs/2026-10-05-podcast-audio-pipeline-design.md`（子项目 B，已实现）
- 说明：批量内容生产（子项目 C）另立规格；本规格只做 A

## 1. 背景与目标

子项目 B 已产出可听样片：`assets/audio/podcast/hege-news-ep1.mp3`、同名 `.vtt` 字幕，以及 `_podcasts/2026-10-05-hege-news-ep1.md`（逐字稿）。但目前：

- `_podcasts/` **未在 `_config.yml` 注册集合**，Jekyll 不构建、不发布该目录；
- 无栏目页、无播放器、无导航入口、无播客 RSS；
- 站点仅有一张横版 logo，没有符合播客平台要求的方形封面。

A 的目标：让访客能在站内**收听**（带字幕），同时对外提供**标准播客 RSS**，可提交到 Apple Podcasts / 小宇宙等平台。

A 的成功标准：

1. 访问 `/podcast/` 看到按期倒序的栏目页；点进 `/podcast/<slug>/` 能播放音频、显示同步 VTT 字幕、读到全文逐字稿并跳转关联原文。
2. 主导航出现「播客」入口。
3. `/podcast.xml` 是结构合法、字段完整的播客 RSS（含 `enclosure` 的 `url/length/type`、iTunes 标签、封面），可由第三方播客客户端解析。
4. 播客逐字稿进入站内搜索。
5. 改动不破坏现有页面构建。

## 2. 非目标

- 不做子项目 C 的内容生产（新闻稿/访谈稿、事实核对）。
- 不引入第三方 JS 播放器库、不写播放器自定义 JS（v1 用原生 HTML5）。
- 不做 `podcast:chapters` 章节标记、不做逐字稿点击跳转、不做平台自动提交。
- 不做音频外链托管、不做分页订阅统计/分析。
- 不改动 B 的音频生产逻辑（仅在其生成的 front matter 上**增加**字段）。

## 3. 现状与约束

- 站点：Jekyll + Minimal Mistakes（`theme: minimal-mistakes-jekyll ~> 4.24.0`），本地 `_layouts/_includes/_sass/_data` 覆盖 Gem 主题。
- GitHub Pages **白名单**只允许 `jekyll-sitemap / jekyll-gist / jekyll-feed / jekyll-include-cache`，**不能新增**第三方播客插件 → RSS 必须以自建 Liquid 模板实现。
- `assets/js/lunr/lunr-store.js` 会遍历 `site.collections` 中 `search != false` 的文档，注册集合后逐字稿自动进搜索。
- 列表渲染可复用 `_includes/documents-collection.html` + `_includes/archive-single.html`。
- 现有页面模式：`_pages/news.md` 等用 `layout: archive`；`_layouts/archive.html` 提供 `#main`、面包屑与标题。
- `site.url = https://hege-official.github.io/`（`absolute_url` 可用）。

## 4. 技术选型

- **播放器**：浏览器原生 `<audio controls>` + `<track kind="captions">`（VTT 字幕可开关），零 JS 依赖。
- **RSS**：自建 `podcast.xml` Liquid 模板（`layout: null`），手写 iTunes / Atom 命名空间标签。
- **元数据**：由 `tools/podcast/build.py` 生成单集 md 时写入 front matter（保持“唯一事实源在生成器”），RSS 与页面直接消费。
- **封面**：`tools/podcast/gen_cover.py`（Pillow）程序化生成 1400×1400 方形 PNG，属自产。

## 5. 集合与路由

`_config.yml` 新增：

```yaml
collections:
  podcasts:
    output: true
```

`defaults` 新增（单集默认）：

```yaml
  - scope:
      path: ""
      type: podcasts
    values:
      layout: podcast
      author_profile: false
      comments: false
      share: false
```

路由（用户定）：

- 栏目页：`/podcast/`
- 单集页：`/podcast/<slug>/`，由 `build.py` 在 front matter 显式写 `permalink: /podcast/<slug>/`（不依赖文件名，URL 稳定；`_podcasts/YYYY-MM-DD-<slug>.md` 文件名不变）。

## 6. 单集页 `_layouts/podcast.html` 与播放器

`_layouts/podcast.html`（基于 `layout: default`，含面包屑回 `/podcast/`；复用单页的 `page__inner-wrap` / `page__content` 类以继承主题排版）：

1. 面包屑 + 标题。
2. **元信息条**：期号（`episode`，显示“第 N 期”）、类型（`episode_type`）、主持人（`hosts`）、嘉宾（`guests`）、时长（`duration`）、发布日期。
3. **播放器**（`{% include podcast-player.html %}`）。
4. **正文**：`{{ content }}`（逐字稿）。
5. **关联原文**：若 `page.related_post`，在 `site.posts` 中按 `url` 找到原文，显示「相关报道：<原文标题>」链接；找不到时退化为直接显示该路径链接。

`_includes/podcast-player.html`：

```html
{% if page.audio %}
<audio class="podcast-player" controls preload="metadata" src="{{ page.audio | relative_url }}">
  {% if page.subtitles %}<track kind="captions" src="{{ page.subtitles | relative_url }}" srclang="zh" label="中文" default>{% endif %}
  您的浏览器不支持音频播放。
</audio>
{% endif %}
```

不放侧栏，不启用评论/分享/作者卡。

## 7. 栏目页 `_pages/podcast.md`

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

按期倒序显示单集；卡片样式复用 `archive-single.html`（标题、日期、`excerpt`）。

## 8. 播客 RSS `podcast.xml`

仓库根新增 `podcast.xml`：

```
---
layout: null
permalink: /podcast.xml
sitemap: false
---
```

结构（`rss` + `itunes` + `atom` 命名空间）：

- `<channel>`
  - `<title>{{ site.title }} · 播客</title>`
  - `<link>{{ '/' | absolute_url }}</link>`
  - `<description>{{ site.description }}</description>`
  - `<language>zh-cn</language>`
  - `<itunes:author>和各中央广播与电视平台</itunes:author>`
  - `<itunes:explicit>no</itunes:explicit>`
  - `<itunes:category text="News" />`
  - `<itunes:image href="{{ '/assets/images/podcast-cover.png' | absolute_url }}" />`
  - `<atom:link href="{{ '/podcast.xml' | absolute_url }}" rel="self" type="application/rss+xml" />`
- 每集 `<item>`（遍历 `site.podcasts`）
  - `<title>`、`<link>{{ ep.url | absolute_url }}</link>`
  - `<guid isPermaLink="true">{{ ep.url | absolute_url }}</guid>`
  - `<pubDate>{{ ep.date | date_to_rfc822 }}</pubDate>`
  - `<description>{{ ep.excerpt | xml_escape }}</description>`
  - `<enclosure url="{{ ep.audio | absolute_url }}" length="{{ ep.audio_bytes }}" type="audio/mpeg" />`
  - `<itunes:duration>{{ ep.duration }}</itunes:duration>`
  - `<itunes:episodeType>full</itunes:episodeType>`
  - `{% if ep.episode %}<itunes:episode>{{ ep.episode }}</itunes:episode>{% endif %}`
  - `<itunes:image href="...封面..." />`

字段取值与默认（用户确认）：

- iTunes 分类：`News`（新闻）；后续可细化子类。
- `itunes:explicit`：`no`。
- 联系邮箱用于平台提交，不写入 feed 的必填项（`itunes:owner` 可选；本规格**不写** owner 块）。
- `enclosure@length` 依赖 `audio_bytes`（见第 9 节）。
- `itunes:duration` 直接用生成时的 `duration`（`MM:SS`，iTunes 接受）。

在 `_includes/head.html` 增加一行发现链接：

```html
<link rel="alternate" type="application/rss+xml" title="和国播客" href="{{ '/podcast.xml' | relative_url }}">
```

## 9. `build.py` front matter 增补

生成 `_podcasts/<date>-<slug>.md` 时，在现有字段基础上**新增**：

- `permalink: /podcast/<slug>/`
- `audio_bytes: <int>`（`assets/audio/podcast/<slug>.mp3` 的字节数，`<enclosure length>` 必需）
- `header.og_image: /assets/images/podcast-cover.png`（社交分享图；主题的 `seo.html` 读取 `header.og_image`，且 hero 只认 `header.image`，故不会产生页首大图）
- `episode: <n>`（可选；来自脚本源新增可选字段 `episode`，缺省不输出）

> 说明：主题不使用 `page.image` 字段；列表缩略图用的是 `header.teaser`。本规格**不**给单集设 `header.teaser`（方形封面作列表缩略观感待定），如需再加。

样片脚本 `tools/podcast/scripts/hege-news-ep1.yml` 增加 `episode: 1`。

> 兼容：B 规格声明 front matter 与 A 对齐；此处仅**新增**字段，不改既有字段，也不改 `docs/播客制作规范.md` 已记录的口播/素材规则。

## 10. 封面生成 `tools/podcast/gen_cover.py`

- 用 Pillow 生成 `assets/images/podcast-cover.png`：1400×1400，方形。
- 视觉：沿用 `hege` 皮肤主色（藏青底 + 香槟金细边），叠加站名「和各政府网」/栏目名「和国播客」文字，可选用 `rhclogo1.png`。
- 自产，无第三方授权；在 `tools/podcast/README.md` 记录生成命令。
- 交付即提交该 PNG（RSS 需要绝对 URL 可访问）。

## 11. 导航 / 搜索 / 样式

- `_data/navigation.yml`：在「社论」与「意见建议」之间插入 `播客 → /podcast/`。
- 搜索：注册集合后逐字稿自动进入 lunr 全文索引（用户确认保留）；如需排除，可在单集 front matter 设 `search: false`。
- 样式：`_sass/minimal-mistakes/_custom.scss` 新增 `.podcast-player`、`.podcast-meta`、`.podcast-related`，沿用 `$hege-*` 变量。

## 12. 验证方式

本仓库无单元测试，验收 = 构建成功 + 检查产物：

1. `bundle exec jekyll build` 成功退出。
2. `_site/podcast/index.html` 存在且包含单集链接。
3. `_site/podcast/hege-news-ep1/index.html` 含 `<audio` 与 `<track ... .vtt`，`track@src` 指向存在的 `/assets/audio/podcast/hege-news-ep1.vtt`。
4. `_site/podcast.xml` 存在，XML 可解析（如用 Python `xml.etree` 验证）；`enclosure@length` == 实际 `hege-news-ep1.mp3` 字节数；`enclosure@url` 为绝对 URL；`itunes:*` 标签齐全。
5. `_site/assets/js/lunr/lunr-store.js`（或搜索索引）包含该单集标题。
6. 回归：现有页面（首页、`/news/`、`/archive/`、文章页、`/feedback/`、`feed.xml`）仍正常构建；`sitemap.xml` 含单集 URL、不含 `podcast.xml`。
7. `tools/podcast` 现有测试仍通过（`python -m unittest discover -s tools/podcast/tests -t tools/podcast`）。

## 13. 风险与取舍

- **GH Pages 白名单**：不能加播客插件，故 RSS 为自建模板，后续 iTunes 规范变化需手工维护。
- **`audio_bytes` 同步**：音频改变必须重跑 `build.py`，否则 `enclosure@length` 过期（生成器为唯一源，属可接受的确定性策略）。
- **封面自产**：风格需一次迭代确认，可能后续微调。
- **搜索体积**：逐字稿全文入 lunr 会增大索引；当前仅 1 集，量小。
- **手改产物会被覆盖**：`_podcasts/*.md` 由 `build.py` 生成，直接编辑会在下次构建被覆盖（唯一源仍是 `scripts/*.yml`）。
- **平台收录**：RSS 合规不代表自动被平台收录，需人工提交（非本规格范围）。
- **不做章节**：`podcast:chapters` 与点击跳转留待后续。

## 14. 决策记录

- A 成功标准：站内收听 + 标准播客 RSS（用户选择）。
- 路由：栏目 `/podcast/`、单集 `/podcast/<slug>/`（用户选择）。
- 单集页内容：播放器 + 全文逐字稿 + 关联原文（用户选择）。
- 入口：仅主导航，位于「社论」与「意见建议」之间（用户选择）。
- 封面：程序化生成 1400×1400（用户选择）。
- 播放器/RSS 实现：原生 HTML5 + 自建 Liquid（路线 1，用户确认）。
- iTunes 分类默认 `News`、explicit=no（本规格默认，可调整）。

## 15. 后续（非本规格范围）

- **C. 内容生产**：按 Hegewiki 正典生产播报稿与访谈稿。
- `podcast:chapters` / 逐字稿点击跳转 / 播放进度高亮。
- 封面迭代与订阅引导（平台提交、站内订阅按钮）。
- 音频外链托管（应对仓库体积）。
- GitHub Actions 版本升级（`actions/checkout`、`peaceiris/actions-gh-pages` 的 Node 20 弃用警告，独立小改动）。
