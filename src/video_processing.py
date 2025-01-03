# video_processing.py
import subprocess
import os
import sys
from tempfile import mkdtemp
import shutil
import signal


# Global variable to store current FFmpeg process
current_process = None

class UserCancellationError(Exception):
    """Custom exception for user-initiated cancellation."""
    pass

def run_ffmpeg_command(command_args, is_ffprobe=False, timeout=None):
    global current_process

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    executable = "ffprobe.exe" if is_ffprobe else "ffmpeg.exe"
    ffmpeg_path = os.path.join(base_path, "ffmpeg", executable)

    if not os.path.exists(ffmpeg_path):
        raise FileNotFoundError(f"{executable} not found at {ffmpeg_path}")

    full_command = [ffmpeg_path] + command_args

    try:
        current_process = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=None if is_ffprobe else subprocess.STARTUPINFO()
        )
        stdout, stderr = current_process.communicate(timeout=timeout)  # Added timeout
        return_code = current_process.returncode
        return return_code, stdout, stderr
    except subprocess.TimeoutExpired:
        # Process timed out, attempt to terminate gracefully
        if current_process.poll() is None:
            try:
                current_process.terminate()
                current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                current_process.kill()
        return -1, None, "TimeoutExpired"
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
        returncode, stdout, stderr = run_ffmpeg_command(command, is_ffprobe=True)

        if returncode != 0:
            # Try alternative method if first method fails
            command = [
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            returncode, stdout, stderr = run_ffmpeg_command(command, is_ffprobe=True)

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

def try_hw_accelerated_command(command, hw_encoder, hw_acceleration_enabled=False):
    """Try hardware acceleration first, fall back to software if it fails"""
    if hw_encoder and hw_acceleration_enabled:  # Check if acceleration is enabled
        try:
            # Try hardware-accelerated encoding
            returncode, stdout, stderr = run_ffmpeg_command(command)
            if returncode == 0:
                return returncode, stdout, stderr

            # If hardware encoding failed, fall back to software encoding
            sw_command = command.copy()
            encoder_index = sw_command.index(hw_encoder)
            sw_command[encoder_index-1:encoder_index+1] = ["-c:v", "libx264"]

            # Replace hardware-specific parameters
            try:
                preset_index = sw_command.index("-preset")
                if "nvenc" in hw_encoder:
                    sw_command[preset_index+1] = "fast"
            except ValueError:
                pass
            try:
                qp_index = sw_command.index("-qp")
                sw_command[qp_index] = "-crf"
            except ValueError:
                pass
            return run_ffmpeg_command(sw_command)
        except Exception:
            # Fall back to software encoding
            sw_command = command.copy()
            encoder_index = sw_command.index(hw_encoder)
            sw_command[encoder_index-1:encoder_index+1] = ["-c:v", "libx264"]
            return run_ffmpeg_command(sw_command)

    # If no hardware acceleration is enabled, use software encoding
    sw_command = command.copy()
    if hw_encoder in sw_command:
        encoder_index = sw_command.index(hw_encoder)
        sw_command[encoder_index-1:encoder_index+1] = ["-c:v", "libx264"]
    return run_ffmpeg_command(sw_command)

def normalize_video(input_file, output_file, lossless=False, hw_encoder=None, hw_acceleration_enabled=False):
    """Normalize video to a consistent format for concatenation"""
    command = [
        "-i", input_file,
        "-map", "0:v:0",  # Select first video stream
        "-map", "0:a:0?",  # Select first audio stream if it exists
    ]

    # Handle hardware acceleration
    if hw_encoder and hw_acceleration_enabled:
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
        if hw_encoder and hw_acceleration_enabled:
            command.extend(["-qp", "18"])  # Hardware equivalent of CRF
        else:
            command.extend(["-crf", "18"])
    else:
        if hw_encoder and hw_acceleration_enabled:
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

    returncode, stdout, stderr = try_hw_accelerated_command(command, hw_encoder, hw_acceleration_enabled)
    if returncode != 0 and returncode != -1:  # -1 indicates process was terminated
        raise RuntimeError(f"Error normalizing video: {stderr.decode().strip()}")
    return returncode == 0

def cut_video_segment(source, output, start, end, lossless, intro=None, outro=None, progress_callback=None, hw_encoder=None, hw_acceleration_enabled=False):
    # Create temporary directory for intermediate files
    temp_dir = mkdtemp()
    temp_files = []

    try:
        # Step 1: Cut the main segment
        temp_main = os.path.join(temp_dir, "temp_main.mp4")
        cut_command = [
            "-i", source,
            "-ss", start,
            "-to", end,
            "-map", "0:v:0",
            "-map", "0:a:0?"
        ]

        # Add hardware acceleration parameters
        if hw_encoder and hw_acceleration_enabled:
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
            if hw_encoder and hw_acceleration_enabled:
                cut_command.extend(["-qp", "18"])
            else:
                cut_command.extend(["-crf", "18"])
        else:
            if hw_encoder and hw_acceleration_enabled:
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
        returncode, stdout, stderr = try_hw_accelerated_command(cut_command, hw_encoder, hw_acceleration_enabled)

        if returncode != 0 and returncode != -1:
            # Only show actual error messages, not progress output
            error_lines = stderr.decode().strip().split('\n')
            error_message = next((line for line in reversed(error_lines) if 'error' in line.lower()), 'Unknown error occurred')
            raise RuntimeError(error_message)
        if returncode == -1:  # Process was terminated
            raise UserCancellationError("Processing was stopped by user")
        temp_files.append(temp_main)

        # After cutting main segment:
        if progress_callback:
            progress_callback(33)  # 33% complete after main cut

        # Step 2: Normalize intro and outro if present
        concat_list = []

        if intro:
            temp_intro = os.path.join(temp_dir, "temp_intro.mp4")
            if normalize_video(intro, temp_intro, lossless, hw_encoder, hw_acceleration_enabled):
                concat_list.append(temp_intro)
                temp_files.append(temp_intro)
            else:
                if current_process is None:  # Process was terminated
                    raise UserCancellationError("Processing was stopped by user")
                else:
                    raise RuntimeError("Error normalizing intro")

        concat_list.append(temp_main)

        if outro:
            temp_outro = os.path.join(temp_dir, "temp_outro.mp4")
            if normalize_video(outro, temp_outro, lossless, hw_encoder, hw_acceleration_enabled):
                concat_list.append(temp_outro)
                temp_files.append(temp_outro)
            else:
                 if current_process is None:  # Process was terminated
                      raise UserCancellationError("Processing was stopped by user")
                 else:
                    raise RuntimeError("Error normalizing outro")

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
            output
        ]
        try:
           returncode, stdout, stderr = run_ffmpeg_command(concat_command, timeout=600)
        except Exception as e:
           raise Exception(f"Concatenation process timed out or failed: {e}")

        if returncode != 0:
             # Only show actual error messages, not progress output
             error_lines = stderr.decode().strip().split('\n')
             error_message = next((line for line in reversed(error_lines) if 'error' in line.lower()), 'Unknown error occurred')
             raise Exception(f"Concatenation failed: {error_message}")

        # After final concatenation:
        if progress_callback:
            progress_callback(100)  # 100% complete

        return True, None

    except UserCancellationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error: {e}"

    finally:
        # Clean up all temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
def process_clips(self, parsed_ranges, source_video, intro_clip, outro_clip, output_location, lossless, original_filename, hw_encoder=None, hw_acceleration_enabled=False):
    self.total_clips = len(parsed_ranges)
    self.start_time = time.time()
    self.processed_clips = 0  # Reset processed clips counter

    try:
        for i, (start_time_str, end_time_str) in enumerate(parsed_ranges, 1):
            if not self.processing_active:
                return  # Exit if processing is stopped

            output_filename = f"Clip_{i}_{original_filename}.mp4"
            output_path = os.path.join(output_location, output_filename)

            def progress_handler(progress):
                if self.processing_active:
                    clip_progress = ((i - 1) * 100 + progress) / self.total_clips
                    self.root.after(0, lambda p=clip_progress: self.update_progress(p))

            success, error_message = cut_video_segment(
                source_video,
                output_path,
                start_time_str,
                end_time_str,
                lossless,
                intro_clip if self.use_intro.get() else None,
                outro_clip if self.use_outro.get() else None,
                progress_callback=progress_handler,
                hw_encoder=hw_encoder if hw_acceleration_enabled else None,
                hw_acceleration_enabled=hw_acceleration_enabled
            )

            if not success:
                if "timeout" in error_message.lower():
                    self.show_error(f"Clip {i} failed: FFmpeg concatenation timed out. Please check your input files or try again with fewer edits.")

                else:
                    self.show_error(f"Error processing clip {i}: {error_message}")
                self.root.after(0, self.stop_processing)
                return

            self.processed_clips += 1

            if not self.processing_active:
                return  # Check again after each clip

        if self.processing_active:
            self.root.after(0, lambda: self.show_info("Video clipping completed!"))

    except Exception as e:
        self.show_error(f"An unexpected error occurred: {str(e)}")
    finally:
        self.root.after(0, self.stop_processing)

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