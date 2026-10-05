import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "build", Path(__file__).resolve().parents[1] / "build.py"
)
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)

from podcast_lib import config  # noqa: E402


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

    def test_missing_file_key_raises(self):
        with self.assertRaises(ValueError):
            build.resolve_bed([{"gain_db": -20}], self.dir)

    def test_non_mapping_entry_raises(self):
        with self.assertRaises(ValueError):
            build.resolve_bed(["bgm/bed.mp3"], self.dir)


class ResolveIntroTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        (self.dir / "stinger").mkdir()
        (self.dir / "stinger" / "intro.mp3").write_bytes(b"x")

    def tearDown(self):
        self._tmp.cleanup()

    def test_none_when_absent(self):
        self.assertIsNone(build.resolve_intro(None, self.dir))

    def test_resolves_defaults(self):
        spec = build.resolve_intro({"file": "stinger/intro.mp3"}, self.dir)
        self.assertEqual(spec["gain_db"], 0.0)
        self.assertEqual(spec["fade_out"], 0.0)
        self.assertTrue(spec["path"].exists())

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            build.resolve_intro({"file": "stinger/nope.mp3"}, self.dir)

    def test_missing_file_key_raises(self):
        with self.assertRaises(ValueError):
            build.resolve_intro({"gain_db": -3}, self.dir)


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

    def test_missing_locator_raises(self):
        with self.assertRaises(ValueError):
            build.resolve_cues([{"file": "sfx/c.mp3"}], self.dir, self.starts)

    def test_both_locators_raise(self):
        with self.assertRaises(ValueError):
            build.resolve_cues(
                [{"file": "sfx/c.mp3", "at": "0", "at_segment": 1}], self.dir, self.starts
            )

    def test_negative_timecode_raises(self):
        with self.assertRaises(ValueError):
            build.resolve_cues([{"file": "sfx/c.mp3", "at": "-5"}], self.dir, self.starts)

    def test_non_integer_at_segment_raises(self):
        with self.assertRaises(ValueError):
            build.resolve_cues(
                [{"file": "sfx/c.mp3", "at_segment": "abc"}], self.dir, self.starts
            )

    def test_missing_file_key_raises(self):
        with self.assertRaises(ValueError):
            build.resolve_cues([{"at": "0"}], self.dir, self.starts)


class BuildMetaTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.audio = self.dir / "ep.mp3"
        self.audio.write_bytes(b"0123456789")

    def tearDown(self):
        self._tmp.cleanup()

    def _episode(self, **overrides):
        values = dict(
            slug="demo", title="标题", date="2026-10-05 09:00:00",
            episode_type="播报", excerpt="简介", publisher="和各政府网",
            related_post="/公告/x/", hosts=["云阳"], guests=[],
            segments=[], bed=[], cues=[], intro=None, episode=None,
        )
        values.update(overrides)
        return config.Episode(**values)

    def test_includes_podcast_fields(self):
        meta = build.build_meta(self._episode(), self.audio)
        self.assertEqual(meta["permalink"], "/podcast/demo/")
        self.assertEqual(meta["audio_bytes"], 10)
        self.assertEqual(meta["header"]["og_image"], "/assets/images/podcast-cover.png")
        self.assertNotIn("episode", meta)

    def test_episode_number_included_when_set(self):
        meta = build.build_meta(self._episode(episode=1), self.audio)
        self.assertEqual(meta["episode"], 1)


if __name__ == "__main__":
    unittest.main()
