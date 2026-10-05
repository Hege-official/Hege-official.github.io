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
        Path(out_path).with_suffix(".srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\n测试字幕\n", encoding="utf-8"
        )

    def test_creates_audio_and_subtitles(self):
        seg = make_segment()
        path = synth.synthesize(seg, self.dir, synth_fn=self._fake_synth)
        self.assertTrue(path.exists())
        self.assertTrue(synth.subtitles_for(path).exists())
        self.assertEqual(len(self.calls), 1)

    def test_second_call_hits_cache(self):
        seg = make_segment()
        synth.synthesize(seg, self.dir, synth_fn=self._fake_synth)

        def boom(seg, out_path):
            raise AssertionError("不应再次合成")

        path = synth.synthesize(seg, self.dir, synth_fn=boom)
        self.assertTrue(path.exists())

    def test_missing_subtitles_triggers_resynth(self):
        seg = make_segment()
        path = synth.synthesize(seg, self.dir, synth_fn=self._fake_synth)
        synth.subtitles_for(path).unlink()
        synth.synthesize(seg, self.dir, synth_fn=self._fake_synth)
        self.assertEqual(len(self.calls), 2)

    def test_no_cache_forces_resynth(self):
        seg = make_segment()
        synth.synthesize(seg, self.dir, synth_fn=self._fake_synth)
        synth.synthesize(seg, self.dir, synth_fn=self._fake_synth, use_cache=False)
        self.assertEqual(len(self.calls), 2)

    def test_whitespace_subtitles_raise(self):
        def ws_synth(seg, out_path):
            Path(out_path).write_bytes(b"audio")
            Path(out_path).with_suffix(".srt").write_text("   \n\n", encoding="utf-8")

        with self.assertRaises(RuntimeError):
            synth.synthesize(make_segment(), self.dir, synth_fn=ws_synth)

    def test_structurally_invalid_subtitles_raise(self):
        def bad_synth(seg, out_path):
            Path(out_path).write_bytes(b"audio")
            Path(out_path).with_suffix(".srt").write_text("not a subtitle", encoding="utf-8")

        with self.assertRaises(RuntimeError):
            synth.synthesize(make_segment(), self.dir, synth_fn=bad_synth)

    def test_whitespace_subtitles_trigger_resynth(self):
        seg = make_segment()
        path = synth.synthesize(seg, self.dir, synth_fn=self._fake_synth)
        synth.subtitles_for(path).write_text("  \n", encoding="utf-8")
        synth.synthesize(seg, self.dir, synth_fn=self._fake_synth)
        self.assertEqual(len(self.calls), 2)

    def test_empty_output_raises(self):
        def empty_synth(seg, out_path):
            Path(out_path).write_bytes(b"")
            Path(out_path).with_suffix(".srt").write_text(
                "1\n00:00:00,000 --> 00:00:01,000\nx\n", encoding="utf-8"
            )

        with self.assertRaises(RuntimeError):
            synth.synthesize(make_segment(), self.dir, synth_fn=empty_synth)

    def test_empty_subtitles_raise(self):
        def no_sub_synth(seg, out_path):
            Path(out_path).write_bytes(b"audio")
            Path(out_path).with_suffix(".srt").write_text("", encoding="utf-8")

        with self.assertRaises(RuntimeError):
            synth.synthesize(make_segment(), self.dir, synth_fn=no_sub_synth)


if __name__ == "__main__":
    unittest.main()
