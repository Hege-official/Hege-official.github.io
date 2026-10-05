# 和国播客 · 音频生产流水线（子项目 B）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一条“YAML 脚本源 → 多音色合成 → 混音（BGM/音效）→ 成品 MP3 + 逐字稿/时间轴”的音频生产流水线，并产出一条可听的播报样片。

**Architecture:** 新增 `tools/podcast/`（已被 Jekyll `exclude`）。核心逻辑拆成 `podcast_lib` 包：`config`（加载/校验脚本与音色）、`synth`（edge-tts 合成 + hash 缓存）、`audio`（ffmpeg 探测/拼接/混音）、`transcript`（时间轴与逐字稿渲染）。`build.py` 是 CLI 编排器，`gen_assets.py` 程序化生成音效/BGM。产物写入仓库根的 `assets/audio/podcast/` 与 `_podcasts/`。

**Tech Stack:** Python 3.14（stdlib `unittest`、`argparse`、`subprocess`、`hashlib`）、`edge-tts` 7.2.8、`imageio-ffmpeg`（自带 ffmpeg 7.1）、`PyYAML`（Jekyll 环境已有）。

**Spec:** `docs/superpowers/specs/2026-10-05-podcast-audio-pipeline-design.md`

## Global Constraints

- Python：3.14（本机 `C:\Python314\python.exe`）。
- 依赖：只用已安装的 `edge-tts`、`imageio-ffmpeg`、`PyYAML`；不新增第三方依赖；测试用 stdlib `unittest`。
- 不要求系统级 ffmpeg；一律通过 `imageio_ffmpeg.get_ffmpeg_exe()` 取得可执行文件。
- 音频规格：采样率 24000、单声道、`-b:a 48k`。
- 输出响度：`loudnorm=I=-16:TP=-1.5:LRA=11`。
- 仓库路径含空格（`D:\Web program\minimal-mistakes-master`）；所有子进程参数用列表传递，拼接清单内路径用单引号包裹。
- `tools/` 已被 `_config.yml` 的 `exclude` 排除，不发布；产物目录是仓库根下的 `assets/audio/podcast/` 与 `_podcasts/`。
- 逐字稿由 YAML 源自动生成，音频与文稿同源。
- 测试命令统一在仓库根执行：`python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`。
- 提交信息用中文，风格对齐现有仓库（`feat:` / `docs:` / `chore:` 前缀）。
- 外部音乐/音效素材必须 CC0/自制/用户提供，并在 `tools/podcast/assets/CREDITS.md` 记录；程序化生成的自产素材无需外部记录。

## Review Focus

以下输入/失败模式规格有隐含要求、但单靠“快乐路径”测试覆盖不到，需在对应任务的测试里钉死：

1. **空或纯空白段落文本** → 应明确报错，绝不静默产出空音频。
2. **`at_segment` 越界 / `at` 时间码非法** → 应清晰报错，而不是崩溃或错位。
3. **未知角色 role / 缺必填字段（title、date）/ role 缺 voice 或 name** → 应给出可定位的报错。
4. **bed/cue 引用的素材文件不存在** → 应给出含路径的清晰报错。
5. **重复构建（缓存命中、输出已存在）** → 应幂等：复用缓存、覆盖输出，不追加、不报错。

---

## 文件结构

```
tools/podcast/
  build.py                 # CLI 编排：合成→拼接→混音→产出 MP3 与逐字稿
  gen_assets.py            # 程序化生成 stinger/sfx/bgm（自产、零版权）
  voices.yml               # 角色 → {voice, name} + defaults
  scripts/
    hege-news-ep1.yml      # 播报样片脚本源（slug 不含日期；日期来自 date 字段）
  assets/
    CREDITS.md             # 外部素材授权记录（入库）
    bgm/ sfx/ stinger/     # 素材源（gitignore，不入库）
  podcast_lib/
    __init__.py
    config.py              # 加载 voices.yml / 脚本，解析为 Segment / Episode
    synth.py               # edge-tts 合成 + 缓存
    audio.py               # ffmpeg：probe_duration / concat_mp3 / mix_episode
    transcript.py          # format_timestamp / parse_timecode / build_timeline / render_episode_md
  tests/
    __init__.py
    test_config.py
    test_synth.py
    test_audio.py
    test_transcript.py
    test_build.py
  README.md                # 命令行用法

产物（仓库根，入库）：
  assets/audio/podcast/<slug>.mp3
  _podcasts/YYYY-MM-DD-<slug>.md

文档：
  docs/播客制作规范.md
```

---

### Task 1: 脚手架、音色表与脚本解析

**Files:**
- Create: `tools/podcast/voices.yml`
- Create: `tools/podcast/podcast_lib/__init__.py`
- Create: `tools/podcast/podcast_lib/config.py`
- Create: `tools/podcast/tests/__init__.py`
- Create: `tools/podcast/tests/test_config.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: 无
- Produces:
  - `podcast_lib.config.ConfigError(ValueError)`
  - `podcast_lib.config.Segment`（frozen dataclass：`role: str, text: str, voice: str, name: str, rate: str, volume: str, pitch: str`）
  - `podcast_lib.config.Episode`（frozen dataclass：`slug, title, date, episode_type, excerpt, publisher, related_post, hosts: list[str], guests: list[str], segments: list[Segment], bed: list[dict], cues: list[dict]`）
  - `podcast_lib.config.load_voices(path) -> dict`（返回 `{"roles": {...}, "defaults": {...}}`）
  - `podcast_lib.config.resolve_segment(raw, voices) -> Segment`
  - `podcast_lib.config.load_episode(path, voices) -> Episode`

- [ ] **Step 1: 写失败的测试**

Create `tools/podcast/tests/__init__.py`（空文件）和 `tools/podcast/tests/test_config.py`：

```python
import tempfile
import unittest
from pathlib import Path

from podcast_lib import config

VOICES = {
    "roles": {"anchor": {"voice": "zh-CN-YunyangNeural", "name": "主播"}},
    "defaults": {"rate": "+0%", "volume": "+0%", "pitch": "+0Hz"},
}


class ResolveSegmentTest(unittest.TestCase):
    def test_applies_role_and_defaults(self):
        seg = config.resolve_segment({"role": "anchor", "text": " 各位听众 "}, VOICES)
        self.assertEqual(seg.text, "各位听众")
        self.assertEqual(seg.voice, "zh-CN-YunyangNeural")
        self.assertEqual(seg.name, "主播")
        self.assertEqual(seg.rate, "+0%")

    def test_per_segment_override(self):
        seg = config.resolve_segment(
            {"role": "anchor", "text": "嗨", "voice": "X", "rate": "+10%", "name": "旁白"},
            VOICES,
        )
        self.assertEqual(seg.voice, "X")
        self.assertEqual(seg.rate, "+10%")
        self.assertEqual(seg.name, "旁白")

    def test_unknown_role_raises(self):
        with self.assertRaises(config.ConfigError):
            config.resolve_segment({"role": "nobody", "text": "嗨"}, VOICES)

    def test_empty_text_raises(self):
        with self.assertRaises(config.ConfigError):
            config.resolve_segment({"role": "anchor", "text": "   "}, VOICES)

    def test_missing_role_raises(self):
        with self.assertRaises(config.ConfigError):
            config.resolve_segment({"text": "嗨"}, VOICES)


class LoadVoicesTest(unittest.TestCase):
    def test_role_without_voice_raises(self):
        bad = {"roles": {"anchor": {"name": "主播"}}}
        with self.assertRaises(config.ConfigError):
            config.load_voices_from(bad)

    def test_defaults_merged(self):
        voices = config.load_voices_from({"roles": VOICES["roles"], "defaults": {"rate": "+5%"}})
        self.assertEqual(voices["defaults"]["rate"], "+5%")
        self.assertEqual(voices["defaults"]["volume"], "+0%")


class LoadEpisodeTest(unittest.TestCase):
    def _write(self, text):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False, encoding="utf-8")
        tmp.write(text)
        tmp.close()
        return Path(tmp.name)

    def test_missing_title_raises(self):
        path = self._write(
            "date: 2026-10-05\nsegments:\n  - role: anchor\n    text: '嗨'\n"
        )
        with self.assertRaises(config.ConfigError):
            config.load_episode(path, VOICES)

    def test_parses_episode(self):
        path = self._write(
            "slug: demo\ntitle: 标题\ndate: 2026-10-05 09:00:00\n"
            "episode_type: 播报\nhosts: ['云阳']\n"
            "segments:\n  - role: anchor\n    text: '嗨'\n"
        )
        ep = config.load_episode(path, VOICES)
        self.assertEqual(ep.slug, "demo")
        self.assertEqual(ep.date, "2026-10-05 09:00:00")
        self.assertEqual(ep.hosts, ["云阳"])
        self.assertEqual(len(ep.segments), 1)

    def test_no_segments_raises(self):
        path = self._write("title: 标题\ndate: 2026-10-05\nsegments: []\n")
        with self.assertRaises(config.ConfigError):
            config.load_episode(path, VOICES)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'podcast_lib'`）。

- [ ] **Step 3: 写最小实现**

Create `tools/podcast/podcast_lib/__init__.py`（空文件）。

Create `tools/podcast/voices.yml`：

```yaml
roles:
  anchor:    { voice: zh-CN-YunyangNeural,  name: 主播 }
  coanchor:  { voice: zh-CN-XiaoxiaoNeural, name: 主播 }
  host:      { voice: zh-CN-XiaoxiaoNeural, name: 主持人 }
  guest:     { voice: zh-CN-YunjianNeural,  name: 嘉宾 }
  guest2:    { voice: zh-CN-XiaoyiNeural,   name: 嘉宾 }
defaults:
  rate: "+0%"
  volume: "+0%"
  pitch: "+0Hz"
```

Create `tools/podcast/podcast_lib/config.py`：

```python
"""加载音色表与单集脚本源，解析为强类型 Segment / Episode。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

FALLBACK_DEFAULTS = {"rate": "+0%", "volume": "+0%", "pitch": "+0Hz"}


class ConfigError(ValueError):
    """脚本源或音色表不合法。"""


@dataclass(frozen=True)
class Segment:
    role: str
    text: str
    voice: str
    name: str
    rate: str
    volume: str
    pitch: str


@dataclass(frozen=True)
class Episode:
    slug: str
    title: str
    date: str
    episode_type: str
    excerpt: str
    publisher: str
    related_post: str
    hosts: list
    guests: list
    segments: list
    bed: list
    cues: list


def _read_yaml(path):
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"找不到文件：{path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML 解析失败：{path}\n{exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"顶层结构必须是映射：{path}")
    return data


def load_voices_from(data):
    roles = data.get("roles") or {}
    defaults = {**FALLBACK_DEFAULTS, **(data.get("defaults") or {})}
    if not roles:
        raise ConfigError("voices 未定义任何角色")
    for role, cfg in roles.items():
        if not isinstance(cfg, dict) or not cfg.get("voice") or not cfg.get("name"):
            raise ConfigError(f"角色 {role} 必须同时设置 voice 与 name")
    return {"roles": roles, "defaults": defaults}


def load_voices(path):
    return load_voices_from(_read_yaml(path))


def resolve_segment(raw, voices):
    if not isinstance(raw, dict):
        raise ConfigError("segment 必须是映射")
    role = raw.get("role")
    if not role:
        raise ConfigError("segment 缺少 role")
    if role not in voices["roles"]:
        raise ConfigError(f"未知角色：{role}（可选：{', '.join(voices['roles'])}）")
    text = (raw.get("text") or "").strip()
    if not text:
        raise ConfigError(f"角色 {role} 的段落 text 为空")
    base = voices["roles"][role]
    defaults = voices["defaults"]
    return Segment(
        role=role,
        text=text,
        voice=raw.get("voice") or base["voice"],
        name=raw.get("name") or base["name"],
        rate=raw.get("rate") or defaults["rate"],
        volume=raw.get("volume") or defaults["volume"],
        pitch=raw.get("pitch") or defaults["pitch"],
    )


def load_episode(path, voices):
    data = _read_yaml(path)
    for key in ("title", "date"):
        if not data.get(key):
            raise ConfigError(f"{path} 缺少必填字段 {key}")
    raw_segments = data.get("segments")
    if not raw_segments:
        raise ConfigError(f"{path} 未包含任何 segments")
    segments = [resolve_segment(s, voices) for s in raw_segments]
    return Episode(
        slug=data.get("slug") or Path(path).stem,
        title=data["title"],
        date=str(data["date"]),
        episode_type=data.get("episode_type", "播报"),
        excerpt=data.get("excerpt", ""),
        publisher=data.get("publisher", "和各政府网"),
        related_post=data.get("related_post", ""),
        hosts=list(data.get("hosts") or []),
        guests=list(data.get("guests") or []),
        segments=segments,
        bed=list(data.get("bed") or []),
        cues=list(data.get("cues") or []),
    )
```

Modify `.gitignore`，在文件末尾追加：

```
# Podcast 音视频生产（源与缓存不入库）
tools/podcast/.cache/
tools/podcast/assets/bgm/
tools/podcast/assets/sfx/
tools/podcast/assets/stinger/
tools/podcast/**/__pycache__/
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: PASS（全部用例通过）。

- [ ] **Step 5: 提交**

```bash
git add tools/podcast/voices.yml tools/podcast/podcast_lib tools/podcast/tests .gitignore
git commit -m "feat: 播客流水线脚手架、音色表与脚本解析"
```

---

### Task 2: 分段合成与缓存

**Files:**
- Create: `tools/podcast/podcast_lib/synth.py`
- Create: `tools/podcast/tests/test_synth.py`

**Interfaces:**
- Consumes: `podcast_lib.config.Segment`
- Produces:
  - `podcast_lib.synth.cache_key(seg) -> str`（16 位 hex）
  - `podcast_lib.synth.default_synth(seg, out_path) -> None`（调用 edge-tts）
  - `podcast_lib.synth.synthesize(seg, cache_dir, synth_fn=None, use_cache=True) -> pathlib.Path`

- [ ] **Step 1: 写失败的测试**

Create `tools/podcast/tests/test_synth.py`：

```python
import tempfile
import unittest
from pathlib import Path

from podcast_lib import synth
from podcast_lib.config import Segment


def make_segment(text="各位听众", voice="V1", rate="+0%"):
    return Segment(
        role="anchor", text=text, voice=voice, name="主播",
        rate=rate, volume="+0%", pitch="+0Hz",
    )


class CacheKeyTest(unittest.TestCase):
    def test_stable_for_same_params(self):
        self.assertEqual(synth.cache_key(make_segment()), synth.cache_key(make_segment()))

    def test_changes_with_text(self):
        self.assertNotEqual(
            synth.cache_key(make_segment(text="A")),
            synth.cache_key(make_segment(text="B")),
        )

    def test_changes_with_voice(self):
        self.assertNotEqual(
            synth.cache_key(make_segment(voice="V1")),
            synth.cache_key(make_segment(voice="V2")),
        )


class SynthesizeTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.calls = []

    def tearDown(self):
        self._tmp.cleanup()

    def _fake_synth(self, seg, out_path):
        self.calls.append(seg.text)
        Path(out_path).write_bytes(b"fake-audio-bytes")

    def test_creates_audio_and_calls_synth_once(self):
        seg = make_segment()
        path = synth.synthesize(seg, self.dir, synth_fn=self._fake_synth)
        self.assertTrue(path.exists())
        self.assertEqual(len(self.calls), 1)

    def test_second_call_hits_cache(self):
        seg = make_segment()
        synth.synthesize(seg, self.dir, synth_fn=self._fake_synth)

        def boom(seg, out_path):
            raise AssertionError("不应再次合成")

        path = synth.synthesize(seg, self.dir, synth_fn=boom)
        self.assertTrue(path.exists())

    def test_no_cache_forces_resynth(self):
        seg = make_segment()
        synth.synthesize(seg, self.dir, synth_fn=self._fake_synth)
        synth.synthesize(seg, self.dir, synth_fn=self._fake_synth, use_cache=False)
        self.assertEqual(len(self.calls), 2)

    def test_empty_output_raises(self):
        def empty_synth(seg, out_path):
            Path(out_path).write_bytes(b"")

        with self.assertRaises(RuntimeError):
            synth.synthesize(make_segment(), self.dir, synth_fn=empty_synth)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: FAIL（`No module named 'podcast_lib.synth'`）。

- [ ] **Step 3: 写最小实现**

Create `tools/podcast/podcast_lib/synth.py`：

```python
"""逐段调用 edge-tts 合成音频，并按参数 hash 缓存。"""
from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

import edge_tts


def cache_key(seg) -> str:
    payload = json.dumps(
        {
            "text": seg.text,
            "voice": seg.voice,
            "rate": seg.rate,
            "volume": seg.volume,
            "pitch": seg.pitch,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


async def _edge_synth(text, voice, rate, volume, pitch, out_path):
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
    await communicate.save(str(out_path))


def default_synth(seg, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_edge_synth(seg.text, seg.voice, seg.rate, seg.volume, seg.pitch, out_path))


def synthesize(seg, cache_dir, synth_fn=None, use_cache=True):
    synth_fn = synth_fn or default_synth
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / f"{cache_key(seg)}.mp3"
    if use_cache and target.exists() and target.stat().st_size > 0:
        return target
    tmp = target.with_suffix(".part.mp3")
    if tmp.exists():
        tmp.unlink()
    synth_fn(seg, tmp)
    if not tmp.exists() or tmp.stat().st_size == 0:
        raise RuntimeError(f"合成未产生有效音频：{seg.text[:20]}…")
    tmp.replace(target)
    return target
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add tools/podcast/podcast_lib/synth.py tools/podcast/tests/test_synth.py
git commit -m "feat: 播客分段合成与 hash 缓存"
```

---

### Task 3: 音频探测与拼接

**Files:**
- Create: `tools/podcast/podcast_lib/audio.py`（本任务只含 probe/concat，混音在 Task 4 追加）
- Create: `tools/podcast/tests/test_audio.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `podcast_lib.audio.ffmpeg_exe() -> str`
  - `podcast_lib.audio.probe_duration(path) -> float`（秒）
  - `podcast_lib.audio.concat_mp3(paths, out_path, work_dir) -> None`

- [ ] **Step 1: 写失败的测试**

Create `tools/podcast/tests/test_audio.py`：

```python
import subprocess
import tempfile
import unittest
from pathlib import Path

from podcast_lib import audio


def make_tone(path, freq, duration):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            audio.ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={duration}",
            "-ar", "24000", "-ac", "1", str(path),
        ],
        check=True,
    )


class ProbeDurationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_reads_expected_duration(self):
        tone = self.dir / "tone.mp3"
        make_tone(tone, 440, 2.0)
        self.assertAlmostEqual(audio.probe_duration(tone), 2.0, delta=0.15)

    def test_missing_file_raises(self):
        with self.assertRaises(RuntimeError):
            audio.probe_duration(self.dir / "nope.mp3")


class ConcatTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_length_is_sum_of_parts(self):
        a = self.dir / "a.mp3"
        b = self.dir / "b.mp3"
        make_tone(a, 440, 1.0)
        make_tone(b, 550, 0.5)
        out = self.dir / "out.mp3"
        audio.concat_mp3([a, b], out, self.dir)
        self.assertAlmostEqual(audio.probe_duration(out), 1.5, delta=0.2)

    def test_empty_list_raises(self):
        with self.assertRaises(ValueError):
            audio.concat_mp3([], self.dir / "out.mp3", self.dir)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: FAIL（`No module named 'podcast_lib.audio'`）。

- [ ] **Step 3: 写最小实现**

Create `tools/podcast/podcast_lib/audio.py`：

```python
"""ffmpeg 封装：探测时长、拼接人声、混音。"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import imageio_ffmpeg


def ffmpeg_exe() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def _run(args):
    proc = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", *[str(a) for a in args]],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 失败：\n{proc.stderr.strip()}")


_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


def probe_duration(path) -> float:
    proc = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-i", str(path)],
        capture_output=True,
        text=True,
    )
    match = _DURATION_RE.search(proc.stderr)
    if not match:
        raise RuntimeError(f"无法读取音频时长：{path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def concat_mp3(paths, out_path, work_dir):
    paths = [Path(p) for p in paths]
    if not paths:
        raise ValueError("没有可拼接的音频段")
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    listing = work_dir / "concat.txt"
    listing.write_text(
        "".join(f"file '{p.resolve().as_posix()}'\n" for p in paths),
        encoding="utf-8",
    )
    _run(["-f", "concat", "-safe", "0", "-i", listing, "-c", "copy", out_path])
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: PASS（需本机可用 ffmpeg，即已安装 imageio-ffmpeg）。

- [ ] **Step 5: 提交**

```bash
git add tools/podcast/podcast_lib/audio.py tools/podcast/tests/test_audio.py
git commit -m "feat: 播客音频时长探测与拼接"
```

---

### Task 4: 铺底音乐与音效混音

**Files:**
- Modify: `tools/podcast/podcast_lib/audio.py`（追加 `mix_episode`）
- Modify: `tools/podcast/tests/test_audio.py`（追加 `MixEpisodeTest`）

**Interfaces:**
- Consumes: `audio.probe_duration`、`audio.ffmpeg_exe`
- Produces:
  - `podcast_lib.audio.mix_episode(voice_track, out_path, work_dir, bed_specs=None, cues_specs=None, sample_rate=24000) -> None`
    - `bed_specs`：`list[dict]`，键 `path: Path, gain_db: float, duck: float, fade_in: float, fade_out: float`
    - `cues_specs`：`list[dict]`，键 `path: Path, start: float, gain_db: float`

- [ ] **Step 1: 写失败的测试**

在 `tools/podcast/tests/test_audio.py` 末尾（`if __name__` 之前）追加：

```python
class MixEpisodeTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _tone(self, name, duration, freq=440):
        path = self.dir / name
        make_tone(path, freq, duration)
        return path

    def test_voice_only_keeps_duration(self):
        voice = self._tone("voice.mp3", 2.0)
        out = self.dir / "out.mp3"
        audio.mix_episode(voice, out, self.dir, [], [])
        self.assertTrue(out.exists())
        self.assertAlmostEqual(audio.probe_duration(out), 2.0, delta=0.3)

    def test_bed_shorter_than_voice_does_not_truncate(self):
        voice = self._tone("voice.mp3", 3.0)
        bed = self._tone("bed.mp3", 0.5, freq=110)
        out = self.dir / "out.mp3"
        audio.mix_episode(
            voice, out, self.dir,
            [{"path": bed, "gain_db": -24, "duck": 0.85, "fade_in": 0.2, "fade_out": 0.2}],
            [],
        )
        self.assertAlmostEqual(audio.probe_duration(out), 3.0, delta=0.3)

    def test_cue_does_not_extend_duration(self):
        voice = self._tone("voice.mp3", 2.0)
        cue = self._tone("cue.mp3", 0.3, freq=880)
        out = self.dir / "out.mp3"
        audio.mix_episode(
            voice, out, self.dir, [],
            [{"path": cue, "start": 1.0, "gain_db": -10}],
        )
        self.assertAlmostEqual(audio.probe_duration(out), 2.0, delta=0.3)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: FAIL（`AttributeError: module 'podcast_lib.audio' has no attribute 'mix_episode'`）。

- [ ] **Step 3: 写最小实现**

在 `tools/podcast/podcast_lib/audio.py` 末尾追加：

```python
def mix_episode(voice_track, out_path, work_dir, bed_specs=None, cues_specs=None, sample_rate=24000):
    """人声轨 + 铺底音乐（自动闪避）+ 定点音效，输出统一响度的单声道 MP3。"""
    voice_track = Path(voice_track)
    bed_specs = bed_specs or []
    cues_specs = cues_specs or []
    total = probe_duration(voice_track)

    inputs = ["-i", str(voice_track)]
    parts = []
    mix_labels = ["0:a"]
    index = 1

    for spec in bed_specs:
        inputs += ["-stream_loop", "-1", "-i", str(spec["path"])]
        gain = float(spec.get("gain_db", 0))
        duck = float(spec.get("duck", 0.85))
        fade_in = float(spec.get("fade_in", 0))
        fade_out = float(spec.get("fade_out", 0))
        fade_out_start = max(0.0, total - fade_out)
        chain = [f"[{index}:a]atrim=0:{total:.3f}", "asetpts=N/SR/TB", f"volume={gain}dB"]
        if fade_in > 0:
            chain.append(f"afade=t=in:st=0:d={fade_in}")
        if fade_out > 0:
            chain.append(f"afade=t=out:st={fade_out_start:.3f}:d={fade_out}")
        parts.append(",".join(chain) + f"[bed{index}]")
        parts.append(
            f"[bed{index}][0:a]sidechaincompress="
            f"threshold=0.05:ratio=8:attack=20:release=350:mix={duck}[bedduck{index}]"
        )
        mix_labels.append(f"bedduck{index}")
        index += 1

    for spec in cues_specs:
        inputs += ["-i", str(spec["path"])]
        delay_ms = int(round(float(spec["start"]) * 1000))
        gain = float(spec.get("gain_db", 0))
        parts.append(f"[{index}:a]adelay={delay_ms}:all=1,volume={gain}dB[cue{index}]")
        mix_labels.append(f"cue{index}")
        index += 1

    if len(mix_labels) == 1:
        parts.append("[0:a]loudnorm=I=-16:TP=-1.5:LRA=11[out]")
    else:
        joined = "".join(f"[{label}]" for label in mix_labels)
        parts.append(f"{joined}amix=inputs={len(mix_labels)}:duration=first:normalize=0[mixed]")
        parts.append("[mixed]loudnorm=I=-16:TP=-1.5:LRA=11[out]")

    _run([
        *inputs,
        "-filter_complex", ";".join(parts),
        "-map", "[out]",
        "-ar", str(sample_rate), "-ac", "1", "-b:a", "48k",
        out_path,
    ])
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: PASS。若时长略有出入，容忍度 delta 0.3 内应通过。

- [ ] **Step 5: 提交**

```bash
git add tools/podcast/podcast_lib/audio.py tools/podcast/tests/test_audio.py
git commit -m "feat: 播客铺底音乐与音效混音"
```

---

### Task 5: 时间轴与逐字稿渲染

**Files:**
- Create: `tools/podcast/podcast_lib/transcript.py`
- Create: `tools/podcast/tests/test_transcript.py`

**Interfaces:**
- Consumes: `podcast_lib.config.Segment`（只读取 `.name`、`.text`）
- Produces:
  - `podcast_lib.transcript.format_timestamp(seconds) -> str`（`"MM:SS"`）
  - `podcast_lib.transcript.parse_timecode(value) -> float`（支持 `"45"` / `"1:02"` / `"00:45.000"` / `"1:02:03.5"`）
  - `podcast_lib.transcript.build_timeline(durations) -> list[float]`
  - `podcast_lib.transcript.render_episode_md(meta, segments, durations) -> str`

- [ ] **Step 1: 写失败的测试**

Create `tools/podcast/tests/test_transcript.py`：

```python
import unittest

from podcast_lib import transcript
from podcast_lib.config import Segment


def seg(name, text):
    return Segment(role="anchor", text=text, voice="V", name=name,
                   rate="+0%", volume="+0%", pitch="+0Hz")


class FormatTimestampTest(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(transcript.format_timestamp(0), "00:00")

    def test_minutes(self):
        self.assertEqual(transcript.format_timestamp(65), "01:05")

    def test_rounds(self):
        self.assertEqual(transcript.format_timestamp(59.6), "01:00")

    def test_long(self):
        self.assertEqual(transcript.format_timestamp(600), "10:00")


class ParseTimecodeTest(unittest.TestCase):
    def test_seconds(self):
        self.assertEqual(transcript.parse_timecode("45"), 45.0)

    def test_mm_ss(self):
        self.assertEqual(transcript.parse_timecode("1:02"), 62.0)

    def test_mm_ss_ms(self):
        self.assertEqual(transcript.parse_timecode("00:45.500"), 45.5)

    def test_hh_mm_ss(self):
        self.assertEqual(transcript.parse_timecode("1:02:03.5"), 3723.5)

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            transcript.parse_timecode("abc")


class BuildTimelineTest(unittest.TestCase):
    def test_cumulative(self):
        self.assertEqual(transcript.build_timeline([1.0, 2.0, 3.0]), [0.0, 1.0, 3.0])


class RenderEpisodeTest(unittest.TestCase):
    def test_contains_front_matter_and_lines(self):
        meta = {
            "title": "第 1 期", "excerpt": "简介", "date": "2026-10-05 09:00:00",
            "episode_type": "播报", "audio": "/assets/audio/podcast/demo.mp3",
            "hosts": ["云阳"], "guests": [], "related_post": "", "publisher": "和各政府网",
        }
        md = transcript.render_episode_md(meta, [seg("主播", "甲"), seg("嘉宾", "乙")], [1.0, 2.0])
        self.assertTrue(md.startswith("---"))
        self.assertIn("duration: 00:03", md)
        self.assertIn("**00:00｜主播**　甲", md)
        self.assertIn("**00:01｜嘉宾**　乙", md)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: FAIL（`No module named 'podcast_lib.transcript'`）。

- [ ] **Step 3: 写最小实现**

Create `tools/podcast/podcast_lib/transcript.py`：

```python
"""时间轴计算与逐字稿 Markdown 渲染。"""
from __future__ import annotations

import yaml


def format_timestamp(seconds) -> str:
    total = int(round(float(seconds)))
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


def parse_timecode(value) -> float:
    parts = str(value).split(":")
    try:
        numbers = [float(p) for p in parts]
    except ValueError as exc:
        raise ValueError(f"无法解析时间码：{value}") from exc
    if len(numbers) == 1:
        return numbers[0]
    if len(numbers) == 2:
        return numbers[0] * 60 + numbers[1]
    if len(numbers) == 3:
        return numbers[0] * 3600 + numbers[1] * 60 + numbers[2]
    raise ValueError(f"无法解析时间码：{value}")


def build_timeline(durations):
    starts = []
    cursor = 0.0
    for duration in durations:
        starts.append(cursor)
        cursor += float(duration)
    return starts


def render_episode_md(meta, segments, durations) -> str:
    starts = build_timeline(durations)
    total = starts[-1] + float(durations[-1]) if durations else 0.0
    front = dict(meta)
    front["duration"] = format_timestamp(total)
    front["transcript"] = True
    header = yaml.safe_dump(front, allow_unicode=True, sort_keys=False).strip()
    lines = ["---", header, "---", "", "> 本页为播客逐字稿，音频见上方播放器。", ""]
    for segment, start in zip(segments, starts):
        lines.append(f"**{format_timestamp(start)}｜{segment.name}**　{segment.text}")
        lines.append("")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add tools/podcast/podcast_lib/transcript.py tools/podcast/tests/test_transcript.py
git commit -m "feat: 播客时间轴与逐字稿渲染"
```

---

### Task 6: 程序化素材生成

**Files:**
- Create: `tools/podcast/gen_assets.py`
- Create: `tools/podcast/tests/test_gen_assets.py`
- Create: `tools/podcast/assets/CREDITS.md`

**Interfaces:**
- Consumes: `podcast_lib.audio.ffmpeg_exe`、`podcast_lib.audio.probe_duration`
- Produces:
  - `tools/podcast/gen_assets.py::generate(base_dir) -> list[Path]`（生成 `stinger/open.mp3`、`stinger/close.mp3`、`sfx/transition.mp3`、`bgm/news-bed.mp3`）

- [ ] **Step 1: 写失败的测试**

Create `tools/podcast/tests/test_gen_assets.py`：

```python
import importlib.util
import tempfile
import unittest
from pathlib import Path

from podcast_lib import audio

SPEC = importlib.util.spec_from_file_location(
    "gen_assets", Path(__file__).resolve().parents[1] / "gen_assets.py"
)
gen_assets = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen_assets)


class GenAssetsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_generates_all_assets_with_audio(self):
        created = gen_assets.generate(self.dir)
        expected = {
            "stinger/open.mp3", "stinger/close.mp3",
            "sfx/transition.mp3", "bgm/news-bed.mp3",
        }
        names = {p.relative_to(self.dir).as_posix() for p in created}
        self.assertEqual(names, expected)
        for path in created:
            self.assertGreater(audio.probe_duration(path), 0.0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: FAIL（`FileNotFoundError` / 找不到 `gen_assets.py`）。

- [ ] **Step 3: 写最小实现**

Create `tools/podcast/gen_assets.py`：

```python
"""程序化生成播客音效与铺底音乐（自产，零版权风险）。"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from podcast_lib import audio

ROOT = Path(__file__).resolve().parent
DEFAULT_DIR = ROOT / "assets"


def _run(args):
    proc = subprocess.run(
        [audio.ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
         *[str(a) for a in args]],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 失败：\n{proc.stderr.strip()}")


def _arpeggio(notes, out_path):
    inputs = []
    for freq, duration in notes:
        inputs += ["-f", "lavfi", "-i", f"sine=frequency={freq}:duration={duration}"]
    count = len(notes)
    chain = "".join(f"[{i}:a]" for i in range(count)) + f"concat=n={count}:v=0:a=1[cat]"
    _run([
        *inputs, "-filter_complex", chain, "-map", "[cat]",
        "-ar", "24000", "-ac", "1", "-b:a", "48k", out_path,
    ])


def _blip(out_path, freq=880.0, duration=0.2):
    _run([
        "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={duration}",
        "-af", "afade=t=in:d=0.02,afade=t=out:st=0.12:d=0.08",
        "-ar", "24000", "-ac", "1", "-b:a", "48k", out_path,
    ])


def _bed(out_path):
    _run([
        "-f", "lavfi", "-i", "sine=frequency=110:duration=8",
        "-f", "lavfi", "-i", "sine=frequency=165:duration=8",
        "-filter_complex",
        "[0:a][1:a]amix=inputs=2:normalize=0,lowpass=f=400,tremolo=f=0.25:d=0.3,volume=-6dB[bed]",
        "-map", "[bed]", "-ar", "24000", "-ac", "1", "-b:a", "48k", out_path,
    ])


def generate(base_dir):
    base = Path(base_dir)
    created = [
        base / "stinger" / "open.mp3",
        base / "stinger" / "close.mp3",
        base / "sfx" / "transition.mp3",
        base / "bgm" / "news-bed.mp3",
    ]
    for path in created:
        path.parent.mkdir(parents=True, exist_ok=True)
    _arpeggio([(523.25, 0.3), (659.25, 0.3), (783.99, 0.55)], base / "stinger" / "open.mp3")
    _arpeggio([(783.99, 0.3), (659.25, 0.3), (523.25, 0.55)], base / "stinger" / "close.mp3")
    _blip(base / "sfx" / "transition.mp3")
    _bed(base / "bgm" / "news-bed.mp3")
    return created


def main(argv=None):
    parser = argparse.ArgumentParser(description="生成播客音效与铺底音乐")
    parser.add_argument("--dir", default=str(DEFAULT_DIR), help="输出目录（默认 tools/podcast/assets）")
    args = parser.parse_args(argv)
    for path in generate(args.dir):
        print(f"✔ {path}（{audio.probe_duration(path):.2f}s）")


if __name__ == "__main__":
    main()
```

Create `tools/podcast/assets/CREDITS.md`：

```markdown
# 播客素材授权记录

本目录下的背景音乐、音效、台标素材必须为 CC0、公共领域或自制。

## 自产素材（程序化生成）

以下素材由 `tools/podcast/gen_assets.py` 用 ffmpeg 合成，属本项目自产，无第三方权利：

| 文件 | 生成方式 |
| --- | --- |
| `stinger/open.mp3` | 上行琶音（523/659/784 Hz） |
| `stinger/close.mp3` | 下行琶音（784/659/523 Hz） |
| `sfx/transition.mp3` | 880 Hz 短促提示音 |
| `bgm/news-bed.mp3` | 110/165 Hz 低通铺底 |

## 外部素材（若引入，逐条登记）

| 文件 | 来源 | 作者 | 协议 | 获取日期 |
| --- | --- | --- | --- | --- |
| （暂无） | | | | |
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: PASS。

- [ ] **Step 5: 生成素材并提交**

Run: `python tools/podcast/gen_assets.py`
Expected: 打印 4 个文件路径与时长（素材被 `.gitignore` 忽略，不入库；`CREDITS.md` 会入库）。

```bash
git add tools/podcast/gen_assets.py tools/podcast/tests/test_gen_assets.py tools/podcast/assets/CREDITS.md
git commit -m "feat: 程序化生成播客音效与铺底音乐"
```

---

### Task 7: 端到端 CLI、样片与文档

**Files:**
- Create: `tools/podcast/build.py`
- Create: `tools/podcast/tests/test_build.py`
- Create: `tools/podcast/scripts/hege-news-ep1.yml`
- Create: `tools/podcast/README.md`
- Create: `docs/播客制作规范.md`

**Interfaces:**
- Consumes: `config`、`synth`、`audio`、`transcript`
- Produces:
  - `tools/podcast/build.py::resolve_bed(specs, assets_dir) -> list[dict]`
  - `tools/podcast/build.py::resolve_cues(specs, assets_dir, segment_starts) -> list[dict]`
  - `tools/podcast/build.py::build_episode(script_path, use_cache=True) -> tuple[Path, Path]`

- [ ] **Step 1: 写失败的测试**

Create `tools/podcast/tests/test_build.py`：

```python
import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "build", Path(__file__).resolve().parents[1] / "build.py"
)
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class ResolveBedTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        (self.dir / "bgm").mkdir()
        (self.dir / "bgm" / "bed.mp3").write_bytes(b"x")

    def tearDown(self):
        self._tmp.cleanup()

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            build.resolve_bed([{"file": "bgm/nope.mp3"}], self.dir)

    def test_resolves_defaults(self):
        specs = build.resolve_bed([{"file": "bgm/bed.mp3"}], self.dir)
        self.assertEqual(specs[0]["gain_db"], 0.0)
        self.assertEqual(specs[0]["duck"], 0.85)


class ResolveCuesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        (self.dir / "sfx").mkdir()
        (self.dir / "sfx" / "c.mp3").write_bytes(b"x")
        self.starts = [0.0, 5.0, 10.0]

    def tearDown(self):
        self._tmp.cleanup()

    def test_at_segment_maps_to_start(self):
        specs = build.resolve_cues(
            [{"file": "sfx/c.mp3", "at_segment": 1}], self.dir, self.starts
        )
        self.assertEqual(specs[0]["start"], 5.0)

    def test_at_segment_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            build.resolve_cues(
                [{"file": "sfx/c.mp3", "at_segment": 9}], self.dir, self.starts
            )

    def test_at_timecode(self):
        specs = build.resolve_cues(
            [{"file": "sfx/c.mp3", "at": "00:07.500"}], self.dir, self.starts
        )
        self.assertEqual(specs[0]["start"], 7.5)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            build.resolve_cues([{"file": "sfx/nope.mp3", "at": "0"}], self.dir, self.starts)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: FAIL（找不到 `build.py`）。

- [ ] **Step 3: 写最小实现**

Create `tools/podcast/build.py`：

```python
"""构建单集播客：合成 → 拼接 → 混音 → 输出 MP3 与逐字稿。"""
from __future__ import annotations

import argparse
from pathlib import Path

from podcast_lib import audio, config, synth, transcript

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
VOICES_PATH = ROOT / "voices.yml"
SCRIPTS_DIR = ROOT / "scripts"
ASSETS_DIR = ROOT / "assets"
CACHE_DIR = ROOT / ".cache"
WORK_DIR = CACHE_DIR / "work"
AUDIO_OUT_DIR = REPO / "assets" / "audio" / "podcast"
EPISODE_OUT_DIR = REPO / "_podcasts"


def resolve_bed(specs, assets_dir):
    resolved = []
    for spec in specs:
        path = Path(assets_dir) / spec["file"]
        if not path.exists():
            raise FileNotFoundError(f"背景音乐不存在：{path}")
        resolved.append({
            "path": path,
            "gain_db": float(spec.get("gain_db", 0)),
            "duck": float(spec.get("duck", 0.85)),
            "fade_in": float(spec.get("fade_in", 0)),
            "fade_out": float(spec.get("fade_out", 0)),
        })
    return resolved


def resolve_cues(specs, assets_dir, segment_starts):
    resolved = []
    for spec in specs:
        path = Path(assets_dir) / spec["file"]
        if not path.exists():
            raise FileNotFoundError(f"音效不存在：{path}")
        if "at" in spec:
            start = transcript.parse_timecode(spec["at"])
        else:
            index = int(spec.get("at_segment", 0))
            if index < 0 or index >= len(segment_starts):
                raise ValueError(f"at_segment 超出范围：{index}（共 {len(segment_starts)} 段）")
            start = segment_starts[index]
        resolved.append({"path": path, "start": start, "gain_db": float(spec.get("gain_db", 0))})
    return resolved


def build_episode(script_path, use_cache=True):
    voices = config.load_voices(VOICES_PATH)
    episode = config.load_episode(script_path, voices)

    AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)
    EPISODE_OUT_DIR.mkdir(parents=True, exist_ok=True)

    segment_paths = [synth.synthesize(s, CACHE_DIR, use_cache=use_cache) for s in episode.segments]
    durations = [audio.probe_duration(p) for p in segment_paths]
    starts = transcript.build_timeline(durations)

    voice_track = WORK_DIR / f"{episode.slug}-voice.mp3"
    audio.concat_mp3(segment_paths, voice_track, WORK_DIR)

    bed = resolve_bed(episode.bed, ASSETS_DIR)
    cues = resolve_cues(episode.cues, ASSETS_DIR, starts)

    out_audio = AUDIO_OUT_DIR / f"{episode.slug}.mp3"
    audio.mix_episode(voice_track, out_audio, WORK_DIR, bed, cues)

    meta = {
        "title": episode.title,
        "excerpt": episode.excerpt,
        "date": episode.date,
        "episode_type": episode.episode_type,
        "audio": f"/assets/audio/podcast/{episode.slug}.mp3",
        "hosts": episode.hosts,
        "guests": episode.guests,
        "related_post": episode.related_post,
        "publisher": episode.publisher,
    }
    md = transcript.render_episode_md(meta, episode.segments, durations)
    out_md = EPISODE_OUT_DIR / f"{str(episode.date)[:10]}-{episode.slug}.md"
    out_md.write_text(md, encoding="utf-8")

    total = audio.probe_duration(out_audio)
    print(f"✔ {episode.slug}")
    print(f"  音频：{out_audio}（{transcript.format_timestamp(total)}，{out_audio.stat().st_size / 1024:.0f} KB）")
    print(f"  逐字稿：{out_md}")
    return out_audio, out_md


def main(argv=None):
    parser = argparse.ArgumentParser(description="构建和国播客音频与逐字稿")
    parser.add_argument("slug", nargs="?", help="脚本 slug（scripts/<slug>.yml）")
    parser.add_argument("--all", action="store_true", help="构建全部脚本")
    parser.add_argument("--no-cache", action="store_true", help="忽略分段缓存")
    args = parser.parse_args(argv)
    use_cache = not args.no_cache

    if args.all:
        scripts = sorted(SCRIPTS_DIR.glob("*.yml"))
        if not scripts:
            raise SystemExit(f"scripts/ 下没有脚本：{SCRIPTS_DIR}")
        for script in scripts:
            build_episode(script, use_cache=use_cache)
    elif args.slug:
        build_episode(SCRIPTS_DIR / f"{args.slug}.yml", use_cache=use_cache)
    else:
        parser.error("请提供 slug 或 --all")


if __name__ == "__main__":
    main()
```

Create `tools/podcast/scripts/hege-news-ep1.yml`：

```yaml
slug: hege-news-ep1
title: "第 1 期｜和各新闻：全国动人代第18届一次会议表决结果公布"
date: 2026-10-05 09:00:00
episode_type: 播报
excerpt: "和各新闻第 1 期：全国动人代第18届一次会议七项议程全部通过，三部法律公布生效。"
publisher: "和各中央广播与电视平台"
related_post: "/公告/napc-18th-session-vote-results/"
hosts: ["云阳"]
guests: []

segments:
  - role: anchor
    text: "各位听众，大家好，这里是和各中央广播与电视平台，欢迎收听《和各新闻》。今天是和各共和国通用纪年十月五日。"
  - role: anchor
    text: "本期节目的头条消息：和各全国大小动物人民代表大会第十八届第一次会议，于九月十二日至十八日在首都艺宫举行。会议共设七项议程，全部获得通过。"
  - role: anchor
    text: "本次大会应到代表四十名，实到四十名，符合法定人数。七项议程中，四项报告获得批准，三部法律文件获得通过。"
  - role: anchor
    text: "三部法律分别是：制定《和各国诉讼法》，修订《和各国刑法》，以及修订《和各共和国政府组织法》。三部法律均经全体代表三分之二以上赞成通过。"
  - role: anchor
    text: "其中，《和各国诉讼法》填补了和各诉讼程序基本法的空白，确立了法院依法独立审判、无罪推定、公开审判、回避等原则，并设立智能化审判专章。"
  - role: anchor
    text: "《和各国刑法》修正案统一了条文编号，修订了追诉时效，并新增与诉讼法的衔接条款。《和各共和国政府组织法》修正案，新增了组成部门职责细则，以及地方政会向本级动人代报告并接受监督的规定。"
  - role: anchor
    text: "三部法律自公布之日起生效，并在和各共和国官方公报上发布。相关文件由和各全国动人代主席团签署公布。"
  - role: anchor
    text: "以上就是本期节目的主要内容。感谢收听《和各新闻》，我们下期再会。"

bed:
  - file: bgm/news-bed.mp3
    gain_db: -24
    duck: 0.85
    fade_in: 1.0
    fade_out: 2.0

cues:
  - at_segment: 7
    file: stinger/close.mp3
    gain_db: -10
```

Create `tools/podcast/README.md`：

```markdown
# 和国播客音频生产流水线

把结构化的 YAML 脚本合成为带背景音乐、音效、多音色的成品 MP3，并同时生成逐字稿与时间轴。
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

## 产物

- `assets/audio/podcast/<slug>.mp3`
- `_podcasts/YYYY-MM-DD-<slug>.md`（含逐字稿与时间轴）
```

Create `docs/播客制作规范.md`：

```markdown
# 和国播客 · 制作规范

> 适用范围：`tools/podcast/` 流水线与 `_podcasts/` 产出的播客节目。
> 事实标准：正典库 Hegewiki（见 `AGENTS.md`）；写作另有 `docs/写作与排版规范.md`。
> 技术规格：`docs/superpowers/specs/2026-10-05-podcast-audio-pipeline-design.md`。

## 一、节目形态

| episode_type | 形态 | 人声 |
| --- | --- | --- |
| 播报 | 政府新闻播报 | `anchor`（男·新闻），可加 `coanchor`（女·新闻） |
| 访谈 | 主持人与嘉宾对话 | `host`（女） + `guest`/`guest2` |

## 二、音色表（`tools/podcast/voices.yml`）

| role | 音色 | 显示名 | 用途 |
| --- | --- | --- | --- |
| `anchor` | zh-CN-YunyangNeural | 主播 | 男·新闻播报 |
| `coanchor` | zh-CN-XiaoxiaoNeural | 主播 | 女·新闻播报 |
| `host` | zh-CN-XiaoxiaoNeural | 主持人 | 访谈主持 |
| `guest` | zh-CN-YunjianNeural | 嘉宾 | 男嘉宾 |
| `guest2` | zh-CN-XiaoyiNeural | 嘉宾 | 女嘉宾 |

段落可用 `voice` / `rate` 覆盖默认。

## 三、脚本写法

唯一事实源为 `tools/podcast/scripts/<slug>.yml`。字段：`slug / title / date / episode_type / excerpt / publisher / related_post / hosts / guests / segments / bed / cues`。

`segments[].text` 是**口播文本**，须可直接朗读：

- 数字写成中文读法（`40` → `四十名`）。
- 专名按读音写，必要时用同音字保证读音正确。
- 不出现 Markdown 语法、链接、模板符号。

## 四、音效与背景音乐

```yaml
bed:
  - file: bgm/news-bed.mp3     # 相对 tools/podcast/assets/
    gain_db: -24               # 铺底音量
    duck: 0.85                 # 闪避强度 0–1（人声处自动压低）
    fade_in: 1.0
    fade_out: 2.0
cues:
  - at_segment: 7              # 或 at: "00:45.000"
    file: stinger/close.mp3
    gain_db: -10
```

- 素材默认由 `python tools/podcast/gen_assets.py` 程序化生成（自产、零版权）。
- 引入外部素材必须是 CC0 / 公共领域 / 自制，并在 `tools/podcast/assets/CREDITS.md` 登记来源、作者、协议、日期。
- 禁止提交来源不明的音乐。

## 五、命名与发布

- `slug` 用英文小写 `-` 连接；文件名即 URL 片段。
- 产物：`assets/audio/podcast/<slug>.mp3` 与 `_podcasts/YYYY-MM-DD-<slug>.md`，均提交入库。
- 生成 md 的 front matter 已按网站播客集合设计，接入栏目后即可显示。
- 素材源与 `.cache/` 不入库（见 `.gitignore`）。

## 六、流程

1. 写 `scripts/<slug>.yml`（口播稿）。
2. 需要时 `python tools/podcast/gen_assets.py` 生成素材。
3. `python tools/podcast/build.py <slug>` 产出 MP3 与逐字稿。
4. 试听：人声清晰、BGM 在人声处闪避、音效落点正确。
5. 提交产物。
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s tools/podcast/tests -t tools/podcast -v`
Expected: PASS（全部用例）。

- [ ] **Step 5: 构建样片并验证**

Run:
```bash
python tools/podcast/gen_assets.py
python tools/podcast/build.py hege-news-ep1
```
Expected:
- `assets/audio/podcast/hege-news-ep1.mp3` 生成，时长 > 0。
- `_podcasts/2026-10-05-hege-news-ep1.md` 生成，含 `duration`、递增时间轴、8 段逐字稿。
- 再次运行同一命令应复用缓存（合成阶段不再联网），输出覆盖、不报错。

人工试听：人声清晰，背景音乐存在且在人声处闪避，结尾台标落在第 8 段起点。

- [ ] **Step 6: 提交**

```bash
git add tools/podcast/build.py tools/podcast/tests/test_build.py tools/podcast/scripts tools/podcast/README.md docs/播客制作规范.md
git add assets/audio/podcast _podcasts
git commit -m "feat: 播客端到端构建、播报样片与制作规范"
```

---

## 自检

**1. 规格覆盖**

| 规格条目 | 对应任务 |
| --- | --- |
| 技术选型 edge-tts / imageio-ffmpeg | Task 2、3 |
| 目录与产物 | Task 1、6、7 |
| 脚本源格式 | Task 1、7 |
| 音色表 | Task 1 |
| 音效与 BGM 来源与版权 | Task 6、7（CREDITS、规范） |
| 混音实现（循环、闪避、定点、loudnorm） | Task 4 |
| build.py 流程与 CLI | Task 7 |
| 逐字稿输出格式与时间轴 | Task 5、7 |
| 命名/体积/入库规则 | Task 1（.gitignore）、Task 7 |
| 验证方式 | 各任务 Step 4 + Task 7 Step 5 |
| 播客制作规范文档 | Task 7 |

**2. 占位符扫描**：无 TBD/TODO；所有代码步骤含完整代码；无“类似上文”。

**3. 类型一致性**：`Segment` 字段（role/text/voice/name/rate/volume/pitch）在 config/synth/transcript 一致；`mix_episode` 的 `bed_specs`/`cues_specs` 键名与 `resolve_bed`/`resolve_cues` 产出键名一致（`path/gain_db/duck/fade_in/fade_out` 与 `path/start/gain_db`）；`build_timeline` 输出用作 `resolve_cues` 的 `segment_starts`。

**4. Review Focus 覆盖**：①空文本→Task 1；②`at_segment` 越界/非法时间码→Task 5、7；③未知角色/缺字段→Task 1；④素材缺失→Task 7；⑤重复构建幂等→Task 2、Task 7 Step 5。
