"""构建单集播客：合成 → 拼接 → 混音 → 输出 MP3、VTT 与逐字稿。"""
from __future__ import annotations

import argparse
import sys
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


def _safe_stdout():
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass


def resolve_bed(specs, assets_dir):
    resolved = []
    for spec in specs:
        if not isinstance(spec, dict) or "file" not in spec:
            raise ValueError(f"bed 条目必须是含 file 键的映射：{spec!r}")
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


def resolve_intro(spec, assets_dir):
    if not spec:
        return None
    if not isinstance(spec, dict) or "file" not in spec:
        raise ValueError(f"intro 必须是含 file 键的映射：{spec!r}")
    path = Path(assets_dir) / spec["file"]
    if not path.exists():
        raise FileNotFoundError(f"片头不存在：{path}")
    return {
        "path": path,
        "gain_db": float(spec.get("gain_db", 0)),
        "fade_out": float(spec.get("fade_out", 0)),
    }


def resolve_cues(specs, assets_dir, segment_starts):
    resolved = []
    for spec in specs:
        if not isinstance(spec, dict) or "file" not in spec:
            raise ValueError(f"cue 条目必须是含 file 键的映射：{spec!r}")
        path = Path(assets_dir) / spec["file"]
        if not path.exists():
            raise FileNotFoundError(f"音效不存在：{path}")
        has_at = "at" in spec
        has_segment = "at_segment" in spec
        if has_at == has_segment:
            raise ValueError(f"cue 必须且只能指定 at 或 at_segment：{spec!r}")
        if has_at:
            start = transcript.parse_timecode(spec["at"])
            if start < 0:
                raise ValueError(f"cue 时间码不能为负：{spec['at']!r}")
        else:
            raw_index = spec["at_segment"]
            if not isinstance(raw_index, int) or isinstance(raw_index, bool):
                raise ValueError(f"at_segment 必须是整数：{raw_index!r}")
            if raw_index < 0 or raw_index >= len(segment_starts):
                raise ValueError(f"at_segment 超出范围：{raw_index}（共 {len(segment_starts)} 段）")
            start = segment_starts[raw_index]
        resolved.append({"path": path, "start": start, "gain_db": float(spec.get("gain_db", 0))})
    return resolved


def build_episode(script_path, use_cache=True):
    voices = config.load_voices(VOICES_PATH)
    episode = config.load_episode(script_path, voices)

    AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)
    EPISODE_OUT_DIR.mkdir(parents=True, exist_ok=True)

    segment_paths = [synth.synthesize(s, CACHE_DIR, use_cache=use_cache) for s in episode.segments]
    durations = [audio.probe_duration(p) for p in segment_paths]
    base_starts = transcript.build_timeline(durations)

    voice_track = WORK_DIR / f"{episode.slug}-voice.mp3"
    audio.concat_mp3(segment_paths, voice_track, WORK_DIR)

    bed = resolve_bed(episode.bed, ASSETS_DIR)
    cues = resolve_cues(episode.cues, ASSETS_DIR, base_starts)
    intro = resolve_intro(episode.intro, ASSETS_DIR)

    out_audio = AUDIO_OUT_DIR / f"{episode.slug}.mp3"
    if intro:
        program = WORK_DIR / f"{episode.slug}-program.mp3"
        audio.mix_episode(voice_track, program, WORK_DIR, bed, cues)
        audio.assemble_with_intro(
            program, out_audio, intro["path"],
            gain_db=intro["gain_db"], fade_out=intro["fade_out"],
        )
        intro_duration = audio.probe_duration(intro["path"])
    else:
        audio.mix_episode(voice_track, out_audio, WORK_DIR, bed, cues)
        intro_duration = 0.0

    starts = [intro_duration + s for s in base_starts]

    srt_paths = [synth.subtitles_for(p) for p in segment_paths]
    out_vtt = AUDIO_OUT_DIR / f"{episode.slug}.vtt"
    out_vtt.write_text(
        transcript.merge_subtitles(
            srt_paths, starts, source_texts=[s.text for s in episode.segments]
        ),
        encoding="utf-8",
    )

    meta = {
        "title": episode.title,
        "excerpt": episode.excerpt,
        "date": episode.date,
        "episode_type": episode.episode_type,
        "audio": f"/assets/audio/podcast/{episode.slug}.mp3",
        "subtitles": f"/assets/audio/podcast/{episode.slug}.vtt",
        "hosts": episode.hosts,
        "guests": episode.guests,
        "related_post": episode.related_post,
        "publisher": episode.publisher,
    }
    md = transcript.render_episode_md(
        meta, episode.segments, durations, start_offset=intro_duration
    )
    out_md = EPISODE_OUT_DIR / f"{str(episode.date)[:10]}-{episode.slug}.md"
    out_md.write_text(md, encoding="utf-8")

    total = audio.probe_duration(out_audio)
    print(f"✔ {episode.slug}")
    print(f"  音频：{out_audio}（{transcript.format_timestamp(total)}，{out_audio.stat().st_size / 1024:.0f} KB）")
    print(f"  字幕：{out_vtt}")
    print(f"  逐字稿：{out_md}")
    return out_audio, out_vtt, out_md


def main(argv=None):
    _safe_stdout()
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
