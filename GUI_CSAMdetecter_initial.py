import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import threading
import os
import sys
import importlib.util
import subprocess

tracker = None

# === Dynamic Module Import Utility ===
def dynamic_import(module_path, name):
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# === Import External Modules Dynamically ===
host_module = dynamic_import(
    os.path.join(os.path.dirname(__file__), "host_and_track.py"),
    "host_and_track"
)
scraper_module = dynamic_import(
    os.path.join(os.path.dirname(__file__), "torrent_scraper_site.py"),
    "torrent_scraper_site"
)

host_file_and_track_peers = host_module.host_file_and_track_peers




# === GUI Functions ===
def launch_monitor_popup():
    popup = tk.Toplevel(root)
    popup.title("Choose Monitoring Mode")
    popup.geometry("320x260")
    popup.transient(root)
    popup.grab_set()

    tk.Label(popup, text="🔍 Choose Monitoring Option:", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Button(popup, text="🧲 Monitor from Magnet", width=30, command=lambda: [popup.destroy(), monitor_ips_from_magnet()]).pack(pady=5)
    tk.Button(popup, text="🌐 Torrent Page URL", width=30, command=lambda: [popup.destroy(), launch_jackett_script()]).pack(pady=5)
    tk.Button(popup, text="🖥️ Host and Monitor", width=30, command=lambda: [popup.destroy(), monitor_from_host()]).pack(pady=5)
    tk.Button(popup, text="⚠️18+ Advanced Detection & Flagging", width=30, command=lambda: [popup.destroy(), advanced_detection_flagging()]).pack(pady=5)

def launch_jackett_script():
    try:
        script_path = os.path.join(os.path.dirname(__file__), "Torrent_Page_Url_JACKET.py")
        subprocess.Popen([sys.executable, script_path])
    except Exception as e:
        messagebox.showerror("Error", f"Could not run Jackett script:\n{e}")


def monitor_ips_from_magnet():
    gui_script_path = os.path.join(os.path.dirname(__file__), "Ip_Tracker_magnet.py")

    def run_and_monitor():
        try:
            status_label.config(text="Status: Loading → Monitor from Magnet")
            root.update_idletasks()
            process = subprocess.Popen(["python", gui_script_path])
            status_label.config(text="Status: Running → Monitor from Magnet")
            process.wait()
            status_label.config(text="Status: Idle")
        except Exception as e:
            status_label.config(text="Status: Error launching Monitor from Magnet")
            messagebox.showerror("Error", f"Could not launch Ip_Tracker_magnet.py:\n{e}")

    threading.Thread(target=run_and_monitor).start()

def monitor_from_host():
    popup = tk.Toplevel(root)
    popup.title("🖥️ Host and Monitor")
    popup.geometry("360x260")
    popup.transient(root)
    popup.grab_set()

    def select_file():
        popup.destroy()
        file_path = filedialog.askopenfilename(title="Select File to Host")
        if file_path:
            messagebox.showinfo("✅ File Selected", f"File selected to host:\n{file_path}")
            threading.Thread(target=host_file_and_track_peers, args=(file_path,)).start()

    def create_dummy_file():
        size_map = {
            "5 MB": 5 * 1024 * 1024,
            "50 MB": 50 * 1024 * 1024,
            "500 MB": 500 * 1024 * 1024,
            "1 GB": 1 * 1024 * 1024 * 1024,
            "2 GB": 2 * 1024 * 1024 * 1024,
            "4 GB": 4 * 1024 * 1024 * 1024,
        }

        file_name = file_entry.get().strip()
        selected_size = size_var.get()
        if not file_name or not selected_size:
            messagebox.showerror("Missing Info", "Please enter a name and select a size.")
            return

        file_path = os.path.join(os.getcwd(), file_name)
        file_size = size_map[selected_size]

        try:
            with open(file_path, "wb") as f:
                f.seek(file_size - 1)
                f.write(b"\0")
            popup.destroy()
            messagebox.showinfo("✅ File Created", f"Dummy file created:\n{file_path}")
            threading.Thread(target=host_file_and_track_peers, args=(file_path,)).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create file:\n{str(e)}")

    tk.Label(popup, text="Choose Hosting Mode:", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Button(popup, text="📂 Select Existing File", command=select_file, width=30).pack(pady=5)

    ttk.Separator(popup, orient="horizontal").pack(fill="x", pady=10)

    tk.Label(popup, text="🆕 Create Dummy File", font=("Arial", 11)).pack()

    file_frame = tk.Frame(popup)
    file_frame.pack(pady=5)
    tk.Label(file_frame, text="Name:").grid(row=0, column=0, padx=5)
    file_entry = tk.Entry(file_frame, width=20)
    file_entry.grid(row=0, column=1)

    tk.Label(file_frame, text="Size:").grid(row=1, column=0, padx=5, pady=5)
    size_var = tk.StringVar()
    size_dropdown = ttk.Combobox(file_frame, textvariable=size_var, values=["5 MB", "50 MB", "500 MB", "1 GB", "2 GB", "4 GB"], state="readonly", width=17)
    size_dropdown.grid(row=1, column=1)
    size_dropdown.set("500 MB")

    tk.Button(popup, text="📁 Create File", command=create_dummy_file, width=25).pack(pady=10)

def advanced_detection_flagging():
    popup = tk.Toplevel(root)
    popup.title("⚠️ Advanced Detection Options")
    popup.geometry("350x220")
    popup.transient(root)
    popup.grab_set()

    tk.Label(popup, text="Choose Detection Mode", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Button(popup, text="🧲 Flag from Magnet", width=30, command=lambda: [popup.destroy(), flag_from_magnet()]).pack(pady=5)
    tk.Button(popup, text="🌐 Flag from Webpages", width=30, command=lambda: [popup.destroy(), flag_from_webpages()]).pack(pady=5)
    tk.Button(popup, text="🤖 Auto-Flag & IP Log (Webpages)", width=30, command=lambda: [popup.destroy(), auto_flag_and_ip_log()]).pack(pady=5)

def flag_from_webpages():
    import threading
    import importlib.util
    import os
    from tkinter import messagebox, Toplevel, Listbox, Button

    def run_scraper_and_show():
        try:
            detection_module_path = os.path.join(os.path.dirname(__file__), "advanced_detection_scrapping.py")
            spec = importlib.util.spec_from_file_location("advanced_scraper", detection_module_path)
            advanced_scraper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(advanced_scraper)

            data = advanced_scraper.run_advanced_scraper(download_mode="partial")
            results = data.get("results", [])

            if not results:
                messagebox.showinfo("No Results", "No suspicious torrents detected.")
                return

            choice_window = Toplevel(root)
            choice_window.title("Suspicious Torrents (Advanced Detection)")
            choice_window.geometry("750x450")

            listbox = Listbox(choice_window, width=100, height=20)
            for idx, res in enumerate(results):
                listbox.insert(tk.END, f"{idx+1}. {res.get('title', 'No Title')} | Size: {res.get('size', 'N/A')} | 🌱 {res.get('seeders', '?')} 🧲 {res.get('leechers', '?')}")
            listbox.pack(pady=10)

            def select_magnet():
                try:
                    selected_index = listbox.curselection()[0]
                    magnet = results[selected_index]["magnet"]
                    messagebox.showinfo("Magnet Selected", f"Magnet copied to clipboard:\n\n{results[selected_index]['title']}")
                    choice_window.clipboard_clear()
                    choice_window.clipboard_append(magnet)
                    choice_window.update()
                    choice_window.destroy()
                except Exception:
                    messagebox.showerror("Error", "No torrent selected.")

            Button(choice_window, text="✅ Select & Copy Magnet", command=select_magnet).pack(pady=5)

        except Exception as e:
            messagebox.showerror("⚠️ Error", f"Failed to launch advanced detection:\n{str(e)}")

    threading.Thread(target=run_scraper_and_show).start()

def flag_from_magnet():
    gui_script_path = os.path.join(os.path.dirname(__file__), "Flag_From_Magnet.py")

    def run_and_monitor():
        try:
            status_label.config(text="Status: Loading → 18+ Advanced Detection → Flag from Magnet")
            root.update_idletasks()

            process = subprocess.Popen(["python", gui_script_path])
            status_label.config(text="Status: Running → 18+ Advanced Detection → Flag from Magnet")
            process.wait()  # Wait for the popup to be closed
            status_label.config(text="Status: Idle")
        except Exception as e:
            status_label.config(text="Status: Error launching Flag from Magnet")
            messagebox.showerror("Error", f"Could not launch Flag_From_Magnet.py:\n{e}")

    threading.Thread(target=run_and_monitor).start()


def auto_flag_and_ip_log():
    messagebox.showinfo("🚧 Coming Soon", "Automatic flagging with IP logging is under development.")


def on_close():
    global tracker
    if tracker and remove_on_exit.get():
        tracker.cleanup()
    root.destroy()

# === GUI Layout ===
root = tk.Tk()
root.title("🧠 Pedo Catcher: IP & Content Monitor")
root.geometry("")
root.protocol("WM_DELETE_WINDOW", on_close)

title = tk.Label(root, text="🎯 Monitor IPs & Detect CSAM", font=("Arial", 18, "bold"))
title.pack(pady=10)

control_frame = tk.Frame(root)
control_frame.pack(pady=5)

tk.Button(control_frame, text="🎬 Start Monitoring", command=launch_monitor_popup, width=20).grid(row=0, column=0, padx=5)

auto_save = tk.BooleanVar()
remove_on_exit = tk.BooleanVar()


# === Status Bar ===
status_label = tk.Label(root, text="Status: Idle", anchor="w")
status_label.pack(fill="x")

# === Bottom Right Buttons: Options & About ===
bottom_frame = tk.Frame(root)
bottom_frame.pack(fill="x", padx=10, pady=(0, 10), anchor="se")

# Place using grid to force it to stay right-aligned
bottom_frame.columnconfigure(0, weight=1)
bottom_frame.columnconfigure(1, weight=1)

def show_settings():
    import json
    import os
    settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')

    def load_settings():
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                return json.load(f)
        return {}

    def save_settings_to_file(data):
        with open(settings_path, 'w') as f:
            json.dump(data, f, indent=4)

    saved = load_settings()

    settings_win = tk.Toplevel(root)
    settings_win.title("⚙️ Settings")
    settings_win.geometry("500x550")
    settings_win.transient(root)
    settings_win.grab_set()

    notebook = ttk.Notebook(settings_win)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # === TAB 1: qBittorrent Settings ===
    qb_frame = tk.Frame(notebook)
    notebook.add(qb_frame, text="qBittorrent")

    entries = [
        ("Username:", "username", ""),
        ("Password:", "password", "", True),
        ("Host:", "host", "http://localhost"),
        ("Port:", "port", "8080"),
        ("Tracker URL:", "tracker", "udp://tracker.openbittorrent.com:80")
    ]

    for i, (label, key, default, *secure) in enumerate(entries):
        tk.Label(qb_frame, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=5)
        show = "*" if secure else None
        entry = tk.Entry(qb_frame, width=30, show=show)
        entry.insert(0, saved.get(key, default))
        entry.grid(row=i, column=1, padx=5, pady=5)
        locals()[f"{key}_entry"] = entry

    def save_qbittorrent_settings():
        for _, key, *_ in entries:
            saved[key] = locals()[f"{key}_entry"].get()
        save_settings_to_file(saved)
        messagebox.showinfo("Saved", "qBittorrent settings saved successfully!")

    tk.Button(qb_frame, text="💾 Save", command=save_qbittorrent_settings).grid(row=len(entries), column=1, pady=10, sticky="e")

        # === TAB 2: Jackett Settings ===
    jackett_frame = tk.Frame(notebook)
    notebook.add(jackett_frame, text="Jackett")

    tk.Label(jackett_frame, text="Jackett API Key:").grid(row=0, column=0, sticky="w", padx=10, pady=(15, 5))
    jackett_key_var = tk.StringVar(value=saved.get("jackett_api_key", ""))
    tk.Entry(jackett_frame, textvariable=jackett_key_var, width=40).grid(row=0, column=1, padx=10, pady=(15, 5))

    tk.Label(jackett_frame, text="Host:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    jackett_host_var = tk.StringVar(value=saved.get("jackett_host", "http://localhost"))
    tk.Entry(jackett_frame, textvariable=jackett_host_var, width=40).grid(row=1, column=1, padx=10)

    tk.Label(jackett_frame, text="Port:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    jackett_port_var = tk.StringVar(value=saved.get("jackett_port", "9117"))
    tk.Entry(jackett_frame, textvariable=jackett_port_var, width=40).grid(row=2, column=1, padx=10)

    def save_jackett_settings():
        saved.update({
            "jackett_api_key": jackett_key_var.get(),
            "jackett_host": jackett_host_var.get(),
            "jackett_port": jackett_port_var.get()
        })
        save_settings_to_file(saved)
        messagebox.showinfo("Saved", "Jackett settings saved!")

    tk.Button(jackett_frame, text="💾 Save", command=save_jackett_settings).grid(row=3, column=1, sticky="e", pady=10)

    # === TAB 3: Other Settings ===
    other_frame = tk.Frame(notebook)
    notebook.add(other_frame, text="Other")

    tk.Label(other_frame, text="Download Folder:").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))
    download_folder_var = tk.StringVar(value=saved.get("download_folder", os.getcwd()))
    tk.Entry(other_frame, textvariable=download_folder_var, width=40).grid(row=0, column=1, sticky="w")

    def choose_download_folder():
        path = filedialog.askdirectory()
        if path:
            download_folder_var.set(path)

    tk.Button(other_frame, text="Browse", command=choose_download_folder).grid(row=0, column=2, padx=5)

    tk.Label(other_frame, text="IPWhois API Key (Premium):").grid(row=2, column=0, sticky="w", padx=10, pady=(10, 2))
    ipwhois_key_var = tk.StringVar(value=saved.get("ipwhois_api_key", ""))
    tk.Entry(other_frame, textvariable=ipwhois_key_var, width=40).grid(row=2, column=1, sticky="w", pady=(0, 10))

    def save_other_settings():
        saved.update({
            "download_folder": download_folder_var.get(),
            "ipwhois_api_key": ipwhois_key_var.get(),
        })
        save_settings_to_file(saved)
        messagebox.showinfo("Saved", "Other settings saved!")

    tk.Button(other_frame, text="💾 Save", command=save_other_settings).grid(row=3, column=1, sticky="e", pady=10)

def show_about():
    messagebox.showinfo("ℹ️ About", "🧠 Pedo Catcher\nVersion: 1.0.0\nAuthor: Ganesh Kishore\n\nMonitors peer IPs from torrents\nand performs content detection.")

settings_button = tk.Button(bottom_frame, text="⚙️ Settings", width=12, command=show_settings)


# === Bottom Right Buttons ===
bottom_frame = tk.Frame(root)
bottom_frame.pack(side="bottom", anchor="e", padx=10, pady=5)

settings_button = tk.Button(bottom_frame, text="⚙️ Settings", width=12, command=show_settings)
settings_button.pack(side="right", padx=(0, 10))

about_button = tk.Button(bottom_frame, text="ℹ️ About", width=8, command=show_about)
about_button.pack(side="right", padx=(0, 10))

root.mainloop()