import os, datetime, ipaddress, csv
from qbittorrentapi import Client

# === CONFIG ===
DB_PATH = r"C:\Users\GANESH\Downloads\pedo catcher proposal+ code\Pedo_cather_code\CSAMdetector&Iptracker\IP2PROXY-LITE-PX11.CSV"

def extract_ip(ip_or_ip_port):
    """Sanitize and strip port from IP:Port string."""
    return ip_or_ip_port.strip().split(":")[0]

def ip_to_int(ip_str):
    """Convert dotted IPv4 to integer."""
    return int(ipaddress.IPv4Address(ip_str.strip()))

def check_ip_in_db(ip_str):
    """Check local proxy DB for info about this IP."""
    ip_clean = extract_ip(ip_str)
    ip_int = ip_to_int(ip_clean)
    try:
        with open(DB_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                ip_from = int(row[0].strip())
                ip_to = int(row[1].strip())
                if ip_from <= ip_int <= ip_to:
                    return {
                        "proxy_type": row[2],
                        "country": row[4],
                        "usage_type": row[9],
                        "asn_org": row[11],
                        "provider": row[14],
                        "vpn": row[9] in ["DCH", "SES"],
                        "proxy": row[2] in ["PUB", "WEB", "TOR"],
                        "tor": row[2] == "TOR",
                        "hosting": row[9] == "DCH",
                    }
    except Exception as e:
        print(f"❌ DB Lookup Error for {ip_str}: {e}")
    return {
        "proxy_type": "N/A", "country": "Unknown", "usage_type": "N/A",
        "asn_org": "N/A", "provider": "", "vpn": False,
        "proxy": False, "tor": False, "hosting": False
    }

class PeerTrackerSmartLite:
    def __init__(self, magnet, host="localhost:8080", user="admin", pw="VzM;5W2wo#v1FIn/xr+R8"):
        self.client = Client(host=host, username=user, password=pw)
        self.client.auth_log_in()
        self.torrent = self._add_torrent(magnet)
        self.peer_log = {}

    def _add_torrent(self, magnet):
        self.client.torrents_add(urls=magnet)
        import time; time.sleep(15)
        for t in self.client.torrents_info():
            if t.magnet_uri == magnet or t.hash.lower() in magnet.lower():
                self.client.torrents_set_download_limit(limit=100 * 1024, torrent_hashes=t.hash)
                return t
        raise Exception("❌ Torrent add failed.")

    def get_peers(self):
        peers_response = self.client.sync.torrent_peers(self.torrent.hash)
        peer_data = peers_response.get('peers', {})
        now = datetime.datetime.now().isoformat()

        for ip, info in peer_data.items():
            key = f"{ip}:{info.get('port')}"
            ip_clean = extract_ip(ip)

            if key not in self.peer_log:
                db_data = check_ip_in_db(ip_clean)
                self.peer_log[key] = {
                    "ip": ip_clean,
                    "port": info.get("port"),
                    "client": info.get("client", "Unknown"),
                    "progress": round(info.get("progress", 0) * 100, 1),
                    "first_seen": now,
                    "last_seen": now,
                    "asn": db_data.get("asn_org", "N/A"),
                    "hostname": db_data.get("provider", "N/A"),
                    "country": db_data.get("country", "Unknown"),
                    "vpn": db_data.get("vpn", False),
                    "proxy": db_data.get("proxy", False),
                    "tor": db_data.get("tor", False),
                    "hosting": db_data.get("hosting", False),
                    "latitude": "N/A", "longitude": "N/A"
                }
            else:
                self.peer_log[key].update({
                    "progress": round(info.get("progress", 0) * 100, 1),
                    "client": info.get("client", "Unknown"),
                    "last_seen": now
                })

        return self.peer_log

    def cleanup(self):
        try:
            self.client.torrents_delete(delete_files=False, torrent_hashes=self.torrent.hash)
        except Exception as e:
            print(f"❌ Error removing torrent: {e}")
