import qbittorrentapi
import time
import re

# === qBittorrent Setup ===
QBITTORRENT_HOST = "localhost:8080"
QBITTORRENT_USERNAME = "admin"
QBITTORRENT_PASSWORD = "VzM;5W2wo#v1FIn/xr+R8"

client = qbittorrentapi.Client(
    host=QBITTORRENT_HOST,
    username=QBITTORRENT_USERNAME,
    password=QBITTORRENT_PASSWORD
)

try:
    client.auth_log_in()
except Exception as e:
    print(f"❌ Could not connect to qBittorrent: {e}")
    exit(1)

# === Magnet Input ===
magnet = input("Paste Magnet Link: ").strip()

# === Extract Info Hash ===
def extract_info_hash(magnet_link):
    match = re.search(r'btih:([a-fA-F0-9]+)', magnet_link)
    if match:
        return match.group(1).lower()
    return None

info_hash = extract_info_hash(magnet)
if not info_hash:
    print("❌ Invalid magnet or no info hash found.")
    exit(1)

# === Add Magnet Paused ===
client.torrents_add(urls=magnet, is_paused=False)
print("⏳ Magnet added. Waiting for metadata...")

# === Wait for Metadata ===
for _ in range(60):  # Wait up to 60 seconds
    try:
        files = client.torrents_files(torrent_hash=info_hash)  # ✅ FIXED PARAM
        if files:
            break
    except qbittorrentapi.NotFound404Error:
        pass  # Metadata not ready yet
    time.sleep(1)
else:
    print("❌ Metadata fetch timeout.")
    client.torrents_delete(delete_files=True, torrent_hashes=info_hash)
    exit(1)

# === Show First 5 Files ===
try:
    files = client.torrents_files(torrent_hash=info_hash)  # ✅ FIXED PARAM
    print("\n📁 First 5 Files in Torrent:")
    for f in files[:5]:
        print(f"• {f.name} ({round(f.size / (1024 ** 2), 2)} MB)")
except Exception as e:
    print(f"❌ Failed to get file list: {e}")

# === Remove Torrent (no download) ===
client.torrents_delete(delete_files=True, torrent_hashes=info_hash)
print("\n🗑️ Torrent removed (no download started).")
