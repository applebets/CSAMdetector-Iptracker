import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import imagehash
import os

def select_image():
    file_path = filedialog.askopenfilename(title="Select Image File", filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp")])
    if file_path:
        image_path_var.set(file_path)

def select_folder():
    folder = filedialog.askdirectory(title="Select Folder with Images")
    if folder:
        folder_path_var.set(folder)

def run_check():
    img_path = image_path_var.get()
    folder_path = folder_path_var.get()

    if not img_path or not os.path.isfile(img_path):
        messagebox.showerror("Error", "Please select a valid image file.")
        return
    if not folder_path or not os.path.isdir(folder_path):
        messagebox.showerror("Error", "Please select a valid folder.")
        return

    try:
        target_hash = imagehash.phash(Image.open(img_path).convert("RGB").resize((224, 224)))
        matches = []

        for root, _, files in os.walk(folder_path):
            for f in files:
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    try:
                        current_path = os.path.join(root, f)
                        candidate_hash = imagehash.phash(Image.open(current_path).convert("RGB").resize((224, 224)))
                        distance = target_hash - candidate_hash
                        if distance <= 4:  # threshold
                            matches.append((f, distance))
                    except Exception as e:
                        continue

        if matches:
            result = "\n".join([f"{f} (distance: {d})" for f, d in matches])
            messagebox.showinfo("✅ Match Found", f"Matching images:\n{result}")
        else:
            messagebox.showinfo("❌ No Match", "No matching images found in the selected folder.")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to compute hash:\n{e}")

# GUI Setup
root = tk.Tk()
root.title("🧪 PoC: Phash Image DB Match")
root.geometry("520x240")
root.resizable(False, False)

image_path_var = tk.StringVar()
folder_path_var = tk.StringVar()

tk.Label(root, text="🖼️ Image to Check:", font=("Arial", 10)).pack(anchor="w", padx=10, pady=(10, 2))
tk.Entry(root, textvariable=image_path_var, width=70).pack(padx=10)
tk.Button(root, text="Browse Image", command=select_image).pack(pady=(0, 10))

tk.Label(root, text="📁 Folder to Compare With:", font=("Arial", 10)).pack(anchor="w", padx=10, pady=(10, 2))
tk.Entry(root, textvariable=folder_path_var, width=70).pack(padx=10)
tk.Button(root, text="Browse Folder", command=select_folder).pack(pady=(0, 10))

tk.Button(root, text="🔍 Compare", command=run_check, bg="#2196F3", fg="white", font=("Arial", 11), width=20).pack(pady=10)

root.mainloop()
