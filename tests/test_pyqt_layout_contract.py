import unittest
from pathlib import Path


class PyQtLayoutContractTests(unittest.TestCase):
    def test_glass_panel_keeps_empty_layouts(self):
        source = (Path(__file__).resolve().parents[1] / "timer_pyqt.py").read_text(encoding="utf-8")

        self.assertIn("if layout is not None:", source)
        self.assertNotIn("if layout:\n            self.setLayout(layout)", source)

    def test_glass_panel_uses_liquid_glass_painter(self):
        source = (Path(__file__).resolve().parents[1] / "timer_pyqt.py").read_text(encoding="utf-8")
        glass_panel_source = source[source.index("class GlassPanel(QFrame):") : source.index("class BeepTimerPanel")]

        self.assertIn("class GlassPanel(QFrame):", source)
        self.assertIn("def paintEvent(self, event):", source)
        self.assertIn("QLinearGradient", source)
        self.assertIn("QRadialGradient", source)
        self.assertIn("top_edge", source)
        self.assertNotIn("drawLine(", glass_panel_source)
        self.assertIn("top_glare.setColorAt(0.00, QColor(255, 255, 255, 0))", glass_panel_source)
        self.assertNotIn("QRectF(rect.left() + rect.width() * 0.05, rect.top() + 1.2, rect.width() * 0.48, 3.2)", glass_panel_source)
        self.assertNotIn("rect.height() * 0.42", glass_panel_source)
        self.assertIn("top_glare_path.addRoundedRect(rect, radius, radius)", glass_panel_source)
        self.assertIn("top_glare.setColorAt(0.18, QColor(255, 255, 255, 92))", glass_panel_source)
        self.assertIn("top_glare.setColorAt(0.68, QColor(126, 239, 229, 16))", glass_panel_source)
        self.assertIn("top_glare.setColorAt(1.00, QColor(255, 255, 255, 0))", glass_panel_source)
        self.assertIn("surface_sheen.setColorAt(0.18, QColor(255, 255, 255, 48))", glass_panel_source)
        self.assertIn("surface_sheen.setColorAt(0.42, QColor(255, 255, 255, 12))", glass_panel_source)
        self.assertIn("side_glare.setColorAt(0.00, QColor(255, 255, 255, 0))", glass_panel_source)
        self.assertNotIn("2.2,", glass_panel_source)
        self.assertNotIn("side_glare_width", glass_panel_source)
        self.assertIn("side_glare_path.addRoundedRect(rect, radius, radius)", glass_panel_source)
        self.assertIn("side_glare.setColorAt(0.86, QColor(126, 239, 229, 48))", glass_panel_source)
        self.assertIn("side_glare.setColorAt(1.00, QColor(255, 255, 255, 0))", glass_panel_source)

    def test_window_shell_has_small_resize_floor(self):
        source = (Path(__file__).resolve().parents[1] / "timer_pyqt.py").read_text(encoding="utf-8")

        self.assertIn("self.setMinimumSize(360, 260)", source)
        self.assertNotIn("self.setMinimumSize(620, 440)", source)


if __name__ == "__main__":
    unittest.main()
