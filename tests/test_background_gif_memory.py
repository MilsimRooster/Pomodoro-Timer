import unittest
from pathlib import Path


class BackgroundGifMemoryTests(unittest.TestCase):
    def test_custom_gif_background_streams_frames(self):
        source = (Path(__file__).resolve().parents[1] / "beep_timer_gui.pyw").read_text(encoding="utf-8")

        self.assertIn("custom_background_gif", source)
        self.assertIn("custom_background_gif.seek", source)
        self.assertNotIn("custom_background_frames.append", source)


if __name__ == "__main__":
    unittest.main()
