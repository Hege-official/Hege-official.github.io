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
    intro: dict | None
    episode: int | None


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
    intro = data.get("intro")
    if intro is not None and not isinstance(intro, dict):
        raise ConfigError(f"{path} 的 intro 必须是映射")
    episode = data.get("episode")
    if episode is not None:
        if isinstance(episode, bool) or not isinstance(episode, int):
            raise ConfigError(f"{path} 的 episode 必须是整数")
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
        intro=intro,
        episode=episode,
    )
