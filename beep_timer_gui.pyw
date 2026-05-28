import tkinter as tk
from tkinter import ttk, messagebox
import glob
import os
import time
import platform
import sys
from pathlib import Path
import pygame
import random
from PIL import Image, ImageDraw, ImageTk, ImageEnhance
import pystray
import threading
import webbrowser
import datetime
from datetime import datetime, timezone
import requests
if platform.system() != 'Windows':
    messagebox.showwarning("Platform", "Tray/audio optimized for Windows.")
    sys.exit(1)
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    media_channel = pygame.mixer.Channel(1)
    AUDIO_AVAILABLE = True
except Exception as e:
    print(f"Audio init failed: {e}")
    media_channel = None
    AUDIO_AVAILABLE = False

APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))

def app_path(*parts):
    return str(APP_DIR.joinpath(*parts))

def resource_path(*parts):
    local_path = APP_DIR.joinpath(*parts)
    if local_path.exists():
        return str(local_path)
    return str(RESOURCE_DIR.joinpath(*parts))
# ------------------- Matrix Theme -------------------
BG_COLOR = "black"
FG_COLOR = "#00FF00"
ACCENT_COLOR = "#003300"
ALERT_RED = "#FF0000"
ALERT_ORANGE = "#FF8800"
GRAY_COLOR = "#888888"
POSITIVE_GREEN = "#00FF88"
NEGATIVE_RED = "#FF4444"
TITLE_FONT = ("Consolas", 16, "bold")
HEADING_FONT = ("Consolas", 13, "bold")
LARGE_PRICE_FONT = ("Consolas", 48, "bold")
MEDIUM_PRICE_FONT = ("Consolas", 32, "bold")
TEXT_FONT = ("Consolas", 11)
BUTTON_FONT = ("Consolas", 11, "bold")
BIG_BUTTON_FONT = ("Consolas", 20, "bold")
SLIDESHOW_INTERVAL = 5000
# ---------------------------------------------------
# Beeps folder for timer/short sounds
BEEPS_FOLDER = app_path("beeps")
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
MEDIA_FOLDER = app_path("media")
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
BACKGROUND_FOLDER = app_path("backgrounds")
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
try:
    root.iconbitmap(resource_path("timer.ico"))
except Exception:
    pass
root.configure(bg=BG_COLOR)
root.resizable(True, True)
root.minsize(520, 420)
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
skin_combo = ttk.Combobox(top_frame, values=["Matrix", "Gallery", "Aggregator", "Metals", "Weather", "Break Time", "Rocket Launches", "Podcasts"], state="readonly", width=16, font=TEXT_FONT)
skin_combo.set("Matrix")
skin_combo.pack(side="right")
minimize_button = tk.Button(top_frame, text="Minimize to Tray", command=lambda: hide_to_tray(), width=18,
                            font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                            activebackground="#004400", relief="flat", bd=0)
minimize_button.pack(side="right", padx=20)
# Hotkey reminder label in top bar
hotkeys_label = tk.Label(top_frame, text="Hotkeys: M=Matrix • G=Gallery • N=News • I=Metals • W=Weather • B=Break • R=Rockets • P=Podcasts",
                         font=("Consolas", 9), bg=BG_COLOR, fg=GRAY_COLOR)
hotkeys_label.pack(side="right", padx=20)

def sync_topbar_layout(event=None):
    width = top_frame.winfo_width()
    if width and width < 980:
        hotkeys_label.pack_forget()
    elif not hotkeys_label.winfo_ismapped():
        hotkeys_label.pack(side="right", padx=20)

top_frame.bind("<Configure>", sync_topbar_layout)

matrix_scroll = tk.Canvas(root, bg=BG_COLOR, highlightthickness=0)
matrix_scrollbar = ttk.Scrollbar(root, orient="vertical", command=matrix_scroll.yview)
matrix_scroll.configure(yscrollcommand=matrix_scrollbar.set)
matrix_content = tk.Frame(matrix_scroll, bg=BG_COLOR)
matrix_window = matrix_scroll.create_window((0, 0), window=matrix_content, anchor="nw")

def sync_matrix_scroll_region(event=None):
    matrix_scroll.configure(scrollregion=matrix_scroll.bbox("all"))

def sync_matrix_width(event=None):
    matrix_scroll.itemconfigure(matrix_window, width=matrix_scroll.winfo_width())

def on_matrix_mousewheel(event):
    matrix_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")

matrix_content.bind("<Configure>", sync_matrix_scroll_region)
matrix_scroll.bind("<Configure>", sync_matrix_width)
matrix_scroll.bind("<Enter>", lambda e: matrix_scroll.focus_set())
matrix_scroll.bind("<MouseWheel>", on_matrix_mousewheel)
def create_image():
    icon_path = resource_path("timer_icon.png")
    if os.path.exists(icon_path):
        try:
            return Image.open(icon_path).convert("RGBA").resize((64, 64), Image.LANCZOS)
        except Exception:
            pass
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
aggregator_hint = None
metals_hint = None
weather_hint = None
break_hint = None
launches_hint = None
podcasts_hint = None
def resize_to_fit(img, width, height):
    if width <= 1 or height <= 1:
        return img
    canvas = Image.new("RGB", (width, height), BG_COLOR)
    img = img.copy()
    img_ratio = img.width / img.height
    win_ratio = width / height
    if img_ratio > win_ratio:
        new_width = width
        new_height = int(new_width / img_ratio)
    else:
        new_height = height
        new_width = int(new_height * img_ratio)
    img = img.resize((new_width, new_height), Image.LANCZOS)
    x = (width - new_width) // 2
    y = (height - new_height) // 2
    canvas.paste(img, (x, y))
    return canvas
def set_background_image(path):
    global current_photo
    width = root.winfo_width()
    height = root.winfo_height()
    if width < 100 or height < 100:
        return
    try:
        img = Image.open(path).convert("RGB")
        img = resize_to_fit(img, width, height)
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
def bind_aggregator_keys():
    root.bind("<Escape>", switch_to_matrix)
def unbind_aggregator_keys():
    root.unbind("<Escape>")
def bind_metals_keys():
    root.bind("<Escape>", switch_to_matrix)
def unbind_metals_keys():
    root.unbind("<Escape>")
def bind_weather_keys():
    root.bind("<Escape>", switch_to_matrix)
def unbind_weather_keys():
    root.unbind("<Escape>")
def bind_break_keys():
    root.bind("<Escape>", switch_to_matrix)
def unbind_break_keys():
    root.unbind("<Escape>")
def bind_launches_keys():
    root.bind("<Escape>", switch_to_matrix)
def unbind_launches_keys():
    root.unbind("<Escape>")
def bind_podcasts_keys():
    root.bind("<Escape>", switch_to_matrix)
def unbind_podcasts_keys():
    root.unbind("<Escape>")
# Helper to switch skins via hotkey
def switch_skin(skin_name):
    skin_combo.set(skin_name)
    apply_skin()
def apply_skin(event=None):
    global current_skin, backgrounds, gallery_hint, aggregator_hint, metals_hint, weather_hint, break_hint, launches_hint, podcasts_hint
    selected = skin_combo.get()
    if selected == "Gallery":
        backgrounds = load_backgrounds()
        if not backgrounds:
            messagebox.showinfo("Gallery Skin", f"No images found!\n\nPut some .jpg, .png, .gif, or .bmp files in:\n{BACKGROUND_FOLDER}\n\nReverting to Matrix skin.")
            skin_combo.set("Matrix")
            selected = "Matrix"
    if selected != current_skin:
        current_skin = selected
        top_frame.pack_forget()
        matrix_scroll.pack_forget()
        matrix_scrollbar.pack_forget()
        timer1_frame.pack_forget()
        sep.pack_forget()
        timer2_frame.pack_forget()
        media_frame.pack_forget()
        volume_label.pack_forget()
        aggregator_frame.pack_forget()
        metals_frame.pack_forget()
        weather_frame.pack_forget()
        break_frame.pack_forget()
        launches_frame.pack_forget()
        podcasts_frame.pack_forget()
        if gallery_hint:
            gallery_hint.place_forget()
        if aggregator_hint:
            aggregator_hint.place_forget()
        if metals_hint:
            metals_hint.place_forget()
        if weather_hint:
            weather_hint.place_forget()
        if break_hint:
            break_hint.place_forget()
        if launches_hint:
            launches_hint.place_forget()
        if podcasts_hint:
            podcasts_hint.place_forget()
        unbind_gallery_keys()
        unbind_aggregator_keys()
        unbind_metals_keys()
        unbind_weather_keys()
        unbind_break_keys()
        unbind_launches_keys()
        unbind_podcasts_keys()
        stop_slideshow()
        background_label.config(image='', bg=BG_COLOR)
        if selected == "Matrix":
            top_frame.pack(fill="x", pady=5)
            pack_matrix_view()
        elif selected == "Gallery":
            start_slideshow()
            bind_gallery_keys()
            if gallery_hint is None:
                gallery_hint = tk.Label(root, text="Gallery Mode",
                                        font=("Consolas", 10), fg=FG_COLOR, bg="#111111", padx=10, pady=5, justify="left")
            gallery_hint.place(relx=0.99, rely=0.99, anchor="se")
        elif selected == "Aggregator":
            aggregator_frame.pack(fill="both", expand=True)
            bind_aggregator_keys()
            if aggregator_hint is None:
                aggregator_hint = tk.Label(root, text="News Aggregator Mode",
                                           font=("Consolas", 10), fg=FG_COLOR, bg="#111111", padx=10, pady=5, justify="left")
            aggregator_hint.place(relx=0.99, rely=0.99, anchor="se")
            refresh_news()
        elif selected == "Metals":
            metals_frame.pack(fill="both", expand=True)
            bind_metals_keys()
            if metals_hint is None:
                metals_hint = tk.Label(root, text="Metals Mode",
                                       font=("Consolas", 10), fg=FG_COLOR, bg="#111111", padx=10, pady=5, justify="left")
            metals_hint.place(relx=0.99, rely=0.99, anchor="se")
            refresh_prices()
        elif selected == "Weather":
            weather_frame.pack(fill="both", expand=True)
            bind_weather_keys()
            if weather_hint is None:
                weather_hint = tk.Label(root, text="Weather Mode",
                                        font=("Consolas", 10), fg=FG_COLOR, bg="#111111", padx=10, pady=5, justify="left")
            weather_hint.place(relx=0.99, rely=0.99, anchor="se")
            refresh_weather()
        elif selected == "Break Time":
            break_frame.pack(fill="both", expand=True)
            bind_break_keys()
            if break_hint is None:
                break_hint = tk.Label(root, text="Break Time",
                                      font=("Consolas", 10), fg=FG_COLOR, bg="#111111", padx=10, pady=5, justify="left")
            break_hint.place(relx=0.99, rely=0.99, anchor="se")
        elif selected == "Rocket Launches":
            launches_frame.pack(fill="both", expand=True)
            bind_launches_keys()
            if launches_hint is None:
                launches_hint = tk.Label(root, text="Rocket Launches Mode",
                                         font=("Consolas", 10), fg=FG_COLOR, bg="#111111", padx=10, pady=5, justify="left")
            launches_hint.place(relx=0.99, rely=0.99, anchor="se")
            refresh_launches()
        elif selected == "Podcasts":
            podcasts_frame.pack(fill="both", expand=True)
            bind_podcasts_keys()
            if podcasts_hint is None:
                podcasts_hint = tk.Label(root, text="Podcasts Mode",
                                         font=("Consolas", 10), fg=FG_COLOR, bg="#111111", padx=10, pady=5, justify="left")
            podcasts_hint.place(relx=0.99, rely=0.99, anchor="se")
            refresh_podcasts()
        on_resize(None)
def on_resize(event=None):
    if current_skin == "Gallery" and backgrounds:
        set_background_image(backgrounds[current_index])
    elif current_skin == "Aggregator":
        news_canvas.configure(scrollregion=news_canvas.bbox("all"))
    elif current_skin == "Weather":
        weather_canvas.configure(scrollregion=weather_canvas.bbox("all"))
    elif current_skin == "Rocket Launches":
        launches_canvas.configure(scrollregion=launches_canvas.bbox("all"))
    elif current_skin == "Podcasts":
        podcasts_canvas.configure(scrollregion=podcasts_canvas.bbox("all"))
root.bind("<Configure>", on_resize)
skin_combo.bind("<<ComboboxSelected>>", apply_skin)
# Aggregator Skin UI
aggregator_frame = tk.Frame(root, bg=BG_COLOR)
agg_top_frame = tk.Frame(aggregator_frame, bg=BG_COLOR)
agg_top_frame.pack(fill="x", pady=10)
tk.Label(agg_top_frame, text="News Aggregator", font=TITLE_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=30)
refresh_button = tk.Button(agg_top_frame, text="Refresh", font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                           activebackground="#004400", relief="flat", command=lambda: refresh_news())
refresh_button.pack(side="right", padx=30)
last_updated_label = tk.Label(agg_top_frame, text="Last updated: Never", font=TEXT_FONT, bg=BG_COLOR, fg=GRAY_COLOR)
last_updated_label.pack(side="right", padx=(0, 20))
news_canvas = tk.Canvas(aggregator_frame, bg=BG_COLOR, highlightthickness=0)
news_scrollbar = ttk.Scrollbar(aggregator_frame, orient="vertical", command=news_canvas.yview)
news_canvas.configure(yscrollcommand=news_scrollbar.set)
news_scrollbar.pack(side="right", fill="y")
news_canvas.pack(side="left", fill="both", expand=True)
news_inner_frame = tk.Frame(news_canvas, bg=BG_COLOR)
news_canvas.create_window((0, 0), window=news_inner_frame, anchor="nw")
news_inner_frame.bind("<Configure>", lambda e: news_canvas.configure(scrollregion=news_canvas.bbox("all")))
# Reliable mouse wheel scrolling for News
news_canvas.bind("<Enter>", lambda e: news_canvas.focus_set())
news_canvas.bind("<MouseWheel>", lambda event: news_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
def refresh_news():
    last_updated_label.config(text="Loading...", fg=FG_COLOR)
    for child in news_inner_frame.winfo_children():
        child.destroy()
    def fetch_and_display():
        try:
            import feedparser
        except ImportError:
            def update_ui():
                last_updated_label.config(text="Library missing", fg=ALERT_RED)
                error_label = tk.Label(news_inner_frame,
                                       text="The 'feedparser' library is not installed.\n\nTo enable Aggregator:\npip install feedparser\n\n(Other skins work without it.)",
                                       font=TEXT_FONT, fg=ALERT_RED, bg=BG_COLOR, justify="left")
                error_label.pack(pady=100, padx=50)
                news_canvas.configure(scrollregion=news_canvas.bbox("all"))
            root.after(0, update_ui)
            return
        feed = feedparser.parse("https://feeds.feedburner.com/breitbart")
        now = datetime.now().strftime("%H:%M:%S")
        def update_ui():
            if hasattr(feed, 'bozo_exception') or (hasattr(feed, 'bozo') and feed.bozo):
                last_updated_label.config(text="Feed error", fg=ALERT_RED)
                error_msg = str(getattr(feed, 'bozo_exception', 'Unknown error'))
                error_label = tk.Label(news_inner_frame, text=f"Error loading feed:\n{error_msg}\n\nCheck internet connection.",
                                       font=TEXT_FONT, fg=ALERT_RED, bg=BG_COLOR, wraplength=800, justify="left")
                error_label.pack(pady=50, padx=30)
            elif not feed.entries:
                last_updated_label.config(text="No items", fg=GRAY_COLOR)
                no_items_label = tk.Label(news_inner_frame, text="No headlines available.\nTry refreshing later.",
                                          font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR)
                no_items_label.pack(pady=50)
            else:
                last_updated_label.config(text=f"Last updated: {now}", fg=GRAY_COLOR)
                for entry in feed.entries[:30]:
                    item_frame = tk.Frame(news_inner_frame, bg=BG_COLOR)
                    item_frame.pack(fill="x", padx=40, pady=12, anchor="w")
                    title_text = entry.get('title', 'Untitled').strip()
                    link = entry.get('link', '').strip()
                    title_label = tk.Label(item_frame, text=title_text, font=HEADING_FONT, fg=FG_COLOR, bg=BG_COLOR,
                                           cursor="hand2" if link else "", justify="left", wraplength=900)
                    title_label.pack(anchor="w")
                    if link:
                        title_label.bind("<Button-1>", lambda e, url=link: webbrowser.open(url))
                        title_label.bind("<Enter>", lambda e: e.widget.config(fg="#00FF88"))
                        title_label.bind("<Leave>", lambda e: e.widget.config(fg=FG_COLOR))
                    summary_text = entry.get('summary', '').strip()
                    if summary_text:
                        sum_label = tk.Label(item_frame, text=summary_text, font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR,
                                             justify="left", wraplength=900)
                        sum_label.pack(anchor="w", pady=(6, 0))
                    pub = entry.get('published', 'No date')
                    date_label = tk.Label(item_frame, text=pub, font=("Consolas", 9), fg=GRAY_COLOR, bg=BG_COLOR)
                    date_label.pack(anchor="w", pady=(6, 0))
                    ttk.Separator(item_frame, orient="horizontal").pack(fill="x", pady=15)
            news_canvas.configure(scrollregion=news_canvas.bbox("all"))
        root.after(0, update_ui)
    threading.Thread(target=fetch_and_display, daemon=True).start()
# Metals Skin UI
metals_frame = tk.Frame(root, bg=BG_COLOR)
metals_top_frame = tk.Frame(metals_frame, bg=BG_COLOR)
metals_top_frame.pack(fill="x", pady=20)
tk.Label(metals_top_frame, text="Live Spot Prices (≈ APMEX)", font=TITLE_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=30)
metals_refresh_btn = tk.Button(metals_top_frame, text="Refresh", font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                               activebackground="#004400", relief="flat", command=lambda: refresh_prices())
metals_refresh_btn.pack(side="right", padx=30)
metals_updated_label = tk.Label(metals_top_frame, text="Last updated: Never", font=TEXT_FONT, bg=BG_COLOR, fg=GRAY_COLOR)
metals_updated_label.pack(side="right", padx=(0, 20))
silver_frame = tk.Frame(metals_frame, bg=BG_COLOR)
silver_frame.pack(fill="x", pady=40)
tk.Label(silver_frame, text="Silver (per oz)", font=("Consolas", 28, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack()
silver_price_label = tk.Label(silver_frame, text="$--.-- USD", font=LARGE_PRICE_FONT, bg=BG_COLOR, fg=FG_COLOR)
silver_price_label.pack()
silver_change_label = tk.Label(silver_frame, text="", font=MEDIUM_PRICE_FONT, bg=BG_COLOR, fg=GRAY_COLOR)
silver_change_label.pack(pady=10)
gold_frame = tk.Frame(metals_frame, bg=BG_COLOR)
gold_frame.pack(fill="x", pady=40)
tk.Label(gold_frame, text="Gold (per oz)", font=("Consolas", 24, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack()
gold_price_label = tk.Label(gold_frame, text="$--.-- USD", font=("Consolas", 40, "bold"), bg=BG_COLOR, fg=FG_COLOR)
gold_price_label.pack()
gold_change_label = tk.Label(gold_frame, text="", font=("Consolas", 24), bg=BG_COLOR, fg=GRAY_COLOR)
gold_change_label.pack(pady=10)
apmex_button = tk.Button(metals_frame, text="View Live on APMEX", font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                         activebackground="#004400", relief="flat",
                         command=lambda: webbrowser.open("https://www.apmex.com/silver-price"))
apmex_button.pack(pady=20)
status_label = tk.Label(metals_frame, text="", font=TEXT_FONT, bg=BG_COLOR, fg=GRAY_COLOR, wraplength=800)
status_label.pack(pady=10)
def refresh_prices():
    metals_updated_label.config(text="Loading...", fg=FG_COLOR)
    status_label.config(text="")
    def fetch_and_display():
        try:
            import yfinance as yf
        except ImportError:
            def update_ui():
                metals_updated_label.config(text="Library missing", fg=ALERT_RED)
                status_label.config(text="The 'yfinance' library is not installed.\n\nTo enable Metals skin:\npip install yfinance\n\n(Other skins work without it.)", fg=ALERT_RED)
            root.after(0, update_ui)
            return
        now = datetime.now().strftime("%H:%M:%S")
        try:
            silver_ticker = yf.Ticker("SI=F")
            gold_ticker = yf.Ticker("GC=F")
            s_info = silver_ticker.info
            g_info = gold_ticker.info
            s_price = s_info.get('currentPrice') or s_info.get('regularMarketPrice') or s_info.get('previousClose') or 'N/A'
            s_change = s_info.get('regularMarketChange') or 0
            s_change_pct = s_info.get('regularMarketChangePercent') or 0
            g_price = g_info.get('currentPrice') or g_info.get('regularMarketPrice') or g_info.get('previousClose') or 'N/A'
            g_change = g_info.get('regularMarketChange') or 0
            g_change_pct = g_info.get('regularMarketChangePercent') or 0
            market_state = " (Market Closed)" if s_info.get('marketState') == 'CLOSED' else ""
            def update_ui():
                metals_updated_label.config(text=f"Last updated: {now}{market_state}", fg=GRAY_COLOR)
                if isinstance(s_price, float):
                    silver_price_label.config(text=f"${s_price:.2f} USD")
                    change_text = f"{s_change:+.2f} ({s_change_pct:+.2f}%)"
                    change_color = POSITIVE_GREEN if s_change >= 0 else NEGATIVE_RED
                    silver_change_label.config(text=change_text, fg=change_color)
                else:
                    silver_price_label.config(text="N/A")
                    silver_change_label.config(text="Data unavailable")
                if isinstance(g_price, float):
                    gold_price_label.config(text=f"${g_price:.2f} USD")
                    g_change_text = f"{g_change:+.2f} ({g_change_pct:+.2f}%)"
                    g_change_color = POSITIVE_GREEN if g_change >= 0 else NEGATIVE_RED
                    gold_change_label.config(text=g_change_text, fg=g_change_color)
                else:
                    gold_price_label.config(text="N/A")
                    gold_change_label.config(text="Data unavailable")
                status_label.config(text="COMEX futures prices - tracks within cents of APMEX spot", fg=GRAY_COLOR)
            root.after(0, update_ui)
        except Exception as e:
            def update_ui():
                metals_updated_label.config(text="Error", fg=ALERT_RED)
                status_label.config(text=f"Failed to fetch prices:\n{str(e)}\n\nCheck internet connection.", fg=ALERT_RED)
            root.after(0, update_ui)
    threading.Thread(target=fetch_and_display, daemon=True).start()
# Weather Skin UI
weather_frame = tk.Frame(root, bg=BG_COLOR)
weather_top_frame = tk.Frame(weather_frame, bg=BG_COLOR)
weather_top_frame.pack(fill="x", pady=10)
tk.Label(weather_top_frame, text="Weather", font=TITLE_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=30)
weather_refresh_btn = tk.Button(weather_top_frame, text="Refresh", font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                                activebackground="#004400", relief="flat", command=lambda: refresh_weather())
weather_refresh_btn.pack(side="right", padx=30)
weather_updated_label = tk.Label(weather_top_frame, text="Last updated: Never", font=TEXT_FONT, bg=BG_COLOR, fg=GRAY_COLOR)
weather_updated_label.pack(side="right", padx=(0, 20))
full_forecast_btn = tk.Button(weather_top_frame, text="Full Forecast (NWS)", font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                              activebackground="#004400", relief="flat",
                              command=lambda: webbrowser.open("https://forecast.weather.gov/MapClick.php?lat=34.7304&lon=-86.5861"))
full_forecast_btn.pack(side="right", padx=20)
weather_canvas = tk.Canvas(weather_frame, bg=BG_COLOR, highlightthickness=0)
weather_scrollbar = ttk.Scrollbar(weather_frame, orient="vertical", command=weather_canvas.yview)
weather_canvas.configure(yscrollcommand=weather_scrollbar.set)
weather_scrollbar.pack(side="right", fill="y")
weather_canvas.pack(side="left", fill="both", expand=True)
weather_inner_frame = tk.Frame(weather_canvas, bg=BG_COLOR)
weather_canvas.create_window((0, 0), window=weather_inner_frame, anchor="nw")
weather_inner_frame.bind("<Configure>", lambda e: weather_canvas.configure(scrollregion=weather_canvas.bbox("all")))
# Reliable mouse wheel scrolling for Weather
weather_canvas.bind("<Enter>", lambda e: weather_canvas.focus_set())
weather_canvas.bind("<MouseWheel>", lambda event: weather_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
WEATHER_CODES = {
    0: "Clear sky ☀️",
    1: "Mainly clear 🌤️",
    2: "Partly cloudy ⛅",
    3: "Overcast ☁️",
    45: "Fog 🌫️",
    48: "Rime fog 🌫️",
    51: "Light drizzle 🌦️",
    53: "Drizzle 🌦️",
    55: "Heavy drizzle 🌦️",
    61: "Light rain 🌧️",
    63: "Rain 🌧️",
    65: "Heavy rain 🌧️",
    71: "Light snow ❄️",
    73: "Snow ❄️",
    75: "Heavy snow ❄️",
    80: "Light showers 🌦️",
    81: "Showers 🌦️",
    82: "Heavy showers 🌦️",
    95: "Thunderstorm ⛈️",
    96: "Thunderstorm w/ hail ⛈️",
    99: "Heavy thunderstorm w/ hail ⛈️",
}
def get_weather_desc(code):
    return WEATHER_CODES.get(code, f"Unknown ({code})")
def refresh_weather():
    weather_updated_label.config(text="Loading...", fg=FG_COLOR)
    for child in weather_inner_frame.winfo_children():
        child.destroy()
    def fetch_and_display():
        try:
            import requests
        except ImportError:
            def update_ui():
                weather_updated_label.config(text="Library missing", fg=ALERT_RED)
                error_label = tk.Label(weather_inner_frame,
                                       text="The 'requests' library is not installed.\n\nTo enable Weather skin:\npip install requests\n\n(Other skins work without it.)",
                                       font=TEXT_FONT, fg=ALERT_RED, bg=BG_COLOR, justify="left")
                error_label.pack(pady=100, padx=50)
                weather_canvas.configure(scrollregion=weather_canvas.bbox("all"))
            root.after(0, update_ui)
            return
        now = datetime.now().strftime("%H:%M:%S")
        try:
            params = {
                "latitude": 34.73,
                "longitude": -86.59,
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
                "hourly": "temperature_2m,weather_code",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "precipitation_unit": "inch",
                "timezone": "America/Chicago",
                "forecast_days": 7
            }
            url = "https://api.open-meteo.com/v1/forecast"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            current = data["current"]
            hourly = data["hourly"]
            daily = data["daily"]
            def update_ui():
                weather_updated_label.config(text=f"Last updated: {now}", fg=GRAY_COLOR)
                curr_temp = current["temperature_2m"]
                curr_desc = get_weather_desc(current["weather_code"])
                temp_label = tk.Label(weather_inner_frame, text=f"{curr_temp:.0f}°F", font=LARGE_PRICE_FONT, fg=FG_COLOR, bg=BG_COLOR)
                temp_label.pack(pady=20)
                desc_label = tk.Label(weather_inner_frame, text=curr_desc, font=HEADING_FONT, fg=FG_COLOR, bg=BG_COLOR)
                desc_label.pack(pady=10)
                details_frame = tk.Frame(weather_inner_frame, bg=BG_COLOR)
                details_frame.pack(pady=20)
                tk.Label(details_frame, text=f"Feels like: {current['apparent_temperature']:.0f}°F", font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR).pack(anchor="w")
                tk.Label(details_frame, text=f"Humidity: {current['relative_humidity_2m']}%", font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR).pack(anchor="w")
                tk.Label(details_frame, text=f"Wind: {current['wind_speed_10m']:.0f} mph", font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR).pack(anchor="w")
                tk.Label(details_frame, text=f"Precip (recent): {current['precipitation']:.2f}\"", font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR).pack(anchor="w")
                ttk.Separator(weather_inner_frame, orient="horizontal").pack(fill="x", pady=30, padx=50)
                tk.Label(weather_inner_frame, text="Next 12 Hours", font=HEADING_FONT, fg=FG_COLOR, bg=BG_COLOR).pack(anchor="w", padx=50)
                for i in range(min(12, len(hourly["time"]))):
                    t = datetime.fromisoformat(hourly["time"][i])
                    hour_str = t.strftime("%-I %p")
                    temp = hourly["temperature_2m"][i]
                    desc = get_weather_desc(hourly["weather_code"][i])
                    hour_label = tk.Label(weather_inner_frame, text=f"{hour_str}: {temp:.0f}°F {desc}", font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR)
                    hour_label.pack(anchor="w", padx=70, pady=4)
                ttk.Separator(weather_inner_frame, orient="horizontal").pack(fill="x", pady=30, padx=50)
                tk.Label(weather_inner_frame, text="7-Day Forecast", font=HEADING_FONT, fg=FG_COLOR, bg=BG_COLOR).pack(anchor="w", padx=50)
                for i in range(len(daily["time"])):
                    t = datetime.fromisoformat(daily["time"][i])
                    day_str = t.strftime("%A %b %d")
                    high = daily["temperature_2m_max"][i]
                    low = daily["temperature_2m_min"][i]
                    precip = daily["precipitation_sum"][i]
                    desc = get_weather_desc(daily["weather_code"][i])
                    day_label = tk.Label(weather_inner_frame, text=f"{day_str}: High {high:.0f}° Low {low:.0f}° Precip {precip:.2f}\" {desc}",
                                         font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR)
                    day_label.pack(anchor="w", padx=70, pady=6)
                weather_canvas.configure(scrollregion=weather_canvas.bbox("all"))
            root.after(0, update_ui)
        except Exception as e:
            def update_ui():
                weather_updated_label.config(text="Error", fg=ALERT_RED)
                error_label = tk.Label(weather_inner_frame, text=f"Failed to load weather:\n{str(e)}\n\nCheck internet and refresh.",
                                       font=TEXT_FONT, fg=ALERT_RED, bg=BG_COLOR, justify="left", wraplength=800)
                error_label.pack(pady=100, padx=50)
                weather_canvas.configure(scrollregion=weather_canvas.bbox("all"))
            root.after(0, update_ui)
    threading.Thread(target=fetch_and_display, daemon=True).start()
# Break Time Skin UI - with YouTube and X
break_frame = tk.Frame(root, bg=BG_COLOR)
break_center = tk.Frame(break_frame, bg=BG_COLOR)
break_center.pack(expand=True)
tk.Label(break_center, text="Break Time - Quick Links", font=TITLE_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(pady=30)
grok_button = tk.Button(break_center, text="Grok Imagine", font=BIG_BUTTON_FONT, width=20, height=2,
                        bg=ACCENT_COLOR, fg=FG_COLOR, activebackground="#004400", relief="flat",
                        command=lambda: webbrowser.open("https://grok.com/imagine"))
grok_button.pack(pady=10)
chatgpt_button = tk.Button(break_center, text="ChatGPT Images", font=BIG_BUTTON_FONT, width=20, height=2,
                           bg=ACCENT_COLOR, fg=FG_COLOR, activebackground="#004400", relief="flat",
                           command=lambda: webbrowser.open("https://chatgpt.com/images"))
chatgpt_button.pack(pady=10)
youtube_button = tk.Button(break_center, text="YouTube", font=BIG_BUTTON_FONT, width=20, height=2,
                           bg=ACCENT_COLOR, fg=FG_COLOR, activebackground="#004400", relief="flat",
                           command=lambda: webbrowser.open("https://www.youtube.com"))
youtube_button.pack(pady=10)
x_button = tk.Button(break_center, text="X", font=BIG_BUTTON_FONT, width=20, height=2,
                     bg=ACCENT_COLOR, fg=FG_COLOR, activebackground="#004400", relief="flat",
                     command=lambda: webbrowser.open("https://x.com"))
x_button.pack(pady=10)
tk.Label(break_center, text="Opens in your default browser • Chill, create, or scroll", font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR).pack(pady=30)
# Rocket Launches Skin UI
launches_frame = tk.Frame(root, bg=BG_COLOR)
launches_top_frame = tk.Frame(launches_frame, bg=BG_COLOR)
launches_top_frame.pack(fill="x", pady=10)
tk.Label(launches_top_frame, text="Upcoming Rocket Launches", font=TITLE_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=30)
launches_refresh_btn = tk.Button(launches_top_frame, text="Refresh", font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                                 activebackground="#004400", relief="flat", command=lambda: refresh_launches())
launches_refresh_btn.pack(side="right", padx=30)
more_launches_btn = tk.Button(launches_top_frame, text="More Details", font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                              activebackground="#004400", relief="flat",
                              command=lambda: webbrowser.open("https://www.spacex.com/launches"))
more_launches_btn.pack(side="right", padx=10)
launches_updated_label = tk.Label(launches_top_frame, text="Last updated: Never", font=TEXT_FONT, bg=BG_COLOR, fg=GRAY_COLOR)
launches_updated_label.pack(side="right", padx=(0, 20))
launches_canvas = tk.Canvas(launches_frame, bg=BG_COLOR, highlightthickness=0)
launches_scrollbar = ttk.Scrollbar(launches_frame, orient="vertical", command=launches_canvas.yview)
launches_canvas.configure(yscrollcommand=launches_scrollbar.set)
launches_scrollbar.pack(side="right", fill="y")
launches_canvas.pack(side="left", fill="both", expand=True)
launches_inner_frame = tk.Frame(launches_canvas, bg=BG_COLOR)
launches_canvas.create_window((0, 0), window=launches_inner_frame, anchor="nw")
launches_inner_frame.bind("<Configure>", lambda e: launches_canvas.configure(scrollregion=launches_canvas.bbox("all")))
# Reliable mouse wheel scrolling for Launches
launches_canvas.bind("<Enter>", lambda e: launches_canvas.focus_set())
launches_canvas.bind("<MouseWheel>", lambda event: launches_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
def refresh_launches():
    launches_updated_label.config(text="Loading...", fg=FG_COLOR)
    for child in launches_inner_frame.winfo_children():
        child.destroy()
    def fetch_and_display():
        now = datetime.now().strftime("%H:%M:%S")
        try:
            url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/"
            params = {"limit": 20}
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            launches = data.get("results", [])
            def update_ui():
                launches_updated_label.config(text=f"Last updated: {now}", fg=GRAY_COLOR)
                if not launches:
                    no_launches_label = tk.Label(launches_inner_frame, text="No upcoming launches found.\nTry refreshing later.",
                                                 font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR)
                    no_launches_label.pack(pady=50)
                else:
                    for launch in launches:
                        item_frame = tk.Frame(launches_inner_frame, bg=BG_COLOR)
                        item_frame.pack(fill="x", padx=40, pady=16, anchor="w")
                        name = launch.get("name", "Unknown Mission")
                        title_label = tk.Label(item_frame, text=name, font=HEADING_FONT, fg=FG_COLOR, bg=BG_COLOR, justify="left")
                        title_label.pack(anchor="w")
                        net = launch.get("net")
                        if net:
                            net_dt = datetime.fromisoformat(net.replace("Z", "+00:00"))
                            local_dt = net_dt.astimezone()
                            time_str = local_dt.strftime("%a, %b %d, %Y %I:%M %p %Z")
                            time_label = tk.Label(item_frame, text=f"Scheduled: {time_str}", font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR)
                            time_label.pack(anchor="w")
                            now_utc = datetime.now(timezone.utc)
                            delta = net_dt - now_utc
                            if delta.total_seconds() > 0:
                                days = delta.days
                                hours, rem = divmod(delta.seconds, 3600)
                                minutes = rem // 60
                                countdown_str = f"T-{days}d {hours:02}h {minutes:02}m"
                                countdown_color = POSITIVE_GREEN if days > 7 else ALERT_ORANGE if days > 1 else ALERT_RED
                                countdown_label = tk.Label(item_frame, text=countdown_str, font=MEDIUM_PRICE_FONT, fg=countdown_color, bg=BG_COLOR)
                                countdown_label.pack(anchor="w", pady=(4, 0))
                            else:
                                past_label = tk.Label(item_frame, text="Launch window passed or ongoing", font=TEXT_FONT, fg=ALERT_ORANGE, bg=BG_COLOR)
                                past_label.pack(anchor="w")
                        rocket = launch["rocket"]["configuration"].get("full_name", "Unknown Rocket")
                        location = launch["pad"]["location"].get("name", "Unknown Location")
                        status = launch["status"].get("abbrev", "TBD")
                        info_str = f"{rocket} • {location} • Status: {status}"
                        info_label = tk.Label(item_frame, text=info_str, font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR)
                        info_label.pack(anchor="w", pady=(4, 0))
                        mission = launch.get("mission")
                        if mission and mission.get("description"):
                            desc = mission["description"]
                            desc_label = tk.Label(item_frame, text=desc, font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR, wraplength=900, justify="left")
                            desc_label.pack(anchor="w", pady=(8, 0))
                        vid_url = None
                        if launch.get("vid_urls") and launch["vid_urls"]:
                            vid_url = launch["vid_urls"][0].get("url")
                        if vid_url:
                            live_label = tk.Label(item_frame, text="Watch Livestream →", font=BUTTON_FONT, fg="#00FF88", bg=BG_COLOR, cursor="hand2")
                            live_label.pack(anchor="w", pady=8)
                            live_label.bind("<Button-1>", lambda e, u=vid_url: webbrowser.open(u))
                            live_label.bind("<Enter>", lambda e: e.widget.config(fg=POSITIVE_GREEN))
                            live_label.bind("<Leave>", lambda e: e.widget.config(fg="#00FF88"))
                        ttk.Separator(item_frame, orient="horizontal").pack(fill="x", pady=20)
                launches_canvas.configure(scrollregion=launches_canvas.bbox("all"))
            root.after(0, update_ui)
        except Exception as e:
            def update_ui():
                launches_updated_label.config(text="Error", fg=ALERT_RED)
                error_label = tk.Label(launches_inner_frame, text=f"Failed to load launches:\n{str(e)}\n\nCheck internet and refresh.",
                                       font=TEXT_FONT, fg=ALERT_RED, bg=BG_COLOR, justify="left", wraplength=800)
                error_label.pack(pady=100, padx=50)
                launches_canvas.configure(scrollregion=launches_canvas.bbox("all"))
            root.after(0, update_ui)
    threading.Thread(target=fetch_and_display, daemon=True).start()
# Podcasts Skin UI
podcasts_frame = tk.Frame(root, bg=BG_COLOR)
podcasts_top_frame = tk.Frame(podcasts_frame, bg=BG_COLOR)
podcasts_top_frame.pack(fill="x", pady=10)
tk.Label(podcasts_top_frame, text="Favorite Podcasts", font=TITLE_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=30)
podcasts_refresh_btn = tk.Button(podcasts_top_frame, text="Refresh", font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                                 activebackground="#004400", relief="flat", command=lambda: refresh_podcasts())
podcasts_refresh_btn.pack(side="right", padx=30)
podcasts_updated_label = tk.Label(podcasts_top_frame, text="Last updated: Never", font=TEXT_FONT, bg=BG_COLOR, fg=GRAY_COLOR)
podcasts_updated_label.pack(side="right", padx=(0, 20))
podcasts_canvas = tk.Canvas(podcasts_frame, bg=BG_COLOR, highlightthickness=0)
podcasts_scrollbar = ttk.Scrollbar(podcasts_frame, orient="vertical", command=podcasts_canvas.yview)
podcasts_canvas.configure(yscrollcommand=podcasts_scrollbar.set)
podcasts_scrollbar.pack(side="right", fill="y")
podcasts_canvas.pack(side="left", fill="both", expand=True)
podcasts_inner_frame = tk.Frame(podcasts_canvas, bg=BG_COLOR)
podcasts_canvas.create_window((0, 0), window=podcasts_inner_frame, anchor="nw")
podcasts_inner_frame.bind("<Configure>", lambda e: podcasts_canvas.configure(scrollregion=podcasts_canvas.bbox("all")))
# Reliable mouse wheel scrolling for Podcasts
podcasts_canvas.bind("<Enter>", lambda e: podcasts_canvas.focus_set())
podcasts_canvas.bind("<MouseWheel>", lambda event: podcasts_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
PODCAST_FEEDS = {
    "The Joe Rogan Experience": "https://feeds.megaphone.fm/GLT1412515089",
    "MrBallen Podcast": "https://feeds.simplecast.com/dloY8UYJ"
}
def refresh_podcasts():
    podcasts_updated_label.config(text="Loading...", fg=FG_COLOR)
    for child in podcasts_inner_frame.winfo_children():
        child.destroy()
    def fetch_and_display():
        now = datetime.now().strftime("%H:%M:%S")
        all_episodes = []
        try:
            import feedparser
        except ImportError:
            def update_ui():
                podcasts_updated_label.config(text="Library missing", fg=ALERT_RED)
                error_label = tk.Label(podcasts_inner_frame, text="feedparser not installed (pip install feedparser)", font=TEXT_FONT, fg=ALERT_RED, bg=BG_COLOR)
                error_label.pack(pady=100)
                podcasts_canvas.configure(scrollregion=podcasts_canvas.bbox("all"))
            root.after(0, update_ui)
            return
        for show_name, feed_url in PODCAST_FEEDS.items():
            feed = feedparser.parse(feed_url)
            if hasattr(feed, 'bozo_exception') or (hasattr(feed, 'bozo') and feed.bozo):
                continue # Skip bad feeds silently
            for entry in feed.entries[:10]:
                all_episodes.append((show_name, entry))
        # Sort all episodes by publish date (newest first)
        all_episodes.sort(key=lambda x: x[1].get('published_parsed', (0,)), reverse=True)
        def update_ui():
            podcasts_updated_label.config(text=f"Last updated: {now}", fg=GRAY_COLOR)
            if not all_episodes:
                no_ep_label = tk.Label(podcasts_inner_frame, text="No episodes loaded – check connection/feeds.", font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR)
                no_ep_label.pack(pady=50)
            else:
                current_show = None
                for show_name, entry in all_episodes:
                    if show_name != current_show:
                        current_show = show_name
                        show_label = tk.Label(podcasts_inner_frame, text=show_name, font=("Consolas", 14, "bold"), fg=POSITIVE_GREEN, bg=BG_COLOR)
                        show_label.pack(anchor="w", padx=40, pady=(20, 8))
                        ttk.Separator(podcasts_inner_frame, orient="horizontal").pack(fill="x", padx=40, pady=(0, 10))
                    item_frame = tk.Frame(podcasts_inner_frame, bg=BG_COLOR)
                    item_frame.pack(fill="x", padx=50, pady=8, anchor="w")
                    title = entry.get('title', 'No title')
                    link = entry.get('link', '')
                    title_label = tk.Label(item_frame, text=title, font=HEADING_FONT, fg=FG_COLOR, bg=BG_COLOR,
                                           cursor="hand2" if link else "", justify="left", wraplength=850)
                    title_label.pack(anchor="w")
                    if link:
                        title_label.bind("<Button-1>", lambda e, url=link: webbrowser.open(url))
                        title_label.bind("<Enter>", lambda e: e.widget.config(fg=POSITIVE_GREEN))
                        title_label.bind("<Leave>", lambda e: e.widget.config(fg=FG_COLOR))
                    pub = entry.get('published', 'No date')
                    date_label = tk.Label(item_frame, text=pub, font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR)
                    date_label.pack(anchor="w", pady=(2, 0))
                    summary = entry.get('summary', '').strip()
                    if summary:
                        sum_label = tk.Label(item_frame, text=summary[:300] + ("..." if len(summary) > 300 else ""),
                                             font=TEXT_FONT, fg=GRAY_COLOR, bg=BG_COLOR, wraplength=850, justify="left")
                        sum_label.pack(anchor="w", pady=(6, 0))
                    ttk.Separator(item_frame, orient="horizontal").pack(fill="x", pady=12)
            podcasts_canvas.configure(scrollregion=podcasts_canvas.bbox("all"))
        root.after(0, update_ui)
    threading.Thread(target=fetch_and_display, daemon=True).start()
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
    if media_channel:
        media_channel.stop()
    if AUDIO_AVAILABLE:
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
        controls.columnconfigure(1, weight=1)
        sound_label = tk.Label(controls, text="Sound:", width=14, anchor="e", bg=BG_COLOR, fg=FG_COLOR, font=TEXT_FONT)
        sound_label.grid(row=0, column=0, sticky="e")
        self.sound_combo = ttk.Combobox(controls, values=display_names, state="readonly", width=26, font=TEXT_FONT)
        self.sound_combo.grid(row=0, column=1, padx=(8, 12), sticky="ew")
        self.sound_combo.set(display_names[0])
        interval_label = tk.Label(controls, text="Interval (min):", width=15, anchor="e", bg=BG_COLOR, fg=FG_COLOR, font=TEXT_FONT)
        interval_label.grid(row=1, column=0, sticky="e")
        self.interval_spin = tk.Spinbox(controls, from_=1, to=60, width=10, font=TEXT_FONT,
                                       bg=BG_COLOR, fg=FG_COLOR, buttonbackground=ACCENT_COLOR,
                                       insertbackground=FG_COLOR, selectbackground=ACCENT_COLOR,
                                       relief="flat")
        self.interval_spin.grid(row=1, column=1, padx=(8, 12), sticky="w")
        self.interval_spin.delete(0, "end")
        self.interval_spin.insert(0, default_min)
        self.play_button = tk.Button(controls, text="Play", command=self.test_beep, width=10,
                                     font=BUTTON_FONT, bg=ACCENT_COLOR, fg=FG_COLOR,
                                     activebackground="#004400", relief="flat")
        self.play_button.grid(row=0, column=2, rowspan=2, padx=(8, 0), pady=2, sticky="e")
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
        if not AUDIO_AVAILABLE:
            return False
        full_file = display_to_full.get(display_name)
        if not full_file:
            return False
        full_path = full_file
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
timer1 = BeepTimer(matrix_content, "Timer 1 (Short)", default_min=5)
timer1_frame = timer1.frame
sep = ttk.Separator(matrix_content, orient="horizontal")
timer2 = BeepTimer(matrix_content, "Timer 2 (Long)", default_min=30)
timer2_frame = timer2.frame
# Media Player section
media_frame = tk.Frame(matrix_content, bg=BG_COLOR)
tk.Label(media_frame, text="Media Player (Chill Mode)", font=HEADING_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(anchor="w", pady=(0, 8))
media_controls = tk.Frame(media_frame, bg=BG_COLOR)
media_controls.pack(fill="x", pady=5)
media_controls.columnconfigure(1, weight=1)
tk.Label(media_controls, text="Track:", width=14, anchor="e", bg=BG_COLOR, fg=FG_COLOR, font=TEXT_FONT).grid(row=0, column=0, sticky="e")
if not media_available:
    media_display_names = ["No media files - add to 'media' folder"]
media_combo = ttk.Combobox(media_controls, values=media_display_names, state="readonly", width=28, font=TEXT_FONT)
media_combo.grid(row=0, column=1, padx=(8, 10), sticky="ew")
shuffle_var = tk.BooleanVar(value=False)
shuffle_check = tk.Checkbutton(media_controls, text="Shuffle", variable=shuffle_var, bg=BG_COLOR, fg=FG_COLOR, selectcolor=ACCENT_COLOR,
                               activebackground=BG_COLOR, activeforeground=FG_COLOR)
shuffle_check.grid(row=0, column=2, padx=10)
monitor_id = None
continuous_active = False

# Corrected shuffle logic - uses a shuffled copy of the playlist and tracks current position
# This ensures true random order without immediate repeats and better distribution
shuffle_playlist = []
shuffle_index = 0

def reshuffle_playlist():
    """Create a new random order of all tracks"""
    global shuffle_playlist, shuffle_index
    if not media_display_names:
        shuffle_playlist = []
        shuffle_index = 0
        return
    shuffle_playlist = media_display_names[:]
    random.shuffle(shuffle_playlist)
    shuffle_index = 0

def get_next_shuffle_track():
    """Get the next track in the current shuffled list, reshuffle when exhausted"""
    global shuffle_index
    if not shuffle_playlist or len(shuffle_playlist) == 0:
        reshuffle_playlist()
    if not shuffle_playlist:
        return media_display_names[0] if media_display_names else None
    
    track = shuffle_playlist[shuffle_index]
    shuffle_index = (shuffle_index + 1) % len(shuffle_playlist)
    if shuffle_index == 0:
        reshuffle_playlist()  # Reshuffle for the next full cycle to keep it fresh
    return track

def play_next():
    if not AUDIO_AVAILABLE:
        current_media_label.config(text="Audio unavailable", fg="red")
        return
    if not media_available or len(media_display_names) == 0:
        current_media_label.config(text="No media files", fg="red")
        return
    media_channel.stop()
    if shuffle_var.get():
        selected = get_next_shuffle_track()
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
    if not AUDIO_AVAILABLE:
        current_media_label.config(text="Audio unavailable", fg="red")
        return
    if not media_available or len(media_display_names) == 0:
        current_media_label.config(text="No media files", fg="red")
        return
    media_channel.stop()
    stop_monitor()
    if shuffle_var.get():
        reshuffle_playlist()  # Start fresh shuffle when play is pressed with shuffle on
        selected = get_next_shuffle_track()
    else:
        selected = media_combo.get()
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
    if media_channel:
        media_channel.stop()
    continuous_active = False
    stop_monitor()
    current_media_label.config(text="Stopped", fg=GRAY_COLOR)

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
    if media_channel and media_channel.get_busy():
        monitor_id = root.after(1000, monitor_playback)
    else:
        play_next()
        monitor_id = root.after(1000, monitor_playback)

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
volume_frame = tk.Frame(media_frame, bg=BG_COLOR)
volume_frame.pack(fill="x", pady=8)
tk.Label(volume_frame, text="Media Volume:", bg=BG_COLOR, fg=FG_COLOR, font=TEXT_FONT).pack(side="left", padx=(20, 10))
volume_var = tk.IntVar(value=70)
def set_media_volume(val):
    if media_channel:
        media_channel.set_volume(int(val) / 100.0)
volume_slider = tk.Scale(volume_frame, from_=0, to=100, orient="horizontal", variable=volume_var,
                         command=set_media_volume, bg=BG_COLOR, fg=FG_COLOR, highlightbackground=BG_COLOR,
                         troughcolor="#003300", activebackground="#004400")
volume_slider.pack(side="left", fill="x", expand=True, padx=(0, 20))
current_media_label = tk.Label(media_frame, text="Not playing", font=TEXT_FONT, bg=BG_COLOR, fg=GRAY_COLOR)
current_media_label.pack(anchor="w", pady=4)
if media_available:
    media_combo.set(media_display_names[0])
else:
    media_combo.config(state="disabled")
    if media_display_names:
        media_combo.set(media_display_names[0])
volume_label = tk.Label(matrix_content, text="(Timer beeps use system volume • Media has independent control)", font=("Consolas", 9), fg=GRAY_COLOR, bg=BG_COLOR)

def pack_matrix_view():
    matrix_scrollbar.pack(side="right", fill="y")
    matrix_scroll.pack(side="left", fill="both", expand=True)
    timer1_frame.pack(fill="x", pady=8, padx=18)
    sep.pack(fill="x", pady=8, padx=28)
    timer2_frame.pack(fill="x", pady=8, padx=18)
    media_frame.pack(fill="x", pady=14, padx=18)
    volume_label.pack(pady=8)
    root.after_idle(sync_matrix_scroll_region)

top_frame.pack(fill="x", pady=5)
pack_matrix_view()
# Global hotkey bindings (case-insensitive)
root.bind("<m>", lambda e: switch_skin("Matrix"))
root.bind("<M>", lambda e: switch_skin("Matrix"))
root.bind("<g>", lambda e: switch_skin("Gallery"))
root.bind("<G>", lambda e: switch_skin("Gallery"))
root.bind("<n>", lambda e: switch_skin("Aggregator"))
root.bind("<N>", lambda e: switch_skin("Aggregator"))
root.bind("<i>", lambda e: switch_skin("Metals"))
root.bind("<I>", lambda e: switch_skin("Metals"))
root.bind("<w>", lambda e: switch_skin("Weather"))
root.bind("<W>", lambda e: switch_skin("Weather"))
root.bind("<b>", lambda e: switch_skin("Break Time"))
root.bind("<B>", lambda e: switch_skin("Break Time"))
root.bind("<r>", lambda e: switch_skin("Rocket Launches"))
root.bind("<R>", lambda e: switch_skin("Rocket Launches"))
root.bind("<p>", lambda e: switch_skin("Podcasts"))
root.bind("<P>", lambda e: switch_skin("Podcasts"))
root.mainloop()
