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
