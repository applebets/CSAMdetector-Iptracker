import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import random
from PIL import Image
import io

def create_dummy_image(path, size_mb, img_format):
    img = Image.new("RGB", (256, 256), color=(random.randint(0,255), random.randint(0,255), random.randint(0,255)))
    buffer = io.BytesIO()

    # Convert extension to format for PIL
    pil_format = img_format.strip(".").upper()
    if pil_format == "JPG":
        pil_format = "JPEG"

    quality = 95 if pil_format == "JPEG" else None
    img.save(buffer, format=pil_format, quality=quality)

    current_size = buffer.tell()
    target_size = int(size_mb * 1024 * 1024)
    if current_size < target_size:
        buffer.write(os.urandom(target_size - current_size))

    with open(path, "wb") as f:
        f.write(buffer.getvalue())

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

def generate_images():
    folder = folder_var.get()
    try:
        size_from = float(size_from_entry.get())
        size_to = float(size_to_entry.get())
        count = int(count_entry.get())
    except:
        messagebox.showerror("Invalid Input", "Please enter valid numbers.")
        return

    if not folder:
        messagebox.showwarning("Folder Missing", "Select a folder to save images.")
        return

    fmt = format_cb.get()
    for i in range(1, count + 1):
        name = f"dummy_{i}{fmt}"
        path = os.path.join(folder, name)
        size_mb = round(random.uniform(size_from, size_to), 2)
        create_dummy_image(path, size_mb, fmt)

    messagebox.showinfo("Done", f"{count} images created in:\n{folder}")

# === GUI ===
root = tk.Tk()
root.title("🖼️ Dummy Image Generator")
root.geometry("400x280")

tk.Label(root, text="Save Folder:").pack(anchor="w", padx=10, pady=(10, 0))
folder_var = tk.StringVar()
tk.Entry(root, textvariable=folder_var, width=40).pack(padx=10)
tk.Button(root, text="Browse", command=browse_folder).pack(padx=10, pady=5)

tk.Label(root, text="Size Range (MB):").pack(anchor="w", padx=10, pady=(10, 0))
range_frame = tk.Frame(root)
range_frame.pack(padx=10)
size_from_entry = tk.Entry(range_frame, width=5)
size_from_entry.insert(0, "1")
size_from_entry.pack(side="left")
tk.Label(range_frame, text="to").pack(side="left", padx=5)
size_to_entry = tk.Entry(range_frame, width=5)
size_to_entry.insert(0, "3")
size_to_entry.pack(side="left")

tk.Label(root, text="Format:").pack(anchor="w", padx=10, pady=(10, 0))
format_cb = ttk.Combobox(root, values=[".jpg", ".png"], width=10)
format_cb.set(".jpg")
format_cb.pack(padx=10)

tk.Label(root, text="Count:").pack(anchor="w", padx=10, pady=(10, 0))
count_entry = tk.Entry(root, width=10)
count_entry.insert(0, "5")
count_entry.pack(padx=10)

tk.Button(root, text="Generate Images", bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"), command=generate_images).pack(pady=15)

root.mainloop()
