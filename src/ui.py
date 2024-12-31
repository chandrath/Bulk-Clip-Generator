# ui.py
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import re
from video_processing import cut_video_segment, get_video_duration, validate_time_range
import threading
import json
import time
from datetime import datetime, timedelta

class MainUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk Clip Generator")

        # Set theme and style
        style = ttk.Style()
        style.theme_use('clam')  # Use 'clam' theme for a modern look

        # Configure custom styles
        style.configure('Modern.TButton', padding=10, font=('Helvetica', 10))
        style.configure('Modern.TEntry', padding=5)
        style.configure('Modern.TFrame', background='#f0f0f0')
        style.configure('Modern.TLabel', font=('Helvetica', 10))
        style.configure('Title.TLabel', font=('Helvetica', 12, 'bold'))
        style.configure('Bold.TLabel', font=('Helvetica', 10, 'bold'))
        style.configure('Italic.TLabel', font=('Helvetica', 8, 'italic'))

        # Main frame with padding
        self.main_frame = ttk.Frame(root, padding="20", style='Modern.TFrame')
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights for the main frame
        self.main_frame.grid_columnconfigure(0, weight=1, uniform="group1")  # Video Settings column
        self.main_frame.grid_columnconfigure(1, weight=1, uniform="group1")  # Output Settings column
        self.main_frame.grid_rowconfigure(1, weight=1)  # Time/Progress row
        self.main_frame.grid_rowconfigure(2, weight=0) # Button row

        # Create sections
        self.create_video_section()
        self.create_output_section()
        self.create_time_section()
        self.create_progress_section()


        # Initialize processing variables
        self.processing_active = False
        self.start_time = None
        self.total_clips = 0
        self.processed_clips = 0
        self.total_duration = 0
        self.current_clip_start = 0

        # Load settings
        self.config_file = "user_config.json"
        self.source_video_history = []
        self.intro_clip_history = []
        self.outro_clip_history = []
        self.output_location_history = []
        self.load_settings()

        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_video_section(self):
        # Source Video Frame
        video_frame = ttk.LabelFrame(self.main_frame, text="Video Settings", padding="10")
        video_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10)) # Added padx

        # Source Video
        ttk.Label(video_frame, text="Source Video:", style='Modern.TLabel').grid(row=0, column=0, sticky="w", pady=5)
        self.source_video_path = tk.StringVar()
        self.source_video_filename = tk.StringVar()
        self.source_video_dir = tk.StringVar()
        self.source_video_combo = ttk.Combobox(video_frame, textvariable=self.source_video_filename, style='Modern.TEntry')
        self.source_video_combo.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(video_frame, text="Browse", command=self.browse_source_video, style='Modern.TButton').grid(row=0, column=2, padx=5)
        ttk.Label(video_frame, textvariable=self.source_video_dir, style='Italic.TLabel').grid(row=1, column=1, sticky="ew", padx=5)

        # Intro Clip
        self.use_intro = tk.BooleanVar()
        ttk.Checkbutton(video_frame, text="Add Intro:", variable=self.use_intro, command=self.toggle_intro_outro).grid(row=2, column=0, sticky="w", pady=5)
        self.intro_clip_path = tk.StringVar()
        self.intro_clip_filename = tk.StringVar()
        self.intro_clip_dir = tk.StringVar()
        self.intro_combo = ttk.Combobox(video_frame, textvariable=self.intro_clip_filename, state="disabled")
        self.intro_combo.grid(row=2, column=1, sticky="ew", padx=5)
        self.intro_button = ttk.Button(video_frame, text="Browse", command=self.browse_intro_clip, state="disabled", style='Modern.TButton')
        self.intro_button.grid(row=2, column=2, padx=5)
        ttk.Label(video_frame, textvariable=self.intro_clip_dir, style='Italic.TLabel').grid(row=3, column=1, sticky="ew", padx=5)

        # Outro Clip
        self.use_outro = tk.BooleanVar()
        ttk.Checkbutton(video_frame, text="Add Outro:", variable=self.use_outro, command=self.toggle_intro_outro).grid(row=4, column=0, sticky="w", pady=5)
        self.outro_clip_path = tk.StringVar()
        self.outro_clip_filename = tk.StringVar()
        self.outro_clip_dir = tk.StringVar()
        self.outro_combo = ttk.Combobox(video_frame, textvariable=self.outro_clip_filename, state="disabled")
        self.outro_combo.grid(row=4, column=1, sticky="ew", padx=5)
        self.outro_button = ttk.Button(video_frame, text="Browse", command=self.browse_outro_clip, state="disabled", style='Modern.TButton')
        self.outro_button.grid(row=4, column=2, padx=5)
        ttk.Label(video_frame, textvariable=self.outro_clip_dir, style='Italic.TLabel').grid(row=5, column=1, sticky="ew", padx=5)

    def create_output_section(self):
        # Output Frame
        output_frame = ttk.LabelFrame(self.main_frame, text="Output Settings", padding="10")
        output_frame.grid(row=0, column=1, sticky="nsew", pady=(0, 10)) # Added padx

        # Output Location
        ttk.Label(output_frame, text="Output Location:", style='Modern.TLabel').grid(row=0, column=0, sticky="w", pady=5)
        self.output_location = tk.StringVar()
        self.output_combo = ttk.Combobox(output_frame, textvariable=self.output_location)
        self.output_combo.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(output_frame, text="Browse", command=self.browse_output_location, style='Modern.TButton').grid(row=0, column=2, padx=5)

        # Quality Settings
        ttk.Label(output_frame, text="Quality:", style='Modern.TLabel').grid(row=1, column=0, sticky="w", pady=5)
        self.quality_var = tk.StringVar(value="Compressed")
        ttk.Radiobutton(output_frame, text="Lossless", variable=self.quality_var, value="Lossless").grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(output_frame, text="Compressed", variable=self.quality_var, value="Compressed").grid(row=1, column=2, sticky="w")

    def create_time_section(self):
         # Time Range Frame
        time_frame = ttk.LabelFrame(self.main_frame, text="Time Ranges", padding="10")
        time_frame.grid(row=1, column=0, sticky="nsew", pady=10, padx=(0,5)) # Adjusted columnspan and padx
        time_frame.grid_columnconfigure(0, weight=1)  # Make the time frame expand

        ttk.Label(time_frame, text="Enter time ranges (e.g., 00:10-00:20, 01:00-01:30):", style='Modern.TLabel').grid(row=0, column=0, sticky="w", pady=5)
        self.time_ranges_text = tk.Text(time_frame, height=5, wrap=tk.WORD)
        self.time_ranges_text.grid(row=1, column=0, sticky="nsew", pady=5)
        self.time_ranges_text.configure(font=('Helvetica', 10))

    def create_progress_section(self):
       # Progress Frame
        progress_frame = ttk.LabelFrame(self.main_frame, text="Progress", padding="10")
        progress_frame.grid(row=1, column=1, sticky="nsew", pady=10, padx=(5, 0))
        progress_frame.grid_columnconfigure(0, weight=1)

        # Progress Labels
        self.progress_text = tk.StringVar(value="Ready to process...")
        ttk.Label(progress_frame, textvariable=self.progress_text, style='Modern.TLabel').grid(row=0, column=0, columnspan=3, sticky="w", pady=5)

        self.time_text = tk.StringVar(value="Estimated time remaining: --:--")
        ttk.Label(progress_frame, textvariable=self.time_text, style='Modern.TLabel').grid(row=1, column=0, columnspan=3, sticky="w", pady=5)

        # Progress Bar
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 5)) # Adjusted pady

        # Buttons Frame
        button_frame = ttk.Frame(progress_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)

        # Process and Clear Buttons
        self.start_stop_button = ttk.Button(button_frame, text="Start Processing", command=self.toggle_processing, style='Modern.TButton')
        self.start_stop_button.grid(row=0, column=0, padx=5)

        ttk.Button(button_frame, text="Clear Fields", command=self.clear_fields, style='Modern.TButton').grid(row=0, column=1, padx=5)

    def process_clips(self, parsed_ranges, source_video, intro_clip, outro_clip, output_location, lossless, original_filename):
        self.total_clips = len(parsed_ranges)
        self.start_time = time.time()

        try:
            for i, (start_time_str, end_time_str) in enumerate(parsed_ranges, 1):
                if not self.processing_active:
                    return  # Exit if processing is stopped

                if not validate_time_range(start_time_str, end_time_str, get_video_duration(source_video)):
                    messagebox.showerror("Error", f"Invalid time range: {start_time_str}-{end_time_str}")
                    self.processing_active = False
                    self.root.after(0, self.stop_processing)
                    return

                output_filename = f"Clip_{i}_{original_filename}.mp4"
                output_path = os.path.join(output_location, output_filename)

                # Create a closure to handle progress updates for current clip
                def progress_handler(progress):
                    if self.processing_active:
                        clip_progress = ((i - 1) * 100 + progress) / self.total_clips
                        self.progress_bar["value"] = clip_progress

                        # Calculate time remaining
                        elapsed_time = time.time() - self.start_time
                        if clip_progress > 0:
                            total_time = (elapsed_time * 100) / clip_progress
                            remaining_time = total_time - elapsed_time
                            elapsed_str = str(timedelta(seconds=int(elapsed_time)))
                            remaining_str = str(timedelta(seconds=int(remaining_time)))
                            self.time_text.set(f"Elapsed: {elapsed_str} | Remaining: {remaining_str}")

                        self.progress_text.set(f"Processing clip {i}/{self.total_clips} ({clip_progress:.1f}%)")
                        self.root.update_idletasks()

                success, error_message = cut_video_segment(
                    source_video,
                    output_path,
                    start_time_str,
                    end_time_str,
                    lossless,
                    intro_clip if self.use_intro.get() else None,
                    outro_clip if self.use_outro.get() else None,
                    progress_callback=progress_handler  # Add this parameter
                )

                if not success:
                    messagebox.showerror("Error", f"Error processing clip {i}: {error_message}")
                    self.processing_active = False
                    self.root.after(0, self.stop_processing)
                    return

            self.processing_active = False
            self.root.after(0, self.stop_processing)
            messagebox.showinfo("Success", "Video clipping completed!")

        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.processing_active = False
            self.root.after(0, self.stop_processing)

    def browse_source_video(self):
        file = filedialog.askopenfile(title="Select Source Video", mode="r")
        if file:
            filename = os.path.basename(file.name)
            dirname = os.path.dirname(file.name)
            self.source_video_path.set(file.name)
            self.source_video_filename.set(filename)
            self.source_video_dir.set(dirname)
            self.update_file_history(file.name, self.source_video_history)
            self.source_video_combo['values'] = [os.path.basename(p) for p in self.source_video_history]

    def browse_intro_clip(self):
        file = filedialog.askopenfile(title="Select Intro Clip", mode="r")
        if file:
            filename = os.path.basename(file.name)
            dirname = os.path.dirname(file.name)
            self.intro_clip_path.set(file.name)
            self.intro_clip_filename.set(filename)
            self.intro_clip_dir.set(dirname)
            self.update_file_history(file.name, self.intro_clip_history)
            self.intro_combo['values'] = [os.path.basename(p) for p in self.intro_clip_history]

    def browse_outro_clip(self):
        file = filedialog.askopenfile(title="Select Outro Clip", mode="r")
        if file:
            filename = os.path.basename(file.name)
            dirname = os.path.dirname(file.name)
            self.outro_clip_path.set(file.name)
            self.outro_clip_filename.set(filename)
            self.outro_clip_dir.set(dirname)
            self.update_file_history(file.name, self.outro_clip_history)
            self.outro_combo['values'] = [os.path.basename(p) for p in self.outro_clip_history]

    def browse_output_location(self):
        folder_selected = filedialog.askdirectory(title="Select Output Location")
        if folder_selected:
            self.output_location.set(folder_selected)
            self.update_file_history(folder_selected, self.output_location_history)
            self.output_combo['values'] = self.output_location_history

    def toggle_intro_outro(self):
        self.intro_combo.config(state="normal" if self.use_intro.get() else "disabled")
        self.intro_button.config(state="normal" if self.use_intro.get() else "disabled")
        if not self.use_intro.get():
            self.intro_clip_path.set("")
            self.intro_clip_filename.set("")
            self.intro_clip_dir.set("")

        self.outro_combo.config(state="normal" if self.use_outro.get() else "disabled")
        self.outro_button.config(state="normal" if self.use_outro.get() else "disabled")
        if not self.use_outro.get():
            self.outro_clip_path.set("")
            self.outro_clip_filename.set("")
            self.outro_clip_dir.set("")

    def clear_fields(self):
        self.source_video_path.set("")
        self.source_video_filename.set("")
        self.source_video_dir.set("")
        self.intro_clip_path.set("")
        self.intro_clip_filename.set("")
        self.intro_clip_dir.set("")
        self.outro_clip_path.set("")
        self.outro_clip_filename.set("")
        self.outro_clip_dir.set("")
        self.time_ranges_text.delete("1.0", tk.END)
        self.output_location.set("")
        self.quality_var.set("Compressed")
        self.use_intro.set(False)
        self.use_outro.set(False)
        self.toggle_intro_outro()
        self.progress_text.set("Ready to process...")
        self.time_text.set("Estimated time remaining: --:--")
        self.progress_bar["value"] = 0

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
                self.intro_clip_history = config.get('intro_clip_history', [])
                self.outro_clip_history = config.get('outro_clip_history', [])
                self.output_location_history = config.get('output_location_history', [])

                self.source_video_combo['values'] = [os.path.basename(p) for p in self.source_video_history]
                self.intro_combo['values'] = [os.path.basename(p) for p in self.intro_clip_history]
                self.outro_combo['values'] = [os.path.basename(p) for p in self.outro_clip_history]
                self.output_combo['values'] = self.output_location_history

                self.source_video_path.set(config.get('source_video_path', ''))
                if self.source_video_path.get():
                    self.source_video_filename.set(os.path.basename(self.source_video_path.get()))
                    self.source_video_dir.set(os.path.dirname(self.source_video_path.get()))

                self.intro_clip_path.set(config.get('intro_clip_path', ''))
                if self.intro_clip_path.get():
                    self.intro_clip_filename.set(os.path.basename(self.intro_clip_path.get()))
                    self.intro_clip_dir.set(os.path.dirname(self.intro_clip_path.get()))

                self.outro_clip_path.set(config.get('outro_clip_path', ''))
                if self.outro_clip_path.get():
                    self.outro_clip_filename.set(os.path.basename(self.outro_clip_path.get()))
                    self.outro_clip_dir.set(os.path.dirname(self.outro_clip_path.get()))

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
            'intro_clip_history': self.intro_clip_history,
            'outro_clip_history': self.outro_clip_history,
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
        if self.processing_active:
            if messagebox.askokcancel("Quit", "Processing is active. Do you want to cancel and quit?"):
                self.processing_active = False
                self.save_settings()
                self.root.destroy()
        else:
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
        intro_clip = self.intro_clip_path.get() if self.use_intro.get() else None
        outro_clip = self.outro_clip_path.get() if self.use_outro.get() else None
        time_ranges_text = self.time_ranges_text.get("1.0", "end-1c").strip()
        output_location = self.output_location.get()
        quality = self.quality_var.get()
        lossless = quality == "Lossless"

        # Validate inputs
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

        # Parse time ranges
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

        # Start processing
        self.start_stop_button.config(text="Stop Processing")
        self.progress_bar["value"] = 0
        self.processing_active = True
        self.progress_text.set("Initializing...")
        self.time_text.set("Calculating time remaining...")
        self.start_stop_button.config(state=tk.NORMAL)  # Ensure button is enabled

        original_filename = os.path.splitext(os.path.basename(source_video))[0]

        # Start processing in a separate thread
        threading.Thread(target=self.process_clips, args=(
            parsed_ranges,
            source_video,
            intro_clip,
            outro_clip,
            output_location,
            lossless,
            original_filename
        )).start()

    def stop_processing(self):
        self.processing_active = False
        self.start_stop_button.config(text="Start Processing")
        self.progress_text.set("Processing stopped")
        self.time_text.set("Estimated time remaining: --:--")
        self.progress_bar["value"] = 0
        self.start_time = None

def create_ui(root):
    return MainUI(root)

if __name__ == '__main__':
    root = tk.Tk()
    app = MainUI(root)
    root.mainloop()