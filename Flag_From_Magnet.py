#"C:\Users\GANESH\Downloads\pedo catcher proposal+ code\Pedo_cather_code\CSAMdetector&Iptracker\Flag_From_Magnet.py"
import os
import re
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import imagehash
import cv2
import fitz  # PyMuPDF-planned pdf support
import shutil
import subprocess
import qbittorrentapi
import numpy as np
from PIL import Image
import tensorflow as tf
import tensorflow_hub

os.makedirs(os.path.join(os.path.dirname(__file__), "saved_downloads"), exist_ok=True)



def delete_torrent_and_files(torrent):
    try:
        client.torrents_delete(delete_files=True, torrent_hashes=torrent.hash)
        safe_insert("🗑️ Deleted torrent and files.\n")
    except Exception as e:
        safe_insert(f"⚠️ Failed to delete files: {e}\n")

def move_or_copy_files(torrent, folder):
    saved_dir = os.path.join(os.path.dirname(__file__), "saved_downloads", torrent.name)
    try:
        os.makedirs(saved_dir, exist_ok=True)
        for root_dir, _, files in os.walk(folder):
            for file in files:
                src = os.path.join(root_dir, file)
                dst = os.path.join(saved_dir, file)
                if keep_files_var.get() == "keep":
                    shutil.copy2(src, dst)
                else:
                    shutil.move(src, dst)
        safe_insert(f"📁 Files {'copied' if keep_files_var.get() == 'keep' else 'moved'} to: {saved_dir}\n")
    except Exception as e:
        safe_insert(f"⚠️ Failed to save files: {e}\n")


def slice_video_to_frames(video_path, output_dir, interval_sec=25, start_time_sec=5):
    os.makedirs(output_dir, exist_ok=True)
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Convert start time and interval into frame counts
    start_frame = int(fps * start_time_sec)
    frame_interval = int(fps * interval_sec)

    current_frame = 0
    saved_count = 0

    while True:
        success, frame = vidcap.read()
        if not success:
            break

        if current_frame >= start_frame and (current_frame - start_frame) % frame_interval == 0:
            frame_path = os.path.join(output_dir, f"{os.path.basename(video_path)}_frame{saved_count:03}.jpg")
            cv2.imwrite(frame_path, frame)
            saved_count += 1

        current_frame += 1
        if current_frame >= total_frames:
            break

    vidcap.release()
    return saved_count

# === Load NSFW Detection Model ===

try:
    model = tf.keras.models.load_model("saved_model.h5", custom_objects={"KerasLayer": tensorflow_hub.KerasLayer})
    LABELS = ['drawings', 'hentai', 'neutral', 'porn', 'sexy']
except Exception as e:
    messagebox.showerror("Model Load Error", f"❌ Failed to load saved_model.h5:\n{e}")
    exit(1)
# === Safe insert from threads ===
def safe_insert(text):
    status_box.after(0, lambda: (
        status_box.insert(tk.END, text),
        status_box.see(tk.END)
    ))

def check_against_db(nsfw_images, db_folder):
    safe_insert("\n🔍 Checking against image database...\n")

    def collect_db_hashes(path):
        hashes = set()
        for root, _, files in os.walk(path):
            for file in files:
                if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    try:
                        img = Image.open(os.path.join(root, file)).convert("RGB").resize((224, 224))
                        h = imagehash.phash(img)
                        hashes.add(h)
                    except:
                        continue
        return hashes

    db_hashes = collect_db_hashes(db_folder)
    match_count = 0

    for img_path in nsfw_images:
        try:
            if os.path.exists(img_path):
                img = Image.open(img_path).convert("RGB").resize((224, 224))
                img_hash = imagehash.phash(img)
                if any(img_hash - h <= 4 for h in db_hashes):  # tolerance = 4
                    safe_insert(f"🟥 Match found: {os.path.basename(img_path)}\n")
                    match_count += 1
        except:
            continue

    safe_insert(f"\n✅ Result: {match_count} matches found out of {len(nsfw_images)}.\n")

# === Load Settings ===
import json

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'settings.json')

def load_qbittorrent_config():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, 'r') as f:
            data = json.load(f)
            return {
                "host": data.get("host", "http://localhost").rstrip('/'),
                "port": str(data.get("port", "8080")),
                "username": data.get("username", "admin"),
                "password": data.get("password", "adminadmin")
            }
    raise FileNotFoundError("❌ settings.json not found!")

# === qBittorrent Client Setup ===
config = load_qbittorrent_config()
if config["host"].endswith(f":{config['port']}"):
    full_host = config["host"]
else:
    if ":" in config["host"][config["host"].find("//") + 2:]:
        config["host"] = config["host"].rsplit(":", 1)[0]
    full_host = f"{config['host']}:{config['port']}"

try:
    client = qbittorrentapi.Client(
        host=full_host,
        username=config["username"],
        password=config["password"]
    )
    client.auth_log_in()
except Exception as e:
    messagebox.showerror("Connection Error", f"❌ Could not connect to qBittorrent Web UI at {full_host}\n{e}")
    exit(1)

# === GUI Setup ===
root = tk.Tk()
# Collapsible state tracker
download_settings_visible = tk.BooleanVar(value=False)
root.title("🧲 Flag from Magnet")
root.geometry("")  
root.resizable(False, False)

# === Input Section ===
input_frame = tk.LabelFrame(root, text="🎯 Magnet Link", font=("Arial", 11, "bold"), padx=10, pady=10)
input_frame.pack(fill="x", padx=15, pady=(15, 5))

magnet_entry = tk.Entry(input_frame, width=85, font=("Arial", 10))
magnet_entry.pack(pady=5)

# DB folder chooser function
def choose_db_folder():
    path = filedialog.askdirectory(title="Select Image Database Folder")
    if path:
        db_folder_path.set(path)

def toggle_download_settings():
    if download_settings_visible.get():
        options_frame.pack_forget()
        options_container.pack_forget()
        toggle_button.config(text="▶️ Download Settings")
        download_settings_visible.set(False)
    else:
        options_container.pack(fill="x", padx=15, pady=(0, 5), before=progress_frame)  # 👈 ensure it's above status
        options_frame.pack(fill="x")
        toggle_button.config(text="▼ Download Settings")
        download_settings_visible.set(True)

        
# === Collapsible Download Settings Header ===
toggle_button = tk.Button(
    root,
    text="▶️ Download Settings",
    font=("Arial", 11, "bold"),
    anchor="w",
    relief="flat",
    command=toggle_download_settings
)
toggle_button.pack(fill="x", padx=15, pady=(10, 0))

options_container = tk.Frame(root)
options_container.pack(fill="x", padx=15, pady=(0, 5))

options_frame = tk.LabelFrame(options_container, text="⚙️ Download Settings", font=("Arial", 11, "bold"), padx=10, pady=10)
# options_frame.pack(fill="x")  ← leave it commented out initially to start collapsed

file_limit_var = tk.StringVar(value="5")
video_limit_var = tk.StringVar(value="1")

# First Row: Image and Video Limits
tk.Label(options_frame, text="Number of images to download:", font=("Arial", 10)).grid(row=0, column=0, sticky="w")
file_limit_menu = ttk.Combobox(options_frame, textvariable=file_limit_var, state="readonly", values=["2", "5", "10", "All"], width=10)
file_limit_menu.grid(row=0, column=1, padx=10, pady=5)

tk.Label(options_frame, text="or videos:", font=("Arial", 10)).grid(row=0, column=2, sticky="w")
video_limit_menu = ttk.Combobox(options_frame, textvariable=video_limit_var, state="readonly", values=["1", "2", "3", "5", "20"], width=10)
video_limit_menu.grid(row=0, column=3, padx=10, pady=5)

# Second Row: Toggle button (non-media download)
download_all_var = tk.BooleanVar(value=False)
download_all_btn = tk.Checkbutton(options_frame, text="📄 Download all files (even non-media like .txt)", variable=download_all_var, font=("Arial", 10))
download_all_btn.grid(row=1, column=0, columnspan=4, sticky="w", pady=(0, 5))

# Third Row: NSFW checkbox
check_nsfw_var = tk.BooleanVar(value=True)
tk.Checkbutton(options_frame, text="🔞 Check for NSFW", variable=check_nsfw_var,
               font=("Arial", 10)).grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))

# Fourth Row: DB toggle
check_db_var = tk.BooleanVar(value=False)
tk.Checkbutton(options_frame, text="🔍 Check Against Database", variable=check_db_var, font=("Arial", 10)).grid(row=3, column=0, columnspan=2, sticky="w", pady=(5, 0))

# DB folder chooser
db_folder_path = tk.StringVar(value="")
db_folder_button = tk.Button(options_frame, text="📁 Choose Database Folder", command=choose_db_folder, font=("Arial", 10), state="disabled")
db_folder_button.grid(row=3, column=1, sticky="w", padx=5)
db_path_label = tk.Label(options_frame, textvariable=db_folder_path, font=("Arial", 9), fg="gray", anchor="w", wraplength=500)
db_path_label.grid(row=4, column=0, columnspan=1, sticky="w", padx=5, pady=(0, 0))

# Preference dropdown (after DB folder stuff)
tk.Label(options_frame, text="Preference:", font=("Arial", 10)).grid(row=6, column=0, sticky="w", pady=(3, 0))

media_preference_var = tk.StringVar(value="Images over Videos")
preference_menu = ttk.Combobox(
    options_frame,
    textvariable=media_preference_var,
    state="readonly",
    values=["Images over Videos", "Videos over Images"],
    width=22
)
preference_menu.grid(row=6, column=1, padx=10, pady=(3, 0))

# === Trace DB toggle to enable/disable folder chooser
def toggle_db_folder(*_):
    if check_db_var.get():
        db_folder_button.config(state="normal")
    else:
        db_folder_path.set("")
        db_folder_button.config(state="disabled")

check_db_var.trace_add("write", toggle_db_folder)


# Keep/Delete toggle
keep_files_var = tk.StringVar(value="keep")
tk.Radiobutton(options_frame, text="📂 Keep Files After Scan", variable=keep_files_var, value="keep", font=("Arial", 10)).grid(row=5, column=0, sticky="w", pady=(2, 0))
tk.Radiobutton(options_frame, text="🗑️ Delete After Scan", variable=keep_files_var, value="delete", font=("Arial", 10)).grid(row=5, column=1, sticky="w", pady=(2, 0))

# === Status Section ===
progress_frame = tk.LabelFrame(root, text="📊 Status & Progress", font=("Arial", 11, "bold"), padx=10, pady=10)
progress_frame.pack(fill="x", padx=15, pady=5)

progress = ttk.Progressbar(progress_frame, orient='horizontal', length=680, mode='determinate', maximum=100)
progress.pack(pady=5)

status_box = scrolledtext.ScrolledText(progress_frame, wrap=tk.WORD, height=14, width=90, font=("Consolas", 10))
status_box.pack()

# === Globals ===
current_hash = None
cancel_flag = threading.Event()
pause_var = tk.StringVar(value="⏸️ Pause")

# === Torrent Logic ===
def extract_info_hash(magnet_link):
    match = re.search(r'btih:([a-fA-F0-9]+)', magnet_link)
    return match.group(1).lower() if match else None

def run_nsfw_filter(torrent, total_files_in_torrent):
    try:
        import shutil
        import time

        folder = torrent.save_path

        # First, check for image files
        image_files = [
            os.path.join(root_dir, file)
            for root_dir, _, files in os.walk(folder)
            for file in files if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ]

        # If no image files, attempt video slicing
        if not image_files:
            video_files = [
                os.path.join(root_dir, file)
                for root_dir, _, files in os.walk(folder)
                for file in files if file.lower().endswith((".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv"))
            ]
            if video_files:
                safe_insert("📽️ No images found. Attempting to slice video(s) for NSFW scan...\n")
                time.sleep(1)  # give qBittorrent a moment to finalize file writes
                slice_dir = os.path.join(os.path.dirname(__file__), "slice_videos")

                # Clear previous sliced frames to avoid mixing
                if os.path.exists(slice_dir):
                    for f in os.listdir(slice_dir):
                        try:
                            os.remove(os.path.join(slice_dir, f))
                        except:
                            continue

                os.makedirs(slice_dir, exist_ok=True)
                image_files = []

                for video in video_files:
                    num_slices = slice_video_to_frames(video, slice_dir, interval_sec=25, start_time_sec=5)
                    safe_insert(f"  ➤ {os.path.basename(video)} → {num_slices} frame(s)\n")
                    image_files.extend([
                        os.path.join(slice_dir, f)
                        for f in os.listdir(slice_dir)
                        if f.startswith(os.path.basename(video)) and f.endswith(".jpg")
                    ])

                safe_insert(f"✅ Total frames collected: {len(image_files)}\n")

        selected_files = image_files

        if not selected_files:
            safe_insert("❌ No images or video frames found to scan.\n")
            return

        nsfw_count = 0
        nsfw_images = []

        for img_path in selected_files:
            try:
                img = Image.open(img_path).convert("RGB").resize((224, 224))
                img_array = np.expand_dims(np.array(img) / 255.0, axis=0)
                preds = model.predict(img_array)[0]
                nsfw_score = preds[1] + preds[3] + preds[4]

                safe_insert(f"\n{os.path.basename(img_path)}\n")
                for lbl, score in zip(LABELS, preds):
                    safe_insert(f"  {lbl}: {score:.2f}\n")
                safe_insert(f"{'NSFW' if nsfw_score >= 0.6 else 'SFW'} (Score: {nsfw_score:.2f})\n")

                if nsfw_score >= 0.6:
                    nsfw_count += 1
                    nsfw_images.append(img_path)

            except Exception as e:
                safe_insert(f"Error processing {os.path.basename(img_path)}: {e}\n")

        safe_insert(f"\nScanned {len(selected_files)} files, flagged {nsfw_count} as NSFW.\n")
        monitor_button.config(state="normal")

        if check_db_var.get() and db_folder_path.get():
            check_against_db(nsfw_images, db_folder_path.get())

        # === FILE CLEANUP or MOVE
        if keep_files_var.get() == "delete":
            delete_torrent_and_files(torrent)

        else:
            # Move to saved_downloads
            saved_dir = os.path.join(os.path.dirname(__file__), "saved_downloads", torrent.name)
            try:
                os.makedirs(saved_dir, exist_ok=True)
                for root_dir, _, files in os.walk(folder):
                    for file in files:
                        src = os.path.join(root_dir, file)
                        dst = os.path.join(saved_dir, file)
                        shutil.copy2(src, dst)
                safe_insert(f"📂 Files copied to: {saved_dir}\n")
            except Exception as e:
                safe_insert(f"⚠️ Failed to copy files: {e}\n")

    except Exception as e:
        safe_insert(f"⚠️ NSFW Filter failed: {e}\n")

       
        # === Move to saved_downloads if keep is selected ===
        if keep_files_var.get() == "keep":
            try:
                dest_dir = os.path.join(os.path.dirname(__file__), "saved_downloads", torrent.name)
                os.makedirs(dest_dir, exist_ok=True)

                for root_dir, _, files in os.walk(folder):
                    for file in files:
                        src_path = os.path.join(root_dir, file)
                        dst_path = os.path.join(dest_dir, file)
                        if os.path.isfile(src_path):
                            shutil.move(src_path, dst_path)
                safe_insert(f"📁 Moved files to: {dest_dir}\n")
            except Exception as e:
                safe_insert(f"⚠️ Failed to move files: {e}\n")

   

    except Exception as e:
        safe_insert(f"⚠️ NSFW Filter failed: {e}\n")


def monitor_torrent(info_hash):
    global current_hash
    cancel_flag.clear()
    cancel_button.config(state="normal")

    while not cancel_flag.is_set():
        torrent = next((t for t in client.torrents_info() if t.hash.lower() == info_hash), None)
        if not torrent:
            status_box.insert(tk.END, "❌ Torrent not found.\n")
            progress["value"] = 0
            return

        prog = round(torrent.progress * 100, 2)
        downloaded_mb = round(torrent.downloaded / (1024 ** 2), 2)
        total_mb = round(torrent.total_size / (1024 ** 2), 2)

        progress["value"] = prog

        # Remove last line (if present) and replace with new progress text
        if status_box.index("end-2l") != status_box.index("1.0"):
            status_box.delete("end-2l", "end-1l")

        status_box.insert(tk.END, f"📊 Progress: {prog:.2f}% | ⬇️ {downloaded_mb}/{total_mb} MB\n")
        status_box.see(tk.END)

        if torrent.progress >= 0.999:
            status_box.insert(tk.END, f"\n✅ Download Complete!\nFile: {torrent.name}\n")
            cancel_button.config(state="disabled")
            total_files = len(client.torrents_files(torrent_hash=info_hash))
            threading.Thread(target=run_nsfw_filter, args=(torrent, total_files), daemon=True).start()
            break

        time.sleep(1)

def start_download():
    global current_hash
    magnet = magnet_entry.get().strip()
    if not magnet.startswith("magnet:?"):
        messagebox.showerror("Invalid", "Invalid magnet link.")
        return

    info_hash = extract_info_hash(magnet)
    if not info_hash:
        status_box.insert(tk.END, "❌ Could not extract hash.\n")
        return

    current_hash = info_hash
    preference = media_preference_var.get()
    download_all = download_all_var.get()
    image_limit = {"2": 2, "5": 5, "10": 10, "All": 9999}.get(file_limit_var.get(), 5)
    video_limit = {"1": 1, "2": 2, "3": 3, "5": 5, "20": 20}.get(video_limit_var.get(), 2)

    existing = {t.hash.lower() for t in client.torrents_info()}
    if info_hash not in existing:
        safe_insert("📥 Adding torrent to qBittorrent...\n")
        client.torrents_add(urls=magnet, is_paused=False)
        time.sleep(2)

    # Wait for metadata
    for _ in range(60):
        try:
            files = client.torrents_files(torrent_hash=info_hash)
            if files:
                break
        except:
            pass
        time.sleep(1)
    else:
        safe_insert("❌ Metadata timeout.\n")
        return

    # Split files
    image_exts = (".jpg", ".jpeg", ".png", ".webp")
    video_exts = (".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv")

    image_files = []
    video_files = []
    other_files = []

    for f in files:
        name = f.name.lower()
        if name.endswith(image_exts):
            image_files.append(f)
        elif name.endswith(video_exts):
            video_files.append(f)
        else:
            other_files.append(f)

    prioritized = []

    if download_all:
        prioritized = files  # All files
        safe_insert("📂 All files selected for download.\n")
    elif preference == "Videos over Images":
        if video_files:
            prioritized = video_files[:video_limit]
            safe_insert(f"🎬 Selected top {len(prioritized)} video(s) for download.\n")
        elif image_files:
            prioritized = image_files[:image_limit]
            safe_insert(f"🖼️ No videos found. Falling back to {len(prioritized)} image(s).\n")
        else:
            safe_insert("❌ No videos or images found to download.\n")
            return
    else:  # Images over Videos
        if image_files:
            prioritized = image_files[:image_limit]
            safe_insert(f"🖼️ Selected top {len(prioritized)} image(s) for download.\n")
        elif video_files:
            prioritized = video_files[:video_limit]
            safe_insert(f"🎬 No images found. Falling back to {len(prioritized)} video(s).\n")
        else:
            safe_insert("❌ No images or videos found to download.\n")
            return

    # Apply priority
    for f in files:
        pri = 1 if f in prioritized else 0
        client.torrents_file_priority(torrent_hash=info_hash, file_ids=[f.id], priority=pri)

    # Start monitor
    threading.Thread(target=monitor_torrent, args=(info_hash,), daemon=True).start()

def cancel_download():
    if current_hash:
        try:
            client.torrents_delete(delete_files=True, torrent_hashes=current_hash)
            cancel_flag.set()
            progress["value"] = 0
            cancel_button.config(state="disabled")
            status_box.insert(tk.END, f"\nCancelled torrent.\n")
        except Exception as e:
            messagebox.showerror("Error", f"Cancel failed: {e}")

def toggle_pause():
    if current_hash:
        torrent = next((t for t in client.torrents_info() if t.hash.lower() == current_hash), None)
        if not torrent:
            return
        if torrent.state.startswith("paused"):
            client.torrents_resume(torrent_hashes=current_hash)
            pause_var.set("⏸️ Pause")
        else:
            client.torrents_pause(torrent_hashes=current_hash)
            pause_var.set("▶️ Resume")

# === Buttons ===
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="🚀 Start Flagging", command=start_download, font=("Arial", 11), bg="#43A047", fg="white", width=20).grid(row=0, column=0, padx=10)
tk.Button(btn_frame, textvariable=pause_var, command=toggle_pause, font=("Arial", 11), bg="#FB8C00", fg="white", width=20).grid(row=0, column=1, padx=10)
cancel_button = tk.Button(btn_frame, text="⛔️ Cancel Download", command=cancel_download, font=("Arial", 11), bg="#E53935", fg="white", width=20, state="disabled")
cancel_button.grid(row=0, column=2, padx=10)

def launch_ip_tracker():
    magnet = magnet_entry.get().strip()
    if not magnet.startswith("magnet:?"):
        messagebox.showerror("Invalid Magnet", "The magnet link is invalid or empty.")
        return

    script_path = os.path.join(os.path.dirname(__file__), "Ip_Tracker_magnet.py")
    try:
        # Run the IP Tracker script in a new process with the magnet as an argument
        subprocess.Popen([sys.executable, script_path, magnet])
        safe_insert("🛰️ Launched IP Tracker with current magnet link.\n")
    except Exception as e:
        messagebox.showerror("Launch Error", f"Failed to launch IP Tracker:\n{e}")

monitor_button = tk.Button(
    btn_frame,
    text="🌐 Monitor IPs",
    command=launch_ip_tracker,
    font=("Arial", 11),
    bg="#1E88E5",
    fg="white",
    width=20,
    state="disabled"
)
monitor_button.grid(row=0, column=3, padx=10)


import sys
if len(sys.argv) > 1:
    magnet_from_arg = sys.argv[1]
    if magnet_from_arg.startswith("magnet:?"):
        magnet_entry.insert(0, magnet_from_arg)
        magnet_entry.config(state="disabled")  # Optional: prevent editing


root.mainloop()
