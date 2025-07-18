import os
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox

def extract_video_frames(video_path, interval=20, start_offset=5):
    if not os.path.exists(video_path):
        messagebox.showerror("Error", "Video file not found.")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        messagebox.showerror("Error", "Failed to open video.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    save_dir = os.path.join(os.path.dirname(__file__), "slice_videos")
    os.makedirs(save_dir, exist_ok=True)

    current_time = start_offset
    frame_count = 0

    while current_time < duration:
        cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
        success, frame = cap.read()
        if not success:
            break
        frame_filename = os.path.join(save_dir, f"frame_{frame_count:03d}_at_{int(current_time)}s.jpg")
        cv2.imwrite(frame_filename, frame)
        print(f"Saved: {frame_filename}")
        frame_count += 1
        current_time += interval

    cap.release()
    messagebox.showinfo("Done", f"Extracted {frame_count} frames to:\n{save_dir}")

def browse_and_process():
    file_path = filedialog.askopenfilename(
        title="Select Video File",
        filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")]
    )
    if file_path:
        extract_video_frames(file_path)

# GUI Setup
root = tk.Tk()
root.title("Video Slicer - Frame Every 20s (Starting at 5s)")
root.geometry("400x200")

label = tk.Label(root, text="Select a video to extract slices from", font=("Arial", 12))
label.pack(pady=20)

btn = tk.Button(root, text="Browse Video", command=browse_and_process, font=("Arial", 12))
btn.pack(pady=10)

root.mainloop()
