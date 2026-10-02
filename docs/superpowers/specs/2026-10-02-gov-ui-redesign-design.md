# 和各政府网 UI 政务化重构 · 设计规格

- 日期：2026-10-02
- 状态：已通过对话设计评审，待用户审阅本规格
- 范围：整站视觉与信息架构重构（含新首页），保持现有内容与部署链路不变

## 1. 背景与目标

本站是基于 Minimal Mistakes 主题的“和各国”架空政府新闻发言网。当前为默认灰度皮肤 + 文章列表式首页，观感偏个人博客，不够“完备、严肃”。

目标：在**不迁移主题、不破坏现有内容与部署**的前提下，把站点重构为**中国政务门户风格、且高级现代**的政府新闻发布站。

成功标准：

1. 首页具备政务门户的信息层级：头条要闻、新闻中心、公告通知、社论评论、侧边信息区。
2. 页头/页脚呈现官方发布气质，配色为藏青 + 中国红 + 香槟金。
3. 文章页、栏目页、搜索页、归档页视觉统一。
4. 文章页不再出现个人作者资料卡与评论区；评论集中到“意见建议”页。
5. `bundle exec jekyll build` 通过；部署链路（main → GitHub Actions → gh-pages）不变。

## 2. 非目标

- 不更换 Jekyll/Minimal Mistakes 主题，不改动 `gh-pages` 部署方式。
- 不重写现有 7 篇文章正文；靠 front matter 默认值兼容。
- 不新增前端框架或构建工具；不改动 JS 产物（无需 `rake js`）。
- 不引入外部字体 CDN（沿用仓库内 `STZhongsong` 与 `Yahei`）。

## 3. 视觉语言（Design Tokens）

以独立皮肤实现，全部走主题变量，不使用主题自带皮肤。

### 配色

| 用途 | Token | 值 |
| --- | --- | --- |
| 主色（页头/页脚/标题/主按钮） | `$hege-navy` | `#0B1F3A` |
| 深主色（页脚） | `$hege-navy-deep` | `#071527` |
| 强调（栏目竖条/当前项/悬停） | `$hege-red` | `#A81C1C` |
| 装饰（细线/描边点缀） | `$hege-gold` | `#C8A96A` |
| 表面底色 | `$surface` | `#F6F7F9` |
| 正文 | `$text-color` | `#1F2A37` |
| 次要文字 | `$muted-text-color` | `#5B6672` |
| 描边 | `$border-color` | `#E3E6EA` |
| 链接 | `$link-color` | 藏青；悬停转绛红 |

### 字体与排版

- 标题：`STZhongsong`（华文中宋，现有）。
- 正文：`Yahei`（微软雅黑，现有）。
- 正文 17px / 行高 1.9；标题 `letter-spacing: 0.02em`。
- 栏目标题统一形态：左侧 3px 绛红竖条 + 藏青标题 + 右侧“更多 ›”。

### 形状、质感、动效

- 圆角 `0`（最大 2px），方正利落。
- 阴影仅用于卡片/浮层：`0 1px 2px rgba(7,21,39,.04), 0 8px 24px rgba(7,21,39,.06)`。
- 容器最大宽约 1200px；首页两栏栅格（正文 2fr + 侧栏 1fr）。
- 过渡统一 `0.2s ease`，无弹跳/花哨动画。

## 4. 信息架构与导航

### 顶部政务条（新增）

- 深藏青底、浅色字。
- 左：标语“和各共和国政府新闻发言网 · 官方信息发布平台”。
- 右：当前日期（`site.time` 中文格式化）+ 搜索入口。
- 移动端隐藏。

### 主导航（重写 `_includes/masthead.html`）

- 白色底：左 logo + 站名（华文中宋、藏青）+ 英文副标题小字。
- 右侧导航：首页 / 要闻 / 新闻 / 公告 / 社论 / 意见建议。
- 当前项红色下划线，悬停转红；保留主题搜索按钮。
- 页头底部 2px 藏青线 + 细金线收口。
- `归档`、`分类`、`标签` 降级到页脚/工具区。

### 栏目页（复用主题 `category` 布局）

- `_pages/news.md` → `/news/`（taxonomy: 新闻）
- `_pages/notices.md` → `/notices/`（taxonomy: 公告）
- `_pages/editorials.md` → `/editorials/`（taxonomy: 社论）

### 意见建议页（新增 `_pages/feedback.md`）

- 开启 `comments: true`，giscus 仅在此页出现。
- 文章页与其它页面关闭评论；文章页移除作者资料卡。

### 页脚（重写 `_includes/footer.html`）

- 深藏青底，四栏：网站信息、栏目导航、友情链接、联系方式（沿用现有 email/location）。
- 底栏：版权 © 和各共和国政府 + 萌ICP备20252104号 + 免责声明“本站为架空世界观创作，与任何现实国家、政府、个人无关”。
- 保留 RSS。

## 5. 首页布局

新增 `_layouts/gov-home.html`，`index.html` 改用它。两栏：正文区 2fr + 侧栏 1fr，移动端堆叠。

```
正文区                                          侧栏
头条要闻：主头条大图 + 分类标签 + 大标题 + 摘要      站内搜索
         + 次条 1–4（标题 + 日期）                  栏目快捷入口
新闻中心 [更多 ›]：卡片 ×6（缩略图/标题/摘要/日期）   站点数据（文章数/分类数）
公告通知 [更多 ›]        | 社论评论 [更多 ›]         联系方式
日期徽标 + 标题列表       | 签名引言 + 标题列表
```

### 数据来源

1. **头条要闻**：默认取 `site.posts` 最新 1 条为主头条、随后 4 条为次条；支持 front matter `featured: true` 指定主头条。主头条用 `header.image`，无图时用藏青渐变占位。
2. **新闻中心**：`新闻` 分类取 6 条卡片，链接 `/news/`。
3. **公告通知**：`公告` 分类取 6 条，日期徽标，链接 `/notices/`。
4. **社论评论**：`社论` 分类取 3 条，配签名引言样式，链接 `/editorials/`。
5. **侧边信息区**：搜索入口、栏目快捷、真实站点统计（`site.posts.size`、`site.categories.size`，不编造）、联系方式。

### 分页处理（重要）

当前 `_config.yml` 启用 `jekyll-paginate`（`paginate: 5`、`paginate_path: /page:num/`），会围绕根 `index.html` 生成 `/page2/` 等分页。新首页是自定义聚合页，不应被分页。实现时**移除** `paginate` 与 `paginate_path` 配置，由栏目页和归档页承担完整浏览入口，避免生成重复内容。

## 6. 文章页 / 列表页 / 搜索页 / 归档页

### 文章页（`layout: single`）

- 面包屑保留，小字灰色 + 红色分隔符。
- 标题区：红色分类标签 + `publisher` 发布单位小标签并排 → 华文中宋大标题 → 元信息行（发布单位 · 日期 · 阅读时长）。
- **发布单位 `publisher`**：新增可选 front matter 字段（如“和各共和国外交部”“和各中央广播与电视平台”）。未填写时回退 `site.name`。现有文章无需改动。
- 正文：17px / 1.9；`h2` 红色左竖条，`h3/h4` 藏青层级；引用块浅底 + 藏青左边线；表格藏青表头白字 + 斑马纹。
- 底部仅保留相关文章卡片；移除评论区与作者资料卡。
- 404 页套用新视觉。

### 栏目/列表页（`archive`、`category`）

- 页首藏青标题区，含栏目名、简短说明、文章计数。
- 列表项改横向卡片（左缩略图 + 右标题/摘要/日期），无图用藏青占位块。
- 分页按钮方正化，当前页藏青底。

### 搜索页（`/search/`）

- 居中大搜索框 + 藏青按钮；结果卡片化并高亮命中词。
- 页头展开的搜索覆盖层底色改藏青、输入框方正化。

### 归档页（`/archive/`）与分类/标签页

- 归档按年份分组，年份标题下加香槟金细线，条目带日期徽标。
- 分类/标签为方正胶囊：藏青描边、悬停绛红填充。

### 组件改色

- `infobox` / `content_box` / `embed_box` 中的 `#4285f4` 等旧色统一替换为藏青/绛红/香槟金 token。

## 7. 技术实现与文件清单

### 新增

- `_sass/minimal-mistakes/skins/_hege.scss`（定制皮肤 token）
- `_sass/minimal-mistakes/_gov.scss`（政务布局与组件样式层）
- `_layouts/gov-home.html`
- `_includes/gov/topbar.html`、`section-header.html`、`hero.html`、`news-card.html`
- `_pages/news.md`、`notices.md`、`editorials.md`、`feedback.md`

### 修改

- `_config.yml`：`minimal_mistakes_skin: hege`；移除 `paginate`/`paginate_path`；posts 默认 `author_profile: false`、`comments: false`。
- `_data/navigation.yml`：新导航结构。
- `_includes/masthead.html`、`_includes/footer.html`：重写。
- `_includes/page__meta.html`：显示 `publisher`（缺失回退站点默认）。
- `assets/css/main.scss`：主题与 `_custom` 之后导入 `_gov`；保留 `@font-face`。
- `_sass/minimal-mistakes/_custom.scss`：旧色替换。
- `index.html`：`layout: gov-home`。

### 不改动

- JS 与 `assets/js/main.min.js`（纯 HTML/CSS 改动）。
- 现有文章正文。

## 8. 验证方式

1. `bundle exec jekyll build --trace` 成功，无 Liquid/Sass 报错。
2. `_site/index.html` 与 `_site/news|notices|editorials|feedback/index.html` 正常生成。
3. 不再生成 `_site/page2/` 等分页目录。
4. 文章页无评论区/作者卡；`/feedback/` 有 giscus 且仅此一处。
5. `bundle exec jekyll serve` 目视检查桌面与移动端。

## 9. 风险

- 主题仍用已弃用的 Sass `@import`，但当前 `jekyll-sass-converter 3.1 + sass-embedded` 可用；新样式沿用同一写法，不引入新方案。
- 新首页聚合逻辑依赖分类名 `新闻`/`公告`/`社论`；若未来改名需同步更新。
- 移除 `paginate` 后，首页不再有传统分页；需依赖栏目页/归档页，已规划对应入口。

## 10. 决策记录

- 视觉方向：中国政务门户风格（用户选择）。
- 改动范围：整站重构含新首页（用户选择）。
- 首页栏目：头条要闻、新闻中心、公告通知、社论评论、侧边信息区（用户多选）。
- 评论与作者卡：改为集中到专门的“意见建议”页（用户选择）。
- 主色调：藏青 + 中国红（用户选择）。
- 发布方：新增 `publisher` 字段，因不同稿件发布单位可能不同（用户指出）。
- 实现路径：A（独立皮肤 + 政务布局层）（用户选择）。
