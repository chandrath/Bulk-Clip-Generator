# video_processing.py
import subprocess
import os
import sys
from tempfile import mkdtemp
import shutil

def run_ffmpeg_command(command_args, is_ffprobe=False):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    executable = "ffprobe.exe" if is_ffprobe else "ffmpeg.exe"
    ffmpeg_path = os.path.join(base_path, "ffmpeg", executable)

    if not os.path.exists(ffmpeg_path):
        raise FileNotFoundError(f"{executable} not found at {ffmpeg_path}")

    full_command = [ffmpeg_path] + command_args
    process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout, stderr, process.returncode

def get_video_duration(video_path):
    command = [
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    try:
        stdout, stderr, returncode = run_ffmpeg_command(command, is_ffprobe=True)
        if returncode == 0:
            return float(stdout.decode().strip())
        raise ValueError(f"Error determining duration: {stderr.decode().strip()}")
    except Exception as e:
        raise RuntimeError(f"Failed to get video duration for {video_path}: {e}")

def normalize_video(input_file, output_file, lossless=False):
    """Normalize video to a consistent format for concatenation"""
    command = [
        "-i", input_file,
        "-map", "0:v:0",  # Select first video stream
        "-map", "0:a:0?",  # Select first audio stream if it exists
        "-c:v", "libx264",
        "-preset", "fast"
    ]

    if lossless:
        command.extend(["-crf", "18"])
    else:
        command.extend(["-crf", "23"])

    command.extend([
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",  # Consistent audio sample rate
        "-pix_fmt", "yuv420p",  # Consistent pixel format
        "-y",
        output_file
    ])

    stdout, stderr, returncode = run_ffmpeg_command(command)
    if returncode != 0:
        raise RuntimeError(f"Error normalizing video: {stderr.decode().strip()}")
    return returncode == 0

def cut_video_segment(input_file, output_file, start_time, end_time, lossless=False, intro_path=None, outro_path=None, progress_callback=None):
    # Create temporary directory for intermediate files
    temp_dir = mkdtemp()
    temp_files = []

    try:
        # Step 1: Cut the main segment
        temp_main = os.path.join(temp_dir, "temp_main.mp4")
        cut_command = [
            "-i", input_file,
            "-ss", start_time,
            "-to", end_time,
            "-map", "0:v:0",  # Select first video stream
            "-map", "0:a:0?",  # Select first audio stream if it exists
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23" if not lossless else "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-pix_fmt", "yuv420p",
            "-y",
            temp_main
        ]

        stdout, stderr, returncode = run_ffmpeg_command(cut_command)
        if returncode != 0:
            raise RuntimeError(f"Error cutting main segment: {stderr.decode().strip()}")
        temp_files.append(temp_main)

        # After cutting main segment:
        if progress_callback:
            progress_callback(33)  # 33% complete after main cut

        # Step 2: Normalize intro and outro if present
        concat_list = []

        if intro_path:
            temp_intro = os.path.join(temp_dir, "temp_intro.mp4")
            if normalize_video(intro_path, temp_intro, lossless):
                concat_list.append(temp_intro)
                temp_files.append(temp_intro)

        concat_list.append(temp_main)

        if outro_path:
            temp_outro = os.path.join(temp_dir, "temp_outro.mp4")
            if normalize_video(outro_path, temp_outro, lossless):
                concat_list.append(temp_outro)
                temp_files.append(temp_outro)

        # After normalizing intro/outro:
        if progress_callback:
            progress_callback(66)  # 66% complete after normalization

        # Step 3: Create concatenation file
        concat_file = os.path.join(temp_dir, "concat.txt")
        with open(concat_file, "w", encoding='utf-8') as f:
            for file_path in concat_list:
                f.write(f"file '{file_path}'\n")
        temp_files.append(concat_file)

        # Step 4: Concatenate all clips
        concat_command = [
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23" if not lossless else "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-pix_fmt", "yuv420p",
            "-y",
            output_file
        ]

        stdout, stderr, returncode = run_ffmpeg_command(concat_command)
        if returncode != 0:
            raise RuntimeError(f"Error concatenating clips: {stderr.decode().strip()}")

        # After final concatenation:
        if progress_callback:
            progress_callback(100)  # 100% complete

        return True, None

    except Exception as e:
        return False, str(e)

    finally:
        # Clean up all temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def validate_time_range(start_str, end_str, duration):
    try:
        start_seconds = parse_time_string(start_str)
        end_seconds = parse_time_string(end_str)
        if not (0 <= start_seconds < duration and 0 < end_seconds <= duration and start_seconds < end_seconds):
            return False
        return True
    except ValueError:
        return False

def parse_time_string(time_string):
    parts = time_string.split(':')
    seconds = 0
    multiplier = 1
    for part in reversed(parts):
        seconds += int(part) * multiplier
        multiplier *= 60
    return seconds

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"