import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from smart_tracker_lite import PeerTrackerSmartLite, check_ip_in_db

tracker = None

def extract_ip(ip_or_ip_port):
    """Strip port if present (e.g., '38.127.210.112:46568' -> '38.127.210.112')"""
    return ip_or_ip_port.strip().split(":")[0]

def start_monitoring():
    global tracker
    magnet = simpledialog.askstring("Magnet Link", "Paste the magnet link:")
    if not magnet:
        return

    def monitor_thread():
        global tracker
        try:
            tracker = PeerTrackerSmartLite(magnet)
            status_label.config(text=f"Monitoring: {tracker.torrent.name}")
            refresh_peers()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            status_label.config(text="Failed to start monitoring.")

    threading.Thread(target=monitor_thread).start()

def refresh_peers():
    global tracker
    if not tracker:
        return
    try:
        peers = tracker.get_peers()
        tree.delete(*tree.get_children())

        for p in peers.values():
            ip_clean = extract_ip(p['ip'])
            db_data = check_ip_in_db(ip_clean)

            tree.insert("", "end", values=(
                f"{ip_clean}:{p['port']}",
                p.get('hostname', 'N/A'),
                p.get('asn', 'N/A'),
                p.get('client', 'Unknown'),
                f"{p.get('progress', 0)}%",
                p.get('country', 'Unknown'),
                "YES" if p.get('vpn', False) else "NO",
                "YES" if p.get('proxy', False) else "NO",
                "YES" if p.get('tor', False) else "NO",
                "YES" if p.get('hosting', False) else "NO",
                p.get('latitude', 'N/A'),
                p.get('longitude', 'N/A'),
            ))
    except Exception as e:
        messagebox.showerror("Error refreshing peers", str(e))

# === GUI SETUP ===
root = tk.Tk()
root.title("Smart IP Tracker Lite (Offline DB)")
root.geometry("1200x500")

btn_start = tk.Button(root, text="Start Monitoring", command=start_monitoring)
btn_start.pack(pady=10)

frame = tk.Frame(root)
frame.pack(fill="both", expand=True, padx=10)

columns = (
    "IP:Port", "Hostname", "ASN Info", "Client", "Progress", "Country",
    "VPN", "Proxy", "TOR", "Hosting", "Latitude", "Longitude"
)
tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=120 if col not in ["IP:Port", "ASN Info", "Hostname"] else 160)

xscroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
yscroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
tree.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
tree.grid(row=0, column=0, sticky="nsew")
yscroll.grid(row=0, column=1, sticky="ns")
xscroll.grid(row=1, column=0, sticky="ew")

frame.grid_rowconfigure(0, weight=1)
frame.grid_columnconfigure(0, weight=1)

status_label = tk.Label(root, text="Status: Idle")
status_label.pack(fill="x")

refresh_btn = tk.Button(root, text="Refresh", command=refresh_peers)
refresh_btn.pack(pady=5)

root.mainloop()
