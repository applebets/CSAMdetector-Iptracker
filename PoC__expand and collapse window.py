import tkinter as tk
from tkinter import ttk, scrolledtext

class CollapsibleFrame(tk.Frame):
    def __init__(self, parent, text="", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.show = tk.BooleanVar(value=True)

        # Header Frame with toggle button
        header = ttk.Frame(self)
        header.pack(fill="x", expand=True)

        self.toggle_button = ttk.Button(header, width=2, text="▼", command=self.toggle)
        self.toggle_button.pack(side="left")

        label = ttk.Label(header, text=text, font=("Arial", 11, "bold"))
        label.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        # Content Frame
        self.content = ttk.Frame(self)
        self.content.pack(fill="x", expand=True)

    def toggle(self):
        if self.show.get():
            self.content.forget()
            self.toggle_button.config(text="▶")
            self.show.set(False)
        else:
            self.content.pack(fill="x", expand=True)
            self.toggle_button.config(text="▼")
            self.show.set(True)

def main():
    root = tk.Tk()
    root.title("Collapsible Frame with Button Between")
    root.geometry("500x500")

    # === Collapsible Section ===
    collapsible = CollapsibleFrame(root, text="⚙️ Download Settings")
    collapsible.pack(fill="x", padx=10, pady=(10, 5))

    # Sample Widgets
    ttk.Label(collapsible.content, text="Number of images to download:").grid(row=0, column=0, sticky="w", pady=2)
    ttk.Combobox(collapsible.content, values=["2", "5", "10", "All"], width=10).grid(row=0, column=1, pady=2, padx=5)

    ttk.Label(collapsible.content, text="Number of videos to download:").grid(row=1, column=0, sticky="w", pady=2)
    ttk.Combobox(collapsible.content, values=["1", "2", "3", "5", "20"], width=10).grid(row=1, column=1, pady=2, padx=5)

    ttk.Checkbutton(collapsible.content, text="Download all files (including non-media)").grid(row=2, column=0, columnspan=2, sticky="w", pady=5)

    ttk.Radiobutton(collapsible.content, text="Keep files after scan", value=1).grid(row=3, column=0, sticky="w", pady=2)
    ttk.Radiobutton(collapsible.content, text="Delete files after scan", value=2).grid(row=3, column=1, sticky="w", pady=2)

    # === Random Button Between ===
    random_btn = ttk.Button(root, text="🎲 Random Button", command=lambda: print("Clicked!"))
    random_btn.pack(pady=(5, 5))

    # === Log Section ===
    log_label = ttk.Label(root, text="📜 Log Output", font=("Arial", 11, "bold"))
    log_label.pack(anchor="w", padx=10, pady=(10, 0))

    log_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10, font=("Consolas", 10))
    log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    log_box.insert(tk.END, "👇 Collapse the settings section above to see this shift!\n\n")
    log_box.insert(tk.END, "This is where real-time logs or progress would be shown.\n")

    root.mainloop()

if __name__ == "__main__":
    main()
