import csv
import os
import ipaddress

def ip_to_int(ip_str):
    """Convert dotted IPv4 string to integer."""
    return int(ipaddress.IPv4Address(ip_str))

def search_ip_int_in_proxy_db(ip_int_to_check, db_path):
    if not os.path.isfile(db_path):
        print(f"❌ Database file not found at:\n{db_path}")
        return None

    with open(db_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            try:
                ip_from = int(row[0].strip())
                ip_to = int(row[1].strip())
                if ip_from <= ip_int_to_check <= ip_to:
                    return {
                        "ip": str(ipaddress.IPv4Address(ip_int_to_check)),
                        "proxy_type": row[2],
                        "country_code": row[3],
                        "country_name": row[4],
                        "region_name": row[5],
                        "city_name": row[6],
                        "isp": row[7],
                        "domain": row[8],
                        "usage_type": row[9],
                        "asn": row[10],
                        "asn_org": row[11],
                        "last_seen": row[12],
                        "threat": row[13],
                        "provider": row[14]
                    }
            except Exception:
                continue
    return None

# === MAIN FLOW ===
db_file = r"C:\Users\GANESH\Downloads\pedo catcher proposal+ code\Pedo_cather_code\CSAMdetector&Iptracker\IP2PROXY-LITE-PX11.CSV"

user_input = input("🔍 Enter an IPv4 address to check (e.g. 38.127.210.112): ").strip()

try:
    ip_int = ip_to_int(user_input)
except ipaddress.AddressValueError:
    print("❌ Invalid IPv4 address format!")
    exit(1)

result = search_ip_int_in_proxy_db(ip_int, db_file)
if result:
    print("\n✅ IP found in proxy DB:")
    for key, value in result.items():
        print(f"{key}: {value}")
else:
    print("\n❌ IP not found in proxy DB.")
