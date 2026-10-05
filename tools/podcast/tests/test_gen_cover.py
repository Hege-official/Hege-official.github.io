import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image

SPEC = importlib.util.spec_from_file_location(
    "gen_cover", Path(__file__).resolve().parents[1] / "gen_cover.py"
)
gen_cover = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen_cover)


class BuildCoverTest(unittest.TestCase):
    def test_square_rgb_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "cover.png"
            gen_cover.build_cover(out, size=1400)
            self.assertTrue(out.exists())
            with Image.open(out) as im:
                self.assertEqual(im.size, (1400, 1400))
                self.assertEqual(im.mode, "RGB")
