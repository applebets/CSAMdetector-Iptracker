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

def generate_filenames(base, count, style, prefix=True):
    result = []
    for i in range(1, count + 1):
        tag = f"{i}." if style == "1." else f"#{i}" if style == "#" else f"_{i}"
        name = f"{tag}{base}" if prefix else f"{base}{tag}"
        result.append(name)
    return result

def create_zip_with_files(path, config, password=None):
    with pyzipper.AESZipFile(path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as z:
        if password:
            z.setpassword(password.encode())
            z.setencryption(pyzipper.WZ_AES, nbits=256)

        if config['image']['enabled']:
            for name in config['image']['names']:
                z.writestr(name + ".jpg", generate_image_bytes())

        if config['video']['enabled']:
            for name in config['video']['names']:
                z.writestr(name + ".mp4", generate_video_bytes(1))

        if config['text']['enabled']:
            for name in config['text']['names']:
                z.writestr(name + ".txt", generate_text_bytes())

# === GUI Setup ===
root = tk.Tk()
root.title("📦 Smart ZIP Host")
root.geometry("600x720")
root.configure(bg="#f5f5f5")

folder_var = tk.StringVar()
zipname_var = tk.StringVar(value="hosted.zip")
lock_var = tk.BooleanVar(value=False)
password_var = tk.StringVar()

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

def toggle_section(frame, btn):
    if frame.winfo_ismapped():
        frame.pack_forget()
        btn.config(text=btn.cget("text").replace("▼", "▶"))
    else:
        frame.pack(fill="x", padx=20, pady=4)
        btn.config(text=btn.cget("text").replace("▶", "▼"))

def create_expandable_file_section(master, label, key, ext):
    container = tk.Frame(master, bg="#f5f5f5")
    container.pack(fill="x", anchor="n")

    btn = tk.Button(container, text=f"▶ {label}", font=("Segoe UI", 10, "bold"), anchor="w", bg="#ddd", relief="flat")
    btn.pack(fill="x", padx=10, pady=(6, 0))

    frame = tk.Frame(container, bg="#ffffff", bd=1, relief="solid")
    preview_box = scrolledtext.ScrolledText(frame, height=5, font=("Consolas", 9), state="disabled")
    preview_box.pack(fill="x", padx=10, pady=(5, 10))

    row1 = tk.Frame(frame, bg="#ffffff")
    row1.pack(pady=2)
    tk.Label(row1, text="Base Name:", bg="#ffffff").pack(side="left", padx=5)
    base_entry = tk.Entry(row1, width=15)
    base_entry.insert(0, key)
    base_entry.pack(side="left")

    row2 = tk.Frame(frame, bg="#ffffff")
    row2.pack(pady=2)
    tk.Label(row2, text="Count:", bg="#ffffff").pack(side="left", padx=5)
    count_entry = tk.Entry(row2, width=5)
    count_entry.insert(0, "3")
    count_entry.pack(side="left", padx=5)

    tk.Label(row2, text="Style:", bg="#ffffff").pack(side="left", padx=(15, 5))
    style_cb = ttk.Combobox(row2, values=["1.", "#", "_"], width=5)
    style_cb.set("1.")
    style_cb.pack(side="left")

    row3 = tk.Frame(frame, bg="#ffffff")
    row3.pack(pady=2)
    prefix_var = tk.BooleanVar(value=True)
    tk.Radiobutton(row3, text="Prefix", variable=prefix_var, value=True, bg="#ffffff").pack(side="left", padx=5)
    tk.Radiobutton(row3, text="Suffix", variable=prefix_var, value=False, bg="#ffffff").pack(side="left")

    def refresh_preview(*_):
        try:
            count = int(count_entry.get())
            base = base_entry.get()
            style = style_cb.get()
            prefix = prefix_var.get()
            names = generate_filenames(base, count, style, prefix)
            preview_box.config(state="normal")
            preview_box.delete("1.0", tk.END)
            for name in names:
                preview_box.insert(tk.END, name + ext + "\n")
            preview_box.config(state="disabled")
        except:
            preview_box.config(state="normal")
            preview_box.delete("1.0", tk.END)
            preview_box.insert(tk.END, "[Invalid Input]")
            preview_box.config(state="disabled")

    for widget in [base_entry, count_entry]:
        widget.bind("<KeyRelease>", refresh_preview)
    style_cb.bind("<<ComboboxSelected>>", refresh_preview)
    prefix_var.trace_add("write", lambda *_: refresh_preview())

    btn.config(command=lambda: toggle_section(frame, btn))
    return {
        "enabled": True,
        "frame": frame,
        "base_entry": base_entry,
        "count_entry": count_entry,
        "style_cb": style_cb,
        "prefix_var": prefix_var,
        "preview": preview_box,
        "refresh": refresh_preview,
        "ext": ext,
        "get_names": lambda: generate_filenames(
            base_entry.get(),
            int(count_entry.get()),
            style_cb.get(),
            prefix_var.get()
        )
    }

# === Layout ===

# ZIP name and folder in same row
row_top = tk.Frame(root, bg="#f5f5f5")
row_top.pack(fill="x", padx=10, pady=2)
tk.Label(row_top, text="ZIP Name:", bg="#f5f5f5").pack(side="left")
tk.Entry(row_top, textvariable=zipname_var, width=25).pack(side="left", padx=5)
tk.Label(row_top, text="Save To:", bg="#f5f5f5").pack(side="left", padx=(15, 5))
tk.Entry(row_top, textvariable=folder_var, width=30).pack(side="left")
tk.Button(row_top, text="📁", command=browse_folder).pack(side="left", padx=5)

# Password Row (now below ZIP name)
pw_row = tk.Frame(root, bg="#f5f5f5")
pw_row.pack(pady=(5, 10), fill="x", padx=10)

def toggle_password_entry():
    if lock_var.get():
        password_entry.config(state="normal")
    else:
        password_entry.config(state="disabled")
        password_var.set("")

tk.Checkbutton(pw_row, text="🔒 Lock ZIP with Password", variable=lock_var, bg="#f5f5f5",
               font=("Segoe UI", 10, "bold"), command=toggle_password_entry).pack(side="left")
password_entry = tk.Entry(pw_row, textvariable=password_var, width=20, state="disabled")
password_entry.pack(side="left", padx=10)

# Sections
image_section = create_expandable_file_section(root, "🖼️ Image Files", "image", ".jpg")
video_section = create_expandable_file_section(root, "🎞️ Video Files", "video", ".mp4")

# Text section
text_container = tk.Frame(root, bg="#f5f5f5")
text_container.pack(fill="x", anchor="n")

text_btn = tk.Button(text_container, text="▶ 📄 Text Files", font=("Segoe UI", 10, "bold"), anchor="w", bg="#ddd", relief="flat")
text_btn.pack(fill="x", padx=10, pady=(6, 0))

text_frame = tk.Frame(text_container, bg="#ffffff", bd=1, relief="solid")
text_enabled = tk.BooleanVar(value=True)
tk.Checkbutton(text_frame, text="Include Text Files", variable=text_enabled, bg="#ffffff").pack(anchor="w", padx=10, pady=5)

tk.Label(text_frame, text="File Names (comma-separated):", bg="#ffffff").pack(anchor="w", padx=10)
text_names_entry = tk.Entry(text_frame, width=50)
text_names_entry.insert(0, "note1,note2")
text_names_entry.pack(padx=10, pady=(0, 10), anchor="w")

def toggle_text_section():
    toggle_section(text_frame, text_btn)
text_btn.config(command=toggle_text_section)

# === Final Button ===
def create_zip():
    folder = folder_var.get()
    if not folder:
        messagebox.showwarning("Folder Missing", "Please select an output folder.")
        return

    name = zipname_var.get()
    if not name.endswith(".zip"):
        name += ".zip"
    path = os.path.join(folder, name)

    try:
        image_section["refresh"]()
        video_section["refresh"]()

        config = {
            "image": {
                "enabled": True,
                "names": image_section["get_names"]()
            },
            "video": {
                "enabled": True,
                "names": video_section["get_names"]()
            },
            "text": {
                "enabled": text_enabled.get(),
                "names": [x.strip() for x in text_names_entry.get().split(",") if x.strip()]
            }
        }

        password = password_var.get() if lock_var.get() and password_var.get() else None
        create_zip_with_files(path, config, password=password)
        messagebox.showinfo("Success", f"✅ ZIP file created:\n{path}")
    except Exception as e:
        messagebox.showerror("Error", f"Something went wrong:\n{e}")

tk.Button(root, text="📦 Create ZIP", command=create_zip, bg="#4CAF50", fg="white",
          font=("Segoe UI", 11, "bold")).pack(pady=15)

root.mainloop()
