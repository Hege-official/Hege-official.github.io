"""时间轴计算、字幕合并与逐字稿 Markdown 渲染。"""
from __future__ import annotations

import re
from pathlib import Path

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


_SRT_TIME_RE = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)")


def _srt_seconds(parts):
    hours, minutes, seconds, millis = parts
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis.ljust(3, "0")[:3]) / 1000


def parse_srt(text):
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [line for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        time_index = 1 if _SRT_TIME_RE.search(lines[1]) else 0
        if time_index == 0 and not _SRT_TIME_RE.search(lines[0]):
            continue
        matches = _SRT_TIME_RE.findall(lines[time_index])
        if len(matches) < 2:
            continue
        cues.append({
            "start": _srt_seconds(matches[0]),
            "end": _srt_seconds(matches[1]),
            "text": " ".join(lines[time_index + 1:]).strip(),
        })
    return cues


def format_vtt_timestamp(seconds) -> str:
    total_ms = int(round(float(seconds) * 1000))
    hours, rem = divmod(total_ms, 3600000)
    minutes, rem = divmod(rem, 60000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def cues_to_vtt(cues) -> str:
    lines = ["WEBVTT", ""]
    for number, cue in enumerate(cues, start=1):
        lines.append(str(number))
        lines.append(f"{format_vtt_timestamp(cue['start'])} --> {format_vtt_timestamp(cue['end'])}")
        lines.append(cue["text"])
        lines.append("")
    return "\n".join(lines)


def merge_subtitles(srt_paths, offsets) -> str:
    cues = []
    for path, offset in zip(srt_paths, offsets):
        for cue in parse_srt(Path(path).read_text(encoding="utf-8")):
            cues.append({
                "start": cue["start"] + float(offset),
                "end": cue["end"] + float(offset),
                "text": cue["text"],
            })
    return cues_to_vtt(cues)


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
