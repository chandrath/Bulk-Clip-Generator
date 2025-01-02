import json
import os
from datetime import datetime, timedelta

class GPUCache:
    def __init__(self, cache_file="gpu_cache.json"):
        self.cache_file = cache_file
        
    def get_cached_gpu_info(self):
        try:
            if not os.path.exists(self.cache_file):
                return None
                
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                
            # Check if cache is less than 24 hours old
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > timedelta(hours=24):
                return None
                
            return cache_data['gpu_info']
        except:
            return None
            
    def save_gpu_info(self, gpu_info):
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'gpu_info': gpu_info
        }
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f)