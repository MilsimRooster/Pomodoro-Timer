# Pomodoro Timer with GUI - Matrix Theme + Skin Selector (Matrix / Pure Gallery Slideshow) + Media Player with Volume & Shuffle + Next Track + Continuous Playback
# Requirements: pip install pystray pillow pygame
# Save as multi_beep_timer.pyw
# Place short beep .wav files in the "beeps" folder (for timers/soundboard)
# Place longer tracks (.wav, .mp3, .ogg) in the "media" folder (for chill/media player mode)

import tkinter as tk
from tkinter import ttk, messagebox
import glob
import os
import time
import platform
import sys
import pygame
import random
from PIL import Image, ImageDraw, ImageTk, ImageEnhance
import pystray
import threading

if platform.system() != 'Windows':
    messagebox.showwarning("Platform", "Tray/audio optimized for Windows.")
    sys.exit(1)

pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
media_channel = pygame.mixer.Channel(1)

# ------------------- Matrix Theme -------------------
BG_COLOR = "black"
FG_COLOR = "#00FF00"
ACCENT_COLOR = "#003300"
ALERT_RED = "#FF0000"
ALERT_ORANGE = "#FF8800"
GRAY_COLOR = "#888888"

TITLE_FONT = ("Consolas", 16, "bold")
HEADING_FONT = ("Consolas", 13, "bold")
TEXT_FONT = ("Consolas", 11)
BUTTON_FONT = ("Consolas", 11, "bold")

SLIDESHOW_INTERVAL = 5000
# ---------------------------------------------------

# Beeps folder for timer/short sounds
BEEPS_FOLDER = "beeps"
if not os.path.exists(BEEPS_FOLDER):
    os.makedirs(BEEPS_FOLDER)

def load_sounds():
    sounds = glob.glob(os.path.join(BEEPS_FOLDER, "*.wav"))
    sounds = sorted(sounds, key=lambda x: os.path.splitext(os.path.basename(x))[0].lower())
    return sounds

available_sounds = load_sounds()
if not available_sounds:
    messagebox.showerror("Error", "No .wav beep files found in the 'beeps' folder.")
    sys.exit(1)

display_names = [os.path.splitext(os.path.basename(f))[0] for f in available_sounds]
display_to_full = dict(zip(display_names, available_sounds))

# Media folder for longer tracks
MEDIA_FOLDER = "media"
if not os.path.exists(MEDIA_FOLDER):
    os.makedirs(MEDIA_FOLDER)

def load_media():
    exts = ["*.wav", "*.mp3", "*.ogg", "*.oga"]
    media_files = []
    for ext in exts:
        media_files.extend(glob.glob(os.path.join(MEDIA_FOLDER, ext)))
        media_files.extend(glob.glob(os.path.join(MEDIA_FOLDER, ext.upper())))
    return sorted(set(media_files), key=lambda x: os.path.splitext(os.path.basename(x))[0].lower())

media_available = load_media()
media_display_names = [os.path.splitext(os.path.basename(f))[0] for f in media_available]
media_to_full = dict(zip(media_display_names, media_available))

# Background images for Gallery skin
BACKGROUND_FOLDER = "backgrounds"
if not os.path.exists(BACKGROUND_FOLDER):
    os.makedirs(BACKGROUND_FOLDER)

def load_backgrounds():
    exts = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.gif"]
    images = []
    for ext in exts:
        images.extend(glob.glob(os.path.join(BACKGROUND_FOLDER, ext)))
        images.extend(glob.glob(os.path.join(BACKGROUND_FOLDER, ext.upper())))
    return sorted(set(images), key=lambda x: x.lower())

backgrounds = load_backgrounds()

def format_seconds(sec):
    sec = max(0, int(sec))
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    elif m > 0:
        return f"{m}m {s:02d}s"
    else:
        return f"{s}s"

root = tk.Tk()
root.title("Pomodoro Timer")
root.configure(bg=BG_COLOR)
root.resizable(True, True)
root.minsize(700, 950)

background_label = tk.Label(root, bg=BG_COLOR)
background_label.place(x=0, y=0, relwidth=1, relheight=1)
background_label.lower()

style = ttk.Style()
style.theme_use('clam')
style.configure("TCombobox", background=BG_COLOR, foreground=FG_COLOR,
                fieldbackground=BG_COLOR, bordercolor=FG_COLOR,
                arrowcolor=FG_COLOR)
style.map("TCombobox",
          fieldbackground=[("readonly", BG_COLOR)],
          background=[("readonly", BG_COLOR)])

top_frame = tk.Frame(root, bg=BG_COLOR)
top_frame.pack(fill="x", pady=5)

title_label = tk.Label(top_frame, text="Pomodoro Timer", font=TITLE_FONT, bg=BG_COLOR, fg=FG_COLOR)
title_label.pack(side="left", padx=20)

skin_label = tk.Label(top_frame, text="Skin:", font=TEXT_FONT, bg=BG_COLOR, fg=FG_COLOR)
skin_label.pack(side="right", padx=(0, 8))

skin_combo = ttk.Combobox(top_frame, values=["Matrix", "Gallery"], state="readonly", width=12, font=TEXT_FONT)
skin_combo.set("Matrix")
skin_combo.pack(side="right")

minimize_button = tk.Button(top_frame, text="Minimize to Tray", command=lambda: hide_to_tray(), width=18,
                            font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                            activebackground="#004400", relief="flat", bd=0)
minimize_button.pack(side="right", padx=20)

def create_image():
    image = Image.new("RGB", (64, 64), BG_COLOR)
    draw = ImageDraw.Draw(image)
    green = (0, 255, 0)
    draw.ellipse((8, 8, 56, 56), outline=green, width=6)
    draw.line((32, 12, 32, 32), fill=green, width=6)
    draw.line((32, 32, 48, 28), fill=green, width=6)
    return image

icon_image = create_image()
current_icon = None

slideshow_id = None
current_index = 0
current_photo = None
current_skin = "Matrix"
gallery_hint = None

def resize_to_cover(img, width, height):
    if width <= 1 or height <= 1:
        return img
    img = img.copy()
    img_ratio = img.width / img.height
    win_ratio = width / height
    if img_ratio > win_ratio:
        new_width = width
        new_height = int(new_width / img_ratio)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        crop_y = (new_height - height) // 2
        img = img.crop((0, crop_y, width, crop_y + height))
    else:
        new_height = height
        new_width = int(new_height * img_ratio)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        crop_x = (new_width - width) // 2
        img = img.crop((crop_x, 0, crop_x + width, height))
    return img

def set_background_image(path):
    global current_photo
    width = root.winfo_width()
    height = root.winfo_height()
    if width < 100 or height < 100:
        return
    try:
        img = Image.open(path).convert("RGB")
        img = resize_to_cover(img, width, height)
        img = ImageEnhance.Brightness(img).enhance(1.0)
        current_photo = ImageTk.PhotoImage(img)
        background_label.config(image=current_photo)
        root.update_idletasks()
    except Exception as e:
        print(f"Error loading image: {e}")

def advance_slide(delta):
    global current_index, slideshow_id
    if not backgrounds:
        return
    if slideshow_id:
        root.after_cancel(slideshow_id)
        slideshow_id = None
    current_index = (current_index + delta) % len(backgrounds)
    set_background_image(backgrounds[current_index])
    slideshow_id = root.after(SLIDESHOW_INTERVAL, lambda: advance_slide(1))

def next_slide(event=None):
    advance_slide(1)

def prev_slide(event=None):
    advance_slide(-1)

def start_slideshow():
    global slideshow_id, current_index
    if slideshow_id:
        root.after_cancel(slideshow_id)
        slideshow_id = None
    if backgrounds:
        current_index = 0
        set_background_image(backgrounds[current_index])
        slideshow_id = root.after(SLIDESHOW_INTERVAL, lambda: advance_slide(1))

def stop_slideshow():
    global slideshow_id
    if slideshow_id:
        root.after_cancel(slideshow_id)
        slideshow_id = None
    background_label.config(image='', bg=BG_COLOR)

def switch_to_matrix(event=None):
    skin_combo.set("Matrix")
    apply_skin()

def bind_gallery_keys():
    root.bind("<Escape>", switch_to_matrix)
    root.bind("<Left>", prev_slide)
    root.bind("<Right>", next_slide)
    root.bind("<Button-1>", next_slide)

def unbind_gallery_keys():
    root.unbind("<Escape>")
    root.unbind("<Left>")
    root.unbind("<Right>")
    root.unbind("<Button-1>")

def apply_skin(event=None):
    global current_skin, backgrounds, gallery_hint
    selected = skin_combo.get()
    if selected == "Gallery":
        backgrounds = load_backgrounds()
        if not backgrounds:
            messagebox.showinfo("Gallery Skin", "No images found!\n\nPut some .jpg, .png, .gif, or .bmp files in the 'backgrounds' folder next to this script for the slideshow.\n\nReverting to Matrix skin.")
            skin_combo.set("Matrix")
            selected = "Matrix"
    if selected != current_skin:
        current_skin = selected
        if selected == "Gallery":
            stop_slideshow()
            start_slideshow()

            top_frame.pack_forget()
            timer1_frame.pack_forget()
            sep.pack_forget()
            timer2_frame.pack_forget()
            media_frame.pack_forget()
            volume_label.pack_forget()

            if gallery_hint is None:
                gallery_hint = tk.Label(root, text="Gallery Mode (auto-advances every 5s)\nClick or → for next • ← for previous\nEsc to return to timers", 
                                        font=("Consolas", 10), fg=FG_COLOR, bg="#111111", padx=10, pady=5, justify="left")
            gallery_hint.place(relx=0.99, rely=0.99, anchor="se")

            bind_gallery_keys()
        else:
            stop_slideshow()
            if gallery_hint:
                gallery_hint.place_forget()

            unbind_gallery_keys()

            top_frame.pack(fill="x", pady=5)
            timer1_frame.pack(fill="x", pady=8, padx=25)
            sep.pack(fill="x", pady=10, padx=40)
            timer2_frame.pack(fill="x", pady=8, padx=25)
            media_frame.pack(fill="x", pady=20, padx=25)
            volume_label.pack(pady=10)

        on_resize(None)

def on_resize(event=None):
    if current_skin == "Gallery" and backgrounds:
        set_background_image(backgrounds[current_index])

root.bind("<Configure>", on_resize)
skin_combo.bind("<<ComboboxSelected>>", apply_skin)

def hide_to_tray():
    global current_icon
    root.withdraw()
    if current_icon is None:
        current_icon = pystray.Icon("Beep Timer", icon_image, "Pomodoro Timer")
        current_icon.menu = pystray.Menu(
            pystray.MenuItem("Restore", show_window),
            pystray.MenuItem("Exit", on_quit)
        )
        threading.Thread(target=current_icon.run, daemon=True).start()

def show_window(icon=None, item=None):
    global current_icon
    if current_icon:
        current_icon.stop()
        current_icon = None
    root.deiconify()
    root.lift()

def on_quit(icon=None, item=None):
    if timer1.running:
        timer1.toggle_timer()
    if timer2.running:
        timer2.toggle_timer()
    media_channel.stop()
    pygame.mixer.quit()
    root.quit()

root.protocol("WM_DELETE_WINDOW", hide_to_tray)

class BeepTimer:
    def __init__(self, parent, label_text, default_min=25):
        self.frame = tk.Frame(parent, bg=BG_COLOR)

        heading_label = tk.Label(self.frame, text=label_text, font=HEADING_FONT, bg=BG_COLOR, fg=FG_COLOR)
        heading_label.pack(anchor="w", pady=(0, 4))

        controls = tk.Frame(self.frame, bg=BG_COLOR)
        controls.pack(fill="x", pady=2)

        sound_label = tk.Label(controls, text="Sound:", width=14, anchor="e", bg=BG_COLOR, fg=FG_COLOR, font=TEXT_FONT)
        sound_label.grid(row=0, column=0, sticky="e")

        self.sound_combo = ttk.Combobox(controls, values=display_names, state="readonly", width=36, font=TEXT_FONT)
        self.sound_combo.grid(row=0, column=1, padx=(8, 20), sticky="w")
        self.sound_combo.set(display_names[0])

        interval_label = tk.Label(controls, text="Interval (min):", width=15, anchor="e", bg=BG_COLOR, fg=FG_COLOR, font=TEXT_FONT)
        interval_label.grid(row=1, column=0, sticky="e")

        self.interval_spin = tk.Spinbox(controls, from_=1, to=60, width=10, font=TEXT_FONT,
                                       bg=BG_COLOR, fg=FG_COLOR, buttonbackground=ACCENT_COLOR,
                                       insertbackground=FG_COLOR, selectbackground=ACCENT_COLOR,
                                       relief="flat")
        self.interval_spin.grid(row=1, column=1, padx=(8, 20), sticky="w")
        self.interval_spin.delete(0, "end")
        self.interval_spin.insert(0, default_min)

        self.play_button = tk.Button(controls, text="Play", command=self.test_beep, width=10,
                                     font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                                     activebackground="#004400", relief="flat")
        self.play_button.grid(row=0, column=2, rowspan=2, padx=20, pady=2)

        self.status_label = tk.Label(self.frame, text="Not running", font=TEXT_FONT, bg=BG_COLOR, fg=GRAY_COLOR)
        self.status_label.pack(anchor="w", pady=2)

        self.elapsed_label = tk.Label(self.frame, text="", font=HEADING_FONT, bg=BG_COLOR, fg=FG_COLOR)
        self.elapsed_label.pack(anchor="w", pady=2)

        self.remaining_label = tk.Label(self.frame, text="", font=("Consolas", 12, "bold"), bg=BG_COLOR, fg=FG_COLOR)
        self.remaining_label.pack(anchor="w", pady=4)

        self.beeps_label = tk.Label(self.frame, text="", font=TEXT_FONT, bg=BG_COLOR, fg=FG_COLOR)
        self.beeps_label.pack(anchor="w", pady=2)

        self.start_button = tk.Button(self.frame, text="Start Timer", command=self.toggle_timer, width=20,
                                      font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                                      activebackground="#004400", relief="raised")
        self.start_button.pack(pady=8)

        self.running = False
        self.after_id = None
        self.countdown_id = None
        self.next_beep_time = None
        self.start_time_unix = None
        self.beep_count = 0

    def fallback_beep(self, repeats=3):
        if repeats > 0:
            root.bell()
            root.after(300, lambda: self.fallback_beep(repeats - 1))

    def play_custom(self, display_name):
        full_file = display_to_full.get(display_name)
        if not full_file:
            return False
        full_path = os.path.abspath(full_file)
        if os.path.exists(full_path):
            try:
                sound = pygame.mixer.Sound(full_path)
                sound.play()
                return True
            except Exception as e:
                print(f"Error playing sound: {e}")
                return False
        return False

    def test_beep(self):
        if not self.play_custom(self.sound_combo.get()):
            self.fallback_beep(3)

    def update_countdown(self):
        if not self.running:
            return

        elapsed_sec = int(time.time() - self.start_time_unix)
        remaining_sec = max(0, int(self.next_beep_time - time.time()))

        self.elapsed_label.config(text=f"Elapsed: {format_seconds(elapsed_sec)}")

        rem_text = f"Next beep in: {format_seconds(remaining_sec)}"
        fg = ALERT_RED if remaining_sec < 60 else ALERT_ORANGE if remaining_sec < 300 else FG_COLOR
        self.remaining_label.config(text=rem_text, fg=fg)

        root.update_idletasks()
        self.countdown_id = root.after(1000, self.update_countdown)

    def do_beep(self):
        self.beep_count += 1
        self.beeps_label.config(text=f"Beeps delivered: {self.beep_count}")
        self.status_label.config(text=f"BEEP #{self.beep_count} @ {time.strftime('%H:%M:%S')}", fg=FG_COLOR)

        if not self.play_custom(self.sound_combo.get()):
            self.fallback_beep(3)

        self.next_beep_time += int(self.interval_spin.get()) * 60
        self.after_id = root.after(int(self.interval_spin.get()) * 60 * 1000, self.do_beep)

    def toggle_timer(self):
        if self.running:
            if self.after_id:
                root.after_cancel(self.after_id)
                self.after_id = None
            if self.countdown_id:
                root.after_cancel(self.countdown_id)
                self.countdown_id = None
            self.running = False

            final_elapsed = int(time.time() - self.start_time_unix) if self.start_time_unix else 0
            self.elapsed_label.config(text=f"Session ended after {format_seconds(final_elapsed)}", fg=GRAY_COLOR)
            self.remaining_label.config(text="")

            self.sound_combo.config(state="readonly")
            self.interval_spin.config(state="normal")

            self.status_label.config(text="Stopped", fg=GRAY_COLOR)
            self.start_button.config(text="Start Timer", bg=ACCENT_COLOR, fg=FG_COLOR)
        else:
            mins = int(self.interval_spin.get())
            if mins < 1 or mins > 60:
                messagebox.showwarning("Invalid", "Interval must be 1-60 minutes.")
                return

            interval_sec = mins * 60
            self.start_time_unix = time.time()
            self.next_beep_time = self.start_time_unix + interval_sec

            self.status_label.config(text=f"Running – {mins} min interval", fg=FG_COLOR)
            self.beeps_label.config(text="Beeps delivered: 0")
            self.beep_count = 0
            self.elapsed_label.config(text="Elapsed: 0s")
            self.remaining_label.config(text=f"Next beep in: {format_seconds(interval_sec)}", fg=FG_COLOR)

            self.sound_combo.config(state="disabled")
            self.interval_spin.config(state="disabled")

            root.after(200, self.update_countdown)
            self.after_id = root.after(interval_sec * 1000, self.do_beep)

            self.running = True
            self.start_button.config(text="Stop Timer", bg=ALERT_RED, fg="white")

timer1 = BeepTimer(root, "Timer 1 (Short)", default_min=5)
timer1_frame = timer1.frame

sep = ttk.Separator(root, orient="horizontal")

timer2 = BeepTimer(root, "Timer 2 (Long)", default_min=30)
timer2_frame = timer2.frame

# Media Player section
media_frame = tk.Frame(root, bg=BG_COLOR)

tk.Label(media_frame, text="Media Player (Chill Mode)", font=HEADING_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(anchor="w", pady=(0, 8))

media_controls = tk.Frame(media_frame, bg=BG_COLOR)
media_controls.pack(fill="x", pady=5)

tk.Label(media_controls, text="Track:", width=14, anchor="e", bg=BG_COLOR, fg=FG_COLOR, font=TEXT_FONT).grid(row=0, column=0, sticky="e")

if not media_available:
    media_display_names = ["No media files - add to 'media' folder"]

media_combo = ttk.Combobox(media_controls, values=media_display_names, state="readonly", width=45, font=TEXT_FONT)
media_combo.grid(row=0, column=1, padx=(8, 10), sticky="w")

shuffle_var = tk.BooleanVar(value=False)
shuffle_check = tk.Checkbutton(media_controls, text="Shuffle", variable=shuffle_var, bg=BG_COLOR, fg=FG_COLOR, selectcolor=ACCENT_COLOR,
                               activebackground=BG_COLOR, activeforeground=FG_COLOR)
shuffle_check.grid(row=0, column=2, padx=10)

# Playback state globals
monitor_id = None
continuous_active = False

def stop_monitor():
    global monitor_id
    if monitor_id is not None:
        root.after_cancel(monitor_id)
        monitor_id = None

def monitor_playback():
    global monitor_id
    if not continuous_active:
        monitor_id = None
        return
    if media_channel.get_busy():
        monitor_id = root.after(1000, monitor_playback)
    else:
        play_next()
        monitor_id = root.after(1000, monitor_playback)

def play_next():
    if not media_available or len(media_display_names) == 0:
        current_media_label.config(text="No media files", fg="red")
        return

    media_channel.stop()

    if shuffle_var.get():
        selected = random.choice(media_display_names)
    else:
        try:
            current_idx = media_display_names.index(media_combo.get())
            next_idx = (current_idx + 1) % len(media_display_names)
            selected = media_display_names[next_idx]
        except (ValueError, IndexError):
            selected = media_display_names[0]

    media_combo.set(selected)
    full_path = media_to_full.get(selected)
    if not full_path or not os.path.exists(full_path):
        current_media_label.config(text="File not found", fg="red")
        return

    try:
        sound = pygame.mixer.Sound(full_path)
        media_channel.play(sound)
        media_channel.set_volume(volume_var.get() / 100.0)
        current_media_label.config(text=f"Playing: {selected}", fg=FG_COLOR)
    except Exception as e:
        messagebox.showerror("Error", f"Could not play {selected}\n{e}")
        current_media_label.config(text="Playback error", fg="red")

def play_media():
    global continuous_active, monitor_id
    if not media_available or len(media_display_names) == 0:
        current_media_label.config(text="No media files", fg="red")
        return

    media_channel.stop()
    stop_monitor()

    selected = media_combo.get()
    if shuffle_var.get():
        selected = random.choice(media_display_names)

    media_combo.set(selected)
    full_path = media_to_full.get(selected)
    if not full_path or not os.path.exists(full_path):
        current_media_label.config(text="File not found", fg="red")
        continuous_active = False
        return

    try:
        sound = pygame.mixer.Sound(full_path)
        media_channel.play(sound)
        media_channel.set_volume(volume_var.get() / 100.0)
        current_media_label.config(text=f"Playing: {selected}", fg=FG_COLOR)

        continuous_active = True
        monitor_id = root.after(1000, monitor_playback)
    except Exception as e:
        messagebox.showerror("Error", f"Could not play {selected}\n{e}")
        current_media_label.config(text="Playback error", fg="red")
        continuous_active = False

def stop_media():
    global continuous_active, monitor_id
    media_channel.stop()
    continuous_active = False
    stop_monitor()
    current_media_label.config(text="Stopped", fg=GRAY_COLOR)

# Buttons
play_media_btn = tk.Button(media_controls, text="Play", width=10, font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                           activebackground="#004400", relief="flat",
                           command=play_media)
play_media_btn.grid(row=0, column=3, padx=5)

stop_media_btn = tk.Button(media_controls, text="Stop", width=10, font=BUTTON_FONT, bg=ALERT_RED, fg="white",
                           activebackground="#880000", relief="flat",
                           command=stop_media)
stop_media_btn.grid(row=0, column=4, padx=5)

next_media_btn = tk.Button(media_controls, text="Next", width=10, font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                           activebackground="#004400", relief="flat",
                           command=play_next)
next_media_btn.grid(row=0, column=5, padx=5)

# Volume control
volume_frame = tk.Frame(media_frame, bg=BG_COLOR)
volume_frame.pack(fill="x", pady=8)

tk.Label(volume_frame, text="Media Volume:", bg=BG_COLOR, fg=FG_COLOR, font=TEXT_FONT).pack(side="left", padx=(20, 10))

volume_var = tk.IntVar(value=70)
def set_media_volume(val):
    media_channel.set_volume(int(val) / 100.0)

volume_slider = tk.Scale(volume_frame, from_=0, to=100, orient="horizontal", variable=volume_var,
                         command=set_media_volume, bg=BG_COLOR, fg=FG_COLOR, highlightbackground=BG_COLOR,
                         troughcolor="#003300", activebackground="#004400")
volume_slider.pack(side="left", fill="x", expand=True, padx=(0, 20))

current_media_label = tk.Label(media_frame, text="Not playing", font=TEXT_FONT, bg=BG_COLOR, fg=GRAY_COLOR)
current_media_label.pack(anchor="w", pady=4)

# Initial combo setup
if media_available:
    media_combo.set(media_display_names[0])
else:
    media_combo.config(state="disabled")
    if media_display_names:
        media_combo.set(media_display_names[0])

volume_label = tk.Label(root, text="(Timer beeps use system volume • Media has independent control)", font=("Consolas", 9), fg=GRAY_COLOR, bg=BG_COLOR)

# Initial layout
top_frame.pack(fill="x", pady=5)
timer1_frame.pack(fill="x", pady=8, padx=25)
sep.pack(fill="x", pady=10, padx=40)
timer2_frame.pack(fill="x", pady=8, padx=25)
media_frame.pack(fill="x", pady=20, padx=25)
volume_label.pack(pady=10)

root.mainloop()