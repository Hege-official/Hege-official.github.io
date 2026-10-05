import subprocess
import tempfile
import unittest
from pathlib import Path

from podcast_lib import audio


def make_tone(path, freq, duration):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            audio.ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={duration}",
            "-ar", "24000", "-ac", "1", str(path),
        ],
        check=True,
    )


class ProbeDurationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_reads_expected_duration(self):
        tone = self.dir / "tone.mp3"
        make_tone(tone, 440, 2.0)
        self.assertAlmostEqual(audio.probe_duration(tone), 2.0, delta=0.15)

    def test_missing_file_raises(self):
        with self.assertRaises(RuntimeError):
            audio.probe_duration(self.dir / "nope.mp3")

    def test_non_ascii_path(self):
        tone = self.dir / "新闻片头.mp3"
        make_tone(tone, 440, 0.5)
        self.assertAlmostEqual(audio.probe_duration(tone), 0.5, delta=0.15)


class ConcatTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_length_is_sum_of_parts(self):
        a = self.dir / "a.mp3"
        b = self.dir / "b.mp3"
        make_tone(a, 440, 1.0)
        make_tone(b, 550, 0.5)
        out = self.dir / "out.mp3"
        audio.concat_mp3([a, b], out, self.dir)
        self.assertAlmostEqual(audio.probe_duration(out), 1.5, delta=0.2)

    def test_empty_list_raises(self):
        with self.assertRaises(ValueError):
            audio.concat_mp3([], self.dir / "out.mp3", self.dir)


class MixEpisodeTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _tone(self, name, duration, freq=440):
        path = self.dir / name
        make_tone(path, freq, duration)
        return path

    def test_voice_only_keeps_duration(self):
        voice = self._tone("voice.mp3", 2.0)
        out = self.dir / "out.mp3"
        audio.mix_episode(voice, out, self.dir, [], [])
        self.assertTrue(out.exists())
        self.assertAlmostEqual(audio.probe_duration(out), 2.0, delta=0.3)

    def test_bed_shorter_than_voice_does_not_truncate(self):
        voice = self._tone("voice.mp3", 3.0)
        bed = self._tone("bed.mp3", 0.5, freq=110)
        out = self.dir / "out.mp3"
        audio.mix_episode(
            voice, out, self.dir,
            [{"path": bed, "gain_db": -24, "duck": 0.85, "fade_in": 0.2, "fade_out": 0.2}],
            [],
        )
        self.assertAlmostEqual(audio.probe_duration(out), 3.0, delta=0.3)

    def test_cue_does_not_extend_duration(self):
        voice = self._tone("voice.mp3", 2.0)
        cue = self._tone("cue.mp3", 0.3, freq=880)
        out = self.dir / "out.mp3"
        audio.mix_episode(
            voice, out, self.dir, [],
            [{"path": cue, "start": 1.0, "gain_db": -10}],
        )
        self.assertAlmostEqual(audio.probe_duration(out), 2.0, delta=0.3)


class AssembleWithIntroTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _tone(self, name, duration, freq=440):
        path = self.dir / name
        make_tone(path, freq, duration)
        return path

    def test_duration_is_intro_plus_program(self):
        intro = self._tone("intro.mp3", 1.0, freq=660)
        program = self._tone("program.mp3", 2.0, freq=440)
        out = self.dir / "out.mp3"
        audio.assemble_with_intro(program, out, intro, gain_db=0, fade_out=0.3)
        self.assertTrue(out.exists())
        self.assertAlmostEqual(audio.probe_duration(out), 3.0, delta=0.3)


if __name__ == "__main__":
    unittest.main()
