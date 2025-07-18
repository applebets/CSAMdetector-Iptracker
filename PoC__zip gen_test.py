import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import pyzipper
from PIL import Image
import io
import os
import random

# === Helper Functions ===
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

def generate_filenames(base, count, prefix, suffix):
    result = []
    for i in range(1, count + 1):
        # Process prefix
        if prefix == "-":
            prefix_str = ""
        elif prefix.startswith("1") and len(prefix) > 1:
            # prefix like "1." or "1_"
            prefix_str = str(i) + prefix[1:]
        elif prefix == "1":
            prefix_str = str(i)
        else:
            prefix_str = prefix + str(i)

        # Process suffix
        if suffix == "-":
            suffix_str = ""
        elif suffix.startswith("1") and len(suffix) > 1:
            # suffix like "1." or "1_"
            suffix_str = str(i) + suffix[1:]
        elif suffix == "1":
            suffix_str = str(i)
        elif suffix[0] in ("_", "#"):
            # suffix like "_1" or "#1"
            suffix_str = suffix[0] + str(i)
        else:
            suffix_str = suffix

        # Compose filename
        name = f"{prefix_str}{base}{suffix_str}"
        result.append(name)
    return result

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

            # Adjust last file to make total exact
            sizes[-1] = int(total_size - sum(sizes[:-1]))

            for name, sz in zip(names, sizes):
                z.writestr(name + ".txt", os.urandom(sz))




# === GUI ===
root = tk.Tk()
root.title("📦 Smart ZIP Host")
root.geometry("700x750")
root.configure(bg="#f5f5f5")

canvas = tk.Canvas(root, bg="#f5f5f5")
scroll = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
frame = tk.Frame(canvas, bg="#f5f5f5")
frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=frame, anchor="nw")
canvas.configure(yscrollcommand=scroll.set)
canvas.pack(side="left", fill="both", expand=True)
scroll.pack(side="right", fill="y")

folder_var = tk.StringVar()
zipname_var = tk.StringVar(value="hosted.zip")
password_var = tk.StringVar()

# === Top Row ===
top = tk.Frame(frame, bg="#f5f5f5")
top.pack(fill="x", pady=5, padx=10)

tk.Label(top, text="ZIP Name:", bg="#f5f5f5").pack(side="left")
tk.Entry(top, textvariable=zipname_var, width=25).pack(side="left", padx=5)
tk.Label(top, text="Save To:", bg="#f5f5f5").pack(side="left", padx=(15, 5))
tk.Entry(top, textvariable=folder_var, width=30).pack(side="left")
tk.Button(top, text="📁", command=lambda: folder_var.set(filedialog.askdirectory())).pack(side="left", padx=5)

# === Password Row ===
pw = tk.Frame(frame, bg="#f5f5f5")
pw.pack(pady=(0, 10), padx=10, anchor="w")
tk.Label(pw, text="Password (recommended):", bg="#f5f5f5", font=("Segoe UI", 10, "bold")).pack(side="left")
tk.Entry(pw, textvariable=password_var, width=25).pack(side="left", padx=10)

# === Expandable Section Factory ===
def create_section(master, label, key, ext):
    container = tk.Frame(master, bg="#f5f5f5")
    container.pack(fill="x", anchor="n")

    section_enabled = tk.BooleanVar(value=False)
    btn = tk.Button(container, text=f"▶ {label}", font=("Segoe UI", 10, "bold"), anchor="w", bg="#ddd", relief="flat")
    btn.pack(fill="x", padx=10, pady=(5, 0))

    frame = tk.Frame(container, bg="#ffffff", bd=1, relief="solid")

    # Top checkbox
    tk.Checkbutton(frame, text=f"Include {label.strip('▶ ')}", variable=section_enabled, bg="#ffffff").pack(anchor="w", padx=10)

    row = tk.Frame(frame, bg="#ffffff")
    row.pack(pady=5, padx=10)

    tk.Label(row, text="Count").grid(row=0, column=0)
    count_entry = tk.Entry(row, width=4)
    count_entry.insert(0, "3")
    count_entry.grid(row=1, column=0)

    tk.Label(row, text="Prefix").grid(row=0, column=1)
    prefix_cb = ttk.Combobox(row, values=["#", "1.", "1_", "-"], width=6)
    prefix_cb.set("1.")
    prefix_cb.grid(row=1, column=1)


    tk.Label(row, text="Base").grid(row=0, column=2)
    base_entry = tk.Entry(row, width=10)
    base_entry.insert(0, key)
    base_entry.grid(row=1, column=2)

    tk.Label(row, text="Suffix").grid(row=0, column=3)
    suffix_cb = ttk.Combobox(row, values=["_1", "#1", "1", "-"], width=6)
    suffix_cb.set("-")
    suffix_cb.grid(row=1, column=3)


    # Size Range Row
    size_row = tk.Frame(frame, bg="#ffffff")
    size_row.pack(pady=2, padx=10)

    tk.Label(size_row, text="Min Size (MB)").grid(row=0, column=0)
    min_size_entry = tk.Entry(size_row, width=6)
    min_size_entry.insert(0, "0.5")
    min_size_entry.grid(row=0, column=1)

    tk.Label(size_row, text="Max Size (MB)").grid(row=0, column=2, padx=(10, 0))
    max_size_entry = tk.Entry(size_row, width=6)
    max_size_entry.insert(0, "1.5")
    max_size_entry.grid(row=0, column=3)


    preview = scrolledtext.ScrolledText(frame, height=5, font=("Consolas", 9), state="disabled")
    preview.pack(fill="x", padx=10, pady=(5, 10))

    def refresh_preview(*_):
        try:
            names = generate_filenames(
                base_entry.get(),
                int(count_entry.get()),
                prefix_cb.get(),
                suffix_cb.get()
            )



            preview.config(state="normal")
            preview.delete("1.0", tk.END)
            for name in names:
                preview.insert(tk.END, name + ext + "\n")
            preview.config(state="disabled")
        except:
            preview.config(state="normal")
            preview.delete("1.0", tk.END)
            preview.insert(tk.END, "[Invalid Input]")
            preview.config(state="disabled")

        

    for w in [base_entry, count_entry]:
        w.bind("<KeyRelease>", refresh_preview)
        prefix_cb.bind("<<ComboboxSelected>>", refresh_preview)
        suffix_cb.bind("<<ComboboxSelected>>", refresh_preview)


    btn.config(command=lambda: toggle())
    def toggle():
        if frame.winfo_ismapped():
            frame.pack_forget()
            btn.config(text=f"▶ {label}")
        else:
            frame.pack(fill="x", padx=20, pady=4)
            btn.config(text=f"▼ {label}")
            refresh_preview()

    return {
        "enabled": section_enabled,
        "count": count_entry,
        "prefix": prefix_cb,
        "suffix": suffix_cb,
        "base": base_entry,
        "preview": preview,
        "min_size": min_size_entry,
        "max_size": max_size_entry,
        "get_names": lambda: generate_filenames(
            base_entry.get(),
            int(count_entry.get()),
            prefix_cb.get(),
            suffix_cb.get()
        )
}



# Create Sections
image_section = create_section(frame, "🖼️ Image Files", "image", ".jpg")
video_section = create_section(frame, "🎞️ Video Files", "video", ".mp4")

# === Text Section
text_container = tk.Frame(frame, bg="#f5f5f5")
text_container.pack(fill="x", anchor="n")

text_btn = tk.Button(text_container, text="▶ 📄 Text Files", font=("Segoe UI", 10, "bold"),
                     anchor="w", bg="#ddd", relief="flat")
text_btn.pack(fill="x", padx=10, pady=(6, 0))

text_frame = tk.Frame(text_container, bg="#ffffff", bd=1, relief="solid")
text_enabled = tk.BooleanVar(value=False)
tk.Checkbutton(text_frame, text="Include Text Files", variable=text_enabled, bg="#ffffff").pack(anchor="w", padx=10, pady=5)

tk.Label(text_frame, text="File Names (comma-separated):", bg="#ffffff").pack(anchor="w", padx=10)
text_names_entry = tk.Entry(text_frame, width=50)
text_names_entry.insert(0, "note1,note2")
text_names_entry.pack(padx=10, pady=(0, 10), anchor="w")
tk.Label(text_frame, text="Total Text Size (MB):", bg="#ffffff").pack(anchor="w", padx=10)
text_size_entry = tk.Entry(text_frame, width=10)
text_size_entry.insert(0, "1.0")
text_size_entry.pack(padx=10, pady=(0, 10), anchor="w")

def toggle_text_section():
    if text_frame.winfo_ismapped():
        text_frame.pack_forget()
        text_btn.config(text="▶ 📄 Text Files")
    else:
        text_frame.pack(fill="x", padx=20, pady=4)
        text_btn.config(text="▼ 📄 Text Files")
text_btn.config(command=toggle_text_section)

def update_total_estimate(*_):
    try:
        total = 0.0

        if image_section["enabled"].get():
            count = int(image_section["count"].get())
            min_s = float(image_section["min_size"].get())
            max_s = float(image_section["max_size"].get())
            total += count * ((min_s + max_s) / 2)

        if video_section["enabled"].get():
            count = int(video_section["count"].get())
            min_s = float(video_section["min_size"].get())
            max_s = float(video_section["max_size"].get())
            total += count * ((min_s + max_s) / 2)

        if text_enabled.get():
            size = float(text_size_entry.get())
            total += size

        zip_est_label.config(text=f"Estimated ZIP size: {total:.2f} MB")
    except:
        zip_est_label.config(text="Estimated ZIP size: [Invalid input]")

# === Global Estimated ZIP Size Label ===
zip_est_label = tk.Label(frame, text="Estimated ZIP size: 0.00 MB", bg="#f5f5f5", fg="blue", font=("Segoe UI", 10, "bold"))
zip_est_label.pack(pady=(10, 0), padx=10, anchor="w")

# === Create ZIP Button
def create_zip():
    folder = folder_var.get()
    zipname = zipname_var.get()
    password = password_var.get()

    if not folder or not zipname:
        messagebox.showerror("Missing Info", "Please provide folder and zip name.")
        return


    if not zipname.endswith(".zip"):
        zipname += ".zip"

    path = os.path.join(folder, zipname)
    try:
        config = {
            "image": {
                "enabled": image_section["enabled"].get(),
                "names": image_section["get_names"](),
                "min": image_section["min_size"].get(),
                "max": image_section["max_size"].get()
},
            "video": {
                "enabled": video_section["enabled"].get(),
                "names": video_section["get_names"](),
                "min": video_section["min_size"].get(),
                "max": video_section["max_size"].get()
},
            "text": {
                "enabled": text_enabled.get(),
                "names": [x.strip() for x in text_names_entry.get().split(",") if x.strip()],
                "size": text_size_entry.get()
}

        }
        if password.strip():
            create_zip_with_files(path, config, password)
        else:
            create_zip_with_files(path, config, None)

        messagebox.showinfo("Success", f"ZIP saved to:\n{path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

tk.Button(frame, text="📦 Create ZIP", command=create_zip, bg="#4CAF50", fg="white",
          font=("Segoe UI", 11, "bold")).pack(pady=15)

# Bind image/video text fields
for section in [image_section, video_section]:
    for w in [section["count"], section["min_size"], section["max_size"]]:
        w.bind("<KeyRelease>", update_total_estimate)
    section["enabled"].trace_add("write", lambda *_: update_total_estimate())

# Bind text fields
text_size_entry.bind("<KeyRelease>", update_total_estimate)
text_enabled.trace_add("write", lambda *_: update_total_estimate())

root.mainloop()



