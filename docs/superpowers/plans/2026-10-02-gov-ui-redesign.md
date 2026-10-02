# 和各政府网 UI 政务化重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把基于 Minimal Mistakes 的“和各政府网”重构为藏青 + 中国红 + 香槟金、中国政务门户风格且高级现代的整站 UI，含新的聚合首页。

**Architecture:** 不改主题、不加前端框架。在 `assets/css/main.scss` 末尾追加一个独立的 `_gov.scss` 样式层，用新的 `_hege` 皮肤覆盖主题变量；重写 `masthead.html` / `footer.html`，新增 `gov/` 局部模板与 `gov-home` 布局；用主题已有的 `category` 布局承载栏目页，用单个 `feedback.md` 承载 giscus。

**Tech Stack:** Jekyll 4.4 + Minimal Mistakes 4.24（本地 vendored）、Liquid、Sass（sass-embedded）、jekyll-include-cache、jekyll-sitemap。

**Spec:** `docs/superpowers/specs/2026-10-02-gov-ui-redesign-design.md`

## Global Constraints

- 不新增 JS 依赖、不改 `assets/js/`，因此**不需要** `rake js`。
- 不引入外部字体 CDN；沿用仓库内 `STZhongsong`（标题）与 `Yahei`（正文）。
- 所有面向用户的文案为简体中文。
- 精确色值：藏青 `#0b1f3a`、深藏青 `#071527`、中国红 `#a81c1c`、香槟金 `#c8a96a`、表面 `#f6f7f9`、正文 `#1f2a37`、次要 `#5b6672`、描边 `#e3e6ea`、链接 `#1d4e89`。
- 每个任务结束时执行 `bundle exec jekyll build --trace` 必须成功。
- 不编辑 `_site/`、`.jekyll-cache/`、已安装的 Gem、`gh-pages` 分支。
- 除 `/feedback/` 外，任何页面不得输出 giscus 评论容器或“评论功能不支持”。

## Review Focus

- 空分类：`新闻`/`公告`/`社论` 任一分类暂无文章时，首页区块应为空而非报错或只留空标题。
- 无 `header.image` / `header.teaser` 的文章：首页卡片与列表应显示藏青占位块，不能出现破图。
- `publisher` 缺失：文章页回退为站点名，绝不渲染空标签。
- 评论泄漏：文章页不得包含 `giscus` 或“评论功能不支持”；仅 `/feedback/` 含 giscus。
- 分页残留：`_site/` 下不得再生成 `page2/`、`page3/` 等目录。
- 搜索：`/search/` 页面与页头搜索覆盖层可正常显示，输入为空时不报错。

---

### Task 1: 皮肤、全局配置与样式层骨架

**Files:**
- Create: `_sass/minimal-mistakes/skins/_hege.scss`
- Create: `_sass/minimal-mistakes/_gov.scss`
- Modify: `_config.yml`
- Modify: `assets/css/main.scss`

**Interfaces:**
- Consumes: 无。
- Produces: Sass 变量 `$hege-navy`、`$hege-navy-deep`、`$hege-red`、`$hege-gold`、`$hege-surface`、`$hege-ink`、`$hege-muted`、`$hege-border`、`$hege-link`；CSS 类 `.gov-section`、`.gov-section__head`、`.gov-section__title`、`.gov-section__more`。

- [ ] **Step 1: 写验证命令，确认当前失败**

在仓库根执行（PowerShell）：

```powershell
bundle exec jekyll build --trace
if (-not (Select-String -Path _site\assets\css\main.css -Pattern '#0b1f3a' -Quiet)) { throw 'FAIL: 皮肤尚未生效' }
```

Expected: 构建可能成功，但断言抛 `FAIL: 皮肤尚未生效`。

- [ ] **Step 2: 修改 `_config.yml`**

把第 14 行 `minimal_mistakes_skin    : "default"` 改为：

```yaml
minimal_mistakes_skin    : "hege" # 政务风皮肤：藏青 + 中国红 + 香槟金
```

在 `permalink:` 区块附近新增中文日期格式（放在 `timezone: Asia/Shanghai` 下一行）：

```yaml
date_format: "%Y年%m月%d日"
```

删除分页配置。找到并**删除**这两行：

```yaml
paginate: 5 # 要显示的文章数量
paginate_path: /page:num/
```

把 `defaults` 区块的 posts 值改为（关闭作者卡与评论，补充发布单位默认值）：

```yaml
defaults:
  # _posts
  - scope:
      path: ""
      type: posts
    values:
      layout: single
      author_profile: false
      read_time: true
      comments: false
      share: false
      related: true
      publisher: "和各政府网"
```

- [ ] **Step 3: 创建皮肤 `_sass/minimal-mistakes/skins/_hege.scss`**

```scss
/* ==========================================================================
   Hege skin — 政务风：藏青 + 中国红 + 香槟金
   ========================================================================== */

/* 自定义 token */
$hege-navy: #0b1f3a;
$hege-navy-deep: #071527;
$hege-red: #a81c1c;
$hege-gold: #c8a96a;
$hege-surface: #f6f7f9;
$hege-ink: #1f2a37;
$hege-muted: #5b6672;
$hege-border: #e3e6ea;
$hege-link: #1d4e89;

/* 覆盖 Minimal Mistakes 变量（必须在主题 partials 之前生效） */
$background-color: #fff;
$text-color: $hege-ink;
$muted-text-color: $hege-muted;
$border-color: $hege-border;
$form-background-color: $hege-surface;
$footer-background-color: $hege-navy-deep;

$primary-color: $hege-navy;
$focus-color: $hege-red;
$link-color: $hege-link;
$link-color-hover: $hege-red;
$link-color-visited: $hege-link;
$masthead-link-color: $hege-navy;
$masthead-link-color-hover: $hege-red;
$navicon-link-color-hover: $hege-navy;

$border-radius: 0;
$box-shadow: 0 1px 2px rgba(7, 21, 39, 0.04), 0 8px 24px rgba(7, 21, 39, 0.06);
```

- [ ] **Step 4: 创建样式层骨架 `_sass/minimal-mistakes/_gov.scss`**

```scss
/* ==========================================================================
   Hege government layout layer
   仅在 main.scss 中于主题之后导入，可使用主题变量与上述 $hege-* token。
   ========================================================================== */

/* 容器与宽度 */
#main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.page,
.archive {
  max-width: none;
  width: 100%;
}

.page__content {
  width: 100% !important;
  margin-right: 0 !important;
}

/* 链接 */
#main a {
  color: $hege-link;

  &:hover {
    color: $hege-red;
  }
}

/* 栏目分节头：左红竖条 + 标题 + 更多 */
.gov-section {
  margin: 2.5rem 0 1rem;
}

.gov-section__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  border-bottom: 1px solid $hege-border;
  padding-bottom: 0.5rem;
}

.gov-section__title {
  position: relative;
  margin: 0;
  padding-left: 0.75rem;
  font-family: "STZhongsong", serif;
  font-size: 1.35rem;
  color: $hege-navy;

  &::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0.15em;
    bottom: 0.15em;
    width: 3px;
    background: $hege-red;
  }
}

.gov-section__more {
  font-size: 0.85rem;
  color: $hege-muted;
}
```

- [ ] **Step 5: 在 `assets/css/main.scss` 末尾导入样式层**

把最后一行 `@import "minimal-mistakes/custom";` 改为：

```scss
@import "minimal-mistakes/custom";
@import "minimal-mistakes/gov";
```

- [ ] **Step 6: 重新执行 Step 1 的验证命令**

Expected: `bundle exec jekyll build --trace` 成功，且断言不再抛错（编译后的 `_site/assets/css/main.css` 含 `#0b1f3a`）。

- [ ] **Step 7: 提交**

```powershell
git add _config.yml assets/css/main.scss _sass/minimal-mistakes/skins/_hege.scss _sass/minimal-mistakes/_gov.scss
git commit -m "feat(ui): 新增政务风皮肤与样式层骨架，调整全局配置"
```

---

### Task 2: 顶部政务条与主导航

**Files:**
- Create: `_includes/gov/topbar.html`
- Modify: `_includes/masthead.html`
- Modify: `_data/navigation.yml`
- Create: `_pages/news.md`、`_pages/notices.md`、`_pages/editorials.md`
- Modify: `_sass/minimal-mistakes/_gov.scss`（追加）

**Interfaces:**
- Consumes: Task 1 的 `$hege-*` token 与 `_gov.scss`。
- Produces: 路由 `/news/`、`/notices/`、`/editorials/`；导航项顺序 `首页 / 要闻 / 新闻 / 公告 / 社论 / 意见建议`。

- [ ] **Step 1: 写验证命令，确认当前失败**

```powershell
bundle exec jekyll build --trace
if (-not (Select-String -Path _site\index.html -Pattern '意见建议' -Quiet)) { throw 'FAIL: 新导航未出现' }
if (-not (Test-Path _site\news\index.html)) { throw 'FAIL: 栏目页 /news/ 未生成' }
```

Expected: 断言抛 `FAIL`。

- [ ] **Step 2: 创建顶部政务条 `_includes/gov/topbar.html`**

```html
<div class="gov-topbar">
  <div class="gov-topbar__inner">
    <span class="gov-topbar__slogan">和各共和国政府新闻发言网 · 官方信息发布平台</span>
    <span class="gov-topbar__meta">
      <time datetime="{{ site.time | date_to_xmlschema }}">{{ site.time | date: "%Y年%m月%d日" }}</time>
      <a href="{{ '/search/' | relative_url }}">站内搜索</a>
      <a href="{{ '/categories/' | relative_url }}">内容分类</a>
    </span>
  </div>
</div>
```

- [ ] **Step 3: 重写 `_includes/masthead.html`**

```html
{% capture logo_path %}{{ site.logo }}{% endcapture %}

{% include gov/topbar.html %}

<div class="masthead">
  <div class="masthead__inner-wrap">
    <div class="masthead__menu">
      <nav id="site-nav" class="greedy-nav">
        {% unless logo_path == empty %}
          <a class="site-logo" href="{{ '/' | relative_url }}"><img src="{{ logo_path | relative_url }}" alt="{{ site.masthead_title | default: site.title }}"></a>
        {% endunless %}
        <a class="site-title" href="{{ '/' | relative_url }}">
          {{ site.masthead_title | default: site.title }}
          {% if site.subtitle %}<span class="site-subtitle">{{ site.subtitle }}</span>{% endif %}
        </a>
        <ul class="visible-links">
          {%- for link in site.data.navigation.main -%}
            <li class="masthead__menu-item">
              <a
                href="{{ link.url | relative_url }}"
                {% if link.description %} title="{{ link.description }}"{% endif %}
                {% if link.target %} target="{{ link.target }}"{% endif %}
              >{{ link.title }}</a>
            </li>
          {%- endfor -%}
        </ul>
        {% if site.search == true %}
        <button class="search__toggle" type="button">
          <span class="visually-hidden">{{ site.data.ui-text[site.locale].search_label | default: "Toggle search" }}</span>
          <i class="fas fa-search"></i>
        </button>
        {% endif %}
        <button class="greedy-nav__toggle hidden" type="button">
          <span class="visually-hidden">{{ site.data.ui-text[site.locale].menu_label | default: "Toggle menu" }}</span>
          <div class="navicon"></div>
        </button>
        <ul class="hidden-links hidden"></ul>
      </nav>
    </div>
  </div>
</div>
```

- [ ] **Step 4: 改写 `_data/navigation.yml`**

```yaml
# main links
main:
  - title: "首页"
    url: /
  - title: "要闻"
    url: /archive/
  - title: "新闻"
    url: /news/
  - title: "公告"
    url: /notices/
  - title: "社论"
    url: /editorials/
  - title: "意见建议"
    url: /feedback/
```

- [ ] **Step 5: 创建三个栏目页**

`_pages/news.md`：

```markdown
---
title: "新闻中心"
layout: category
taxonomy: 新闻
permalink: /news/
author_profile: false
---
```

`_pages/notices.md`：

```markdown
---
title: "公告通知"
layout: category
taxonomy: 公告
permalink: /notices/
author_profile: false
---
```

`_pages/editorials.md`：

```markdown
---
title: "社论评论"
layout: category
taxonomy: 社论
permalink: /editorials/
author_profile: false
---
```

- [ ] **Step 6: 在 `_gov.scss` 末尾追加顶部条与页头样式**

```scss
/* 顶部政务条 */
.gov-topbar {
  background: $hege-navy;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.8rem;
}

.gov-topbar__inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.4rem 1.5rem;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.gov-topbar a {
  color: rgba(255, 255, 255, 0.85);
  margin-left: 1rem;

  &:hover {
    color: #fff;
  }
}

/* 主导航 */
.masthead {
  border-bottom: 2px solid $hege-navy;
  box-shadow: 0 1px 0 $hege-gold;
  background: #fff;
}

.masthead__inner-wrap {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.9rem 1.5rem;
}

.site-logo img {
  max-height: 56px;
}

.site-title {
  font-family: "STZhongsong", serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: $hege-navy;
}

.site-subtitle {
  display: block;
  font-family: "Yahei", sans-serif;
  font-size: 0.75rem;
  font-weight: 400;
  color: $hege-muted;
}

.greedy-nav {
  background: transparent;

  a {
    color: $hege-navy;
    font-weight: 600;
    font-family: "Yahei", sans-serif;
  }

  .visible-links a:hover {
    color: $hege-red;
  }
}

@media (max-width: 768px) {
  .gov-topbar {
    display: none;
  }
}
```

- [ ] **Step 7: 重新执行 Step 1 的验证命令**

Expected: 构建成功；`_site/index.html` 含“意见建议”；`_site/news/index.html` 存在。

- [ ] **Step 8: 提交**

```powershell
git add _includes/gov/topbar.html _includes/masthead.html _data/navigation.yml _pages/news.md _pages/notices.md _pages/editorials.md _sass/minimal-mistakes/_gov.scss
git commit -m "feat(ui): 重写页头为政务条 + 主导航，新增栏目页"
```

---

### Task 3: 页脚

**Files:**
- Modify: `_includes/footer.html`
- Modify: `_sass/minimal-mistakes/_gov.scss`（追加）

**Interfaces:**
- Consumes: `$hege-*` token；`site.footer.links`、`site.author.email`、`site.author.location`、`site.name`。
- Produces: `.gov-footer`、`.gov-footer__bottom` 结构。

- [ ] **Step 1: 写验证命令，确认当前失败**

```powershell
bundle exec jekyll build --trace
if (-not (Select-String -Path _site\index.html -Pattern '架空世界观创作' -Quiet)) { throw 'FAIL: 页脚免责声明缺失' }
```

Expected: 抛 `FAIL`。

- [ ] **Step 2: 重写 `_includes/footer.html`**

```html
<div class="gov-footer">
  <div class="gov-footer__col gov-footer__brand">
    <img src="{{ site.logo | relative_url }}" alt="{{ site.name }}" class="gov-footer__logo">
    <h3>{{ site.name | default: site.title }}</h3>
    <p>{{ site.description }}</p>
  </div>

  <div class="gov-footer__col">
    <h3>栏目导航</h3>
    <ul>
      <li><a href="{{ '/news/' | relative_url }}">新闻中心</a></li>
      <li><a href="{{ '/notices/' | relative_url }}">公告通知</a></li>
      <li><a href="{{ '/editorials/' | relative_url }}">社论评论</a></li>
      <li><a href="{{ '/feedback/' | relative_url }}">意见建议</a></li>
    </ul>
  </div>

  <div class="gov-footer__col">
    <h3>友情链接</h3>
    <ul>
      {% for link in site.footer.links %}
        {% if link.label and link.url %}
          <li><a href="{{ link.url }}" rel="nofollow noopener noreferrer">{{ link.label }}</a></li>
        {% endif %}
      {% endfor %}
      {% unless site.atom_feed.hide %}
        <li><a href="{% if site.atom_feed.path %}{{ site.atom_feed.path }}{% else %}{{ '/feed.xml' | relative_url }}{% endif %}">RSS 订阅</a></li>
      {% endunless %}
    </ul>
  </div>

  <div class="gov-footer__col">
    <h3>联系我们</h3>
    <ul>
      {% if site.author.email %}<li><a href="mailto:{{ site.author.email }}">{{ site.author.email }}</a></li>{% endif %}
      {% if site.author.location %}<li>{{ site.author.location }}</li>{% endif %}
    </ul>
  </div>
</div>

<div class="gov-footer__bottom">
  <p>&copy; {{ site.time | date: '%Y' }} {{ site.name | default: site.title }}。保留所有权利。</p>
  <p><a href="https://icp.gov.moe/?keyword=20252104" target="_blank" rel="noopener">萌ICP备20252104号</a></p>
  <p class="gov-footer__disclaimer">免责声明：本站为架空世界观创作，内容与任何现实国家、政府、个人无关。</p>
</div>
```

- [ ] **Step 3: 在 `_gov.scss` 末尾追加页脚样式**

```scss
/* 页脚 */
.page__footer {
  background: $hege-navy-deep;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 3rem;
}

.gov-footer {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem 1.5rem;
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr 1fr;
  gap: 2rem;
}

.gov-footer h3 {
  font-family: "STZhongsong", serif;
  font-size: 1rem;
  color: #fff;
  margin: 0 0 0.75rem;
}

.gov-footer__logo {
  max-height: 48px;
  margin-bottom: 0.5rem;
}

.gov-footer ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.gov-footer li {
  margin-bottom: 0.4rem;
}

.gov-footer a {
  color: rgba(255, 255, 255, 0.8);

  &:hover {
    color: $hege-gold;
  }
}

.gov-footer__bottom {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 1.5rem 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.6);

  a {
    color: rgba(255, 255, 255, 0.6);

    &:hover {
      color: $hege-gold;
    }
  }

  p {
    margin: 0.2rem 0;
  }
}

.gov-footer__disclaimer {
  color: $hege-gold;
}

@media (max-width: 900px) {
  .gov-footer {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 600px) {
  .gov-footer {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 4: 重新执行 Step 1 的验证命令**

Expected: 构建成功，断言通过。

- [ ] **Step 5: 提交**

```powershell
git add _includes/footer.html _sass/minimal-mistakes/_gov.scss
git commit -m "feat(ui): 重写页脚为政务四栏布局并加免责声明"
```

---

### Task 4: 首页聚合布局

**Files:**
- Create: `_includes/gov/section-header.html`
- Create: `_includes/gov/hero.html`
- Create: `_includes/gov/news-card.html`
- Create: `_layouts/gov-home.html`
- Modify: `index.html`
- Modify: `_sass/minimal-mistakes/_gov.scss`（追加）

**Interfaces:**
- Consumes: `$hege-*` token；`site.posts`、`site.categories`；Task 2 的 `/news/`、`/notices/`、`/editorials/`。
- Produces: 布局名 `gov-home`；include 参数：`section-header.html`（`title`、`url`）、`news-card.html`（`post`）。

- [ ] **Step 1: 写验证命令，确认当前失败**

```powershell
bundle exec jekyll build --trace
if (-not (Select-String -Path _site\index.html -Pattern '头条要闻' -Quiet)) { throw 'FAIL: 首页头条区缺失' }
if (-not (Select-String -Path _site\index.html -Pattern '公告通知' -Quiet)) { throw 'FAIL: 首页公告区缺失' }
if (Test-Path _site\page2) { throw 'FAIL: 分页目录仍被生成' }
```

Expected: 至少第一条断言抛 `FAIL`（此时首页仍是旧布局）。

- [ ] **Step 2: 创建 `_includes/gov/section-header.html`**

```html
<div class="gov-section__head">
  <h2 class="gov-section__title">{{ include.title }}</h2>
  {% if include.url %}<a class="gov-section__more" href="{{ include.url | relative_url }}">更多 ›</a>{% endif %}
</div>
```

- [ ] **Step 3: 创建 `_includes/gov/hero.html`**

```html
{% assign featured = site.posts | where_exp: "p", "p.featured == true" | first %}
{% if featured %}
  {% assign main_post = featured %}
{% else %}
  {% assign main_post = site.posts.first %}
{% endif %}

{% if main_post %}
<section class="gov-section gov-hero-section">
  <div class="gov-section__head">
    <h2 class="gov-section__title">头条要闻</h2>
    <a class="gov-section__more" href="{{ '/archive/' | relative_url }}">更多 ›</a>
  </div>

  <div class="gov-hero">
    <a class="gov-hero__lead" href="{{ main_post.url | relative_url }}">
      {% if main_post.header.image %}
        <img src="{{ main_post.header.image | relative_url }}" alt="{{ main_post.title | escape }}">
      {% else %}
        <span class="gov-hero__placeholder"></span>
      {% endif %}
      <span class="gov-hero__body">
        {% for category in main_post.categories %}<span class="gov-hero__cat">{{ category }}</span>{% endfor %}
        <span class="gov-hero__title">{{ main_post.title }}</span>
        {% if main_post.excerpt %}<span class="gov-hero__excerpt">{{ main_post.excerpt | markdownify | strip_html | truncate: 90 }}</span>{% endif %}
      </span>
    </a>

    <ul class="gov-hero__side">
      {% assign secondary = site.posts | where_exp: "p", "p.url != main_post.url" %}
      {% for post in secondary limit: 4 %}
        <li>
          <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
          <time datetime="{{ post.date | date_to_xmlschema }}">{{ post.date | date: "%Y-%m-%d" }}</time>
        </li>
      {% endfor %}
    </ul>
  </div>
</section>
{% endif %}
```

- [ ] **Step 4: 创建 `_includes/gov/news-card.html`**

```html
{% assign post = include.post %}
{% if post.header.teaser %}
  {% assign card_img = post.header.teaser %}
{% elsif post.header.image %}
  {% assign card_img = post.header.image %}
{% else %}
  {% assign card_img = '' %}
{% endif %}

<article class="gov-card">
  <a class="gov-card__link" href="{{ post.url | relative_url }}">
    {% if card_img != '' %}
      <span class="gov-card__media"><img src="{{ card_img | relative_url }}" alt=""></span>
    {% else %}
      <span class="gov-card__media gov-card__media--ph"></span>
    {% endif %}
    <h3 class="gov-card__title">{{ post.title }}</h3>
    {% if post.excerpt %}<p class="gov-card__excerpt">{{ post.excerpt | markdownify | strip_html | truncate: 70 }}</p>{% endif %}
    <div class="gov-card__meta">
      {{ post.date | date: "%Y-%m-%d" }}{% if post.publisher %} · {{ post.publisher }}{% endif %}
    </div>
  </a>
</article>
```

- [ ] **Step 5: 创建 `_layouts/gov-home.html`**

```html
---
layout: default
author_profile: false
---

<div class="gov-home">
  <div class="gov-home__main">
    {% include gov/hero.html %}

    {% assign news_posts = site.categories["新闻"] %}
    {% if news_posts.size > 0 %}
    <section class="gov-section">
      {% include gov/section-header.html title="新闻中心" url="/news/" %}
      <div class="gov-cards">
        {% for post in news_posts limit: 6 %}{% include gov/news-card.html post=post %}{% endfor %}
      </div>
    </section>
    {% endif %}

    {% assign notice_posts = site.categories["公告"] %}
    {% assign editorial_posts = site.categories["社论"] %}
    {% if notice_posts.size > 0 or editorial_posts.size > 0 %}
    <div class="gov-home__two">
      {% if notice_posts.size > 0 %}
      <section class="gov-section">
        {% include gov/section-header.html title="公告通知" url="/notices/" %}
        <ul class="gov-notice">
          {% for post in notice_posts limit: 6 %}
            <li>
              <span class="gov-notice__date">{{ post.date | date: "%m-%d" }}</span>
              <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
            </li>
          {% endfor %}
        </ul>
      </section>
      {% endif %}

      {% if editorial_posts.size > 0 %}
      <section class="gov-section">
        {% include gov/section-header.html title="社论评论" url="/editorials/" %}
        <ul class="gov-notice">
          {% for post in editorial_posts limit: 3 %}
            <li>
              <span class="gov-notice__date">社论</span>
              <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
            </li>
          {% endfor %}
        </ul>
      </section>
      {% endif %}
    </div>
    {% endif %}
  </div>

  <aside class="gov-home__aside">
    <div class="gov-side-block">
      <h2 class="gov-side-title">站内搜索</h2>
      <a class="gov-side-search" href="{{ '/search/' | relative_url }}">
        <span>请输入关键词</span>
        <span class="gov-side-search__btn">搜索</span>
      </a>
    </div>

    <div class="gov-side-block">
      <h2 class="gov-side-title">栏目导航</h2>
      <ul class="gov-side-links">
        <li><a href="{{ '/news/' | relative_url }}">新闻中心</a></li>
        <li><a href="{{ '/notices/' | relative_url }}">公告通知</a></li>
        <li><a href="{{ '/editorials/' | relative_url }}">社论评论</a></li>
        <li><a href="{{ '/archive/' | relative_url }}">全部文章</a></li>
        <li><a href="{{ '/categories/' | relative_url }}">内容分类</a></li>
      </ul>
    </div>

    <div class="gov-side-block">
      <h2 class="gov-side-title">站点数据</h2>
      <ul class="gov-side-stats">
        <li><strong>{{ site.posts.size }}</strong><span>发布文章</span></li>
        <li><strong>{{ site.categories.size }}</strong><span>内容分类</span></li>
      </ul>
    </div>

    <div class="gov-side-block">
      <h2 class="gov-side-title">联系我们</h2>
      <ul class="gov-side-links">
        {% if site.author.email %}<li><a href="mailto:{{ site.author.email }}">{{ site.author.email }}</a></li>{% endif %}
        {% if site.author.location %}<li>{{ site.author.location }}</li>{% endif %}
      </ul>
    </div>
  </aside>
</div>
```

- [ ] **Step 6: 修改 `index.html`**

```html
---
layout: gov-home
---
```

- [ ] **Step 7: 在 `_gov.scss` 末尾追加首页样式**

```scss
/* 首页栅格 */
.gov-home {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: 2.5rem;
  padding: 2rem 0;
}

/* 头条区 */
.gov-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  gap: 1.25rem;
}

.gov-hero__lead {
  position: relative;
  display: block;
  overflow: hidden;
  background: $hege-navy-deep;
}

.gov-hero__lead img {
  display: block;
  width: 100%;
  height: 100%;
  max-height: 360px;
  object-fit: cover;
}

.gov-hero__placeholder {
  display: block;
  height: 320px;
  background: linear-gradient(135deg, $hege-navy, $hege-navy-deep);
}

.gov-hero__body {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 1.25rem;
  color: #fff;
  background: linear-gradient(transparent, rgba(7, 21, 39, 0.88));
}

.gov-hero__cat {
  display: inline-block;
  margin-right: 0.5rem;
  padding: 0.1rem 0.45rem;
  font-size: 0.72rem;
  background: $hege-red;
}

.gov-hero__title {
  display: block;
  margin-top: 0.4rem;
  font-family: "STZhongsong", serif;
  font-size: 1.5rem;
  line-height: 1.4;
}

.gov-hero__excerpt {
  display: block;
  margin-top: 0.4rem;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.82);
}

.gov-hero__side {
  list-style: none;
  margin: 0;
  padding: 0;
}

.gov-hero__side li {
  border-bottom: 1px solid $hege-border;
  padding: 0.7rem 0;
}

.gov-hero__side a {
  display: block;
  color: $hege-navy;
  font-weight: 600;
}

.gov-hero__side time {
  display: block;
  margin-top: 0.2rem;
  font-size: 0.75rem;
  color: $hege-muted;
}

/* 新闻卡片 */
.gov-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.25rem;
}

.gov-card {
  border: 1px solid $hege-border;
  background: #fff;
  transition: box-shadow 0.2s ease, transform 0.2s ease;

  &:hover {
    box-shadow: 0 1px 2px rgba(7, 21, 39, 0.04), 0 8px 24px rgba(7, 21, 39, 0.06);
    transform: translateY(-2px);
  }
}

.gov-card__link {
  display: block;
  color: inherit;
}

.gov-card__media {
  display: block;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: $hege-surface;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.gov-card__media--ph {
  background: linear-gradient(135deg, $hege-navy, $hege-navy-deep);
}

.gov-card__title {
  margin: 0.75rem;
  font-family: "STZhongsong", serif;
  font-size: 1rem;
  color: $hege-navy;
}

.gov-card__excerpt {
  margin: 0 0.75rem;
  font-size: 0.85rem;
  color: $hege-muted;
}

.gov-card__meta {
  margin: 0.5rem 0.75rem 0.75rem;
  font-size: 0.75rem;
  color: $hege-muted;
}

/* 公告 / 社论列表 */
.gov-home__two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.gov-notice {
  list-style: none;
  margin: 0;
  padding: 0;
}

.gov-notice li {
  display: flex;
  gap: 0.75rem;
  align-items: baseline;
  padding: 0.55rem 0;
  border-bottom: 1px dashed $hege-border;
}

.gov-notice__date {
  flex: 0 0 auto;
  color: $hege-red;
  font-weight: 700;
  font-size: 0.8rem;
}

.gov-notice a {
  color: $hege-ink;

  &:hover {
    color: $hege-red;
  }
}

/* 侧栏 */
.gov-side-block {
  margin-bottom: 1.5rem;
  padding: 1rem 1.1rem;
  background: $hege-surface;
  border-top: 3px solid $hege-navy;
}

.gov-side-title {
  margin: 0 0 0.75rem;
  font-family: "STZhongsong", serif;
  font-size: 1.05rem;
  color: $hege-navy;
}

.gov-side-search {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  border: 1px solid $hege-border;
  background: #fff;
  color: $hege-muted;
}

.gov-side-search__btn {
  color: $hege-navy;
  font-weight: 700;
}

.gov-side-links {
  list-style: none;
  margin: 0;
  padding: 0;

  a {
    display: block;
    padding: 0.35rem 0;
    border-bottom: 1px solid $hege-border;
    color: $hege-ink;

    &:hover {
      color: $hege-red;
    }
  }
}

.gov-side-stats {
  display: flex;
  gap: 1rem;
  list-style: none;
  margin: 0;
  padding: 0;
  text-align: center;

  li {
    flex: 1;
  }

  strong {
    display: block;
    font-size: 1.5rem;
    color: $hege-red;
  }
}

@media (max-width: 1024px) {
  .gov-home {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .gov-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .gov-hero,
  .gov-home__two {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .gov-cards {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 8: 重新执行 Step 1 的验证命令**

Expected: 构建成功；`_site/index.html` 含“头条要闻”“公告通知”；不再生成 `_site/page2`。

- [ ] **Step 9: 验证空分类不残留空标题（手动）**

临时把 `_posts/2025-12-31-xinnianzhufu25-26.md` 的 `categories: [公告]` 改为 `categories: [公告临时]`，重新构建，确认首页“公告通知”整段消失（而非只留标题）；随后用 `git checkout -- _posts/2025-12-31-xinnianzhufu25-26.md` 还原。

- [ ] **Step 10: 提交**

```powershell
git add _includes/gov/section-header.html _includes/gov/hero.html _includes/gov/news-card.html _layouts/gov-home.html index.html _sass/minimal-mistakes/_gov.scss
git commit -m "feat(ui): 新增政务聚合首页与卡片组件，移除分页"
```

---

### Task 5: 文章页（发布单位、移除评论与作者卡、意见建议页）

**Files:**
- Modify: `_layouts/single.html`
- Modify: `_includes/page__meta.html`
- Create: `_pages/feedback.md`
- Modify: `_data/ui-text.yml`
- Modify: `_sass/minimal-mistakes/_gov.scss`（追加）

**Interfaces:**
- Consumes: Task 1 的 posts 默认值（`author_profile: false`、`comments: false`、`publisher: "和各政府网"`）。
- Produces: 文章标题上方 `.page__badges`；元信息行显示发布单位；`.page__meta-publisher`；路由 `/feedback/`。

- [ ] **Step 1: 写验证命令，确认当前失败**

```powershell
bundle exec jekyll build --trace
$post = Get-ChildItem _site -Recurse -Filter index.html | Where-Object { $_.FullName -match '\\公告\\' } | Select-Object -First 1
if (-not $post) { $post = Get-ChildItem _site -Recurse -Filter index.html | Select-Object -First 1 }
if (Select-String -Path $post.FullName -Pattern '评论功能不支持' -Quiet) { throw 'FAIL: 文章页仍输出“评论功能不支持”' }
if (-not (Test-Path _site\feedback\index.html)) { throw 'FAIL: 意见建议页未生成' }
if (-not (Select-String -Path _site\feedback\index.html -Pattern 'giscus' -Quiet)) { throw 'FAIL: 意见建议页缺少 giscus' }
```

Expected: 至少第三条断言抛 `FAIL`。

- [ ] **Step 2: 修改 `_layouts/single.html` 标题区加入徽章**

把第 32–40 行这段：

```liquid
      {% unless page.header.overlay_color or page.header.overlay_image %}
        <header>
          {% if page.title -%}
          <h1 id="page-title" class="page__title" itemprop="headline">
```

改为：

```liquid
      {% unless page.header.overlay_color or page.header.overlay_image %}
        <header>
          {% assign publisher = page.publisher | default: site.name %}
          <div class="page__badges">
            {% for category in page.categories %}
              <a class="page__badge page__badge--cat" href="{{ category | slugify | prepend: '#' | prepend: site.category_archive.path | relative_url }}">{{ category }}</a>
            {% endfor %}
            {% if publisher %}<span class="page__badge page__badge--pub">{{ publisher }}</span>{% endif %}
          </div>
          {% if page.title -%}
          <h1 id="page-title" class="page__title" itemprop="headline">
```

- [ ] **Step 3: 修改 `_layouts/single.html` 移除评论 else 分支**

把第 69–73 行这段：

```liquid
    {% if site.comments.provider and page.comments %}
      {% include comments.html %}
    {% else %}
      <p>评论功能不支持</p>
    {% endif %}
```

改为：

```liquid
    {% if site.comments.provider and page.comments %}
      {% include comments.html %}
    {% endif %}
```

- [ ] **Step 4: 修改 `_includes/page__meta.html` 加入发布单位**

把 `<p class="page__meta">` 之后到第一个 `{% endif %}` 之前的结构改为先输出发布单位。将第 3–13 行这段：

```liquid
  <p class="page__meta">
    {% if document.show_date and document.date %}
      {% assign date = document.date %}
      <span class="page__meta-date">
        <i class="far {% if include.type == 'grid' and document.read_time and document.show_date %}fa-fw {% endif %}fa-calendar-alt" aria-hidden="true"></i>
        {% assign date_format = site.date_format | default: "%B %-d, %Y" %}
        <time datetime="{{ date | date_to_xmlschema }}">{{ date | date: date_format }}</time>
      </span>
    {% endif %}

    {% if document.read_time and document.show_date %}<span class="page__meta-sep"></span>{% endif %}
```

改为：

```liquid
  <p class="page__meta">
    {% assign publisher = document.publisher | default: site.name %}
    {% if publisher %}
      <span class="page__meta-publisher">
        <i class="fas fa-fw fa-landmark" aria-hidden="true"></i>
        {{ publisher }}
      </span>
    {% endif %}

    {% if publisher and document.date %}<span class="page__meta-sep"></span>{% endif %}

    {% if document.date %}
      {% assign date = document.date %}
      <span class="page__meta-date">
        <i class="far {% if include.type == 'grid' and document.read_time and document.show_date %}fa-fw {% endif %}fa-calendar-alt" aria-hidden="true"></i>
        {% assign date_format = site.date_format | default: "%B %-d, %Y" %}
        <time datetime="{{ date | date_to_xmlschema }}">{{ date | date: date_format }}</time>
      </span>
    {% endif %}

    {% if document.read_time and document.date %}<span class="page__meta-sep"></span>{% endif %}
```

- [ ] **Step 5: 创建 `_pages/feedback.md`**

```markdown
---
title: "意见建议"
layout: single
permalink: /feedback/
author_profile: false
comments: true
---

欢迎各界就本站内容与政务工作提出意见建议。请依法依规、理性文明发言，共同维护清朗网络空间。
```

- [ ] **Step 6: 修改 `_data/ui-text.yml` 的 `zh` 区块文案**

把第 402 行：

```yaml
  related_label              : "猜您还喜欢"
```

改为：

```yaml
  related_label              : "相关阅读"
```

- [ ] **Step 7: 在 `_gov.scss` 末尾追加文章页与徽章样式**

```scss
/* 文章页徽章 */
.page__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.75rem;
}

.page__badge {
  font-size: 0.75rem;
  padding: 0.15rem 0.5rem;
}

.page__badge--cat {
  background: $hege-red;
  color: #fff;
}

.page__badge--pub {
  border: 1px solid $hege-navy;
  color: $hege-navy;
}

/* 文章排版 */
.page__title {
  font-family: "STZhongsong", serif;
  font-size: 2rem;
  line-height: 1.35;
  color: $hege-navy;
}

.page__content {
  font-size: 1.0625rem;
  line-height: 1.9;
}

.page__content h2 {
  padding-left: 0.6rem;
  border-left: 4px solid $hege-red;
  color: $hege-navy;
}

.page__content h3,
.page__content h4 {
  color: $hege-navy;
}

.page__content blockquote {
  padding: 0.75rem 1rem;
  background: $hege-surface;
  border-left: 4px solid $hege-navy;
}

.page__content table th {
  background: $hege-navy;
  color: #fff;
}

.page__content table tr:nth-child(even) {
  background: $hege-surface;
}

.page__meta-publisher {
  font-weight: 700;
  color: $hege-navy;
}
```

- [ ] **Step 8: 重新执行 Step 1 的验证命令**

Expected: 构建成功；文章页不再出现“评论功能不支持”；`_site/feedback/index.html` 存在且含 `giscus`。

- [ ] **Step 9: 额外确认作者卡与评论未泄漏**

```powershell
if (Select-String -Path _site\公告\*\index.html -Pattern 'author-profile|giscus' -Quiet) { throw 'FAIL: 文章页仍含作者卡或评论' }
```

Expected: 无输出、无异常。

- [ ] **Step 10: 提交**

```powershell
git add _layouts/single.html _includes/page__meta.html _pages/feedback.md _data/ui-text.yml _sass/minimal-mistakes/_gov.scss
git commit -m "feat(ui): 文章页发布单位徽章、移除评论与作者卡，新增意见建议页"
```

---

### Task 6: 列表页、归档、搜索与标签样式

**Files:**
- Modify: `_includes/archive-single.html`
- Modify: `_sass/minimal-mistakes/_gov.scss`（追加）

**Interfaces:**
- Consumes: `$hege-*` token；`post.header.teaser`、`post.header.image`。
- Produces: 列表项始终渲染 `.archive__item-teaser`（含 `header.image` 回退）；卡片 / 分页 / 分类标签 / 搜索覆盖层样式。

- [ ] **Step 1: 写验证命令，确认当前失败**

```powershell
bundle exec jekyll build --trace
if (-not (Select-String -Path _site\notices\index.html -Pattern 'archive__item-teaser' -Quiet)) { throw 'FAIL: 列表页未渲染缩略图' }
```

Expected: 抛 `FAIL`（当前 `archive-single.html` 仅在 grid 模式渲染缩略图）。

- [ ] **Step 2: 修改 `_includes/archive-single.html`**

把第 1–19 行这段：

```liquid
{% if post.header.teaser %}
  {% capture teaser %}{{ post.header.teaser }}{% endcapture %}
{% else %}
  {% assign teaser = site.teaser %}
{% endif %}

{% if post.id %}
  {% assign title = post.title | markdownify | remove: "<p>" | remove: "</p>" %}
{% else %}
  {% assign title = post.title %}
{% endif %}

<div class="{{ include.type | default: 'list' }}__item">
  <article class="archive__item" itemscope itemtype="https://schema.org/CreativeWork"{% if post.locale %} lang="{{ post.locale }}"{% endif %}>
    {% if include.type == "grid" and teaser %}
      <div class="archive__item-teaser">
        <img src="{{ teaser | relative_url }}" alt="">
      </div>
    {% endif %}
```

改为：

```liquid
{% if post.header.teaser %}
  {% capture teaser %}{{ post.header.teaser }}{% endcapture %}
{% elsif post.header.image %}
  {% capture teaser %}{{ post.header.image }}{% endcapture %}
{% else %}
  {% assign teaser = site.teaser %}
{% endif %}

{% if post.id %}
  {% assign title = post.title | markdownify | remove: "<p>" | remove: "</p>" %}
{% else %}
  {% assign title = post.title %}
{% endif %}

<div class="{{ include.type | default: 'list' }}__item">
  <article class="archive__item" itemscope itemtype="https://schema.org/CreativeWork"{% if post.locale %} lang="{{ post.locale }}"{% endif %}>
    {% if teaser %}
      <div class="archive__item-teaser">
        <img src="{{ teaser | relative_url }}" alt="">
      </div>
    {% endif %}
```

- [ ] **Step 3: 在 `_gov.scss` 末尾追加列表 / 分页 / 标签 / 搜索样式**

```scss
/* 列表与归档 */
.archive__item {
  border-bottom: 1px solid $hege-border;
  padding-bottom: 1.25rem;
  margin-bottom: 1.25rem;
}

.list__item .archive__item {
  display: flex;
  gap: 1.25rem;
  align-items: flex-start;
}

.archive__item-teaser {
  flex: 0 0 220px;
  overflow: hidden;

  img {
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
  }
}

.archive__item-title a {
  font-family: "STZhongsong", serif;
  color: $hege-navy;

  &:hover {
    color: $hege-red;
  }
}

/* 分页 */
.pagination {
  text-align: center;

  li a,
  li span {
    border: 1px solid $hege-border;
    border-radius: 0;
    padding: 0.3rem 0.7rem;
  }

  .current {
    background: $hege-navy;
    color: #fff;
    border-color: $hege-navy;
  }

  a:hover {
    background: $hege-red;
    border-color: $hege-red;
    color: #fff;
  }
}

/* 分类 / 标签胶囊 */
.page__taxonomy-item {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border: 1px solid $hege-navy;
  border-radius: 0;
  color: $hege-navy;

  &:hover {
    background: $hege-red;
    border-color: $hege-red;
    color: #fff;
  }
}

/* 搜索覆盖层 */
.search-content {
  background: $hege-navy;
}

.search-input {
  border-radius: 0;
}

/* 归档年份标题 */
.archive .taxonomy__section,
.archive h2.archive__subtitle {
  border-bottom: 1px solid $hege-gold;
  color: $hege-navy;
  font-family: "STZhongsong", serif;
}

@media (max-width: 600px) {
  .list__item .archive__item {
    flex-direction: column;
  }

  .archive__item-teaser {
    flex: 0 0 auto;
    width: 100%;
  }
}
```

- [ ] **Step 4: 重新执行 Step 1 的验证命令**

Expected: 构建成功，`_site/notices/index.html` 含 `archive__item-teaser`。

- [ ] **Step 5: 提交**

```powershell
git add _includes/archive-single.html _sass/minimal-mistakes/_gov.scss
git commit -m "feat(ui): 列表卡片、分页、标签与搜索样式，列表项支持缩略图"
```

---

### Task 7: 自定义组件改色

**Files:**
- Modify: `_sass/minimal-mistakes/_custom.scss`
- Modify: `_sass/minimal-mistakes/_gov.scss`（追加 infobox 覆盖）

**Interfaces:**
- Consumes: Task 1 的 `$hege-*` token。
- Produces: 无新的对外接口；仅颜色替换。

- [ ] **Step 1: 写验证命令，确认当前失败**

```powershell
bundle exec jekyll build --trace
if (Select-String -Path _site\assets\css\main.css -Pattern '#4285f4' -Quiet) { throw 'FAIL: 旧组件蓝色仍在' }
```

Expected: 抛 `FAIL`。

- [ ] **Step 2: 替换 `_custom.scss` 中的旧色**

把：

```scss
  border-left: 5px solid #4285f4; // A nice accent color
```

改为：

```scss
  border-left: 5px solid $hege-red;
```

把：

```scss
    color: #4285f4;
    font-size: 0.95em;
```

改为：

```scss
    color: $hege-navy;
    font-size: 0.95em;
```

把：

```scss
        color: #4285f4;
```

改为：

```scss
        color: $hege-red;
```

把 infobox 边框与表头底色：

```scss
  border: 1px solid #a2a9b1;
  background-color: #f8f9fa;
```

改为：

```scss
  border: 1px solid $hege-border;
  background-color: $hege-surface;
```

把：

```scss
  background-color: #eaf3ff; /* A light blue, similar to Wikipedia */
```

改为：

```scss
  background-color: $hege-surface;
  color: $hege-navy;
```

- [ ] **Step 3: 在 `_gov.scss` 末尾追加 infobox 政务化覆盖**

```scss
/* Infobox 政务化 */
.infobox {
  border-color: $hege-border;
  background: $hege-surface;
}

.infobox-header {
  background: $hege-navy;
  color: #fff;
}

.infobox-label {
  color: $hege-navy;
}
```

- [ ] **Step 4: 重新执行 Step 1 的验证命令**

Expected: 构建成功，编译 CSS 不再含 `#4285f4`。

- [ ] **Step 5: 提交**

```powershell
git add _sass/minimal-mistakes/_custom.scss _sass/minimal-mistakes/_gov.scss
git commit -m "style(ui): 自定义组件配色统一为藏青/绛红/香槟金"
```

---

### Task 8: 全站回归验证与收尾

**Files:**
- Modify: 必要时 `_sass/minimal-mistakes/_gov.scss` 或相关 include
- Modify: `README.md`（更新“开发手册”命令处，补一句构建命令）

**Interfaces:**
- Consumes: 前七个任务的全部产物。
- Produces: 通过验收的站点。

- [ ] **Step 1: 全量构建**

```powershell
bundle exec jekyll build --trace
```

Expected: 成功，无 Liquid / Sass 报错。

- [ ] **Step 2: 关键页面存在性**

```powershell
$pages = @(
  '_site\index.html',
  '_site\news\index.html',
  '_site\notices\index.html',
  '_site\editorials\index.html',
  '_site\feedback\index.html',
  '_site\archive\index.html',
  '_site\categories\index.html',
  '_site\search\index.html'
)
foreach ($p in $pages) { if (-not (Test-Path $p)) { throw "FAIL: 缺少 $p" } }
```

Expected: 无异常。

- [ ] **Step 3: 无分页残留**

```powershell
if (Get-ChildItem _site -Directory | Where-Object { $_.Name -like 'page*' }) { throw 'FAIL: 仍生成分页目录' }
```

Expected: 无异常。

- [ ] **Step 4: 评论只在反馈页**

```powershell
$leaks = Get-ChildItem _site -Recurse -Filter index.html |
  Where-Object { $_.FullName -notmatch '\\feedback\\' } |
  Where-Object { Select-String -Path $_.FullName -Pattern 'giscus|评论功能不支持' -Quiet }
if ($leaks) { throw "FAIL: 评论泄漏 -> $($leaks.FullName -join ', ')" }
if (-not (Select-String -Path _site\feedback\index.html -Pattern 'giscus' -Quiet)) { throw 'FAIL: 反馈页缺少 giscus' }
```

Expected: 无异常。

- [ ] **Step 5: 旧色与占位符扫描**

```powershell
if (Select-String -Path _site\assets\css\main.css -Pattern '#4285f4' -Quiet) { throw 'FAIL: 旧蓝色残留' }
if (Select-String -Path _sass\minimal-mistakes\_gov.scss -Pattern 'TODO|FIXME' -Quiet) { throw 'FAIL: 计划残留占位符' }
```

Expected: 无异常。

- [ ] **Step 6: 本地目视检查**

```powershell
bundle exec jekyll serve
```

在浏览器分别检查桌面宽（≥1200px）与移动宽（375px）下的：首页、`/news/`、一篇文章、`/feedback/`、`/search/`、`/archive/`。确认：页头政务条与导航、栏目分节头、卡片占位、页脚四栏与免责声明均正常；文章页无评论区与作者卡。

- [ ] **Step 7: 更新 README 开发手册**

把 `README.md` 中：

```markdown
## 开发手册

`Bundle exec jekyll serve` 在线预览
```

改为：

```markdown
## 开发手册

- `bundle exec jekyll serve` 在线预览（修改 `_config.yml` 后需重启）
- `bundle exec jekyll build` 构建，产物在 `_site/`
```

- [ ] **Step 8: 提交**

```powershell
git add -A
git commit -m "docs: 更新开发手册并完成政务化 UI 回归验证"
```

---

## 执行顺序依赖

- Task 1 是所有任务的前置（token 与样式层）。
- Task 2、Task 3 相互独立，均依赖 Task 1。
- Task 4 依赖 Task 1、Task 2（导航 URL）。
- Task 5 依赖 Task 1；Task 6 依赖 Task 1；Task 7 依赖 Task 1。
- Task 8 依赖前七个任务。
