#"C:\Users\GANESH\Downloads\pedo catcher proposal+ code\Pedo_cather_code\CSAMdetector&Iptracker\Flag_From_Magnet.py"
import os
import re
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import imagehash

import qbittorrentapi
import numpy as np
from PIL import Image
import tensorflow as tf
import tensorflow_hub

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
root.title("🧲 Flag from Magnet")
root.geometry("720x650")
root.resizable(False, False)

# === Input Section ===
input_frame = tk.LabelFrame(root, text="🎯 Magnet Link", font=("Arial", 11, "bold"), padx=10, pady=10)
input_frame.pack(fill="x", padx=15, pady=(15, 5))

magnet_entry = tk.Entry(input_frame, width=85, font=("Arial", 10))
magnet_entry.pack(pady=5)

# === Options Section ===
options_frame = tk.LabelFrame(root, text="⚙️ Download Settings", font=("Arial", 11, "bold"), padx=10, pady=10)
options_frame.pack(fill="x", padx=15, pady=5)

file_limit_var = tk.StringVar(value="5")
tk.Label(options_frame, text="Number of files to download:", font=("Arial", 10)).grid(row=0, column=0, sticky="w")
file_limit_menu = ttk.Combobox(options_frame, textvariable=file_limit_var, state="readonly", values=["2", "5", "10", "All"], width=10)
file_limit_menu.grid(row=0, column=1, padx=10, pady=5)

# === NEW: Check for NSFW (visual only)
check_nsfw_var = tk.BooleanVar(value=True)
tk.Checkbutton(options_frame, text="🔞 Check for NSFW", variable=check_nsfw_var,
               font=("Arial", 10)).grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))

# Check Against DB (placeholder)
check_db_var = tk.BooleanVar(value=False)
tk.Checkbutton(options_frame, text="🔍 Check Against Database", variable=check_db_var, font=("Arial", 10)).grid(row=2, column=0, columnspan=3, sticky="w", pady=(5, 0))

db_folder_path = tk.StringVar(value="")

def choose_db_folder():
    path = tk.filedialog.askdirectory(title="Select Image Database Folder")
    if path:
        db_folder_path.set(path)

db_folder_button = tk.Button(options_frame, text="📁 Choose Database Folder", command=choose_db_folder, font=("Arial", 10), state="disabled")
db_folder_button.grid(row=2, column=1, sticky="w", padx=5)

# Label to display selected folder path
db_path_label = tk.Label(options_frame, textvariable=db_folder_path, font=("Arial", 9), fg="gray", anchor="w", wraplength=500)
db_path_label.grid(row=4, column=0, columnspan=3, sticky="w", padx=5, pady=(2, 0))

def toggle_db_folder(*_):
    if check_db_var.get():
        db_folder_button.config(state="normal")
    else:
        db_folder_path.set("")
        db_folder_button.config(state="disabled")

check_db_var.trace_add("write", toggle_db_folder)

# Keep/Delete toggle
keep_files_var = tk.StringVar(value="keep")
tk.Radiobutton(options_frame, text="📂 Keep Files After Scan", variable=keep_files_var, value="keep", font=("Arial", 10)).grid(row=5, column=0, sticky="w", pady=(5, 0))
tk.Radiobutton(options_frame, text="🗑️ Delete After Scan", variable=keep_files_var, value="delete", font=("Arial", 10)).grid(row=5, column=1, sticky="w", pady=(5, 0))

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
        folder = torrent.save_path
        image_files = [
            os.path.join(root_dir, file)
            for root_dir, _, files in os.walk(folder)
            for file in files if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ]

        selected_files = image_files[:max_files]
        if not selected_files:
            safe_insert("No images found.\n")
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

        # === DB MATCHING ===
        if check_db_var.get() and db_folder_path.get():
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

            db_hashes = collect_db_hashes(db_folder_path.get())
            match_found = False

            for img_path in nsfw_images:
                try:
                    if os.path.exists(img_path):
                        img = Image.open(img_path).convert("RGB").resize((224, 224))
                        img_hash = imagehash.phash(img)
                        if any(img_hash - h <= 4 for h in db_hashes):  # tolerance = 4
                            safe_insert(f"🟥 Match found: {os.path.basename(img_path)}\n")
                            match_found = True
                except:
                    continue

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

        # === DELETE AFTER DB CHECK ===
        if keep_files_var.get() == "delete":
            try:
                client.torrents_delete(delete_files=True, torrent_hashes=torrent.hash)
                safe_insert("🗑️ Deleted torrent and files.\n")
            except Exception as e:
                safe_insert(f"⚠️ Failed to delete files: {e}\n")

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
    global current_hash, max_files
    magnet = magnet_entry.get().strip()
    if not magnet.startswith("magnet:?"):
        messagebox.showerror("Invalid", "Invalid magnet link.")
        return

    info_hash = extract_info_hash(magnet)
    if not info_hash:
        status_box.insert(tk.END, "Could not extract hash.\n")
        return

    current_hash = info_hash
    max_files = {"2": 2, "5": 5, "10": 10, "All": 9999}.get(file_limit_var.get(), 5)

    existing = {t.hash.lower() for t in client.torrents_info()}
    if info_hash not in existing:
        status_box.insert(tk.END, "Adding to qBittorrent...\n")
        client.torrents_add(urls=magnet, is_paused=False)
        time.sleep(2)

    for _ in range(60):
        try:
            files = client.torrents_files(torrent_hash=info_hash)
            if files:
                break
        except:
            pass
        time.sleep(1)
    else:
        status_box.insert(tk.END, "Metadata timeout.\n")
        return

    file_ids = [f.id for f in client.torrents_files(torrent_hash=info_hash)]
    for fid in file_ids:
        priority = 1 if fid in file_ids[:max_files] else 0
        client.torrents_file_priority(torrent_hash=info_hash, file_ids=[fid], priority=priority)

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


import sys
if len(sys.argv) > 1:
    magnet_from_arg = sys.argv[1]
    if magnet_from_arg.startswith("magnet:?"):
        magnet_entry.insert(0, magnet_from_arg)
        magnet_entry.config(state="disabled")  # Optional: prevent editing


root.mainloop()
