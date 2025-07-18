import os
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import threading
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox, scrolledtext
import json

HEADERS = {"User-Agent": "Mozilla/5.0"}
DEFAULT_MAX_TORRENTS = 15

def parse_detail_page(url, log_func=print):
    domain = urlparse(url).netloc.lower()
    return parse_generic(url, log_func)

def parse_generic(url, log_func=print):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        log_func(f"    ⚠️ Failed to fetch detail page {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    magnet_tag = soup.find("a", href=re.compile(r"magnet:\?xt=urn:btih:"))
    if not magnet_tag:
        log_func(f"    ⚠️ No magnet link found on {url}")
        return None

    magnet = magnet_tag["href"]
    dn_match = re.search(r"dn=([^&]+)", magnet)
    title = urllib.parse.unquote(dn_match.group(1)) if dn_match else (soup.title.string.strip() if soup.title else "Unknown Title")

    size = "Unknown"
    size_patterns = [
        re.compile(r"Size:?\s*([\d\.]+\s*(?:[MGTPK]i?B))", re.IGNORECASE),
        re.compile(r"([\d\.]+\s*(?:[MGTPK]i?B))\s*Size", re.IGNORECASE)
    ]
    for tag in soup.find_all(["td", "div", "li", "span", "p", "font"]):
        text = tag.get_text(strip=True)
        for pat in size_patterns:
            match = pat.search(text)
            if match:
                size = match.group(1)
                break
        if size != "Unknown":
            break

    seeders = leechers = 0
    for tag in soup.find_all(["td", "div", "li", "span", "font"]):
        text = tag.get_text(strip=True)
        if not seeders:
            match = re.search(r"Seeders?:?\s*(\d+)", text, re.IGNORECASE)
            if match:
                seeders = int(match.group(1))
        if not leechers:
            match = re.search(r"Leechers?:?\s*(\d+)", text, re.IGNORECASE)
            if match:
                leechers = int(match.group(1))
        if seeders and leechers:
            break

    return {
        "title": title,
        "magnet": magnet,
        "size": size,
        "seeders": seeders,
        "leechers": leechers
    }

def get_detail_links(listing_url, max_count=50, log_func=print):
    try:
        response = requests.get(listing_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        log_func(f"❌ Failed to fetch listing page {listing_url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(k in href.lower() for k in ["torrent", "details", "view"]):
            full_url = urllib.parse.urljoin(listing_url, href)
            if full_url not in links:
                links.append(full_url)

    return links[:max_count]

def scrape_all_sources(sources, max_links=50, max_torrents=None, log_func=print):
    log_func("🔍 Scraping multiple torrent sources...")
    all_results = []
    total_added = 0
    for site in sources:
        log_func(f"🌐 Scraping from: {site}")
        links = get_detail_links(site, max_count=max_links, log_func=log_func)
        log_func(f"  ➡ Found {len(links)} detail links on {site}")

        for i, link in enumerate(links, 1):
            if max_torrents and total_added >= max_torrents:
                log_func(f"🔶 Reached max torrents limit: {max_torrents}")
                return all_results
            info = parse_detail_page(link, log_func)
            if info:
                all_results.append(info)
                total_added += 1
    return all_results

class ScraperGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🌐 Torrent Scraper")
        self.geometry("980x480")  # reduced height to ~80%
        self.sources = []

        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True)

        right_frame = tk.Frame(main_frame, width=280)
        right_frame.pack(side="right", fill="y")

        tk.Label(left_frame, text="📄 Activity Log", font=("Arial", 11, "bold")).pack(anchor="w", padx=10)
        self.output_box = scrolledtext.ScrolledText(left_frame, font=("Consolas", 10), width=80, height=20)
        self.output_box.pack(padx=10, pady=5, fill="both", expand=True)

        tk.Label(right_frame, text="🔗 List of Sites", font=("Arial", 11, "bold")).pack(pady=(5, 0))
        self.listbox = tk.Listbox(right_frame, font=("Arial", 10), width=40, height=14)
        self.listbox.pack(padx=10, pady=5, fill="y")

        btn_frame = tk.Frame(right_frame)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="➕ Add", command=self.add_url, width=8).grid(row=0, column=0, padx=2)
        tk.Button(btn_frame, text="🗑 Delete", command=self.delete_url, width=8).grid(row=0, column=1, padx=2)
        tk.Button(btn_frame, text="📂 Load", command=self.load_urls, width=8).grid(row=1, column=0, padx=2, pady=3)
        tk.Button(btn_frame, text="💾 Save", command=self.save_urls, width=8).grid(row=1, column=1, padx=2, pady=3)

        self.scrape_btn = tk.Button(right_frame, text="🚀 Start Scraping", command=self.start_scraping_thread, width=30)
        self.scrape_btn.pack(pady=10)

    def log(self, msg):
        self.output_box.insert(tk.END, msg + "\n")
        self.output_box.see(tk.END)
        self.update()

    def add_url(self):
        url = simpledialog.askstring("Add URL", "Enter torrent listing page URL:", parent=self)
        if url:
            self.listbox.insert(tk.END, url)
            self.sources.append(url)

    def delete_url(self):
        try:
            idx = self.listbox.curselection()[0]
            self.listbox.delete(idx)
            del self.sources[idx]
        except IndexError:
            messagebox.showwarning("Warning", "Select a URL to delete.")

    def save_urls(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.sources, f, indent=2)
                messagebox.showinfo("Saved", f"URLs saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save URLs:\n{e}")

    def load_urls(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self.sources.clear()
                self.listbox.delete(0, tk.END)
                for url in loaded:
                    self.sources.append(url)
                    self.listbox.insert(tk.END, url)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load URLs:\n{e}")

    def start_scraping_thread(self):
        self.scrape_btn.config(state=tk.DISABLED)
        self.output_box.delete(1.0, tk.END)
        self.log("🚀 Starting scraping...\n")
        thread = threading.Thread(target=self.run_scraper)
        thread.daemon = True
        thread.start()

    def run_scraper(self):
        if not self.sources:
            self.log("⚠️ No sources provided! Please add URLs before scraping.")
            self.scrape_btn.config(state=tk.NORMAL)
            return

        results = scrape_all_sources(
            sources=self.sources,
            max_links=50,
            max_torrents=25,
            log_func=self.log
        )

        if not results:
            self.log("❌ No torrents found.")
        else:
            self.log("\n📋 Name                              Size     Seeders  Leechers")
            self.log("=" * 70)
            for i, t in enumerate(results, 1):
                name = (t['title'][:30] + '...') if len(t['title']) > 33 else t['title']
                self.log(f"{i:>2}. {name:<33} {t['size']:<8} {t['seeders']:<8} {t['leechers']:<8}")
        self.log("\n🎯 Scraping completed.")
        self.scrape_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    app = ScraperGUI()
    app.mainloop()
