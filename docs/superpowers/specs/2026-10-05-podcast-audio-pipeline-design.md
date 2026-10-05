# 和国播客 · 音频生产流水线（子项目 B）· 设计规格

- 日期：2026-10-05
- 状态：已通过对话设计评审，待用户审阅本规格
- 范围：音频生产流水线（脚本源 → 多音色合成 → 混音 → 成品 MP3 + 逐字稿/时间轴），并产出一条播报样片
- 说明：网站播客栏目（子项目 A）与批量内容生产（子项目 C）另立规格；本规格只做 B

## 1. 背景与目标

本站是“和各国”架空政府新闻发言网（Jekyll + Minimal Mistakes）。现只有图文内容，用户希望新增**播客节目**，包含「政府新闻播报」与「访谈/对话」两种形态，并要求产出**实际音频**、**真人向稿件 + 分镜/时间轴**，以及**网站集成**。

整体偏大，拆为三个可独立验收的子项目：

| 子项目 | 内容 | 本规格 |
| --- | --- | --- |
| **B. 音频生产流水线** | 脚本源 → 合成 → 混音 → 成品音频与逐字稿 | ✅ 本文档 |
| A. 网站播客栏目 | `_podcasts` 集合、列表/详情页、播放器、播客 RSS | 另立 |
| C. 内容生产 | 新闻播报稿 + 访谈稿，事实取自 Hegewiki 正典 | 另立 |

B 的成功标准：

1. 一条命令即可把结构化脚本源合成为带背景音乐、音效、多音色的成品 MP3。
2. 同一命令同时产出一份逐字稿 Markdown（含真实时间轴），音频与文稿同源、不会不一致。
3. 产出**一条可听的播报样片**（MP3 + 逐字稿），作为后续 A/C 的基础。
4. 全流程**零付费、零 API key**。

## 2. 非目标

- 不做网站侧集合注册、播放器、导航与 RSS（属 A）。
- 不做真人在线录音、不做真人声克隆、不追求播音级音质。
- 不做自动配乐选曲、不做自动事实核查（内容事实由 C 阶段按正典把关）。
- 不引入除 `edge-tts` / `imageio-ffmpeg` 之外的音频依赖，不要求系统级安装 ffmpeg。

## 3. 技术选型与可行性（已实测）

| 环节 | 方案 | 实测结论 |
| --- | --- | --- |
| 语音合成 | `edge-tts` 7.2.8（微软 Edge 神经语音） | ✅ 已成功合成 MP3，联网正常，免费、无 key |
| 音频拼接/混音/测时长 | `imageio-ffmpeg` 自带静态 ffmpeg 7.1 | ✅ 已安装并取到可执行文件，兼容 Python 3.14 |
| 中文音色 | zh-CN 系列共 8 个音色 | ✅ 含新闻级男/女声 |
| 环境 | Python 3.14.4 / Node 24 / Windows | ✅ |

选 `imageio-ffmpeg` 而非系统 ffmpeg：本机无系统 ffmpeg，该包自带二进制，`pip install` 即可用，避免让用户手动配置 PATH。

## 4. 目录与产物

### 4.1 新增源文件（`tools/` 已被 Jekyll `exclude`，不发布）

```
tools/podcast/
  voices.yml            # 角色 → {音色, 显示名}
  build.py              # 合成 → 混音 → 测时长 → 生成 MP3 与逐字稿
  scripts/
    <slug>.yml          # 单集脚本源（唯一事实源）
  assets/
    bgm/                # 背景音乐源（CC0 / 自制 / 程序化生成）
    sfx/                # 转场、提示音
    stinger/            # 片头/片尾台标
    CREDITS.md          # 外部素材来源/作者/协议/日期记录
  gen-assets.py         # 程序化生成片头/转场等素材（可选运行）
  .cache/               # 分段音频缓存（按文本 hash），gitignore
  README.md             # 命令行用法
```

### 4.2 产物（提交入库，供 A 阶段使用）

```
assets/audio/podcast/<slug>.mp3      # 成品音频
_podcasts/YYYY-MM-DD-<slug>.md       # front matter + 逐字稿 + 时间轴
```

> 生成时 `_podcasts/` 尚未在 `_config.yml` 注册集合，故 B 阶段该目录不会被 Jekyll 发布；A 阶段注册后即自动上线。

## 5. 脚本源格式

单集唯一事实源为 `tools/podcast/scripts/<slug>.yml`：

```yaml
slug: 2026-10-05-和国政府新闻播报-第1期
title: "第 1 期｜和国政府新闻播报"
date: 2026-10-05 09:00:00
episode_type: 播报            # 播报 | 访谈
excerpt: "一句话简介，≤ 90 字"
publisher: "和各中央广播与电视平台"   # 可选，缺省用“和各政府网”
related_post: "/新闻/xxx/"     # 可选，关联站内文章
hosts: ["云阳"]               # 主播显示名
guests: []                    # 访谈才有

segments:                     # 按顺序合成、拼接
  - role: anchor
    text: "各位听众，大家好，这里是和国政府广播，欢迎收听本期新闻播报。"
  - role: anchor
    text: "……"
  - role: guest
    text: "……"                # 访谈段落
    voice: zh-CN-YunjianNeural   # 可选覆盖
    rate: "+5%"                  # 可选覆盖

bed:                          # 铺底音乐（可多条）
  - file: bgm/news-bed.mp3
    gain_db: -22
    duck_db: -10
    fade_in: 1.5
    fade_out: 2.0

cues:                         # 定点音效
  - at_segment: 0             # 以第 N 段起点定位
    file: stinger/open.mp3
    gain_db: -6
  - at: "00:45.000"           # 或以绝对时间定位
    file: sfx/transition.mp3
    gain_db: -8
```

规则：

- `segments[].text` 必须是**可直接朗读的口播文本**，数字/符号按读音写（由作者在 C 阶段保证）。
- 未声明 `bed` / `cues` 时纯人声输出。
- 段落级 `voice` / `rate` 覆盖 `voices.yml` 默认。

## 6. 音色表（`voices.yml`）

```yaml
roles:
  anchor:    { voice: zh-CN-YunyangNeural,  name: 主播 }    # 男 · News · 专业可靠
  coanchor:  { voice: zh-CN-XiaoxiaoNeural, name: 主播 }    # 女 · News · 温暖
  host:      { voice: zh-CN-XiaoxiaoNeural, name: 主持人 }  # 访谈主持
  guest:     { voice: zh-CN-YunjianNeural,  name: 嘉宾 }    # 男 · 热情
  guest2:    { voice: zh-CN-XiaoyiNeural,   name: 嘉宾 }    # 女 · 活泼
defaults:
  rate: "+0%"
  volume: "+0%"
  pitch: "+0Hz"
```

- 播报：`anchor` 单人或 `anchor`+`coanchor`。
- 访谈：`host` + `guest`/`guest2`，音色天然区分说话人。
- `name` 用于逐字稿显示名，可被脚本源角色名覆盖。

## 7. 音效与背景音乐

### 7.1 素材来源（按优先级）

1. **程序化生成**（默认、零版权）：`gen-assets.py` 用 ffmpeg 合成
   - `stinger/open.mp3`、`stinger/close.mp3`：简单和弦/音阶上下行台标；
   - `sfx/transition.mp3`：短促扫频/提示音；
   - `bgm/news-bed.mp3`：低音量、无旋律感的中性铺底（正弦/极简脉冲）。
2. **CC0 / 无版权素材**：如 Pixabay Music 等明确允许商用免署名的曲库，下载后放入 `tools/podcast/assets/`。
3. **自制/用户提供**：用户提供有明确授权的文件。

### 7.2 版权底线（强制）

- 只接受 **CC0 / 公共领域 / 自产**，或协议明确允许本项目用途且已记录来源与协议。
- 禁止提交来源不明的音乐；每个外部素材在 `tools/podcast/assets/CREDITS.md` 记录来源、作者、协议、获取日期。
- 成品 MP3 会把素材烘进去，故素材源文件本身不发布；但授权记录必须留存。

## 8. 混音实现（ffmpeg）

用 `imageio-ffmpeg` 提供的 ffmpeg，按 `filter_complex` 构建：

1. 人声轨：各段 MP3 顺序 concat。
2. `bed`：循环（`aloop`）并裁剪到人声总长，`volume` 施加 `gain_db`，两端 `afade` 淡入淡出；再以人声为 sidechain 走 `sidechaincompress` 实现自动闪避（`duck_db`）。
3. `cues`：`adelay` 定位到目标时间，`volume` 施加 `gain_db`。
4. `amix` 合并人声 + bed + cues；用 ffmpeg `loudnorm` 统一响度（目标 `I=-16`，播客常用）后输出 MP3（24kHz 单声道 48kbps）。

## 9. `build.py` 流程

1. 读入 `scripts/<slug>.yml` 与 `voices.yml`（`--all` 时遍历全部脚本）。
2. 逐段调用 edge-tts 合成临时 MP3；缓存键 = 文本 + 音色 + rate/volume/pitch 的 hash，命中则复用（改文本或音色会自动失效）。
3. 拼接人声轨，叠加 `bed` 与 `cues` 混音，输出 `assets/audio/podcast/<slug>.mp3`。
4. 用 ffprobe 读每段与总时长 → 计算累计**时间轴**。
5. 渲染逐字稿 Markdown（front matter + 分段内容 + 时间戳）写到 `_podcasts/YYYY-MM-DD-<slug>.md`。
6. 打印结果摘要（时长、体积、输出路径）。

命令行：

```bash
python tools/podcast/build.py <slug>      # 构建单集
python tools/podcast/build.py --all       # 构建全部
python tools/podcast/build.py --no-cache  # 忽略缓存
```

## 10. 逐字稿输出格式

生成的 `_podcasts/YYYY-MM-DD-<slug>.md`：

```markdown
---
title: "第 1 期｜和国政府新闻播报"
excerpt: "……"
date: 2026-10-05 09:00:00
episode_type: 播报
audio: /assets/audio/podcast/<slug>.mp3
duration: "05:32"
hosts: ["云阳"]
guests: []
related_post: "/新闻/xxx/"
transcript: true
publisher: "和各中央广播与电视平台"
---

> 本页为播客逐字稿，音频见上方播放器（A 阶段接入）。

**00:00｜主播**　各位听众，大家好……

**00:12｜主播**　……
```

- 时间戳来自真实音频时长，即“分镜/时间轴”。
- front matter 字段与 A 阶段集合设计对齐，A 接入后无需改动。

## 11. 命名、体积与入库规则

- 单集 `slug`：英文小写 + `-`，或可读中文短语（与既有 `_posts` 中文化 URL 习惯一致），保证文件名可作 URL。
- 音频规格：24kHz 单声道 48kbps；5 分钟 ≈ 1.8MB，15 分钟 ≈ 5.4MB。
- 成品 MP3 与生成 md 直接提交（与仓库提交 `main.min.js` 的既有习惯一致）。
- `.gitignore` 追加：`tools/podcast/.cache/`、`tools/podcast/assets/bgm/`、`tools/podcast/assets/sfx/`、`tools/podcast/assets/stinger/`（素材源不入库）；`tools/podcast/assets/CREDITS.md` 例外，必须入库。
- 体积监控：仓库接近阈值时再考虑外链托管（列为后续风险，不在 B 内解决）。

## 12. 验证方式

本仓库无单元测试，验收 = 运行结果：

1. `python tools/podcast/build.py <slug>` 成功退出，无异常。
2. `assets/audio/podcast/<slug>.mp3` 存在且 ffprobe 报时长 > 0、可正常播放。
3. `_podcasts/YYYY-MM-DD-<slug>.md` 生成，时间轴递增、段落与脚本源一致。
4. 人工试听：人声清晰、背景音乐存在且在人声处明显闪避、片头/转场音效落在预期位置。

## 13. 风险与取舍

- **逐字稿由 YAML 生成**：想改文稿须改 YAML 源（用户已选“YAML 自动生成”，换取两端一致）。
- **TTS 读音**：中文数字/专名读音由口播文本控制，个别专名可能需用同音字微调。
- **音色缓存**：缓存只按文本+参数 hash，属确定性策略；`--no-cache` 可强制重算。
- **仓库体积**：MP3 入库会持续增大 git 体积，量大后需迁外链。
- **音质**：edge-tts 为通用神经语音，非“政府播音员”专用音色，观感以可用为先。
- **素材版权**：程序化生成无风险；外部素材必须留授权记录，否则不得入库。

## 14. 决策记录

- 先做子项目：B（用户选择）。
- 逐字稿来源：YAML 源自动生成（用户选择）。
- 音色构成：播报与访谈两种都要（用户选择）。
- 音乐/音效素材：程序化生成为主，另可搜索 CC0 素材（用户选择）。
- 音频引擎：edge-tts；ffmpeg 走 imageio-ffmpeg（实测决定）。
- 网站承载：独立播客栏目（用户选择，属 A 阶段）。

## 15. 后续（非本规格范围）

- **A. 网站播客栏目**：`_config.yml` 注册 `collections.podcasts`；`_layouts/podcast.html`；`_includes/podcast-player.html`；`_pages/podcast.md`；导航入口；独立 `podcast.xml`（含 `<enclosure>`）；样式入 `_sass/minimal-mistakes/_custom.scss`。
- **C. 内容生产**：从既有 `_posts` 与 Hegewiki 正典改写播报稿；设计访谈选题与虚构嘉宾；遵守 `docs/写作与排版规范.md`。
- **配套文档**：`docs/播客制作规范.md`（音色表、脚本写法、音效/BGM 规则与版权、命名、发布流程），与 `docs/写作与排版规范.md` 并列。
