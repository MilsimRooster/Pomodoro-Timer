# Timer PyQt Liquid Glass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Timer's Tkinter visual shell with a PyQt6 shell that looks like Command Center while preserving timer, media, news, metals, weather, tray, and image/GIF background behavior.

**Architecture:** Create a new focused PyQt entrypoint, `timer_pyqt.py`, leaving the old Tk file available as fallback. Use a `BackgroundWidget` like Command Center for static/GIF backgrounds, glass-styled panels over it, and separate page widgets for Timer, News, Metals, and Weather.

**Tech Stack:** Python 3.11, PyQt6, pygame, feedparser, yfinance, requests, PyInstaller.

---

### Task 1: PyQt Shell

**Files:**
- Create: `E:\games\timer\timer_pyqt.py`
- Modify: `E:\games\timer\TIMER.spec`
- Test: `E:\games\timer\tests\test_pyqt_shell_source.py`

- [ ] Add source-level tests that assert the PyQt shell contains `BackgroundWidget`, GIF support via `QMovie`, and a `TimerWindow`.
- [ ] Create `timer_pyqt.py` with reusable resource/settings helpers, media/beep discovery, BackgroundWidget, page widgets, and tray behavior.
- [ ] Update `TIMER.spec` to build `timer_pyqt.py`.
- [ ] Run `py_compile`, unit tests, source smoke launch, PyInstaller build, and exe smoke launch.
