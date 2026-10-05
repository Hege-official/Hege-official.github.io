"""程序化生成播客音效与铺底音乐（自产，零版权风险）。"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from podcast_lib import audio

ROOT = Path(__file__).resolve().parent
DEFAULT_DIR = ROOT / "assets"


def _safe_stdout():
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass


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
    _safe_stdout()
    parser = argparse.ArgumentParser(description="生成播客音效与铺底音乐")
    parser.add_argument("--dir", default=str(DEFAULT_DIR), help="输出目录（默认 tools/podcast/assets）")
    args = parser.parse_args(argv)
    for path in generate(args.dir):
        print(f"✔ {path}（{audio.probe_duration(path):.2f}s）")


if __name__ == "__main__":
    main()
