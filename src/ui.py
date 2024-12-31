import tkinter as tk
from tkinter import filedialog, ttk
import os

class MainUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk Clip Generator")

        # Configure grid layout weights for resizing
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=2)
        self.root.grid_rowconfigure(tk.ALL, weight=1)

        # Source Video
        tk.Label(self.root, text="Source Video:").grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.source_video_path = tk.StringVar()
        tk.Entry(self.root, textvariable=self.source_video_path, state="readonly").grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        tk.Button(self.root, text="Browse", command=self.browse_source_video).grid(row=0, column=2, sticky="ew", padx=5, pady=5)

        # Intro Clip
        self.use_intro = tk.BooleanVar()
        tk.Checkbutton(self.root, text="Add Intro Clip:", variable=self.use_intro, command=self.toggle_intro_outro).grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.intro_clip_path = tk.StringVar()
        self.intro_entry = tk.Entry(self.root, textvariable=self.intro_clip_path, state="disabled")
        self.intro_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.intro_button = tk.Button(self.root, text="Browse", command=self.browse_intro_clip, state="disabled")
        self.intro_button.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        # Outro Clip
        self.use_outro = tk.BooleanVar()
        tk.Checkbutton(self.root, text="Add Outro Clip:", variable=self.use_outro, command=self.toggle_intro_outro).grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        self.outro_clip_path = tk.StringVar()
        self.outro_entry = tk.Entry(self.root, textvariable=self.outro_clip_path, state="disabled")
        self.outro_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.outro_button = tk.Button(self.root, text="Browse", command=self.browse_outro_clip, state="disabled")
        self.outro_button.grid(row=2, column=2, sticky="ew", padx=5, pady=5)

        # Time Selection
        tk.Label(self.root, text="Time Ranges (e.g., 00:10-00:20, 01:00-01:30):").grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.time_ranges_text = tk.Text(self.root, height=5)
        self.time_ranges_text.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        # Output Location
        tk.Label(self.root, text="Output Location:").grid(row=5, column=0, sticky="ew", padx=5, pady=5)
        self.output_location = tk.StringVar()
        tk.Entry(self.root, textvariable=self.output_location, state="readonly").grid(row=5, column=1, sticky="ew", padx=5, pady=5)
        tk.Button(self.root, text="Browse", command=self.browse_output_location).grid(row=5, column=2, sticky="ew", padx=5, pady=5)

        # Quality Toggle
        tk.Label(self.root, text="Quality:").grid(row=6, column=0, sticky="ew", padx=5, pady=5)
        self.quality_var = tk.StringVar(value="Compressed")
        tk.Radiobutton(self.root, text="Lossless", variable=self.quality_var, value="Lossless").grid(row=6, column=1, sticky="w", padx=5, pady=5)
        tk.Radiobutton(self.root, text="Compressed", variable=self.quality_var, value="Compressed").grid(row=6, column=2, sticky="w", padx=5, pady=5)

        # Start Processing Button
        tk.Button(self.root, text="Start Processing", command=self.start_processing).grid(row=7, column=0, columnspan=3, pady=20)

        # Progress Bar
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.grid(row=8, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

    def browse_source_video(self):
        filename = filedialog.askopenfilename(title="Select Source Video")
        self.source_video_path.set(filename)

    def browse_intro_clip(self):
        filename = filedialog.askopenfilename(title="Select Intro Clip")
        self.intro_clip_path.set(filename)

    def browse_outro_clip(self):
        filename = filedialog.askopenfilename(title="Select Outro Clip")
        self.outro_clip_path.set(filename)

    def browse_output_location(self):
        folder_selected = filedialog.askdirectory(title="Select Output Location")
        self.output_location.set(folder_selected)

    def toggle_intro_outro(self):
        if self.use_intro.get():
            self.intro_entry.config(state="normal")
            self.intro_button.config(state="normal")
        else:
            self.intro_entry.config(state="disabled")
            self.intro_clip_path.set("")
            self.intro_button.config(state="disabled")

        if self.use_outro.get():
            self.outro_entry.config(state="normal")
            self.outro_button.config(state="normal")
        else:
            self.outro_entry.config(state="disabled")
            self.outro_clip_path.set("")
            self.outro_button.config(state="disabled")

    def start_processing(self):
        # Placeholder for processing logic
        source_video = self.source_video_path.get()
        intro_clip = self.intro_clip_path.get()
        outro_clip = self.outro_clip_path.get()
        time_ranges = self.time_ranges_text.get("1.0", "end-1c")
        output_location = self.output_location.get()
        quality = self.quality_var.get()

        print("Starting processing...")
        print(f"Source Video: {source_video}")
        if self.use_intro.get():
            print(f"Intro Clip: {intro_clip}")
        if self.use_outro.get():
            print(f"Outro Clip: {outro_clip}")
        print(f"Time Ranges: {time_ranges}")
        print(f"Output Location: {output_location}")
        print(f"Quality: {quality}")
        # Here you would call the video processing logic

def create_ui(root):
    MainUI(root)

if __name__ == '__main__':
    root = tk.Tk()
    create_ui(root)
    root.mainloop()