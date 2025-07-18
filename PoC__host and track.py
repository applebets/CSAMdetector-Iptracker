import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import qbittorrentapi
import hashlib
import bencodepy
import time
import socket
import datetime
from ipwhois import IPWhois

TRACKER_URL = "udp://tracker.opentrackr.org:1337/announce"
SAVE_DIR = "host_logs"

VPN_KEYWORDS = ['nordvpn', 'expressvpn', 'proxy', 'cloud', 'vultr', 'tor', 'digitalocean', 'amazon', 'google', 'microsoft', 'linode', 'vpn', 'ovh']
os.makedirs(SAVE_DIR, exist_ok=True)

class TorrentHostApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📦 File Torrent Hoster (bencodepy)")
        self.root.geometry("700x500")

        ttk.Label(root, text="📁 File to Host:").pack(pady=(10, 0))
        file_frame = ttk.Frame(root)
        file_frame.pack(pady=5, fill='x', padx=10)

        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var, width=70)
        self.file_entry.pack(side='left', fill='x', expand=True)

        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side='left', padx=5)

        self.create_btn = ttk.Button(root, text="🚀 Create & Host Torrent", command=self.create_and_host)
        self.create_btn.pack(pady=10)

        ttk.Label(root, text="🔗 Magnet Link (from qBittorrent):").pack()
        self.magnet_text = tk.Text(root, height=3, width=90)
        self.magnet_text.pack(padx=10, pady=5)

        self.refresh_btn = ttk.Button(root, text="🔄 Refresh Peers", command=self.refresh_peers)
        self.refresh_btn.pack(pady=5)

        ttk.Label(root, text="🌐 Connected Peers:").pack()
        self.peers_box = scrolledtext.ScrolledText(root, height=15, width=90, font=("Consolas", 10))
        self.peers_box.pack(padx=10, pady=5)

        self.client = None
        self.torrent_hash = None
        self.torrent_name = None

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.file_var.set(path)

    def make_torrent_file(self, file_path, torrent_path):
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        piece_length = 256 * 1024
        with open(file_path, "rb") as f:
            pieces = b''
            while True:
                piece = f.read(piece_length)
                if not piece:
                    break
                sha1 = hashlib.sha1(piece).digest()
                pieces += sha1
        torrent_dict = {
            b'announce': TRACKER_URL.encode(),
            b'info': {
                b'name': file_name.encode(),
                b'length': file_size,
                b'piece length': piece_length,
                b'pieces': pieces
            }
        }
        encoded = bencodepy.encode(torrent_dict)
        with open(torrent_path, "wb") as f:
            f.write(encoded)

    def login_qb(self):
        from json import load
        with open('settings.json') as f:
            conf = load(f)
        self.client = qbittorrentapi.Client(
            host=f"{conf['host']}:{conf['port']}",
            username=conf['username'],
            password=conf['password']
        )
        self.client.auth_log_in()

    def create_and_host(self):
        file_path = self.file_var.get()
        if not os.path.isfile(file_path):
            messagebox.showerror("Invalid", "Select a valid file.")
            return

        torrent_path = file_path + ".torrent"
        self.create_btn.config(state="disabled")
        threading.Thread(target=self._create_and_host_thread, args=(file_path, torrent_path), daemon=True).start()

    def _create_and_host_thread(self, file_path, torrent_path):
        try:
            self.make_torrent_file(file_path, torrent_path)
            self.login_qb()
            self.client.torrents_add(torrent_files=torrent_path, is_paused=False)
            time.sleep(5)
            for t in self.client.torrents_info():
                if t.name == os.path.basename(file_path):
                    self.torrent_hash = t.hash
                    self.torrent_name = t.name
                    magnet = t.magnet_uri
                    self.magnet_text.delete("1.0", tk.END)
                    self.magnet_text.insert(tk.END, magnet)
                    break
            self.append_log("✅ Torrent added and hosting started.")
        except Exception as e:
            self.append_log(f"❌ Error: {e}")
        finally:
            self.create_btn.config(state="normal")

    def refresh_peers(self):
        if not self.torrent_hash:
            return
        threading.Thread(target=self._refresh_peers_thread, daemon=True).start()

    def _refresh_peers_thread(self):
        self.append_log("🔍 Fetching peers...")
        try:
            peers_data = self.client.sync.torrent_peers(self.torrent_hash).get("peers", {})
            self.peers_box.delete("1.0", tk.END)
            for i, (ip, info) in enumerate(peers_data.items(), 1):
                hostname = self.reverse_dns(ip)
                asn = self.asn_lookup(ip)
                vpn = self.is_vpn(asn, hostname)
                self.append_log(f"{i}. {ip} | {asn} | {hostname} | VPN: {'YES' if vpn else 'NO'}")
        except Exception as e:
            self.append_log(f"❌ Error fetching peers: {e}")

    def append_log(self, msg):
        self.peers_box.insert(tk.END, msg + "\n")
        self.peers_box.see(tk.END)
        self.root.update()

    def reverse_dns(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return "N/A"

    def asn_lookup(self, ip):
        try:
            obj = IPWhois(ip)
            res = obj.lookup_rdap(depth=1)
            return f"AS{res.get('asn', 'N/A')} - {res.get('asn_description', 'N/A')}"
        except:
            return "N/A"

    def is_vpn(self, asn_desc, hostname):
        return any(k in asn_desc.lower() for k in VPN_KEYWORDS) or any(k in hostname.lower() for k in VPN_KEYWORDS)


if __name__ == "__main__":
    root = tk.Tk()
    app = TorrentHostApp(root)
    root.mainloop()
