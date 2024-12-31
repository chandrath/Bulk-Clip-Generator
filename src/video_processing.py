import subprocess
import os
import sys


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


def reencode_to_uniform_format(input_file, output_file):
    command = [
        "-i", input_file,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-strict", "experimental",
        "-y", output_file
    ]
    stdout, stderr, returncode = run_ffmpeg_command(command)
    return returncode == 0, stderr.decode().strip()


def cut_video_segment(input_file, output_file, start_time, end_time, lossless=False, intro_path=None, outro_path=None):
    temp_main = "temp_main.mp4"
    temp_concat_file = "temp_concat_list.txt"

    try:
        # Step 1: Cut the main segment
        command = ["-i", input_file, "-ss", start_time, "-to", end_time]
        video_codec_options = ["-c:v", "copy"] if lossless else ["-c:v", "libx264", "-preset", "fast", "-crf", "23"]
        audio_codec_options = ["-c:a", "copy"] if lossless else ["-c:a", "aac", "-strict", "experimental"]
        command += video_codec_options + audio_codec_options + ["-y", temp_main]
        stdout, stderr, returncode = run_ffmpeg_command(command)
        if returncode != 0:
            raise RuntimeError(f"Error cutting main segment: {stderr.decode().strip()}")

        # Step 2: Prepare the concatenation list
        with open(temp_concat_file, "w") as f:
            if intro_path:
                f.write(f"file '{intro_path}'\n")
            f.write(f"file '{temp_main}'\n")
            if outro_path:
                f.write(f"file '{outro_path}'\n")

        # Step 3: Concatenate all clips
        concat_command = [
            "-f", "concat",
            "-safe", "0",
            "-i", temp_concat_file,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-strict", "experimental",
            "-y", output_file
        ]
        stdout, stderr, returncode = run_ffmpeg_command(concat_command)
        if returncode != 0:
            raise RuntimeError(f"Error concatenating clips: {stderr.decode().strip()}")

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        # Cleanup temporary files
        for temp_file in [temp_main, temp_concat_file]:
            if os.path.exists(temp_file):
                os.remove(temp_file)


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
