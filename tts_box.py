import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import asyncio
import edge_tts
import pygame
import threading
import os
import time
import warnings
import glob
import tempfile
from pydub import AudioSegment

warnings.filterwarnings("ignore", category=UserWarning)

# =========================
# Helper: Cleanup Temporary Files
# =========================
def cleanup_temp_files():
    """Stops the mixer and deletes cached mp3 files from the system Temp folder."""
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
    except:
        pass
    time.sleep(0.2)
    
    temp_dir = tempfile.gettempdir()
    for pattern in ["_preview_*.mp3", "_cache_*.mp3"]:
        full_pattern = os.path.join(temp_dir, pattern)
        for f in glob.glob(full_pattern):
            try: os.remove(f)
            except: pass

# =========================
# Multi-language UI Configuration (Updated with Icons)
# =========================
LANG_CONFIG = {
    "Chinese": {
        "voice": "zh-CN-XiaoxiaoNeural",
        "lang_lbl": "选择语言:", 
        "title": "朗读盒子", "input": "贴上文字 (每行一段)", "pause": "暂停 (秒)",
        "save": "💾", "view": "▶", "pst": "Ⅱ", "stp": "■", "ext": "Exit", "done": "完成！", "cfm": "确定离开？"
    },
    "English (UK)": {
        "voice": "en-GB-SoniaNeural",
        "lang_lbl": "Select Language:",
        "title": "TTS Box (UK)", "input": "Paste Text (One per line)", "pause": "Pause (s)",
        "save": "💾", "view": "▶", "pst": "Ⅱ", "stp": "■", "ext": "Exit", "done": "Done!", "cfm": "Exit now?"
    },
    "Japanese": {
        "voice": "ja-JP-NanamiNeural", 
        "lang_lbl": "言語を選択:",
        "title": "読み上げボックス", "input": "テキストを貼り付け", "pause": "一時停止",
        "save": "💾", "view": "▶", "pst": "Ⅱ", "stp": "■", "ext": "Exit", "done": "完了！", "cfm": "終了しますか？"
    },
    "Malay": {
        "voice": "ms-MY-YasminNeural",
        "lang_lbl": "Pilih Bahasa:",
        "title": "Kotak TTS", "input": "Tampal Teks", "pause": "Jeda (s)",
        "save": "💾", "view": "▶", "pst": "Ⅱ", "stp": "■", "ext": "Exit", "done": "Siap!", "cfm": "Keluar sekarang?"
    },
    "Korean": {
        "voice": "ko-KR-SunHiNeural",
        "lang_lbl": "언어 선택:",
        "title": "음성 변환기", "input": "텍스트 붙여넣기", "pause": "일시 정지",
        "save": "💾", "view": "▶", "pst": "Ⅱ", "stp": "■", "ext": "Exit", "done": "완료!", "cfm": "종료하시겠습니까?"
    },
    "Thai": {
        "voice": "th-TH-PremwadeeNeural", 
        "lang_lbl": "เลือกภาษา:",
        "title": "กล่องอ่านออกเสียง", "input": "วางข้อความ", "pause": "หยุดชั่วคราว",
        "save": "💾", "view": "▶", "pst": "Ⅱ", "stp": "■", "ext": "Exit", "done": "สำเร็จ!", "cfm": "ยืนยันการออก?"
    },
    "Vietnamese": {
        "voice": "vi-VN-HoaiMyNeural",
        "lang_lbl": "Chọn ngôn ngữ:",
        "title": "Hộp Đọc Văn Bản", "input": "Dán văn bản", "pause": "Tạm dừng",
        "save": "💾", "view": "▶", "pst": "Ⅱ", "stp": "■", "ext": "Exit", "done": "Xong!", "cfm": "Bạn có muốn thoát?"
    },
    "Tamil": {
        "voice": "ta-IN-PallaviNeural",
        "lang_lbl": "மொழியைத் தேர்ந்தெடுக்கவும்:",
        "title": "உரை பெட்டி", "input": "உரையை ஒட்டவும்", "pause": "இடைநிறுத்தம்",
        "save": "💾", "view": "▶", "pst": "Ⅱ", "stp": "■", "ext": "Exit", "done": "முடிந்தது!", "cfm": "வெளியேறவா?"
    }
}

pygame.mixer.init()
cleanup_temp_files()

# =========================
# Core Logic
# =========================
async def perform_audio_synthesis(text_lines, pause_duration, final_path, p_bar, s_text):
    fragments = []
    line_count = len(text_lines)
    selected_voice = LANG_CONFIG[ui_language_var.get()]["voice"]
    temp_dir = tempfile.gettempdir()
    
    try:
        master_track = AudioSegment.empty()
        silence_gap = AudioSegment.silent(duration=int(pause_duration * 1000))
        
        for index, content in enumerate(text_lines):
            stripped_text = content.strip()
            if not stripped_text: continue
            s_text.set("Wait...")
            p_bar.set(((index + 1) / line_count) * 70)
            app_window.update_idletasks()
            
            temp_file = os.path.join(temp_dir, f"_cache_{int(time.time()*1000)}_{index}.mp3")
            communicate = edge_tts.Communicate(stripped_text, selected_voice)
            await communicate.save(temp_file)
            fragments.append(temp_file)
            
        for index, file_path in enumerate(fragments):
            master_track += AudioSegment.from_mp3(file_path)
            if index < len(fragments) - 1: 
                master_track += silence_gap
            p_bar.set(70 + ((index + 1) / len(fragments)) * 30)
            app_window.update_idletasks()
            
        master_track.export(final_path, format="mp3")
        s_text.set(LANG_CONFIG[ui_language_var.get()]["done"])
    except Exception as e:
        s_text.set("Error")
        messagebox.showerror("Error", f"Failed: {str(e)}")
    finally:
        for path in fragments:
            if os.path.exists(path):
                try: os.remove(path)
                except: pass

def start_process_thread(mode="export"):
    raw_input = main_text_box.get("1.0", tk.END).strip()
    if not raw_input: return
    try: pause_val = float(pause_entry.get())
    except: pause_val = 1.0
    valid_lines = [line for line in raw_input.splitlines() if line.strip()]
    
    if mode == "export":
        save_path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3", "*.mp3")])
        if save_path: 
            threading.Thread(target=lambda: asyncio.run(perform_audio_synthesis(valid_lines, pause_val, save_path, progress_var, status_var)), daemon=True).start()
    else:
        def preview_task():
            cleanup_temp_files()
            preview_file = os.path.join(tempfile.gettempdir(), f"_preview_{int(time.time())}.mp3")
            asyncio.run(perform_audio_synthesis(valid_lines, pause_val, preview_file, progress_var, status_var))
            if os.path.exists(preview_file):
                pygame.mixer.music.load(preview_file)
                pygame.mixer.music.play()
        threading.Thread(target=preview_task, daemon=True).start()

# =========================
# UI Layout
# =========================
app_window = tk.Tk()
app_window.geometry("850x650")
app_window.configure(bg="#f8f9fa")

# Try to load your icon
try: app_window.iconbitmap("app.ico")
except: pass

ui_language_var = tk.StringVar(value="Chinese")
progress_var = tk.DoubleVar(value=0)
status_var = tk.StringVar(value="")

def update_ui_language(*args):
    config = LANG_CONFIG[ui_language_var.get()]
    app_window.title(config["title"])
    lbl_language_select.config(text=config["lang_lbl"])
    lbl_input_hint.config(text=config["input"])
    lbl_pause_hint.config(text=config["pause"])
    btn_save.config(text=config["save"])
    btn_preview.config(text=config["view"])
    btn_pause.config(text=config["pst"])
    btn_stop.config(text=config["stp"])
    btn_exit.config(text=config["ext"])
    status_var.set("Ready")

header_frame = tk.Frame(app_window, bg="#f8f9fa")
header_frame.pack(fill="x", padx=10, pady=5)
lbl_language_select = tk.Label(header_frame, bg="#f8f9fa", font=("Arial", 9))
lbl_language_select.pack(side="left")
tk.OptionMenu(header_frame, ui_language_var, *LANG_CONFIG.keys()).pack(side="left", padx=5)
lbl_input_hint = tk.Label(header_frame, bg="#f8f9fa", font=("Arial", 10, "bold"))
lbl_input_hint.pack(side="left", padx=10)

action_frame = tk.Frame(app_window, bg="#f8f9fa")
action_frame.pack(side="bottom", fill="x", padx=10, pady=15)
for i in range(5): action_frame.columnconfigure(i, weight=1)
# Increased font size for icons
BTN_STYLE = {"font": ("Segoe UI Symbol", 16, "bold"), "relief": "flat", "pady": 12, "fg": "white"}

btn_save = tk.Button(action_frame, bg="#28a745", **BTN_STYLE, command=lambda: start_process_thread("export"))
btn_save.grid(row=0, column=0, padx=3, sticky="nsew")
btn_preview = tk.Button(action_frame, bg="#007bff", **BTN_STYLE, command=lambda: start_process_thread("preview"))
btn_preview.grid(row=0, column=1, padx=3, sticky="nsew")
btn_pause = tk.Button(action_frame, bg="#fd7e14", **BTN_STYLE, command=lambda: pygame.mixer.music.pause() if pygame.mixer.music.get_busy() else pygame.mixer.music.unpause())
btn_pause.grid(row=0, column=2, padx=3, sticky="nsew")
btn_stop = tk.Button(action_frame, bg="#dc3545", **BTN_STYLE, command=lambda: pygame.mixer.music.stop())
btn_stop.grid(row=0, column=3, padx=3, sticky="nsew")

def handle_exit():
    if messagebox.askyesno("Exit", LANG_CONFIG[ui_language_var.get()]["cfm"]):
        cleanup_temp_files()
        app_window.destroy()
btn_exit = tk.Button(action_frame, bg="#6c757d", **BTN_STYLE, command=handle_exit)
btn_exit.grid(row=0, column=4, padx=3, sticky="nsew")

status_frame = tk.Frame(app_window, bg="#f8f9fa")
status_frame.pack(side="bottom", fill="x", padx=20)
ttk.Progressbar(status_frame, variable=progress_var, maximum=100).pack(fill="x")
tk.Label(status_frame, textvariable=status_var, bg="#f8f9fa", font=("Arial", 9)).pack()

config_frame = tk.Frame(app_window, bg="#f8f9fa")
config_frame.pack(side="bottom", pady=5)
lbl_pause_hint = tk.Label(config_frame, bg="#f8f9fa")
lbl_pause_hint.pack(side="left")
pause_entry = tk.Entry(config_frame, width=5, font=("Arial", 12), justify="center")
pause_entry.insert(0, "1.0")
pause_entry.pack(side="left", padx=5)

text_frame = tk.Frame(app_window)
text_frame.pack(fill="both", expand=True, padx=10, pady=5)
main_text_box = tk.Text(text_frame, font=("Arial", 14), relief="flat")
main_text_box.pack(side="left", fill="both", expand=True)
scrollbar = tk.Scrollbar(text_frame, command=main_text_box.yview)
scrollbar.pack(side="right", fill="y")
main_text_box.config(yscrollcommand=scrollbar.set)

app_window.protocol("WM_DELETE_WINDOW", handle_exit)
ui_language_var.trace_add("write", update_ui_language)
update_ui_language()
app_window.mainloop()