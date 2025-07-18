import os
import sys
import json
import hashlib
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import bencodepy
import qbittorrentapi

# === Config Paths ===
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
    else:
        return None

class TorrentHostApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📦 Create and Seed Torrent")
        self.root.geometry("600x450")

        ttk.Label(root, text="Select File to Create and Host Torrent:").pack(pady=(10, 5))

        self.path_var = tk.StringVar()
        path_frame = ttk.Frame(root)
        path_frame.pack(padx=10, pady=5, fill='x')

        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=60)
        self.path_entry.pack(side='left', fill='x', expand=True)

        ttk.Button(path_frame, text="Browse", command=self.browse_path).pack(side='left', padx=5)

        ttk.Button(root, text="📄 Create .torrent & Host", command=self.create_torrent).pack(pady=10)

        ttk.Label(root, text="Status Log:").pack()
        self.log_box = scrolledtext.ScrolledText(root, height=12, width=75, font=("Consolas", 10))
        self.log_box.pack(padx=10, pady=10)

        self.client = None  # qBittorrent client

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def browse_path(self):
        path = filedialog.askopenfilename()
        if not path:
            path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)

    def create_torrent(self):
        path = self.path_var.get()
        if not os.path.exists(path):
            messagebox.showerror("Error", "Invalid file or folder path.")
            return

        if os.path.isdir(path):
            messagebox.showerror("Not Supported", "📁 Folder torrents are not supported in this mode. Please select a file.")
            return

        threading.Thread(target=self._create_torrent_thread, args=(path,), daemon=True).start()

    def _create_torrent_thread(self, file_path):
        self.log(f"🔧 Creating torrent for: {file_path}")
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            piece_length = 256 * 1024  # 256 KB
            pieces = b''

            with open(file_path, 'rb') as f:
                while True:
                    piece = f.read(piece_length)
                    if not piece:
                        break
                    sha1 = hashlib.sha1(piece).digest()
                    pieces += sha1

            torrent_dict = {
                b'announce': b'udp://tracker.opentrackr.org:1337/announce',
                b'info': {
                    b'name': file_name.encode(),
                    b'length': file_size,
                    b'piece length': piece_length,
                    b'pieces': pieces
                }
            }

            encoded = bencodepy.encode(torrent_dict)
            torrent_path = file_path + ".torrent"
            with open(torrent_path, "wb") as f:
                f.write(encoded)

            self.log(f"✅ Torrent file created at: {torrent_path}")
            self.log("🚀 Sending torrent to qBittorrent to begin seeding...")

            if self.setup_qbittorrent_client():
                self.send_to_qbittorrent(torrent_path, os.path.dirname(file_path))
            else:
                self.fallback_open_qbittorrent(torrent_path, os.path.dirname(file_path))

        except Exception as e:
            self.log(f"❌ Error creating torrent: {e}")

    def setup_qbittorrent_client(self):
        config = load_qbittorrent_config()
        if not config:
            self.log("❌ settings.json missing or invalid!")
            return False

        full_host = config["host"]
        if not full_host.endswith(f":{config['port']}"):
            if ":" in full_host[full_host.find("//") + 2:]:
                full_host = full_host.rsplit(":", 1)[0]
            full_host = f"{full_host}:{config['port']}"

        self.log(f"🔗 Logging into qBittorrent Web UI at {full_host} ...")
        try:
            self.client = qbittorrentapi.Client(
                host=full_host,
                username=config["username"],
                password=config["password"]
            )
            self.client.auth_log_in()
            self.log("✅ Logged in to qBittorrent successfully.")
            return True
        except Exception as e:
            self.log(f"❌ Login failed: {e}")
            return False

    def send_to_qbittorrent(self, torrent_path, save_path):
        try:
            with open(torrent_path, 'rb') as f:
                self.client.torrents_add(
                    torrent_files=f.read(),
                    save_path=save_path,
                    is_paused=False,
                    use_auto_torrent_management=False
                )
            self.log("✅ Torrent added to qBittorrent for seeding.")
        except Exception as e:
            self.log(f"❌ Failed to add torrent to qBittorrent: {e}")
            self.fallback_open_qbittorrent(torrent_path, save_path)

    def fallback_open_qbittorrent(self, torrent_path, save_path):
        try:
            if sys.platform.startswith("win"):
                self.log("💡 Using Windows fallback: opening with qBittorrent via shell...")
                os.startfile(torrent_path)  # Simple fallback
                self.log("✅ Opened .torrent with default handler (likely qBittorrent).")
            else:
                self.log("⚠️ Auto-launch only supported on Windows. Please open the .torrent file manually.")
        except Exception as e:
            self.log(f"❌ Fallback failed: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TorrentHostApp(root)
    root.mainloop()
