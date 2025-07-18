import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import random

def create_dummy_video(path, size_mb):
    target_size = int(size_mb * 1024 * 1024)
    with open(path, "wb") as f:
        f.write(os.urandom(target_size))

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

def generate_videos():
    folder = folder_var.get()
    try:
        size_from = float(size_from_entry.get())
        size_to = float(size_to_entry.get())
        count = int(count_entry.get())
    except:
        messagebox.showerror("Invalid Input", "Please enter valid numbers.")
        return

    if not folder:
        messagebox.showwarning("Folder Missing", "Select a folder to save video files.")
        return

    fmt = format_cb.get()
    for i in range(1, count + 1):
        name = f"video_{i}{fmt}"
        path = os.path.join(folder, name)
        size_mb = round(random.uniform(size_from, size_to), 2)
        create_dummy_video(path, size_mb)

    messagebox.showinfo("Done", f"{count} dummy video files created in:\n{folder}")

# === GUI ===
root = tk.Tk()
root.title("🎥 Dummy Video Generator")
root.geometry("400x280")

tk.Label(root, text="Save Folder:").pack(anchor="w", padx=10, pady=(10, 0))
folder_var = tk.StringVar()
tk.Entry(root, textvariable=folder_var, width=40).pack(padx=10)
tk.Button(root, text="Browse", command=browse_folder).pack(padx=10, pady=5)

tk.Label(root, text="Size Range (MB):").pack(anchor="w", padx=10, pady=(10, 0))
range_frame = tk.Frame(root)
range_frame.pack(padx=10)
size_from_entry = tk.Entry(range_frame, width=5)
size_from_entry.insert(0, "5")
size_from_entry.pack(side="left")
tk.Label(range_frame, text="to").pack(side="left", padx=5)
size_to_entry = tk.Entry(range_frame, width=5)
size_to_entry.insert(0, "10")
size_to_entry.pack(side="left")

tk.Label(root, text="Format:").pack(anchor="w", padx=10, pady=(10, 0))
format_cb = ttk.Combobox(root, values=[".mp4", ".avi", ".mov"], width=10)
format_cb.set(".mp4")
format_cb.pack(padx=10)

tk.Label(root, text="Count:").pack(anchor="w", padx=10, pady=(10, 0))
count_entry = tk.Entry(root, width=10)
count_entry.insert(0, "3")
count_entry.pack(padx=10)

tk.Button(root, text="Generate Videos", bg="#2196F3", fg="white",
          font=("Segoe UI", 10, "bold"), command=generate_videos).pack(pady=15)

root.mainloop()
