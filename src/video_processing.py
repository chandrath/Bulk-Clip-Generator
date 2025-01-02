# video_processing.py
import subprocess
import os
import sys
from tempfile import mkdtemp
import shutil
import signal

# Global variable to store current FFmpeg process
current_process = None

def run_ffmpeg_command(command_args, is_ffprobe=False):
    global current_process

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    executable = "ffprobe.exe" if is_ffprobe else "ffmpeg.exe"
    ffmpeg_path = os.path.join(base_path, "ffmpeg", executable)

    if not os.path.exists(ffmpeg_path):
        raise FileNotFoundError(f"{executable} not found at {ffmpeg_path}")

    # Log the command being run for debugging
    full_command = [ffmpeg_path] + command_args

    try:
        current_process = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=None if is_ffprobe else subprocess.STARTUPINFO()
        )
        stdout, stderr = current_process.communicate(timeout=15)  # Added timeout
        return_code = current_process.returncode
        return stdout, stderr, return_code
    except subprocess.TimeoutExpired:
        # Process timed out, attempt to terminate gracefully
        if current_process.poll() is None:
            try:
                current_process.terminate()
                current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                current_process.kill()
        return None, None, -1  # Indicate process was terminated
    except Exception as e:
        raise RuntimeError(f"Failed to execute {executable}: {str(e)}")
    finally:
        current_process = None  # Ensure process is cleared

def terminate_current_process():
    global current_process
    if current_process and current_process.poll() is None:
        try:
            current_process.terminate()
            current_process.wait(timeout=5)  # Wait up to 5 seconds for graceful termination
        except subprocess.TimeoutExpired:
            current_process.kill()  # Force kill if process doesn't terminate gracefully
        except Exception as e:
            print(f"Error terminating process: {e}")
        finally:
            current_process = None
        return True
    return False

def get_video_duration(video_path):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    command = [
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    try:
        stdout, stderr, returncode = run_ffmpeg_command(command, is_ffprobe=True)

        if returncode != 0:
            # Try alternative method if first method fails
            command = [
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            stdout, stderr, returncode = run_ffmpeg_command(command, is_ffprobe=True)

        if returncode != 0:
            stderr_text = stderr.decode().strip() if stderr else "Unknown error"
            raise ValueError(f"FFprobe error (code {returncode}): {stderr_text}")

        duration_str = stdout.decode().strip()
        if not duration_str:
            raise ValueError("No duration information found in video file")

        return float(duration_str)

    except ValueError as ve:
        raise RuntimeError(f"Failed to get video duration: {str(ve)}")
    except Exception as e:
        raise RuntimeError(f"Failed to get video duration: {str(e)}")

def normalize_video(input_file, output_file, lossless=False, hw_encoder=None):
    """Normalize video to a consistent format for concatenation"""
    command = [
        "-i", input_file,
        "-map", "0:v:0",  # Select first video stream
        "-map", "0:a:0?",  # Select first audio stream if it exists
    ]

    # Handle hardware acceleration
    if hw_encoder:
        command.extend(["-c:v", hw_encoder])
        if hw_encoder == "h264_nvenc":
            command.extend(["-preset", "p4"])  # NVIDIA preset
        elif hw_encoder == "h264_amf":
            command.extend(["-quality", "speed"])  # AMD preset
        elif hw_encoder == "h264_qsv":
            command.extend(["-preset", "faster"])  # Intel QuickSync preset
    else:
        command.extend([
            "-c:v", "libx264",
            "-preset", "fast"
        ])

    if lossless:
        if hw_encoder:
            command.extend(["-qp", "18"])  # Hardware equivalent of CRF
        else:
            command.extend(["-crf", "18"])
    else:
        if hw_encoder:
            command.extend(["-qp", "23"])
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
    if returncode != 0 and returncode != -1:  # -1 indicates process was terminated
        raise RuntimeError(f"Error normalizing video: {stderr.decode().strip()}")
    return returncode == 0

def cut_video_segment(input_file, output_file, start_time, end_time, lossless=False, 
                     intro_path=None, outro_path=None, progress_callback=None, hw_encoder=None):
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
            "-map", "0:v:0",
            "-map", "0:a:0?"
        ]

        # Add hardware acceleration parameters
        if hw_encoder:
            cut_command.extend(["-c:v", hw_encoder])
            if hw_encoder == "h264_nvenc":
                cut_command.extend(["-preset", "p4"])
            elif hw_encoder == "h264_amf":
                cut_command.extend(["-quality", "speed"])
            elif hw_encoder == "h264_qsv":
                cut_command.extend(["-preset", "faster"])
        else:
            cut_command.extend([
                "-c:v", "libx264",
                "-preset", "fast"
            ])

        # Add quality settings
        if lossless:
            if hw_encoder:
                cut_command.extend(["-qp", "18"])
            else:
                cut_command.extend(["-crf", "18"])
        else:
            if hw_encoder:
                cut_command.extend(["-qp", "23"])
            else:
                cut_command.extend(["-crf", "23"])

        cut_command.extend([
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-pix_fmt", "yuv420p",
            "-y",
            temp_main
        ])

        stdout, stderr, returncode = run_ffmpeg_command(cut_command)
        if returncode != 0 and returncode != -1:
            # Only show actual error messages, not progress output
            error_lines = stderr.decode().strip().split('\n')
            error_message = next((line for line in reversed(error_lines) if 'error' in line.lower()), 'Unknown error occurred')
            raise RuntimeError(error_message)
        if returncode == -1:  # Process was terminated
            return False, "Processing was stopped by user"
        temp_files.append(temp_main)

        # After cutting main segment:
        if progress_callback:
            progress_callback(33)  # 33% complete after main cut

        # Step 2: Normalize intro and outro if present
        concat_list = []

        if intro_path:
            temp_intro = os.path.join(temp_dir, "temp_intro.mp4")
            if normalize_video(intro_path, temp_intro, lossless, hw_encoder):
                concat_list.append(temp_intro)
                temp_files.append(temp_intro)
            elif current_process is None:  # Process was terminated
                return False, "Processing was stopped by user"

        concat_list.append(temp_main)

        if outro_path:
            temp_outro = os.path.join(temp_dir, "temp_outro.mp4")
            if normalize_video(outro_path, temp_outro, lossless, hw_encoder):
                concat_list.append(temp_outro)
                temp_files.append(temp_outro)
            elif current_process is None:  # Process was terminated
                return False, "Processing was stopped by user"

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
        if returncode != 0 and returncode != -1:
            # Only show actual error messages, not progress output
            error_lines = stderr.decode().strip().split('\n')
            error_message = next((line for line in reversed(error_lines) if 'error' in line.lower()), 'Unknown error occurred')
            raise RuntimeError(error_message)
        if returncode == -1:  # Process was terminated
            return False, "Processing was stopped by user"


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