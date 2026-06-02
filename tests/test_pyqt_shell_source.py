import unittest
from pathlib import Path


class PyQtShellSourceTests(unittest.TestCase):
    def test_pyqt_shell_has_background_and_pages(self):
        source = (Path(__file__).resolve().parents[1] / "timer_pyqt.py").read_text(encoding="utf-8")

        self.assertIn("class BackgroundWidget", source)
        self.assertIn("QMovie", source)
        self.assertIn("class TimerWindow", source)
        self.assertIn("Choose Image/GIF", source)


if __name__ == "__main__":
    unittest.main()
