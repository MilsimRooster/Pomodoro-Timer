# Pomodoro Timer

A Windows-focused Pomodoro timer with dual countdowns, custom alert sounds, a gallery background mode, tray support, and a small built-in media player.

## Features

- Dual timers for short breaks and long focus sessions
- Custom WAV alert sounds from the `beeps` folder
- Gallery skin that displays local images from `backgrounds`
- Matrix, Gallery, Aggregator, Metals, Weather, Break Time, Rocket Launches, and Podcasts modes
- Local media playback from `media`
- System tray minimize/restore
- Resizable Tkinter UI
- Polished app and tray icon

## Requirements

- Windows 10/11
- Python 3.11 recommended
- Python packages:

```powershell
python -m pip install -r requirements.txt
```

## Run From Source

```powershell
python .\beep_timer_gui.pyw
```

The repo includes the required `beeps` folder. Optional local folders:

- `backgrounds`: `.jpg`, `.jpeg`, `.png`, `.bmp`, or `.gif` files for Gallery mode
- `media`: `.wav`, `.mp3`, `.ogg`, or `.oga` files for the media player

Those folders can be large and personal, so only `beeps` is tracked by default.

## Build EXE

Install PyInstaller:

```powershell
python -m pip install pyinstaller
```

Build:

```powershell
python -m PyInstaller --noconfirm --onefile --windowed --name TIMER --icon timer.ico --add-data "timer.ico;." --add-data "timer_icon.png;." beep_timer_gui.pyw
```

The output will be created at:

```text
dist\TIMER.exe
```

For normal use, keep `beeps`, `backgrounds`, and `media` beside the EXE. The EXE can run without `backgrounds` or `media`, but it needs at least one WAV file in `beeps`.
