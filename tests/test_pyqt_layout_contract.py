import unittest
from pathlib import Path


class PyQtLayoutContractTests(unittest.TestCase):
    def test_glass_panel_keeps_empty_layouts(self):
        source = (Path(__file__).resolve().parents[1] / "timer_pyqt.py").read_text(encoding="utf-8")

        self.assertIn("if layout is not None:", source)
        self.assertNotIn("if layout:\n            self.setLayout(layout)", source)

    def test_glass_panel_uses_liquid_glass_painter(self):
        source = (Path(__file__).resolve().parents[1] / "timer_pyqt.py").read_text(encoding="utf-8")

        self.assertIn("class GlassPanel(QFrame):", source)
        self.assertIn("def paintEvent(self, event):", source)
        self.assertIn("QLinearGradient", source)
        self.assertIn("QRadialGradient", source)
        self.assertIn("top_edge", source)
        self.assertIn("right_edge", source)
        self.assertIn("glint_width", source)

    def test_window_shell_has_small_resize_floor(self):
        source = (Path(__file__).resolve().parents[1] / "timer_pyqt.py").read_text(encoding="utf-8")

        self.assertIn("self.setMinimumSize(360, 260)", source)
        self.assertNotIn("self.setMinimumSize(620, 440)", source)


if __name__ == "__main__":
    unittest.main()
