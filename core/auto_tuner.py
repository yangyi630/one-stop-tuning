import time
import threading
from enum import Enum


class OptimizationLevel(Enum):
    MINIMUM = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    ULTRA = 4


class AutoTuner:
    def __init__(self, performance_monitor, system_tuner, game_settings):
        self.perf_monitor = performance_monitor
        self.system_tuner = system_tuner
        self.game_settings = game_settings
        
        self.running = False
        self.tune_thread = None
        
        self.current_level = OptimizationLevel.HIGH
        self.target_fps = 60
        self.min_fps = 45
        
        self.tune_interval = 10
        self.consecutive_stutters = 0
        self.consecutive_smooth = 0
        self.max_consecutive_stutters = 3
        self.max_consecutive_smooth = 5
        
        self.tune_history = []
        self.callbacks = []
    
    def start(self, initial_level=None):
        if self.running:
            return
        
        if initial_level:
            self.current_level = initial_level
        
        self.running = True
        self.consecutive_stutters = 0
        self.consecutive_smooth = 0
        self.tune_thread = threading.Thread(target=self._tune_loop, daemon=True)
        self.tune_thread.start()
    
    def stop(self):
        self.running = False
        if self.tune_thread:
            self.tune_thread.join(timeout=2)
    
    def _tune_loop(self):
        while self.running:
            try:
                time.sleep(self.tune_interval)
                
                if not self.running:
                    break
                
                stats = self.perf_monitor.get_stats()
                current_fps = stats["fps"]
                is_stuttering = self.perf_monitor.is_stuttering()
                
                action_taken = None
                
                if is_stuttering or current_fps < self.min_fps:
                    self.consecutive_stutters += 1
                    self.consecutive_smooth = 0
                    
                    if self.consecutive_stutters >= self.max_consecutive_stutters:
                        if self._decrease_quality():
                            action_taken = "降低画质"
                            self.consecutive_stutters = 0
                elif current_fps >= self.target_fps * 1.2:
                    self.consecutive_smooth += 1
                    self.consecutive_stutters = 0
                    
                    if self.consecutive_smooth >= self.max_consecutive_smooth:
                        if self._increase_quality():
                            action_taken = "提升画质"
                            self.consecutive_smooth = 0
                else:
                    self.consecutive_stutters = 0
                    self.consecutive_smooth = 0
                
                record = {
                    "time": time.time(),
                    "fps": current_fps,
                    "cpu": stats["cpu"],
                    "gpu": stats["gpu"],
                    "stuttering": is_stuttering,
                    "level": self.current_level.name,
                    "action": action_taken
                }
                self.tune_history.append(record)
                
                if len(self.tune_history) > 100:
                    self.tune_history = self.tune_history[-100:]
                
                for callback in self.callbacks:
                    try:
                        callback(record)
                    except Exception:
                        pass
                        
            except Exception as e:
                print(f"Auto tuner error: {e}")
                time.sleep(1)
    
    def _decrease_quality(self):
        levels = list(OptimizationLevel)
        current_idx = levels.index(self.current_level)
        
        if current_idx > 0:
            self.current_level = levels[current_idx - 1]
            self._apply_settings()
            return True
        return False
    
    def _increase_quality(self):
        levels = list(OptimizationLevel)
        current_idx = levels.index(self.current_level)
        
        if current_idx < len(levels) - 1:
            self.current_level = levels[current_idx + 1]
            self._apply_settings()
            return True
        return False
    
    def _apply_settings(self):
        if self.game_settings:
            self.game_settings.apply_preset(self.current_level)
    
    def set_target_fps(self, fps):
        self.target_fps = fps
    
    def set_min_fps(self, fps):
        self.min_fps = fps
    
    def set_tune_interval(self, seconds):
        self.tune_interval = max(5, seconds)
    
    def manual_tune(self, direction):
        if direction == "up":
            return self._increase_quality()
        elif direction == "down":
            return self._decrease_quality()
        return False
    
    def get_current_level(self):
        return self.current_level
    
    def get_tune_history(self):
        return self.tune_history.copy()
    
    def add_callback(self, callback):
        self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_recommendation(self):
        stats = self.perf_monitor.get_stats()
        fps = stats["fps"]
        cpu = stats["cpu"]
        gpu = stats["gpu"]
        
        recommendations = []
        
        if fps < 30:
            recommendations.append("严重卡顿，建议大幅降低画质设置")
            recommendations.append("关闭抗锯齿和阴影效果")
            recommendations.append("降低渲染分辨率")
        elif fps < 60:
            if gpu > 90:
                recommendations.append("GPU负载过高，建议降低画质")
                recommendations.append("降低纹理质量和特效等级")
            elif cpu > 90:
                recommendations.append("CPU负载过高，关闭后台程序")
                recommendations.append("降低物理模拟和粒子效果")
            else:
                recommendations.append("帧率偏低，可适当降低画质")
        elif fps >= 120:
            recommendations.append("帧率充足，可尝试提升画质")
            recommendations.append("开启更高画质设置以获得更好视觉体验")
        else:
            recommendations.append("运行流畅，当前设置较为平衡")
        
        if self.perf_monitor.is_stuttering():
            recommendations.append("检测到卡顿掉帧，建议降低画质")
            recommendations.append("关闭垂直同步可能减少卡顿")
        
        return recommendations
