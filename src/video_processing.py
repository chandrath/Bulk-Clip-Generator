# video_processing.py
import subprocess
import os
import sys

def run_ffmpeg_command(command_args, is_ffprobe=False):
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle (using PyInstaller)
        base_path = sys._MEIPASS
    else:
        # If the application is run normally
        base_path = os.path.dirname(os.path.abspath(__file__))

    if is_ffprobe:
      ffmpeg_path = os.path.join(base_path, "ffmpeg", "ffprobe.exe")
    else:
        ffmpeg_path = os.path.join(base_path, "ffmpeg", "ffmpeg.exe")

    full_command = [ffmpeg_path] + command_args
    process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout, stderr, process.returncode

def cut_video_segment(input_file, output_file, start_time, end_time, lossless=False, intro_path=None, outro_path=None):
    command = ["-i", input_file, "-ss", start_time, "-to", end_time]
    video_codec_options = ["-c:v", "copy"] if lossless else ["-c:v", "libx264", "-crf", "23", "-preset", "fast"]
    audio_codec_options = ["-c:a", "copy"] if lossless else ["-c:a", "aac", "-strict", "experimental"]

    if intro_path and outro_path:
        temp_output_file = "intermediate_clip.mp4"
        cut_command = command + video_codec_options + audio_codec_options + ["-y", temp_output_file]
        stdout, stderr, returncode = run_ffmpeg_command(cut_command)
        if returncode != 0:
            return False, stderr.decode()

        concat_list_file = "concat_list.txt"
        with open(concat_list_file, "w") as f:
            f.write(f"file '{intro_path}'\n")
            f.write(f"file '{temp_output_file}'\n")
            f.write(f"file '{outro_path}'\n")

        concat_command = [
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_file,
            "-c", "copy",
            "-y", output_file
        ]
        stdout, stderr, returncode = run_ffmpeg_command(concat_command)
        os.remove(temp_output_file)
        os.remove(concat_list_file)
        return returncode == 0, stderr.decode()

    elif intro_path:
         temp_output_file = "intermediate_clip.mp4"
         cut_command = command + video_codec_options + audio_codec_options + ["-y", temp_output_file]
         stdout, stderr, returncode = run_ffmpeg_command(cut_command)
         if returncode != 0:
             return False, stderr.decode()

         concat_list_file = "concat_list.txt"
         with open(concat_list_file, "w") as f:
             f.write(f"file '{intro_path}'\n")
             f.write(f"file '{temp_output_file}'\n")

         concat_command = [
             "-f", "concat",
             "-safe", "0",
             "-i", concat_list_file,
             "-c", "copy",
             "-y", output_file
         ]
         stdout, stderr, returncode = run_ffmpeg_command(concat_command)
         os.remove(temp_output_file)
         os.remove(concat_list_file)
         return returncode == 0, stderr.decode()

    elif outro_path:
        cut_command = command + video_codec_options + audio_codec_options + ["-y", output_file]
        stdout, stderr, returncode = run_ffmpeg_command(cut_command)
        return returncode == 0, stderr.decode()

    else:
        command.extend(video_codec_options)
        command.extend(audio_codec_options)
        command.extend(["-y", output_file])
        stdout, stderr, returncode = run_ffmpeg_command(command)
        return returncode == 0, stderr.decode()

def get_video_duration(video_path):
    command = [
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    try:
      stdout, stderr, returncode = run_ffmpeg_command(command, is_ffprobe=True)
      if returncode == 0 :
          duration = float(stdout.decode().strip())
          return duration
      else :
        return None
    except (ValueError):
        return None

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

def validate_time_range(start_str, end_str, duration):
    try:
        start_seconds = parse_time_string(start_str)
        end_seconds = parse_time_string(end_str)
        if not (0 <= start_seconds < duration and 0 < end_seconds <= duration and start_seconds < end_seconds):
            return False
        return True
    except ValueError:
        return False