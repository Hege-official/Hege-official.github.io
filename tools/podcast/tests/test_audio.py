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


if __name__ == "__main__":
    unittest.main()
