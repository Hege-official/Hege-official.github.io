import tempfile
import unittest
from pathlib import Path

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


SRT_SAMPLE = (
    "1\n00:00:00,100 --> 00:00:02,062\n各位听众，大家好。\n\n"
    "2\n00:00:02,012 --> 00:00:04,100\n这里是和各新闻。\n"
)


class SubtitleTest(unittest.TestCase):
    def test_parse_srt(self):
        cues = transcript.parse_srt(SRT_SAMPLE)
        self.assertEqual(len(cues), 2)
        self.assertAlmostEqual(cues[0]["start"], 0.1, places=3)
        self.assertAlmostEqual(cues[0]["end"], 2.062, places=3)
        self.assertEqual(cues[1]["text"], "这里是和各新闻。")

    def test_format_vtt_timestamp(self):
        self.assertEqual(transcript.format_vtt_timestamp(0.1), "00:00:00.100")
        self.assertEqual(transcript.format_vtt_timestamp(3723.5), "01:02:03.500")

    def test_cues_to_vtt(self):
        vtt = transcript.cues_to_vtt(transcript.parse_srt(SRT_SAMPLE))
        self.assertTrue(vtt.startswith("WEBVTT"))
        self.assertIn("00:00:00.100 --> 00:00:02.062", vtt)
        self.assertIn("这里是和各新闻。", vtt)

    def test_merge_subtitles_shifts(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.srt"
            b = Path(tmp) / "b.srt"
            a.write_text(SRT_SAMPLE, encoding="utf-8")
            b.write_text(SRT_SAMPLE, encoding="utf-8")
            vtt = transcript.merge_subtitles([a, b], [0.0, 10.0])
        self.assertIn("00:00:10.100 --> 00:00:12.062", vtt)


if __name__ == "__main__":
    unittest.main()
