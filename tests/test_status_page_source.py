import unittest
from pathlib import Path


class StatusPageSourceTests(unittest.TestCase):
    def test_weather_and_metals_share_status_page_with_separate_cards(self):
        source = (Path(__file__).resolve().parents[1] / "timer_pyqt.py").read_text(encoding="utf-8")

        self.assertIn("class StatusPage", source)
        self.assertIn('self.pages_btn.addItems(["Timer", "News", "Status"])', source)
        self.assertIn("self.weather_card = GlassPanel", source)
        self.assertIn("self.silver_card = GlassPanel", source)
        self.assertIn("self.gold_card = GlassPanel", source)
        self.assertIn("Qt.Key.Key_W: 2", source)
        self.assertIn("Qt.Key.Key_I: 2", source)


if __name__ == "__main__":
    unittest.main()
