# 和国播客音频生产流水线

把结构化的 YAML 脚本合成为带背景音乐、音效、多音色的成品 MP3，并同时生成逐句 VTT 字幕与逐字稿时间轴。
详细规则见 `docs/播客制作规范.md`。

## 环境

- Python 3.14
- 依赖（已安装）：`edge-tts`、`imageio-ffmpeg`、`PyYAML`

## 用法

```bash
# 生成音效与铺底音乐（首次或需要重生成时，输出到 tools/podcast/assets/）
python tools/podcast/gen_assets.py

# 构建单集（读取 tools/podcast/scripts/<slug>.yml）
python tools/podcast/build.py hege-news-ep1

# 构建全部
python tools/podcast/build.py --all

# 忽略分段缓存
python tools/podcast/build.py <slug> --no-cache

# 运行测试
python -m unittest discover -s tools/podcast/tests -t tools/podcast -v
```

脚本可选 `intro` 字段配置片头预滚（播放完片头后主播才开口）；外部素材（含片头）放入 `tools/podcast/assets/` 并在 `CREDITS.md` 登记。详见 `docs/播客制作规范.md`。

## 产物

- `assets/audio/podcast/<slug>.mp3`
- `assets/audio/podcast/<slug>.vtt`（逐句字幕，WebVTT）
- `_podcasts/YYYY-MM-DD-<slug>.md`（含逐字稿与时间轴）

## 网站附产物

- 单集发布到 `/podcast/<slug>/`，栏目页 `/podcast/`，RSS `/podcast.xml`（见 `docs/播客制作规范.md`）。
- 生成播客封面：`python tools/podcast/gen_cover.py` → `assets/images/podcast-cover.png`。
