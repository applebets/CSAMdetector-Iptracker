import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import random
from PIL import Image
import io
import os
import pyzipper

#ZIP OPTION CODE
def generate_image_bytes():
    img = Image.new("RGB", (256, 256), color=(random.randint(0,255), random.randint(0,255), random.randint(0,255)))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()

def generate_video_bytes(size_mb):
    return os.urandom(int(size_mb * 1024 * 1024))

def generate_text_bytes(lines=15):
    return '\n'.join(
        ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=80)) for _ in range(lines)
    ).encode("utf-8")

def create_zip_with_files(path, config, password):
    if password:
        zf = pyzipper.AESZipFile(path, 'w', compression=pyzipper.ZIP_DEFLATED,
                                 encryption=pyzipper.WZ_AES)
        zf.setpassword(password.encode())
        zf.setencryption(pyzipper.WZ_AES, nbits=256)
    else:
        zf = pyzipper.AESZipFile(path, 'w', compression=pyzipper.ZIP_DEFLATED)

    with zf as z:
        if config['image']['enabled']:
            for name in config['image']['names']:
                min_mb = float(config['image']['min'])
                max_mb = float(config['image']['max'])
                size_mb = random.uniform(min_mb, max_mb)
                img_bytes = generate_image_bytes()
                target_size = int(size_mb * 1024 * 1024)
                padding_needed = max(0, target_size - len(img_bytes))
                img_bytes += os.urandom(padding_needed)
                z.writestr(name + ".jpg", img_bytes)

        if config['video']['enabled']:
            for name in config['video']['names']:
                min_mb = float(config['video']['min'])
                max_mb = float(config['video']['max'])
                size_mb = random.uniform(min_mb, max_mb)
                z.writestr(name + ".mp4", generate_video_bytes(size_mb))

        if config['text']['enabled']:
            total_size = float(config['text']['size']) * 1024 * 1024  # MB to bytes
            names = config['text']['names']
            num_files = len(names)

            if num_files == 0:
                return

            # Generate random weights for distribution
            weights = [random.uniform(0.8, 1.2) for _ in range(num_files)]
            total_weight = sum(weights)

            # Calculate individual sizes
            sizes = [int(total_size * (w / total_weight)) for w in weights]
            sizes[-1] = int(total_size - sum(sizes[:-1]))  # Adjust last file to make total exact

            for name, sz in zip(names, sizes):
                z.writestr(name + ".txt", os.urandom(sz))

# === Setup ===
root = tk.Tk()
root.title("🛠 Dummy File Generator")
root.geometry("650x500")
root.configure(bg="#f5f5f5")

HEADER_FONT = ("Segoe UI", 12, "bold")
LABEL_FONT = ("Segoe UI", 10)
PREVIEW_FONT = ("Consolas", 9)

def create_dummy_image(path, size_mb, image_format=".jpg"):
    format_map = {
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".png": "PNG",
        ".bmp": "BMP"
    }

    width, height = 256, 256
    image = Image.new("RGB", (width, height), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    
    format_clean = image_format.lower()
    save_format = format_map.get(format_clean, format_clean.strip("."))

    quality = 95 if save_format == "JPEG" else None
    buffer = io.BytesIO()
    image.save(buffer, format=save_format, quality=quality)

    current_size = buffer.tell()
    target_size = int(size_mb * 1024 * 1024)

    if current_size < target_size:
        pad_size = target_size - current_size
        buffer.write(os.urandom(pad_size))

    with open(path, "wb") as f:
        f.write(buffer.getvalue())

def create_dummy_video(path, size_mb):
    # Create a dummy video-like binary file with random data
    target_size = int(size_mb * 1024 * 1024)
    with open(path, "wb") as f:
        f.write(os.urandom(target_size))

# === Preview Generator ===
def generate_preview(prefix, base, suffix, count):
    result = []
    try:
        count = int(count)
    except:
        return result

    for i in range(1, count + 1):
        # --- Prefix ---
        if prefix == "-":
            pre = ""
        elif prefix.startswith("1") and len(prefix) > 1:
            pre = str(i) + prefix[1:]
        elif prefix == "1":
            pre = str(i)
        else:
            pre = prefix + str(i)

        # --- Suffix ---
        if suffix == "-":
            suf = ""
        elif suffix.startswith("1") and len(suffix) > 1:
            suf = str(i) + suffix[1:]
        elif suffix == "1":
            suf = str(i)
        elif suffix[0] in ("_", "#"):
            suf = suffix[0] + str(i)
        else:
            suf = suffix

        result.append(f"{pre}{base}{suf}")
    return result


# === Scrollable Container ===
main_frame = tk.Frame(root, bg="#f5f5f5")
main_frame.pack(fill="both", expand=True)

canvas = tk.Canvas(main_frame, bg="#f5f5f5")
scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
scrollable_content = tk.Frame(canvas, bg="#f5f5f5")

scrollable_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

canvas.create_window((0, 0), window=scrollable_content, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# === Title ===
tk.Label(scrollable_content, text="📁 Files to Host", font=("Segoe UI", 14, "bold"), bg="#f5f5f5").pack(pady=(10, 5))

# === File Section Builder ===
def create_file_section(master, title, formats):
    outer = tk.Frame(master, bg="#f5f5f5")
    outer.pack(fill="x", pady=6, padx=12)

    enabled = tk.BooleanVar(value=False)  # default enabled

    btn = tk.Button(outer, text=f"▶ {title}", font=HEADER_FONT, anchor="w", bg="#ddd", relief="flat")
    btn.pack(fill="x")

    frame = tk.Frame(outer, bg="#ffffff", bd=1, relief="solid")
    include_row = tk.Frame(frame, bg="#ffffff")
    include_row.pack(fill="x", pady=(5, 2))
    include_cb = tk.Checkbutton(include_row, text=f"Include {title.strip('▶ ')}", variable=enabled, bg="#ffffff", font=LABEL_FONT)
    include_cb.pack(side="left", padx=10)

    folder_name_entry = None
    if "Text" in title:
        tk.Label(include_row, text="Text Filename:", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=(10, 5))
        folder_name_entry = tk.Entry(include_row, width=20)
        folder_name_entry.insert(0, "Note")
        folder_name_entry.pack(side="left")
    else:
        tk.Label(include_row, text="Folder name:", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=(10, 5))
        folder_name_entry = tk.Entry(include_row, width=15)
        default_folder = title.strip("▶ ").strip().lower()
        if "image" in default_folder:
            default_folder = "img"
        elif "video" in default_folder:
            default_folder = "vid"
        folder_name_entry.insert(0, default_folder)

        folder_name_entry.pack(side="left")


    preview_box = None
    if "Text" not in title:
        preview_box = scrolledtext.ScrolledText(frame, height=5, font=PREVIEW_FONT, state="disabled", wrap="word")
        preview_box.pack(fill="x", padx=10, pady=(0, 10))


    def toggle():
        if frame.winfo_ismapped():
            frame.pack_forget()
            btn.config(text=f"▶ {title}")
        else:
            frame.pack(fill="x", padx=10, pady=4)
            btn.config(text=f"▼ {title}")
            refresh_preview()

    btn.config(command=toggle)


    mode_var = tk.StringVar(value="create")

    radio_frame = tk.Frame(frame, bg="#ffffff")
    radio_frame.pack(fill="x", pady=(5, 0))

    tk.Radiobutton(radio_frame, text="📁 Create Files", variable=mode_var, value="create", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=10)
    tk.Radiobutton(radio_frame, text="📂 Select Files from Folder", variable=mode_var, value="select", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=10)

    folder_frame = tk.Frame(frame, bg="#ffffff")
    browse_button = tk.Button(folder_frame, text="Browse", font=("Segoe UI", 9))
    selected_label = tk.Label(folder_frame, text="No folder selected", bg="#ffffff", font=("Segoe UI", 9, "italic"), fg="gray")

    def browse_folder(label):
        folder = filedialog.askdirectory()
        if folder:
            label.config(text=folder)

    browse_button.config(command=lambda: browse_folder(selected_label))

    def update_visibility():
        if mode_var.get() == "select":
            browse_button.grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
            selected_label.grid(row=1, column=1, columnspan=3, sticky="w")
        else:
            browse_button.grid_forget()
            selected_label.grid_forget()

    mode_var.trace_add("write", lambda *_: update_visibility())

    row1 = tk.Frame(frame, bg="#ffffff")
    row1.pack(fill="x", pady=2)

    tk.Label(row1, text="Prefix:", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    prefix_cb = ttk.Combobox(row1, values=["#", "1.", "1_", "1", "-"], width=6)
    prefix_cb.set("1.")
    prefix_cb.pack(side="left", padx=(0, 10))

    tk.Label(row1, text="Base Name:", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    base_name = tk.Entry(row1, width=16)
    base_name.insert(0, "FileA")
    base_name.pack(side="left", padx=(0, 10))

    tk.Label(row1, text="Suffix:", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    suffix_cb = ttk.Combobox(row1, values=["_1", "#1", "1", "-"], width=6)
    suffix_cb.set("-")
    suffix_cb.pack(side="left")

    row2 = tk.Frame(frame, bg="#ffffff")
    row2.pack(fill="x", pady=2)
    tk.Label(row2, text="Format:", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    format_cb = ttk.Combobox(row2, values=formats, width=12)
    format_cb.set(formats[0])
    format_cb.pack(side="left", padx=(0, 10))
    tk.Label(row2, text="Count:", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    count_entry = tk.Entry(row2, width=8)
    count_entry.insert(0, "10")
    count_entry.pack(side="left")

    row3 = tk.Frame(frame, bg="#ffffff")
    row3.pack(fill="x", pady=2)
    tk.Label(row3, text="Size Range (MB):", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    size_from = tk.Entry(row3, width=6)
    size_from.insert(0, "1")
    size_from.pack(side="left", padx=(0, 5))
    tk.Label(row3, text="to", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    size_to = tk.Entry(row3, width=6)
    size_to.insert(0, "5")
    size_to.pack(side="left", padx=(0, 5))

    def refresh_preview(*_):
        if mode_var.get() == "create":
            if preview_box:
                preview_box.config(state="normal")
                preview_box.delete("1.0", tk.END)
                names = generate_preview(prefix_cb.get(), base_name.get(), suffix_cb.get(), count_entry.get())
                preview_box.insert(tk.END, "\n".join(names))
                preview_box.config(state="disabled")


    prefix_cb.bind("<<ComboboxSelected>>", refresh_preview)
    suffix_cb.bind("<<ComboboxSelected>>", refresh_preview)
    base_name.bind("<KeyRelease>", refresh_preview)
    count_entry.bind("<KeyRelease>", refresh_preview)

    # Special logic for text files
    text_input_box = None
    if "Text" in title:
        for widget in [row1, row2, row3]:
            widget.pack_forget()

        text_input_box = scrolledtext.ScrolledText(frame, height=6, font=PREVIEW_FONT, wrap="word", fg="gray")
        text_input_box.insert(tk.END, "Insert text here")
        text_input_box.pack(fill="x", padx=10, pady=(5, 10))

        def clear_placeholder(event):
            if text_input_box.get("1.0", tk.END).strip() == "Insert text here":
                text_input_box.delete("1.0", tk.END)
                text_input_box.config(fg="black")

        def restore_placeholder(event):
            if text_input_box.get("1.0", tk.END).strip() == "":
                text_input_box.insert(tk.END, "Insert text here")
                text_input_box.config(fg="gray")

        text_input_box.bind("<FocusIn>", clear_placeholder)
        text_input_box.bind("<FocusOut>", restore_placeholder)

    return {
        "enabled": enabled,
        "prefix_cb": prefix_cb,
        "suffix_cb": suffix_cb,
        "base_name": base_name,
        "format_cb": format_cb,
        "count_entry": count_entry,
        "size_from": size_from,
        "size_to": size_to,
        "frame": frame,
        "btn": btn,
        "folder_entry": folder_name_entry,
        "text_box": text_input_box if "Text" in title else None
    }



# === Sections ===
image_section = create_file_section(scrollable_content, "🖼️ Image Files", [".jpg", ".png"])
video_section = create_file_section(scrollable_content, "🎥 Video Files", [".mp4", ".avi", ".mov"])
video_section["is_video"] = True
# === ZIP Section with Internal Files ===
def create_zip_file_section(master):
    outer = tk.Frame(master, bg="#f5f5f5")
    outer.pack(fill="x", pady=6, padx=12)

    # Expand/Collapse button
    btn = tk.Button(outer, text="▶ 📦 ZIP Files", font=HEADER_FONT, anchor="w", bg="#ddd", relief="flat")
    btn.pack(fill="x")

    frame = tk.Frame(outer, bg="#ffffff", bd=1, relief="solid")

    # Top row: ZIP name and Password
    row = tk.Frame(frame, bg="#ffffff")
    row.pack(fill="x", padx=10, pady=(10, 0))
    tk.Label(row, text="ZIP Name:", bg="#ffffff", font=LABEL_FONT).pack(side="left")
    zipname_entry = tk.Entry(row, width=20)
    zipname_entry.insert(0, "hosted.zip")
    zipname_entry.pack(side="left", padx=(5, 15))

    tk.Label(row, text="Password:", bg="#ffffff", font=LABEL_FONT).pack(side="left")
    password_entry = tk.Entry(row, width=20, show="*")
    password_entry.pack(side="left", padx=(5, 5))

    # Internal file sections
    inner_frame = tk.Frame(frame, bg="#ffffff")
    inner_frame.pack(fill="x", padx=5, pady=5)

    def section_factory(parent, label, key, ext):
        section_enabled = tk.BooleanVar(value=False)

        container = tk.Frame(parent, bg="#ffffff")
        container.pack(fill="x", pady=(8, 0))

        btn = tk.Button(container, text=f"▶ {label}", font=("Segoe UI", 10, "bold"), anchor="w", bg="#ddd", relief="flat")
        btn.pack(fill="x")
        
        sub_frame = tk.Frame(container, bg="#ffffff", bd=1, relief="solid")

        # Enable checkbox
        tk.Checkbutton(sub_frame, text=f"Include {label.strip('▶ ')}", variable=section_enabled, bg="#ffffff").pack(anchor="w", padx=10, pady=(5, 0))

        row = tk.Frame(sub_frame, bg="#ffffff")
        row.pack(padx=10, pady=(5, 0))
        tk.Label(row, text="Count", bg="#ffffff").grid(row=0, column=0)
        count = tk.Entry(row, width=4)
        count.insert(0, "3")
        count.grid(row=1, column=0)

        tk.Label(row, text="Prefix", bg="#ffffff").grid(row=0, column=1)
        prefix = ttk.Combobox(row, values=["#", "1.", "1_", "-"], width=6)
        prefix.set("1.")
        prefix.grid(row=1, column=1)

        tk.Label(row, text="Base", bg="#ffffff").grid(row=0, column=2)
        base = tk.Entry(row, width=10)
        base.insert(0, key)
        base.grid(row=1, column=2)

        tk.Label(row, text="Suffix", bg="#ffffff").grid(row=0, column=3)
        suffix = ttk.Combobox(row, values=["_1", "#1", "1", "-"], width=6)
        suffix.set("-")
        suffix.grid(row=1, column=3)

        size_row = tk.Frame(sub_frame, bg="#ffffff")
        size_row.pack(padx=10, pady=(5, 0))
        tk.Label(size_row, text="Min MB", bg="#ffffff").grid(row=0, column=0)
        size_from = tk.Entry(size_row, width=6)
        size_from.insert(0, "0.5")
        size_from.grid(row=0, column=1)

        tk.Label(size_row, text="Max MB", bg="#ffffff").grid(row=0, column=2, padx=(10, 0))
        size_to = tk.Entry(size_row, width=6)
        size_to.insert(0, "1.5")
        size_to.grid(row=0, column=3)

        preview = scrolledtext.ScrolledText(sub_frame, height=5, font=PREVIEW_FONT, state="disabled", wrap="word")
        preview.pack(fill="x", padx=10, pady=(5, 10))

        def generate_names():
            return generate_preview(prefix.get(), base.get(), suffix.get(), count.get())

        def refresh_preview(*_):
            names = generate_names()
            preview.config(state="normal")
            preview.delete("1.0", tk.END)
            preview.insert(tk.END, "\n".join(name + ext for name in names))
            preview.config(state="disabled")

        # Bind inputs
        for w in [count, base]: w.bind("<KeyRelease>", refresh_preview)
        prefix.bind("<<ComboboxSelected>>", refresh_preview)
        suffix.bind("<<ComboboxSelected>>", refresh_preview)

        # Toggle show/hide
        def toggle():
            if sub_frame.winfo_ismapped():
                sub_frame.pack_forget()
                btn.config(text=f"▶ {label}")
            else:
                sub_frame.pack(fill="x", padx=10, pady=4)
                btn.config(text=f"▼ {label}")
                refresh_preview()

        btn.config(command=toggle)

        return {
            "enabled": section_enabled,
            "count": count,
            "prefix": prefix,
            "base": base,
            "suffix": suffix,
            "min": size_from,
            "max": size_to,
            "get_names": generate_names
        }

    image = section_factory(inner_frame, "🖼️ Image Files", "image", ".jpg")
    video = section_factory(inner_frame, "🎥 Video Files", "video", ".mp4")
    text = section_factory(inner_frame, "📄 Text Files", "note", ".txt")

    # Toggle ZIP section
    def toggle_zip():
        if frame.winfo_ismapped():
            frame.pack_forget()
            btn.config(text="▶ 📦 ZIP Files")
        else:
            frame.pack(fill="x", padx=10, pady=4)
            btn.config(text="▼ 📦 ZIP Files")

    btn.config(command=toggle_zip)

    return {
        "zipname": zipname_entry,
        "password": password_entry,
        "frame": frame,
        "btn": btn,
        "image": image,
        "video": video,
        "text": text
    }

# ✅ Add to layout
zip_section = create_zip_file_section(scrollable_content)

text_section  = create_file_section(scrollable_content, "📄 Text Files", [".txt"])

def create_output_settings_section(master):
    outer = tk.Frame(master, bg="#ffffff", bd=1, relief="solid")
    outer.pack(fill="x", pady=6, padx=12, anchor="n")

    # --- Expand/Collapse toggle ---
    section_frame = tk.Frame(outer, bg="#ffffff")
    log_display_box = scrolledtext.ScrolledText(outer, height=8, font=PREVIEW_FONT, state="normal", wrap="word")

    expanded = tk.BooleanVar(value=False)

    def toggle():
        if expanded.get():
            section_frame.pack(fill="x", padx=10, pady=4)
            log_display_box.pack(fill="x", padx=10, pady=(0, 10))
            toggle_btn.config(text="▼ Output Settings / IP Log")
        else:
            section_frame.pack_forget()
            log_display_box.pack_forget()
            toggle_btn.config(text="▶ Output Settings / IP Log")

    toggle_btn = tk.Button(
        outer, text="▶ Output Settings / IP Log", font=HEADER_FONT,
        bg="#ffffff", relief="flat", anchor="w", command=lambda: expanded.set(not expanded.get())
    )
    toggle_btn.pack(fill="x", padx=10, pady=(10, 0))

    expanded.trace_add("write", lambda *_: toggle())

    # --- Seeder & Leecher Counts ---
    row1 = tk.Frame(section_frame, bg="#ffffff")
    row1.pack(fill="x", pady=(5, 2))

    tk.Label(row1, text="Seeders (Sandbox peers):", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    seeders_entry = tk.Entry(row1, width=5)
    seeders_entry.insert(0, "2")
    seeders_entry.pack(side="left", padx=(0, 15))

    tk.Label(row1, text="Leechers (peersim peers):", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    leechers_entry = tk.Entry(row1, width=5)
    leechers_entry.insert(0, "20")
    leechers_entry.pack(side="left")

    # --- Save Hosted Files Row ---
    row_host = tk.Frame(section_frame, bg="#ffffff")
    row_host.pack(fill="x", pady=(5, 5))

    tk.Label(row_host, text="Save hosted files to:", bg="#ffffff", font=LABEL_FONT).pack(side="left", padx=(0, 5))

    hosted_folder_var = tk.StringVar(value="")

    def browse_hosted_folder():
        folder = filedialog.askdirectory()
        if folder:
            hosted_folder_var.set(folder)

    host_browse_btn = tk.Button(row_host, text="Browse", font=("Segoe UI", 9), command=browse_hosted_folder)
    host_browse_btn.pack(side="left", padx=5)

    host_path_label = tk.Label(row_host, textvariable=hosted_folder_var, bg="#ffffff", font=("Segoe UI", 9, "italic"), fg="gray")
    host_path_label.pack(side="left", padx=5, expand=True)

    # --- Save logs row ---
    row2 = tk.Frame(section_frame, bg="#ffffff")
    row2.pack(fill="x", pady=(5, 5))

    save_logs_var = tk.BooleanVar(value=False)

    save_logs_btn = tk.Checkbutton(row2, text="Save Logs", variable=save_logs_var, bg="#ffffff", font=LABEL_FONT)
    save_logs_btn.pack(side="left", padx=(0, 10))

    browse_button = tk.Button(row2, text="Browse", font=("Segoe UI", 9), state="disabled")
    browse_button.pack(side="left", padx=5)

    selected_folder = tk.StringVar(value="No folder selected")
    folder_display = tk.Label(row2, textvariable=selected_folder, bg="#ffffff", font=("Segoe UI", 9, "italic"), fg="gray")
    folder_display.pack(side="left", padx=5, expand=True)

    def choose_folder():
        folder = filedialog.askdirectory()
        if folder:
            selected_folder.set(folder)

    def toggle_browse(*_):
        browse_button.config(state="normal" if save_logs_var.get() else "disabled")

    save_logs_var.trace_add("write", toggle_browse)
    browse_button.config(command=choose_folder)

    return seeders_entry, leechers_entry, save_logs_var, selected_folder, log_display_box, hosted_folder_var


# ✅ This line actually adds the Output Settings section to the GUI
seeders_entry, leechers_entry, save_logs_var, log_folder_var, ip_log_box, hosted_folder_var = create_output_settings_section(scrollable_content)

# === Final Buttons ===
btn_frame = tk.Frame(scrollable_content, bg="#f5f5f5")
btn_frame.pack(pady=10)

def host_files():
    if not hosted_folder_var.get():
        tk.messagebox.showwarning("Missing Path", "Please select a folder to save hosted files.")
        return

    output_folder = hosted_folder_var.get()
    all_sections = [image_section, video_section, text_section]
    total_files_created = 0

    for section in all_sections:
        if not section["enabled"].get():
            continue

    # Extract user inputs safely
        prefix = section["prefix_cb"].get()
        base_name = section["base_name"].get()
        suffix = section["suffix_cb"].get()
        ext = section["format_cb"].get()
        ext_lower = ext.lower()

        try:
            count = int(section["count_entry"].get())
            size_from = float(section["size_from"].get())
            size_to = float(section["size_to"].get())
        except ValueError:
            tk.messagebox.showerror("Error", f"Invalid size or count in {ext} section.")
            continue

        filenames = generate_preview(prefix, base_name, suffix, count)
        subfolder = section["folder_entry"].get().strip() or "misc"
        target_dir = os.path.join(output_folder, subfolder)
        os.makedirs(target_dir, exist_ok=True)

    # === Handle TEXT files with text box input ===
        if ext_lower == ".txt" and section.get("text_box"):
            content = section["text_box"].get("1.0", tk.END).strip()
            if content and content != "Insert text here":
                    filename = section["folder_entry"].get().strip() or "Note"
                    path = os.path.join(output_folder, filename + ".txt")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    ip_log_box.insert(tk.END, f"[+] Created: {filename}.txt ({len(content)} chars)\n")
            else:
                ip_log_box.insert(tk.END, "[!] Skipped: No text entered.\n")
            continue  # Don't make multiple dummy `.txt` files

    # === Handle image/video files ===
    for name in filenames:
        size_mb = round(random.uniform(size_from, size_to), 2)
        path = os.path.join(target_dir, name + ext)
        if ext_lower == ".txt":
            continue

        ip_log_box.insert(tk.END, f"[+] Created: {name}{ext} ({size_mb:.2f} MB)\n")
        ip_log_box.see(tk.END)

        if ext_lower in [".mp4", ".avi", ".mov"]:
            create_dummy_video(path, size_mb)
        elif ext_lower in [".zip", ".7z"]:
            with open(path, "wb") as f:
                f.write(os.urandom(int(size_mb * 1024 * 1024)))
        elif ext_lower in [".jpg", ".png", ".bmp"]:
            create_dummy_image(path, size_mb, image_format=ext)



        
        # === ZIP Creation Section ===
    if zip_section["zipname"].get():
        zipname = zip_section["zipname"].get()
        if not zipname.lower().endswith(".zip"):
            zipname += ".zip"
        password = zip_section["password"].get()
        zip_path = os.path.join(output_folder, zipname)


        zip_config = {
            "image": {
                "enabled": zip_section["image"]["enabled"].get(),
                "min": zip_section["image"]["min"].get(),
                "max": zip_section["image"]["max"].get(),
                "names": zip_section["image"]["get_names"](),
            },
            "video": {
                "enabled": zip_section["video"]["enabled"].get(),
                "min": zip_section["video"]["min"].get(),
                "max": zip_section["video"]["max"].get(),
                "names": zip_section["video"]["get_names"](),
            },
            "text": {
                "enabled": zip_section["text"]["enabled"].get(),
                "size": zip_section["text"]["max"].get(),  # uses 'max' as total size
                "names": zip_section["text"]["get_names"](),
            },
        }

        create_zip_with_files(zip_path, zip_config, password)
        total_files_created += 1
    if save_logs_var.get() and log_folder_var.get() != "No folder selected":
        log_path = os.path.join(log_folder_var.get(), "generation_log.txt")
        with open(log_path, "w") as log_file:
            log_file.write(ip_log_box.get("1.0", tk.END))

    tk.messagebox.showinfo("Done", f"✅ {total_files_created} files created in:\n{output_folder}")

# Create a Label for estimated size below all sections and above buttons
estimated_size_var = tk.StringVar(value="Estimated size of hosted files: 0.00 MB")
estimated_size_label = tk.Label(scrollable_content, textvariable=estimated_size_var, font=LABEL_FONT, bg="#f5f5f5")
estimated_size_label.pack(pady=(5,10))

def safe_float(val, default=0.0):
    try:
        return float(val)
    except:
        return default

def safe_int(val, default=0):
    try:
        return int(val)
    except:
        return default

def calculate_estimated_size():
    total_size = 0.0

    sections_to_check = [image_section, video_section]

    # Images and Videos sections
    for section in sections_to_check:
        if section["enabled"].get():
            count = safe_int(section["count_entry"].get(), 0)
            size_from = safe_float(section["size_from"].get(), 0)
            size_to = safe_float(section["size_to"].get(), 0)
            avg_size = (size_from + size_to) / 2
            total_size += count * avg_size

    # ZIP Section internal files
    if zip_section["zipname"].get() and zip_section["zipname"].get().strip() != "":
        for key in ["image", "video", "text"]:
            internal = zip_section[key]
            if internal["enabled"].get():
                count = safe_int(internal["count"].get(), 0)
                size_from = safe_float(internal["min"].get(), 0)
                size_to = safe_float(internal["max"].get(), 0)
                avg_size = (size_from + size_to) / 2
                total_size += count * avg_size

    estimated_size_var.set(f"Estimated size of hosted files: {total_size:.2f} MB")

def bind_zip_internal_changes(section):
    widgets = [
        section["count"],
        section["min"],
        section["max"],
        section["enabled"]
    ]
    for w in widgets:
        if isinstance(w, tk.Entry):
            w.bind("<KeyRelease>", lambda e: calculate_estimated_size())
        elif isinstance(w, tk.BooleanVar):
            w.trace_add("write", lambda *args: calculate_estimated_size())


def bind_to_changes(section):
    widgets = [
        section["count_entry"],
        section["size_from"],
        section["size_to"],
        section["enabled"]
    ]
    for w in widgets:
        if isinstance(w, tk.Entry):
            w.bind("<KeyRelease>", lambda e: calculate_estimated_size())
        elif isinstance(w, tk.BooleanVar):
            w.trace_add("write", lambda *args: calculate_estimated_size())

bind_to_changes(image_section)
bind_to_changes(video_section)
bind_zip_internal_changes(zip_section["image"])
bind_zip_internal_changes(zip_section["video"])
bind_zip_internal_changes(zip_section["text"])


# Bind ZIP name change to recalc (if ZIP disabled by empty name)
zip_section["zipname"].bind("<KeyRelease>", lambda e: calculate_estimated_size())

# Initial call on startup
calculate_estimated_size()

tk.Button(btn_frame, text="🎯 Host Files", font=("Segoe UI", 12, "bold"),
          bg="#4CAF50", fg="white", padx=20, pady=10,
          command=host_files).pack(side="left", padx=10)

tk.Button(btn_frame, text="🕵️ Monitor IP", font=("Segoe UI", 12, "bold"),
          bg="#2196F3", fg="white", padx=20, pady=10).pack(side="left", padx=10)

tk.Button(btn_frame, text="🔄 Refresh IP", font=("Segoe UI", 12),
          bg="#FF9800", fg="white", padx=10, pady=10).pack(side="left", padx=10)

root.mainloop()
