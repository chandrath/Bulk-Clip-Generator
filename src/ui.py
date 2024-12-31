# ui.py
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import re
from video_processing import cut_video_segment, get_video_duration, validate_time_range
import threading
import json

class MainUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk Clip Generator")

        # Configure grid layout weights for resizing
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=2)
        self.root.grid_rowconfigure(tk.ALL, weight=1)

        # --- UI Elements ---
        # Source Video
        tk.Label(self.root, text="Source Video:").grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.source_video_path = tk.StringVar()
        self.source_video_combo = ttk.Combobox(self.root, textvariable=self.source_video_path)
        self.source_video_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        tk.Button(self.root, text="Browse", command=self.browse_source_video).grid(row=0, column=2, sticky="ew", padx=5, pady=5)

        # Intro Clip
        self.use_intro = tk.BooleanVar()
        tk.Checkbutton(self.root, text="Add Intro Clip:", variable=self.use_intro, command=self.toggle_intro_outro).grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.intro_clip_path = tk.StringVar()
        self.intro_combo = ttk.Combobox(self.root, textvariable=self.intro_clip_path, state="disabled")
        self.intro_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.intro_button = tk.Button(self.root, text="Browse", command=self.browse_intro_clip, state="disabled")
        self.intro_button.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        # Outro Clip
        self.use_outro = tk.BooleanVar()
        tk.Checkbutton(self.root, text="Add Outro Clip:", variable=self.use_outro, command=self.toggle_intro_outro).grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        self.outro_clip_path = tk.StringVar()
        self.outro_combo = ttk.Combobox(self.root, textvariable=self.outro_clip_path, state="disabled")
        self.outro_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.outro_button = tk.Button(self.root, text="Browse", command=self.browse_outro_clip, state="disabled")
        self.outro_button.grid(row=2, column=2, sticky="ew", padx=5, pady=5)

        # Time Selection
        tk.Label(self.root, text="Time Ranges (e.g., 00:10-00:20, 01:00-01:30):").grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.time_ranges_text = tk.Text(self.root, height=5)
        self.time_ranges_text.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        # Output Location
        tk.Label(self.root, text="Output Location:").grid(row=5, column=0, sticky="ew", padx=5, pady=5)
        self.output_location = tk.StringVar()
        self.output_combo = ttk.Combobox(self.root, textvariable=self.output_location)
        self.output_combo.grid(row=5, column=1, sticky="ew", padx=5, pady=5)
        tk.Button(self.root, text="Browse", command=self.browse_output_location).grid(row=5, column=2, sticky="ew", padx=5, pady=5)

        # Quality Toggle
        tk.Label(self.root, text="Quality:").grid(row=6, column=0, sticky="ew", padx=5, pady=5)
        self.quality_var = tk.StringVar(value="Compressed")
        tk.Radiobutton(self.root, text="Lossless", variable=self.quality_var, value="Lossless").grid(row=6, column=1, sticky="w", padx=5, pady=5)
        tk.Radiobutton(self.root, text="Compressed", variable=self.quality_var, value="Compressed").grid(row=6, column=2, sticky="w", padx=5, pady=5)

        # Buttons
        self.start_stop_button = tk.Button(self.root, text="Start Processing", command=self.toggle_processing, font=("Arial", 12, "bold"), padx=20, pady=10)
        self.start_stop_button.grid(row=7, column=0, columnspan=3, pady=20)
        tk.Button(self.root, text="Clear Fields", command=self.clear_fields).grid(row=8, column=0, columnspan=3, pady=10)

        # Progress Bar
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.grid(row=9, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.processing_active = False

        # File History and Settings
        self.source_video_history = []
        self.output_location_history = []
        self.config_file = "user_config.json"
        self.load_settings()

        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def clear_fields(self):
        self.source_video_path.set("")
        self.intro_clip_path.set("")
        self.outro_clip_path.set("")
        self.time_ranges_text.delete("1.0", tk.END)
        self.output_location.set("")
        self.quality_var.set("Compressed")
        self.use_intro.set(False)
        self.use_outro.set(False)
        self.toggle_intro_outro()

    def browse_source_video(self):
        file = filedialog.askopenfile(title="Select Source Video", mode="r")
        if file:
            filename = file.name
            self.source_video_path.set(filename)
            self.update_file_history(filename, self.source_video_history)
            self.source_video_combo['values'] = self.source_video_history

    def browse_intro_clip(self):
        file = filedialog.askopenfile(title="Select Intro Clip", mode="r")
        if file:
            filename = file.name
            self.intro_clip_path.set(filename)
            self.update_file_history(filename, self.source_video_history)
            self.intro_combo['values'] = self.source_video_history

    def browse_outro_clip(self):
        file = filedialog.askopenfile(title="Select Outro Clip", mode="r")
        if file:
            filename = file.name
            self.outro_clip_path.set(filename)
            self.update_file_history(filename, self.source_video_history)
            self.outro_combo['values'] = self.source_video_history

    def browse_output_location(self):
        folder_selected = filedialog.askdirectory(title="Select Output Location")
        self.output_location.set(folder_selected)
        self.update_file_history(folder_selected, self.output_location_history)
        self.output_combo['values'] = self.output_location_history

    def toggle_intro_outro(self):
        self.intro_combo.config(state="normal" if self.use_intro.get() else "disabled")
        self.intro_button.config(state="normal" if self.use_intro.get() else "disabled")
        if not self.use_intro.get():
            self.intro_clip_path.set("")

        self.outro_combo.config(state="normal" if self.use_outro.get() else "disabled")
        self.outro_button.config(state="normal" if self.use_outro.get() else "disabled")
        if not self.use_outro.get():
            self.outro_clip_path.set("")

    def update_file_history(self, filepath, history_list):
        if filepath in history_list:
            history_list.remove(filepath)
        history_list.insert(0, filepath)
        if len(history_list) > 10:
            history_list.pop()

    def load_settings(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.source_video_history = config.get('source_video_history', [])
                self.output_location_history = config.get('output_location_history', [])
                self.source_video_combo['values'] = self.source_video_history
                self.output_combo['values'] = self.output_location_history
                self.source_video_path.set(config.get('source_video_path', ''))
                self.intro_clip_path.set(config.get('intro_clip_path', ''))
                self.outro_clip_path.set(config.get('outro_clip_path', ''))
                self.use_intro.set(config.get('use_intro', False))
                self.use_outro.set(config.get('use_outro', False))
                self.toggle_intro_outro()
                self.time_ranges_text.delete("1.0", tk.END)
                self.time_ranges_text.insert(tk.END, config.get('time_ranges_text', ''))
                self.output_location.set(config.get('output_location', ''))
                self.quality_var.set(config.get('quality_var', 'Compressed'))
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {self.config_file}")

    def save_settings(self):
        config = {
            'source_video_history': self.source_video_history,
            'output_location_history': self.output_location_history,
            'source_video_path': self.source_video_path.get(),
            'intro_clip_path': self.intro_clip_path.get(),
            'outro_clip_path': self.outro_clip_path.get(),
            'use_intro': self.use_intro.get(),
            'use_outro': self.use_outro.get(),
            'time_ranges_text': self.time_ranges_text.get("1.0", tk.END).strip(),
            'output_location': self.output_location.get(),
            'quality_var': self.quality_var.get()
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

    def on_closing(self):
        self.save_settings()
        self.root.destroy()

    def toggle_processing(self):
        if self.processing_active:
            self.stop_processing()
        else:
            self.start_processing()

    def start_processing(self):
        if self.processing_active:
            messagebox.showinfo("Processing", "A processing task is already active.")
            return

        source_video = self.source_video_path.get()
        intro_clip = self.intro_clip_path.get()
        outro_clip = self.outro_clip_path.get()
        time_ranges_text = self.time_ranges_text.get("1.0", "end-1c").strip()
        output_location = self.output_location.get()
        quality = self.quality_var.get()
        lossless = quality == "Lossless"

        if not source_video or not os.path.exists(source_video):
            messagebox.showerror("Error", "Please select a valid source video file.")
            return
        if self.use_intro.get() and (not intro_clip or not os.path.exists(intro_clip)):
            messagebox.showerror("Error", "Please select a valid intro clip file.")
            return
        if self.use_outro.get() and (not outro_clip or not os.path.exists(outro_clip)):
            messagebox.showerror("Error", "Please select a valid outro clip file.")
            return
        if not output_location or not os.path.exists(output_location):
            messagebox.showerror("Error", "Please select a valid output location.")
            return
        if not time_ranges_text:
            messagebox.showerror("Error", "Please enter time ranges.")
            return

        time_ranges = time_ranges_text.split(',')
        parsed_ranges = []
        for range_str in time_ranges:
            match = re.match(r"(\d{1,2}:?\d{2}:?\d{2}|\d{1,2}:?\d{2})-(\d{1,2}:?\d{2}:?\d{2}|\d{1,2}:?\d{2})", range_str.strip())
            if match:
                start_time_str, end_time_str = match.groups()
                parsed_ranges.append((start_time_str, end_time_str))
            else:
                messagebox.showerror("Error", f"Invalid time range format: {range_str.strip()}")
                return

        duration = get_video_duration(source_video)
        if duration is None:
            messagebox.showerror("Error", f"Could not determine the duration of the source video.")
            return

        self.start_stop_button.config(text="Stop Processing", fg="red")
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = len(parsed_ranges)
        self.processing_active = True

        original_filename = os.path.splitext(os.path.basename(source_video))[0]

        # Start video processing in a separate thread
        threading.Thread(target=self.process_clips, args=(parsed_ranges, source_video, intro_clip, outro_clip, output_location, lossless, original_filename,)).start()

    def process_clips(self, parsed_ranges, source_video, intro_clip, outro_clip, output_location, lossless, original_filename):
        try:
            for i, (start_time_str, end_time_str) in enumerate(parsed_ranges):
                if not self.processing_active:
                    return
                if not validate_time_range(start_time_str, end_time_str, get_video_duration(source_video)):
                    messagebox.showerror("Error", f"Invalid time range: {start_time_str}-{end_time_str} exceeds video duration or is improperly formatted.")
                    self.processing_active = False
                    self.root.after(0, self.stop_processing)  # Ensure UI update happens in main thread
                    return

                output_filename = f"Clip_{i+1}_{original_filename}.mp4"
                output_path = os.path.join(output_location, output_filename)

                print(f"Processing clip {i+1}/{len(parsed_ranges)}: {start_time_str} - {end_time_str}")
                success, error_message = cut_video_segment(
                    source_video,
                    output_path,
                    start_time_str,
                    end_time_str,
                    lossless,
                    intro_clip if self.use_intro.get() else None,
                    outro_clip if self.use_outro.get() else None
                )

                if success:
                    self.progress_bar["value"] = i + 1
                    self.root.update_idletasks()
                else:
                    messagebox.showerror("Error", f"Error processing clip {i+1}: {error_message}")
                    self.processing_active = False
                    self.root.after(0, self.stop_processing)  # Ensure UI update happens in main thread
                    return

            self.processing_active = False
            self.root.after(0, self.stop_processing)  # Ensure UI update happens in main thread
            messagebox.showinfo("Success", "Video clipping completed!")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.processing_active = False
            self.root.after(0, self.stop_processing)  # Ensure UI update happens in main thread

    def stop_processing(self):
        self.processing_active = False
        self.start_stop_button.config(text="Start Processing", fg="black")

def create_ui(root):
    return MainUI(root)

if __name__ == '__main__':
    root = tk.Tk()
    create_ui(root)
    root.mainloop()