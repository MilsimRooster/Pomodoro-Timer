# Pomodoro Timer 🍅

**The ultimate hacker-movie-inspired Pomodoro timer**  
A dual-timer Pomodoro beast with Matrix green-on-black vibes, full-screen gallery slideshow mode, custom beeps, and an endless shuffling chill media player. Built for deep focus sessions in true cyberpunk style.

## 🚀 Features

- **Dual Pomodoro Timers**  
  - Timer 1: Short intervals (default 5 min – perfect for breaks)  
  - Timer 2: Long sessions (default 30 min – classic focus pomodoro)  
  - Custom interval (1-60 min) + selectable beep sounds

- **Matrix Theme**
  - Classic black background with glowing green Consolas text

- **Gallery Skin Mode** 🖼️
  - Switch to full-screen auto-advancing slideshow (every 5s)  
  - Click or arrow keys to navigate, Esc to return  
  - Loads images from local `backgrounds` folder

- **Built-in Media Player** 🎧  
  - Play local tracks (.wav, .mp3, .ogg) from `media` folder  
  - Play / Stop / Next buttons  
  - Shuffle mode (true random every track)  
  - **Continuous playback** – auto-advances when song ends (sequential or shuffled)  
  - Independent volume slider

- **System Tray Support** 🗕  
  - Minimize to tray with custom green icon  
  - Restore or exit from tray menu

- **Custom Sounds** 🔊  
  - Short beep .wav files in `beeps` folder for timer alerts  
  - Fallback to system bell if load fails

## 📦 Requirements

- Python 3.7+ (tested on 3.13)
- Install dependencies:
  ```bash
  pip install pystray pillow pygame
