import glob
import html
import json
import os
import random
import re
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path

import pygame
import requests
from PyQt6.QtCore import QRectF, Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QIcon,
    QLinearGradient,
    QMovie,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QSystemTrayIcon,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
SETTINGS_DIR = Path(os.getenv("APPDATA", str(APP_DIR))).joinpath("Timer")
SETTINGS_FILE = SETTINGS_DIR.joinpath("settings.json")
DEGREE_F = chr(176) + "F"


def app_path(*parts):
    return APP_DIR.joinpath(*parts)


def resource_path(*parts):
    local = APP_DIR.joinpath(*parts)
    return local if local.exists() else RESOURCE_DIR.joinpath(*parts)


def load_settings():
    try:
        if SETTINGS_FILE.exists():
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def save_settings(settings):
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def discover(folder, exts):
    base = app_path(folder)
    base.mkdir(exist_ok=True)
    files = []
    for ext in exts:
        files.extend(glob.glob(str(base / ext)))
        files.extend(glob.glob(str(base / ext.upper())))
    return sorted(set(files), key=lambda p: Path(p).stem.lower())


def fmt_seconds(sec):
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s" if m else f"{s}s"


def plain_text(value, limit=None):
    text = re.sub(r"<[^>]+>", " ", html.unescape(str(value or "")))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] if limit else text


class BackgroundWidget(QWidget):
    def __init__(self, image_path=""):
        super().__init__()
        self.pixmap = QPixmap()
        self.movie = None
        self.scaled = QPixmap()
        self.scaled_size = None
        self.set_background(image_path)

    def set_background(self, image_path):
        self.scaled = QPixmap()
        self.scaled_size = None
        if self.movie:
            self.movie.stop()
            try:
                self.movie.frameChanged.disconnect(self.update)
            except Exception:
                pass
            self.movie = None
        self.pixmap = QPixmap()
        if image_path and Path(image_path).exists():
            if image_path.lower().endswith(".gif"):
                self.movie = QMovie(image_path)
                if self.movie.isValid():
                    self.movie.frameChanged.connect(self.update)
                    self.movie.start()
                else:
                    self.movie = None
                    self.pixmap = QPixmap(image_path)
            else:
                self.pixmap = QPixmap(image_path)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        frame = self.movie.currentPixmap() if self.movie else self.pixmap
        if not frame.isNull():
            if self.movie or self.scaled_size != self.size():
                self.scaled = frame.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                self.scaled_size = self.size()
            x = (self.width() - self.scaled.width()) // 2
            y = (self.height() - self.scaled.height()) // 2
            painter.drawPixmap(x, y, self.scaled)
        else:
            painter.fillRect(self.rect(), QColor("#071018"))
        painter.fillRect(self.rect(), QColor(3, 7, 12, 150))


class WorkerSignals(QObject):
    done = pyqtSignal(object)


class GlassPanel(QFrame):
    def __init__(self, layout=None):
        super().__init__()
        self.setObjectName("glassPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        if layout is not None:
            self.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(1.0, 1.0, -1.0, -1.0)
        radius = 8.0
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        body = QLinearGradient(rect.topLeft(), rect.bottomRight())
        body.setColorAt(0.00, QColor(236, 250, 255, 50))
        body.setColorAt(0.18, QColor(79, 143, 184, 44))
        body.setColorAt(0.55, QColor(6, 16, 28, 92))
        body.setColorAt(1.00, QColor(1, 7, 14, 116))
        painter.fillPath(path, QBrush(body))

        haze = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
        haze.setColorAt(0.00, QColor(255, 255, 255, 40))
        haze.setColorAt(0.24, QColor(225, 250, 255, 18))
        haze.setColorAt(0.58, QColor(255, 255, 255, 4))
        haze.setColorAt(1.00, QColor(6, 14, 24, 36))
        painter.fillPath(path, QBrush(haze))

        glare = QRadialGradient(rect.left() + rect.width() * 0.16, rect.top() + rect.height() * 0.02, rect.width() * 0.62)
        glare.setColorAt(0.00, QColor(255, 255, 255, 72))
        glare.setColorAt(0.30, QColor(255, 255, 255, 26))
        glare.setColorAt(0.62, QColor(255, 255, 255, 0))
        glare.setColorAt(1.00, QColor(255, 255, 255, 0))
        painter.fillPath(path, QBrush(glare))

        surface_sheen = QLinearGradient(
            rect.left() + rect.width() * 0.02,
            rect.top() + rect.height() * 0.03,
            rect.left() + rect.width() * 0.68,
            rect.top() + rect.height() * 0.88,
        )
        surface_sheen.setColorAt(0.00, QColor(255, 255, 255, 0))
        surface_sheen.setColorAt(0.18, QColor(255, 255, 255, 48))
        surface_sheen.setColorAt(0.42, QColor(255, 255, 255, 12))
        surface_sheen.setColorAt(0.78, QColor(255, 255, 255, 0))
        surface_sheen.setColorAt(1.00, QColor(255, 255, 255, 0))
        painter.fillPath(path, QBrush(surface_sheen))

        bottom_glare = QRadialGradient(rect.left() + rect.width() * 0.78, rect.bottom(), rect.width() * 0.26)
        bottom_glare.setColorAt(0.00, QColor(255, 255, 255, 68))
        bottom_glare.setColorAt(0.30, QColor(174, 235, 255, 30))
        bottom_glare.setColorAt(1.00, QColor(255, 255, 255, 0))
        painter.fillPath(path, QBrush(bottom_glare))

        top_glare_path = QPainterPath()
        top_glare_path.addRoundedRect(rect, radius, radius)
        top_glare = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
        top_glare.setColorAt(0.00, QColor(255, 255, 255, 0))
        top_glare.setColorAt(0.18, QColor(255, 255, 255, 92))
        top_glare.setColorAt(0.44, QColor(255, 255, 255, 22))
        top_glare.setColorAt(0.68, QColor(126, 239, 229, 16))
        top_glare.setColorAt(1.00, QColor(255, 255, 255, 0))
        painter.fillPath(top_glare_path.intersected(path), QBrush(top_glare))

        top_edge = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.top())
        top_edge.setColorAt(0.00, QColor(255, 255, 255, 112))
        top_edge.setColorAt(0.18, QColor(255, 255, 255, 62))
        top_edge.setColorAt(0.56, QColor(186, 242, 255, 32))
        top_edge.setColorAt(1.00, QColor(68, 174, 186, 84))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QBrush(top_edge), 1.25))
        painter.drawRoundedRect(rect, radius, radius)

        painter.setPen(QPen(QColor(255, 255, 255, 38), 1.0))
        painter.drawRoundedRect(rect.adjusted(3.0, 3.0, -3.0, -3.0), radius - 3.0, radius - 3.0)

        side_glare_path = QPainterPath()
        side_glare_path.addRoundedRect(rect, radius, radius)
        side_glare = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.top())
        side_glare.setColorAt(0.00, QColor(255, 255, 255, 0))
        side_glare.setColorAt(0.64, QColor(255, 255, 255, 0))
        side_glare.setColorAt(0.86, QColor(126, 239, 229, 48))
        side_glare.setColorAt(1.00, QColor(255, 255, 255, 0))
        painter.fillPath(side_glare_path.intersected(path), QBrush(side_glare))

        super().paintEvent(event)


class BeepTimerPanel(GlassPanel):
    def __init__(self, title, sounds, sound_map, default_min):
        super().__init__()
        self.sounds = sound_map
        self.running = False
        self.next_beep = 0
        self.started = 0
        self.count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.beep_timer = QTimer(self)
        self.beep_timer.setSingleShot(True)
        self.beep_timer.timeout.connect(self.do_beep)

        layout = QGridLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setHorizontalSpacing(10)
        heading = QLabel(title.upper())
        heading.setObjectName("panelTitle")
        layout.addWidget(heading, 0, 0, 1, 2)
        layout.addWidget(QLabel("Sound"), 1, 0)
        self.sound = QComboBox()
        self.sound.addItems(sounds or ["No sounds"])
        layout.addWidget(self.sound, 1, 1)
        layout.addWidget(QLabel("Interval"), 2, 0)
        self.interval = QSpinBox()
        self.interval.setRange(1, 60)
        self.interval.setValue(default_min)
        layout.addWidget(self.interval, 2, 1)
        self.play = QPushButton("Play")
        self.play.clicked.connect(self.play_sound)
        self.start = QPushButton("Start Timer")
        self.start.clicked.connect(self.toggle)
        layout.addWidget(self.play, 1, 2)
        layout.addWidget(self.start, 2, 2)
        self.status = QLabel("Not running")
        layout.addWidget(self.status, 3, 0, 1, 3)

    def play_sound(self):
        name = self.sound.currentText()
        path = self.sounds.get(name)
        if path:
            try:
                pygame.mixer.Sound(path).play()
            except Exception:
                QApplication.beep()

    def toggle(self):
        if self.running:
            self.running = False
            self.timer.stop()
            self.beep_timer.stop()
            self.start.setText("Start Timer")
            self.status.setText("Stopped")
            self.sound.setEnabled(True)
            self.interval.setEnabled(True)
            return
        mins = self.interval.value()
        self.running = True
        self.started = time.time()
        self.next_beep = self.started + mins * 60
        self.count = 0
        self.start.setText("Stop Timer")
        self.sound.setEnabled(False)
        self.interval.setEnabled(False)
        self.timer.start(1000)
        self.beep_timer.start(mins * 60 * 1000)
        self.tick()

    def do_beep(self):
        if not self.running:
            return
        self.count += 1
        self.play_sound()
        self.next_beep = time.time() + self.interval.value() * 60
        self.beep_timer.start(self.interval.value() * 60 * 1000)
        self.tick()

    def tick(self):
        if not self.running:
            return
        self.status.setText(f"Elapsed {fmt_seconds(time.time() - self.started)}  |  Next beep {fmt_seconds(self.next_beep - time.time())}  |  Beeps {self.count}")


class TimerPage(QWidget):
    def __init__(self, sounds, sound_map, media, media_map):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 18)
        layout.setSpacing(12)
        self.short = BeepTimerPanel("Timer 1 (Short)", sounds, sound_map, 5)
        self.long = BeepTimerPanel("Timer 2 (Long)", sounds, sound_map, 30)
        layout.addWidget(self.short)
        layout.addWidget(self.long)
        self.media_map = media_map
        self.media_channel = pygame.mixer.Channel(1) if pygame.mixer.get_init() else None
        self.media_active = False
        self.media_was_busy = False
        self.media_poll = QTimer(self)
        self.media_poll.timeout.connect(self.check_media_finished)
        self.media_poll.start(1000)
        media_layout = QGridLayout()
        self.media_panel = GlassPanel(media_layout)
        media_layout.addWidget(QLabel("MEDIA PLAYER"), 0, 0, 1, 5)
        self.media_combo = QComboBox()
        self.media_combo.addItems(media or ["No media files"])
        self.shuffle = QCheckBox("Shuffle")
        play = QPushButton("Play")
        stop = QPushButton("Stop")
        nxt = QPushButton("Next")
        play.clicked.connect(self.play_media)
        stop.clicked.connect(self.stop_media)
        nxt.clicked.connect(self.next_media)
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(70)
        self.volume.valueChanged.connect(lambda v: self.media_channel and self.media_channel.set_volume(v / 100))
        self.now = QLabel("Not playing")
        media_layout.addWidget(self.media_combo, 1, 0, 1, 2)
        media_layout.addWidget(self.shuffle, 1, 2)
        media_layout.addWidget(play, 1, 3)
        media_layout.addWidget(stop, 1, 4)
        media_layout.addWidget(nxt, 1, 5)
        media_layout.addWidget(QLabel("Volume"), 2, 0)
        media_layout.addWidget(self.volume, 2, 1, 1, 5)
        media_layout.addWidget(self.now, 3, 0, 1, 6)
        layout.addWidget(self.media_panel)
        layout.addStretch(1)

    def selected_media(self):
        if self.shuffle.isChecked() and self.media_map:
            names = list(self.media_map.keys())
            current = self.media_combo.currentText()
            choices = [name for name in names if name != current] or names
            name = random.choice(choices)
            self.media_combo.setCurrentText(name)
            return name
        return self.media_combo.currentText()

    def play_media(self, name=None):
        if not self.media_channel:
            self.now.setText("Audio unavailable")
            return
        name = name or self.selected_media()
        self.media_combo.setCurrentText(name)
        path = self.media_map.get(name)
        if not path:
            return
        self.media_channel.stop()
        sound = pygame.mixer.Sound(path)
        self.media_channel.set_volume(self.volume.value() / 100)
        self.media_channel.play(sound)
        self.media_active = True
        self.media_was_busy = True
        self.now.setText(f"Playing: {name}")

    def stop_media(self):
        if self.media_channel:
            self.media_channel.stop()
        self.media_active = False
        self.media_was_busy = False
        self.now.setText("Stopped")

    def next_media(self):
        names = list(self.media_map.keys())
        if names:
            if self.shuffle.isChecked():
                current = self.media_combo.currentText()
                choices = [name for name in names if name != current] or names
                name = random.choice(choices)
                self.play_media(name)
            else:
                idx = (self.media_combo.currentIndex() + 1) % len(names)
                self.media_combo.setCurrentIndex(idx)
                self.play_media(self.media_combo.currentText())

    def check_media_finished(self):
        if not self.media_channel or not self.media_active:
            return
        busy = self.media_channel.get_busy()
        if self.media_was_busy and not busy:
            self.next_media()
            return
        self.media_was_busy = busy


class NewsPage(QWidget):
    FEEDS = {
        "Breitbart": "https://feeds.feedburner.com/breitbart",
        "Fox News": "https://moxie.foxnews.com/google-publisher/latest.xml",
        "Washington Examiner": "https://www.washingtonexaminer.com/feed/",
        "The Daily Wire": "https://www.dailywire.com/feeds/rss.xml",
        "The Federalist": "https://thefederalist.com/feed/",
        "National Review": "https://www.nationalreview.com/feed/",
    }

    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self.signals.done.connect(self.apply_result)
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("News Aggregator"))
        top.addStretch(1)
        self.updated = QLabel("Last updated: Never")
        btn = QPushButton("Refresh")
        btn.clicked.connect(self.refresh)
        top.addWidget(self.updated)
        top.addWidget(btn)
        layout.addLayout(top)
        self.list = QVBoxLayout()
        wrap = QWidget()
        wrap.setLayout(self.list)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(wrap)
        layout.addWidget(scroll)

    def refresh(self):
        self.updated.setText("Loading...")
        QApplication.processEvents()
        self.fetch()

    def fetch(self):
        try:
            import feedparser
            entries = []
            errors = 0
            for name, url in self.FEEDS.items():
                feed = feedparser.parse(url)
                if getattr(feed, "bozo", False):
                    errors += 1
                for entry in feed.entries[:8]:
                    entries.append((entry.get("published_parsed") or entry.get("updated_parsed") or (0,), name, entry))
            entries.sort(key=lambda x: x[0], reverse=True)
            self.apply_result((entries[:40], errors))
        except Exception as e:
            self.apply_result(([], str(e)))

    def apply_result(self, result):
        entries, errors = result
        while self.list.count():
            item = self.list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if isinstance(errors, str):
            self.updated.setText("Error")
            self.list.addWidget(QLabel(errors))
            return
        self.updated.setText(f"Last updated: {datetime.now().strftime('%H:%M:%S')} - {errors} feed error(s)")
        for _, source, entry in entries:
            panel = GlassPanel(QVBoxLayout())
            panel.layout().addWidget(QLabel(source.upper()))
            title = QLabel(plain_text(entry.get("title", "Untitled")))
            title.setWordWrap(True)
            title.setObjectName("newsTitle")
            link = entry.get("link", "")
            if link:
                title.setCursor(Qt.CursorShape.PointingHandCursor)
                title.mousePressEvent = lambda e, url=link: webbrowser.open(url)
            panel.layout().addWidget(title)
            summary = QLabel(plain_text(entry.get("summary", ""), 420))
            summary.setWordWrap(True)
            panel.layout().addWidget(summary)
            self.list.addWidget(panel)
        self.list.addStretch(1)


class MetalsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self.signals.done.connect(self.apply_result)
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("Live Spot Prices"))
        top.addStretch(1)
        self.updated = QLabel("Last updated: Never")
        btn = QPushButton("Refresh")
        btn.clicked.connect(self.refresh)
        top.addWidget(self.updated)
        top.addWidget(btn)
        layout.addLayout(top)
        grid = QGridLayout()
        panel = GlassPanel(grid)
        self.silver = QLabel("$--.-- USD")
        self.gold = QLabel("$--.-- USD")
        self.silver.setObjectName("bigValue")
        self.gold.setObjectName("bigValue")
        grid.addWidget(QLabel("Silver"), 0, 0)
        grid.addWidget(self.silver, 1, 0)
        grid.addWidget(QLabel("Gold"), 0, 1)
        grid.addWidget(self.gold, 1, 1)
        self.status = QLabel("")
        grid.addWidget(self.status, 2, 0, 1, 2)
        layout.addWidget(panel)
        layout.addStretch(1)

    def refresh(self):
        self.updated.setText("Loading...")
        QApplication.processEvents()
        self.fetch()

    def fetch(self):
        try:
            import yfinance as yf
            s = yf.Ticker("SI=F").info
            g = yf.Ticker("GC=F").info
            data = (
                s.get("currentPrice") or s.get("regularMarketPrice") or s.get("previousClose"),
                g.get("currentPrice") or g.get("regularMarketPrice") or g.get("previousClose"),
            )
            self.apply_result((data, None))
        except Exception as e:
            self.apply_result((None, str(e)))

    def apply_result(self, result):
        data, error = result
        if error:
            self.updated.setText("Error")
            self.status.setText(error)
            return
        silver, gold = data
        self.silver.setText(f"${silver:.2f} USD" if isinstance(silver, (int, float)) else "N/A")
        self.gold.setText(f"${gold:.2f} USD" if isinstance(gold, (int, float)) else "N/A")
        self.updated.setText(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")


WEATHER_CODES = {0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Fog", 51: "Drizzle", 61: "Rain", 63: "Rain", 65: "Heavy rain", 71: "Snow", 80: "Showers", 95: "Thunderstorms"}


class WeatherPage(QWidget):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self.signals.done.connect(self.apply_result)
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("Weather"))
        top.addStretch(1)
        nws = QPushButton("Full Forecast (NWS)")
        nws.clicked.connect(lambda: webbrowser.open("https://forecast.weather.gov/MapClick.php?lat=34.7304&lon=-86.5861"))
        self.updated = QLabel("Last updated: Never")
        btn = QPushButton("Refresh")
        btn.clicked.connect(self.refresh)
        top.addWidget(nws)
        top.addWidget(self.updated)
        top.addWidget(btn)
        layout.addLayout(top)
        self.content = QVBoxLayout()
        panel = GlassPanel(self.content)
        panel.setObjectName("weatherPanel")
        layout.addWidget(panel, 1)

    def refresh(self):
        self.updated.setText("Loading...")
        QApplication.processEvents()
        self.fetch()

    def fetch(self):
        try:
            url = (
                "https://api.open-meteo.com/v1/forecast?latitude=34.7304&longitude=-86.5861"
                "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
                "&hourly=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"
                "&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&timezone=America%2FChicago"
            )
            data = requests.get(url, timeout=10).json()
            self.apply_result((data, None))
        except Exception as e:
            self.apply_result((None, str(e)))

    def apply_result(self, result):
        data, error = result
        while self.content.count():
            item = self.content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if error:
            self.updated.setText("Error")
            self.content.addWidget(QLabel(error))
            return
        current = data["current"]
        temp = QLabel(f"{current['temperature_2m']:.0f}{DEGREE_F}")
        temp.setObjectName("weatherTemp")
        temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc = QLabel(WEATHER_CODES.get(current.get("weather_code"), "Weather"))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details = QLabel(
            f"Feels like: {current['apparent_temperature']:.0f}{DEGREE_F}\n"
            f"Humidity: {current['relative_humidity_2m']}%\n"
            f"Wind: {current['wind_speed_10m']:.0f} mph\n"
            f"Precip: {current['precipitation']:.2f}\""
        )
        details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content.addStretch(1)
        self.content.addWidget(temp)
        self.content.addWidget(desc)
        self.content.addWidget(details)
        self.content.addStretch(1)
        self.updated.setText(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")


class StatusPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 18)
        layout.setSpacing(12)

        top = QHBoxLayout()
        title = QLabel("Weather / Metals")
        title.setObjectName("sectionTitle")
        top.addWidget(title)
        top.addStretch(1)
        nws = QPushButton("Full Forecast (NWS)")
        nws.clicked.connect(lambda: webbrowser.open("https://forecast.weather.gov/MapClick.php?lat=34.7304&lon=-86.5861"))
        apmex = QPushButton("APMEX")
        apmex.clicked.connect(lambda: webbrowser.open("https://www.apmex.com/silver-price"))
        refresh_weather = QPushButton("Refresh Weather")
        refresh_weather.clicked.connect(self.refresh_weather)
        refresh_metals = QPushButton("Refresh Metals")
        refresh_metals.clicked.connect(self.refresh_metals)
        top.addWidget(nws)
        top.addWidget(apmex)
        top.addWidget(refresh_weather)
        top.addWidget(refresh_metals)
        layout.addLayout(top)

        cards = QGridLayout()
        cards.setSpacing(12)
        layout.addLayout(cards)
        self.weather_card = GlassPanel(QVBoxLayout())
        self.silver_card = GlassPanel(QVBoxLayout())
        self.gold_card = GlassPanel(QVBoxLayout())
        for card in (self.weather_card, self.silver_card, self.gold_card):
            card.layout().setContentsMargins(18, 16, 18, 16)
            card.layout().setSpacing(8)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        cards.addWidget(self.weather_card, 0, 0)
        cards.addWidget(self.silver_card, 0, 1)
        cards.addWidget(self.gold_card, 0, 2)
        layout.addStretch(1)

        self.weather_updated = QLabel("Weather: Never")
        self.weather_temp = QLabel("--")
        self.weather_temp.setObjectName("statusValue")
        self.weather_desc = QLabel("Waiting for weather")
        self.weather_details = QLabel("")
        for widget in (QLabel("Weather"), self.weather_temp, self.weather_desc, self.weather_details, self.weather_updated):
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.weather_card.layout().addWidget(widget)

        self.silver_updated = QLabel("Metals: Never")
        self.silver_price = QLabel("$--.--")
        self.silver_price.setObjectName("statusValue")
        for widget in (QLabel("Silver"), self.silver_price, self.silver_updated):
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.silver_card.layout().addWidget(widget)

        self.gold_updated = QLabel("Metals: Never")
        self.gold_price = QLabel("$--.--")
        self.gold_price.setObjectName("statusValue")
        for widget in (QLabel("Gold"), self.gold_price, self.gold_updated):
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.gold_card.layout().addWidget(widget)

    def refresh_weather(self):
        self.weather_updated.setText("Weather: Loading...")
        QApplication.processEvents()
        try:
            url = (
                "https://api.open-meteo.com/v1/forecast?latitude=34.7304&longitude=-86.5861"
                "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
                "&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&timezone=America%2FChicago"
            )
            current = requests.get(url, timeout=10).json()["current"]
            self.weather_temp.setText(f"{current['temperature_2m']:.0f}{DEGREE_F}")
            self.weather_desc.setText(WEATHER_CODES.get(current.get("weather_code"), "Weather"))
            self.weather_details.setText(
                f"Feels like {current['apparent_temperature']:.0f}{DEGREE_F}\n"
                f"Humidity {current['relative_humidity_2m']}%\n"
                f"Wind {current['wind_speed_10m']:.0f} mph\n"
                f"Precip {current['precipitation']:.2f}\""
            )
            self.weather_updated.setText(f"Weather: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            self.weather_updated.setText("Weather: Error")
            self.weather_details.setText(str(e))

    def refresh_metals(self):
        self.silver_updated.setText("Metals: Loading...")
        self.gold_updated.setText("Metals: Loading...")
        QApplication.processEvents()
        try:
            import yfinance as yf
            s = yf.Ticker("SI=F").info
            g = yf.Ticker("GC=F").info
            silver = s.get("currentPrice") or s.get("regularMarketPrice") or s.get("previousClose")
            gold = g.get("currentPrice") or g.get("regularMarketPrice") or g.get("previousClose")
            self.silver_price.setText(f"${silver:.2f}" if isinstance(silver, (int, float)) else "N/A")
            self.gold_price.setText(f"${gold:.2f}" if isinstance(gold, (int, float)) else "N/A")
            stamp = datetime.now().strftime("%H:%M:%S")
            self.silver_updated.setText(f"Metals: {stamp}")
            self.gold_updated.setText(f"Metals: {stamp}")
        except Exception as e:
            self.silver_updated.setText("Metals: Error")
            self.gold_updated.setText(str(e))


class TimerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pomodoro Timer")
        self.setMinimumSize(360, 260)
        self.resize(1120, 760)
        try:
            self.setWindowIcon(QIcon(str(resource_path("timer.ico"))))
        except Exception:
            pass
        self.settings = load_settings()
        self.background = BackgroundWidget(self.settings.get("background_path", ""))
        self.setCentralWidget(self.background)
        root = QVBoxLayout(self.background)
        root.setContentsMargins(14, 10, 14, 14)
        root.setSpacing(10)
        header = QHBoxLayout()
        title = QLabel("Pomodoro Timer")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch(1)
        self.bg_btn = QToolButton()
        self.bg_btn.setText("Background")
        self.bg_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self.bg_btn)
        choose = QAction("Choose Image/GIF", self)
        choose.triggered.connect(self.choose_background)
        default = QAction("Use Default", self)
        default.triggered.connect(self.clear_background)
        menu.addAction(choose)
        menu.addAction(default)
        self.bg_btn.setMenu(menu)
        self.pages_btn = QComboBox()
        self.pages_btn.addItems(["Timer", "News", "Status"])
        self.pages_btn.currentIndexChanged.connect(lambda i: self.stack.setCurrentIndex(i))
        tray = QPushButton("Minimize to Tray")
        tray.clicked.connect(self.hide)
        header.addWidget(tray)
        header.addWidget(self.bg_btn)
        header.addWidget(self.pages_btn)
        root.addLayout(header)

        sounds = [Path(p).stem for p in discover("beeps", ["*.wav"])]
        sound_map = {Path(p).stem: p for p in discover("beeps", ["*.wav"])}
        media = [Path(p).stem for p in discover("media", ["*.wav", "*.mp3", "*.ogg", "*.oga"])]
        media_map = {Path(p).stem: p for p in discover("media", ["*.wav", "*.mp3", "*.ogg", "*.oga"])}
        self.stack = QStackedWidget()
        self.timer_page = TimerPage(sounds, sound_map, media, media_map)
        self.news_page = NewsPage()
        self.status_page = StatusPage()
        for page in (self.timer_page, self.news_page, self.status_page):
            self.stack.addWidget(page)
        root.addWidget(self.stack, 1)
        self.stack.currentChanged.connect(self.pages_btn.setCurrentIndex)
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        menu = QMenu()
        show = QAction("Restore", self)
        show.triggered.connect(self.showNormal)
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(show)
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.show()
        self.apply_styles()

    def choose_background(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Timer Background", str(Path.home()), "Images and GIFs (*.png *.jpg *.jpeg *.bmp *.webp *.gif)")
        if path:
            self.settings["background_path"] = path
            save_settings(self.settings)
            self.background.set_background(path)

    def clear_background(self):
        self.settings.pop("background_path", None)
        save_settings(self.settings)
        self.background.set_background("")

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { color: #edf8ff; font-family: Segoe UI; font-size: 12px; background: transparent; }
            QLabel#title { font-size: 22px; font-weight: 800; }
            QLabel#sectionTitle { font-size: 18px; font-weight: 800; }
            QFrame#glassPanel {
                background: transparent;
                border: none;
            }
            QLabel#panelTitle, QLabel#newsTitle { font-weight: 800; color: #ffffff; }
            QLabel#bigValue, QLabel#weatherTemp, QLabel#statusValue { font-size: 56px; font-weight: 800; color: #fffed7; }
            QPushButton, QToolButton, QComboBox, QSpinBox {
                border: 1px solid rgba(235, 252, 255, 176);
                border-right-color: rgba(91, 215, 224, 160);
                border-bottom-color: rgba(255, 255, 255, 88);
                border-radius: 8px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 62),
                    stop: 0.17 rgba(65, 119, 154, 132),
                    stop: 0.52 rgba(12, 31, 50, 108),
                    stop: 1 rgba(4, 13, 25, 102)
                );
                color: #ffffff;
                padding: 7px 10px;
            }
            QPushButton:hover, QToolButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 96),
                    stop: 0.19 rgba(112, 204, 244, 184),
                    stop: 0.5 rgba(38, 112, 156, 154),
                    stop: 1 rgba(7, 27, 48, 132)
                );
                border-color: #ffffff;
            }
            QScrollArea, QStackedWidget { border: none; background: transparent; }
            QScrollBar:vertical { background: rgba(8, 14, 22, 130); width: 12px; }
            QScrollBar::handle:vertical { background: rgba(111, 147, 184, 170); border-radius: 5px; }
        """)

    def keyPressEvent(self, event):
        key_map = {
            Qt.Key.Key_M: 0,
            Qt.Key.Key_N: 1,
            Qt.Key.Key_I: 2,
            Qt.Key.Key_W: 2,
        }
        page = key_map.get(event.key())
        if page is not None:
            self.stack.setCurrentIndex(page)
            event.accept()
            return
        super().keyPressEvent(event)


def main():
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    app = QApplication(sys.argv)
    win = TimerWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
