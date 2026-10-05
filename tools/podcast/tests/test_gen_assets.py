import importlib.util
import tempfile
import unittest
from pathlib import Path

from podcast_lib import audio

SPEC = importlib.util.spec_from_file_location(
    "gen_assets", Path(__file__).resolve().parents[1] / "gen_assets.py"
)
gen_assets = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen_assets)


class GenAssetsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_generates_all_assets_with_audio(self):
        created = gen_assets.generate(self.dir)
        expected = {
            "stinger/open.mp3", "stinger/close.mp3",
            "sfx/transition.mp3", "bgm/news-bed.mp3",
        }
        names = {p.relative_to(self.dir).as_posix() for p in created}
        self.assertEqual(names, expected)
        for path in created:
            self.assertGreater(audio.probe_duration(path), 0.0)


if __name__ == "__main__":
    unittest.main()
