# gpu_utils.py
import subprocess
import re
import platform
from gpu_cache import GPUCache

class GPUDetector:
    def __init__(self):
        self.gpu_cache = GPUCache()
        self.nvidia_available = False
        self.amd_available = False
        self.intel_quicksync_available = False
        
        # Try to load from cache first
        cached_info = self.gpu_cache.get_cached_gpu_info()
        if cached_info:
            self.nvidia_available = cached_info.get('nvidia', False)
            self.amd_available = cached_info.get('amd', False)
            self.intel_quicksync_available = cached_info.get('intel', False)
        else:
            self.detect_gpus()
            # Save to cache
            self.gpu_cache.save_gpu_info({
                'nvidia': self.nvidia_available,
                'amd': self.amd_available,
                'intel': self.intel_quicksync_available
            })

    def detect_gpus(self):
        system = platform.system()
        
        if system == "Windows":
            # Check for NVIDIA GPU
            try:
                nvidia_smi = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
                self.nvidia_available = nvidia_smi.returncode == 0
            except FileNotFoundError:
                self.nvidia_available = False
            except Exception as e:
                print(f"Error detecting NVIDIA GPU: {e}")
                self.nvidia_available = False

            # Check for Intel QuickSync
            try:
                dxdiag = subprocess.run(['dxdiag', '/t'], capture_output=True, text=True)
                self.intel_quicksync_available = 'Intel' in dxdiag.stdout
            except FileNotFoundError:
                 self.intel_quicksync_available = False
            except Exception as e:
                print(f"Error detecting Intel QuickSync: {e}")
                self.intel_quicksync_available = False

            # Check for AMD GPU
            try:
                wmic = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                    capture_output=True, text=True)
                self.amd_available = any('AMD' in line or 'Radeon' in line 
                                       for line in wmic.stdout.splitlines())
            except FileNotFoundError:
                self.amd_available = False
            except Exception as e:
                print(f"Error detecting AMD GPU: {e}")
                self.amd_available = False

    def get_available_encoders(self):
        encoders = []
        if self.nvidia_available:
            encoders.append(("NVIDIA NVENC", "h264_nvenc"))
        if self.amd_available:
            encoders.append(("AMD AMF", "h264_amf"))
        if self.intel_quicksync_available:
            encoders.append(("Intel QuickSync", "h264_qsv"))
        return encoders

    def is_any_gpu_available(self):
        return any([self.nvidia_available, self.amd_available, self.intel_quicksync_available])