"""逐段调用 edge-tts 合成音频与字幕，并按参数 hash 缓存。"""
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


def subtitles_for(media_path):
    return Path(media_path).with_suffix(".srt")


def _has_cues(path) -> bool:
    try:
        return "-->" in Path(path).read_text(encoding="utf-8")
    except OSError:
        return False


async def _edge_synth(text, voice, rate, volume, pitch, media_path, srt_path):
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
    submaker = edge_tts.SubMaker()
    with open(media_path, "wb") as media:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                media.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)
    Path(srt_path).write_text(submaker.get_srt(), encoding="utf-8")


def default_synth(seg, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(
        _edge_synth(seg.text, seg.voice, seg.rate, seg.volume, seg.pitch, out_path, subtitles_for(out_path))
    )


def synthesize(seg, cache_dir, synth_fn=None, use_cache=True):
    synth_fn = synth_fn or default_synth
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / f"{cache_key(seg)}.mp3"
    target_srt = subtitles_for(target)
    if (
        use_cache
        and target.exists() and target.stat().st_size > 0
        and _has_cues(target_srt)
    ):
        return target
    tmp = target.with_suffix(".part.mp3")
    tmp_srt = subtitles_for(tmp)
    for stale in (tmp, tmp_srt):
        if stale.exists():
            stale.unlink()
    synth_fn(seg, tmp)
    if not tmp.exists() or tmp.stat().st_size == 0:
        raise RuntimeError(f"合成未产生有效音频：{seg.text[:20]}…")
    if not _has_cues(tmp_srt):
        raise RuntimeError(f"合成未产生有效字幕：{seg.text[:20]}…")
    tmp.replace(target)
    tmp_srt.replace(target_srt)
    return target
