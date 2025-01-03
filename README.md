<!-- Cover Icon -->
<p align="center">
  <img src="app_icon.png" alt="Bulk Clip Generator Icon" width="200" height="200">
</p>

<h1 align="center">Bulk Clip Generator</h1>

<p align="center">
  ✂️ Effortlessly extract multiple video clips, **with intro/outro support**, from a single source video.
</p>

---

The **Bulk Clip Generator** simplifies the process of creating multiple clips from a longer video. Instead of manually cutting each segment, this application allows you to define multiple time ranges and generate individual video files for each. This is ideal for content creators, educators, YouTubers, podcasters, or anyone needing to extract specific moments from videos quickly and efficiently to publish separate clips. The ability to add separate intro and outro videos to the beginning and end of each generated clip further enhances your workflow. This free and open-source GUI tool streamlines your video editing workflow, saving time and effort.

<small><i>Bulk Clip Generator is primarily tested and developed on Windows. While the source code is platform-independent, building the application on Linux or macOS may require platform-specific dependencies and procedures.</i></small>

## Features

- ✅ **Bulk Clipping:** Define multiple start and end times to extract numerous clips in one go.
- ✅ **Intro/Outro Integration:** **Easily add separate intro and outro videos to the beginning and end of each generated clip.** This allows for consistent branding and professional introductions/endings across all your clips.
- ✅ **Time Range Input:** Easily input time ranges in a clear and understandable format (e.g., `00:00-01:30, 05:00-06:15`).
- ✅ **Quality Control:** Choose between lossless and compressed output to balance quality and file size.
- ✅ **Hardware Acceleration:** Leverage NVIDIA NVENC, AMD AMF, or Intel QuickSync for significantly faster processing (if available).
- ✅ **Progress Tracking:** Real-time progress updates for each clip and overall processing time.
- ✅ **Intuitive GUI:** User-friendly interface for easy navigation and operation.
- ✅ **Save Settings:** Remembers your preferences for source videos, output locations, and more.

---

## Screenshots

### Main Interface and Features Overview

![Bulk Clip Generator UI](https://i.imgur.com/xlDV1Yk.jpeg)

---

## Getting Started

### Prerequisites

To run the program:

- Python 3.8+ installed (if running from source).
- Required Python packages: `tkinter`, `ttkbootstrap`, `pillow`, `ffmpeg-python`, and potentially others (see `requirements.txt`).
- **FFmpeg:** **FFmpeg is required for video processing and is not included in the source code.** You need to download it separately and ensure it's correctly placed.

### Installing FFmpeg

Bulk Clip Generator relies on FFmpeg for video processing. If you don't have it installed:

- **Download:** Download the latest release from [FFmpeg official website](https://ffmpeg.org/download.html). Choose the appropriate build for your system.
- **Placement:** After downloading, extract the archive and place the FFmpeg executables (`ffmpeg.exe` and `ffprobe.exe` on Windows) in the `ffmpeg` subdirectory within the project's root directory. The directory structure should look like this:

```
Bulk-Clip-Generator/
├── main.py
├── ui.py
├── menu.py
├── video_processing.py
├── gpu_utils.py
├── gpu_cache.py
├── ffmpeg/
│   ├── ffmpeg.exe
│   └── ffprobe.exe
├── ... (other project files)
├── requirements.txt
└── app_icon.ico
```

- **Adding to PATH (Alternative):** Alternatively, you can add the FFmpeg `bin` directory to your system's PATH environment variable.

**OS-Specific Instructions:**

- **Windows:**
  1. Download the latest release from [FFmpeg official website](https://ffmpeg.org/download.html). Choose the appropriate build for your system.
  2. Extract the downloaded archive to a directory (e.g., `C:\ffmpeg`).
  3. Add the `bin` directory within the extracted folder to your system's PATH environment variable.
- **macOS:**
  ```bash
  brew install ffmpeg
  ```
- **Linux (Debian/Ubuntu):**
  ```bash
  sudo apt update
  sudo apt install ffmpeg
  ```
  Refer to your specific distribution's documentation for installation instructions.

### Installation (Application)

#### **Run as Executable (Recommended)**

1. Download the latest release from the [Releases Page](https://github.com/yourusername/Bulk-Clip-Generator/releases).
2. Run the `BulkClipGenerator.exe` file.

**Note Regarding Antivirus:** Some antivirus programs might flag the executable as a potential threat. This is common for applications built with tools like PyInstaller. You can review the source code or choose to "allow" or "whitelist" the application in your antivirus settings.

#### **Run from Source**

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/Bulk-Clip-Generator.git
   cd Bulk-Clip-Generator
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Usage

1. **Select Source Video:** Click "File" > "Open Source Video" to choose the video you want to clip.
2. **Enter Time Ranges:** In the "Time Ranges" section, enter the desired clip start and end times, separated by a hyphen, and each range separated by a comma (e.g., `00:10-00:20, 01:00-01:30`). You can also use the "+" button to add time ranges using a dedicated time selector.
3. **Optional Intro/Outro:** If desired, select intro and outro videos using the respective browse buttons. Enable the "Add Intro" and "Add Outro" checkboxes.
4. **Set Output Location:** Choose where the generated clips will be saved.
5. **Select Quality:** Choose between "Lossless" for original quality or "Compressed" for smaller file sizes.
6. **Start Processing:** Click "Start Processing" to begin the clipping process. The progress will be displayed in the "Progress" section.
7. **View Output:** Once completed, click "Show Output Folder" to open the directory containing the generated clips.

## Building from Source with PyInstaller

To create a standalone executable for the Bulk Clip Generator application, follow these instructions:

**Prerequisites:**

1. **Python and Pip:** Ensure you have Python (version 3.8 or higher) and `pip` installed.
2. **PyInstaller:** Install it using pip:
   ```bash
   pip install pyinstaller
   ```

**Steps:**

1. **Navigate to the project directory** in your terminal.
2. **Run the PyInstaller command:**

   ```bash
   pyinstaller --onefile --windowed --icon=app_icon.ico main.py --add-data "ffmpeg/:ffmpeg/"
   ```

   - `--onefile`: Creates a single executable file.
   - `--windowed`: Creates an executable without a console window.
   - `--icon=app_icon.ico`: Specifies the icon file for the executable.
   - `--add-data "ffmpeg/:ffmpeg/"`: **Important:** This includes the `ffmpeg` directory in the build. Ensure the `ffmpeg` directory (containing `ffmpeg.exe`, `ffprobe.exe`, etc.) is in the same directory as your `main.py` before running this command.

3. **Locate the Executable:** The executable will be in the `dist` folder.

**Note:** Including FFmpeg directly within the executable increases its size but makes distribution easier. Ensure the `ffmpeg` directory contains the necessary FFmpeg executables for your target platform.

## Roadmap

- [ ] Add support for different video codecs and formats.
- [ ] Implement batch processing of multiple source videos.
- [ ] Explore options for more advanced editing features.

## License

Bulk Clip Generator is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0).
