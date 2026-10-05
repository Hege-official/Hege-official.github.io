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
