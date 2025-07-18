# Ip_Tracker_magnet.py

import qbittorrentapi
import time
import os
import socket
import datetime
import json
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from ipwhois import IPWhois
import sys

magnet_arg = None
if len(sys.argv) > 1:
    magnet_arg = sys.argv[1]
    
# === CONFIG ===
BASE_DIR = os.path.dirname(__file__)
SAVE_DIR = os.path.join(BASE_DIR, 'Ip_tracker_log')
MAGNET_TEMP_FILE = os.path.join(BASE_DIR, 'last_magnet.txt')
DOWNLOAD_LIMIT_KBPS = 100  # throttle qBittorrent download

VPN_ASN_KEYWORDS = [
    'nordvpn', 'expressvpn', 'digitalocean', 'amazon', 'google', 'microsoft',
    'linode', 'vultr', 'aws', 'vpn', 'hetzner', 'cloud', 'proxy', 'tor', 'ovh'
]
VPN_HOSTNAME_KEYWORDS = ['vpn', 'proxy', 'tor', 'cloud', 'server']

class PeerTracker:
    def __init__(self, magnet_link, ipwhois_mode="free", ipwhois_api_key=None, max_peers=10, refresh_interval="manual"):
        self.ipwhois_mode = ipwhois_mode
        self.api_key = ipwhois_api_key
        self.max_peers = max_peers
        self.refresh_interval = refresh_interval
        self.client = self._login_qb()
        self.torrent = self._add_and_get_torrent(magnet_link)
        self.all_peers = {}
        self.deleted = False

        with open(MAGNET_TEMP_FILE, 'w') as f:
            f.write(magnet_link)

    def _login_qb(self):
        host = "http://localhost"
        port = "8080"
        full_host = f"{host}:{port}"
        try:
            client = qbittorrentapi.Client(
                host=full_host,
                username="admin",
                password="adminadmin"
            )
            client.auth_log_in()
            return client
        except Exception as e:
            raise ConnectionError(f"❌ Could not connect to qBittorrent Web UI at {full_host}\n{e}")

    def _add_and_get_torrent(self, magnet):
        self.client.torrents_add(urls=magnet)
        time.sleep(10)
        for torrent in self.client.torrents_info():
            if torrent.state != 'error' and (torrent.magnet_uri == magnet or torrent.hash.lower() in magnet.lower()):
                self.client.torrents_set_download_limit(
                    limit=DOWNLOAD_LIMIT_KBPS * 1024, torrent_hashes=torrent.hash)
                return torrent
        raise Exception("❌ Torrent not found or failed to add.")

    def _reverse_dns_lookup(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return "N/A"

    def _query_ipwhois_free(self, ip):
        try:
            resp = requests.get(f"https://freeapi.ipwhois.io/json/{ip}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "asn": data.get("asn", "N/A"),
                    "asn_desc": data.get("org", "N/A"),
                    "hostname": data.get("hostname", "N/A")
                }
        except:
            pass
        return {"asn": "N/A", "asn_desc": "N/A", "hostname": "N/A"}

    def _query_ipwhois_premium(self, ip):
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.get(f"https://ipwhois.app/json/{ip}", headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "asn": f"AS{data.get('asn', 'N/A')}",
                    "asn_desc": data.get("asn_org", "N/A"),
                    "hostname": data.get("hostname", "N/A") or "N/A"
                }
        except:
            pass
        return {"asn": "N/A", "asn_desc": "N/A", "hostname": "N/A"}

    def _get_peer_info(self, ip):
        if self.ipwhois_mode == "free":
            info = self._query_ipwhois_free(ip)
        elif self.ipwhois_mode == "premium" and self.api_key:
            info = self._query_ipwhois_premium(ip)
        else:
            info = {"asn": "N/A", "asn_desc": "N/A", "hostname": "N/A"}
        return info["asn"], info["asn_desc"], info["hostname"]

    def _is_probably_vpn(self, asn_desc, hostname):
        asn_desc = asn_desc.lower()
        hostname = hostname.lower()
        return any(k in asn_desc for k in VPN_ASN_KEYWORDS) or any(k in hostname for k in VPN_HOSTNAME_KEYWORDS)

    def get_updated_peers(self):
        if self.deleted:
            try:
                with open(MAGNET_TEMP_FILE, 'r') as f:
                    magnet = f.read().strip()
                self.torrent = self._add_and_get_torrent(magnet)
                self.deleted = False
            except Exception as e:
                raise RuntimeError(f"Torrent was deleted and failed to re-add: {e}")

        peers_response = self.client.sync.torrent_peers(self.torrent.hash)
        peer_data = list(peers_response.get('peers', {}).items())[:self.max_peers]
        now = datetime.datetime.now()

        for ip, info in peer_data:
            key = f"{ip}:{info.get('port')}"
            asn, asn_desc, hostname = self._get_peer_info(ip)

            new_peer = {
                "ip": ip,
                "port": info.get("port", "N/A"),
                "hostname": hostname,
                "asn": f"{asn} - {asn_desc}",
                "client": info.get("client", "Unknown"),
                "progress": round(info.get("progress", 0) * 100, 1),
                "country": info.get("country", "Unknown"),
                "first_seen": now,
                "last_seen": now,
                "is_vpn": self._is_probably_vpn(asn_desc, hostname)
            }

            if key not in self.all_peers:
                self.all_peers[key] = new_peer
            else:
                self.all_peers[key].update({
                    'last_seen': now,
                    'progress': new_peer['progress'],
                    'client': new_peer['client'],
                    'country': new_peer['country']
                })

        if not self.deleted:
            self.cleanup()
            self.deleted = True

        return self.all_peers

    def save_log(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_name = "".join(c for c in self.torrent.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_name}_{timestamp}.txt"
        filepath = os.path.join(SAVE_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Torrent: {self.torrent.name}\nLogged at: {timestamp}\n\n")
            f.write("IP Address:Port       | Hostname               | ASN Info                     | Client         | Progress | Country       | VPN?\n")
            f.write("-" * 110 + "\n")
            for p in self.all_peers.values():
                ip_port = f"{p['ip']}:{p['port']}"
                f.write(f"{ip_port:<20} {p['hostname'][:22]:<22} {p['asn'][:27]:<27} {p['client'][:14]:<14} "
                        f"{str(p['progress']) + '%':>8} {p['country'][:13]:<13} {'YES' if p['is_vpn'] else 'NO':>3}\n")

    def cleanup(self):
        try:
            self.client.torrents_delete(delete_files=True, torrent_hashes=self.torrent.hash)
        except Exception as e:
            print(f"❌ Error removing torrent and files: {e}")

# === GUI WIDGET SETUP SNIPPET ===
def build_monitor_gui():
    root = tk.Tk()
    root.title("🧲 Monitor from Magnet")
    root.configure(bg="#f8f8f8")

    style = ttk.Style()
    style.configure("TLabel", background="#f8f8f8", font=("Segoe UI", 10))
    style.configure("TButton", font=("Segoe UI", 10, "bold"))

    frm = ttk.Frame(root, padding=20)
    frm.pack()

    ttk.Label(frm, text="Enter Magnet Link:").grid(row=0, column=0, columnspan=4, sticky="w")

    magnet_var = tk.StringVar()
    if magnet_arg:
        magnet_var.set(magnet_arg)  # Autofill passed magnet link

    magnet_entry = ttk.Entry(frm, textvariable=magnet_var, width=70)
    magnet_entry.grid(row=1, column=0, columnspan=4, pady=5)

    ttk.Label(frm, text="Max Peers:").grid(row=2, column=0, sticky="w")
    peer_value = tk.IntVar(value=10)
    peer_slider = ttk.Scale(frm, from_=1, to=100, orient="horizontal", variable=peer_value)
    peer_slider.grid(row=2, column=1, sticky="we", padx=(5, 5), columnspan=2)

    peer_label = ttk.Label(frm, text=str(peer_value.get()), width=4)
    peer_label.grid(row=2, column=3, sticky="w")

    def update_label(val):
        peer_label.config(text=str(int(float(val))))

    peer_slider.config(command=update_label)

    infinite_var = tk.IntVar()
    infinite_chk = ttk.Checkbutton(frm, text="∞", variable=infinite_var)
    infinite_chk.grid(row=2, column=4, sticky="w", padx=(10, 0))

    ttk.Label(frm, text="Refresh Interval:").grid(row=3, column=0, columnspan=4, sticky="w", pady=(5, 0))
    refresh_var = tk.StringVar(value="manual")
    refresh_menu = ttk.Combobox(frm, textvariable=refresh_var, values=["manual", "10s", "30s", "60s"], state="readonly")
    refresh_menu.grid(row=4, column=0, columnspan=4, sticky="we")

    def start():
        magnet = magnet_entry.get().strip()
        max_peers = 999 if infinite_var.get() else int(round(peer_slider.get()))
        refresh_interval = refresh_var.get()

        try:
            tracker = PeerTracker(magnet_link=magnet, max_peers=max_peers, refresh_interval=refresh_interval)
            peers = tracker.get_updated_peers()
            tracker.save_log()
            messagebox.showinfo("✅ Tracking Done", f"Tracked {len(peers)} peers. Log saved.")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Failed to start tracking:\n\n{str(e)}")

    ttk.Button(frm, text="Start Monitoring", command=start).grid(row=5, column=0, columnspan=5, pady=15)

    root.mainloop()


if __name__ == "__main__":
    build_monitor_gui()
