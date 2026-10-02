# AGENTS.md

本仓库是基于 Minimal Mistakes 主题搭建的 “和各国” 架空政府新闻网站（Jekyll）。
所有面向用户的内容均为中文，新增内容与界面文案请保持中文。

## 常用命令

- 安装依赖：`bundle install`（Gem 源是 `https://gems.ruby-china.com/`，不是 rubygems.org）。
- 本地预览：`bundle exec jekyll serve`。`_config.yml` **不会**热重载，修改后必须重启服务。
- 构建（CI 使用，产物在 `_site/`）：`bundle exec jekyll build`。构建报错含义不清时加 `--trace`。
- 修改 `assets/js/_main.js` 或 `assets/js/plugins/*.js` 后需重新打包 JS：`rake js`。
- 本仓库没有单元测试。验证方式 = 成功执行 `bundle exec jekyll build` 并检查 `_site/`。
- **不要**直接运行 `rake`：默认任务包含 `changelog`，它依赖本仓库并不存在的 `CHANGELOG.md` 和 `docs/`。请改用 `rake js`（必要时 `rake copyright` / `rake version`）。

## 架构与易踩坑

- 主题有两套来源：`_config.yml` 设置 `theme: minimal-mistakes-jekyll`（Gemfile 锁定 `~> 4.24.0`），同时本仓库又完整内置了主题源码。本地 `_layouts/`、`_includes/`、`_sass/`、`_data/`、`assets/` 会**覆盖 Gem 主题**，因此请修改本地文件，不要改已安装的 Gem。
- `_site/` 与 `.jekyll-cache/` 是生成产物且已被 gitignore，切勿编辑。
- `_includes/masthead.html`、`footer.html` 通过 `include_cached` 加载，缓存键只含 include 路径与传入参数：页面相关内容必须作为参数传入（如 `{% include_cached masthead.html page_url=page.url %}`），否则所有页面会复用首个渲染页的结果。修改被缓存的 include 后若页面未更新，删除 `.jekyll-cache/` 再构建。
- JS：页面只加载 `assets/js/main.min.js`（见 `_includes/scripts.html`）。`assets/js/_main.js`、`assets/js/plugins/**`、`assets/js/vendor/**` 都被 Jekyll 构建排除。请修改这些源文件后执行 `rake js` 重新生成 `main.min.js`，否则浏览器端看不到改动。
- 搜索使用 lunr，并开启 `search_full_content: true`。`assets/js/lunr/lunr-store.js` 是一个 Liquid 模板（front matter 为 `layout: none`），构建时会根据全部 collection 文档重新生成，不要手动编辑其中的数据。
- 评论使用 giscus（配置在 `_config.yml`），仅 `/feedback/` 页开启；文章页已移除评论与作者卡。
- 部署：每次推送到 `main` 会触发 `.github/workflows/jekyll-build.yml`，通过 `peaceiris/actions-gh-pages` 把 `_site/` 发布到 `gh-pages` 分支。切勿直接提交到 `gh-pages`，也不要手动编辑 `_site`。CI 使用 Ruby 3.2（本地版本可能不同）。

## 内容创作

- 文章放在 `_posts/YYYY-MM-DD-slug.md`，继承 `_config.yml` 中的默认值：`layout: single`、`author_profile: false`、`comments: false`、`publisher: "和各政府网"`、`related: true`。发布方可在文章 front matter 用 `publisher` 单独覆盖。
- 永久链接为 `/:categories/:title/`，因此 front matter 的 `categories`（例如 `categories: [公告]`）决定文章 URL。
- 站点字体在 `assets/css/main.scss` 中以内联方式定制（微软雅黑）。新增组件样式请写入 `_sass/minimal-mistakes/_custom.scss`，`main.scss` 会在最后导入它。
- 在原生 Minimal Mistakes 基础上新增的自定义组件 include：
  - `{% include infobox.html %}` —— 维基百科风格侧边信息框，完全由 front matter 驱动：`infobox_header`、`infobox_image`、`infobox_caption`，以及 `infobox_data`（`label`/`value` 列表）。
  - `{% include content_box.html title="..." icon="info-circle" content="..." %}` —— 随文排列的 Markdown 内容框。
  - `{% include embed_box.html title="..." icon="star" content="..." %}` —— 带边框的维基百科风格嵌入框。
  - `{% include video provider="bilibili|youtube|vimeo|google-drive" id="..." [danmaku=0] %}`。
  - `{% include latex.html %}` —— 加载 MathJax 2.7。
- `README.md` 是本项目的说明与 TODO 清单（并非上游主题的 README）。
