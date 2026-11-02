import time
import threading
import psutil
from collections import deque
import win32gui
import win32process

try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False


class PerformanceMonitor:
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.callbacks = []
        
        self.fps_history = deque(maxlen=60)
        self.cpu_history = deque(maxlen=60)
        self.gpu_history = deque(maxlen=60)
        self.memory_history = deque(maxlen=60)
        self.frame_time_history = deque(maxlen=60)
        
        self.current_fps = 0
        self.current_cpu = 0
        self.current_gpu = 0
        self.current_memory = 0
        self.current_frame_time = 0
        
        self.game_pid = None
        self.last_frame_time = time.time()
        self.frame_count = 0
        self.stutter_count = 0
        self.stutter_threshold = 50
    
    def start(self, game_pid=None):
        if self.running:
            return
        
        self.game_pid = game_pid
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        fps_start_time = time.time()
        fps_frame_count = 0
        
        while self.running:
            try:
                self.current_cpu = psutil.cpu_percent(interval=0.1)
                self.cpu_history.append(self.current_cpu)
                
                if HAS_GPUTIL:
                    try:
                        gpus = GPUtil.getGPUs()
                        if gpus:
                            self.current_gpu = gpus[0].load * 100
                            self.current_memory = gpus[0].memoryUsed
                    except Exception:
                        mem = psutil.virtual_memory()
                        self.current_memory = mem.used / (1024**2)
                else:
                    mem = psutil.virtual_memory()
                    self.current_memory = mem.used / (1024**2)
                
                self.memory_history.append(self.current_memory)
                self.gpu_history.append(self.current_gpu)
                
                fps_frame_count += 1
                current_time = time.time()
                if current_time - fps_start_time >= 1.0:
                    self.current_fps = fps_frame_count / (current_time - fps_start_time)
                    self.fps_history.append(self.current_fps)
                    
                    if self.fps_history:
                        avg_fps = sum(self.fps_history) / len(self.fps_history)
                        if self.current_fps < avg_fps * 0.7:
                            self.stutter_count += 1
                    
                    fps_start_time = current_time
                    fps_frame_count = 0
                
                self.current_frame_time = (1.0 / self.current_fps * 1000) if self.current_fps > 0 else 0
                self.frame_time_history.append(self.current_frame_time)
                
                for callback in self.callbacks:
                    try:
                        callback(self.get_stats())
                    except Exception:
                        pass
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(0.5)
    
    def get_stats(self):
        return {
            "fps": self.current_fps,
            "cpu": self.current_cpu,
            "gpu": self.current_gpu,
            "memory": self.current_memory,
            "frame_time": self.current_frame_time,
            "stutter_count": self.stutter_count,
            "fps_avg": sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0,
            "fps_min": min(self.fps_history) if self.fps_history else 0,
            "fps_max": max(self.fps_history) if self.fps_history else 0,
            "cpu_avg": sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else 0,
            "gpu_avg": sum(self.gpu_history) / len(self.gpu_history) if self.gpu_history else 0
        }
    
    def is_stuttering(self):
        if len(self.fps_history) < 10:
            return False
        
        avg_fps = sum(self.fps_history) / len(self.fps_history)
        recent_fps = list(self.fps_history)[-10:]
        recent_avg = sum(recent_fps) / len(recent_fps)
        
        if recent_avg < avg_fps * 0.8:
            return True
        
        frame_times = list(self.frame_time_history)[-10:]
        if frame_times:
            avg_frame_time = sum(frame_times) / len(frame_times)
            high_frame_times = [ft for ft in frame_times if ft > self.stutter_threshold]
            if len(high_frame_times) > len(frame_times) * 0.3:
                return True
        
        return False
    
    def get_performance_grade(self):
        fps = self.current_fps
        if fps >= 120:
            return "极佳", 100
        elif fps >= 90:
            return "优秀", 85
        elif fps >= 60:
            return "良好", 70
        elif fps >= 45:
            return "一般", 50
        elif fps >= 30:
            return "较差", 30
        else:
            return "很差", 10
    
    def add_callback(self, callback):
        self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def reset_stutter_count(self):
        self.stutter_count = 0
