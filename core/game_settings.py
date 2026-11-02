import os
import json
import win32con
import win32api
import time


class GameSettings:
    def __init__(self, game_name="暗区突围"):
        self.game_name = game_name
        self.settings = {}
        self.config_path = None
        self.original_settings = None
        
        self.presets = {
            "minimum": {
                "resolution_scale": 0.5,
                "texture_quality": 0,
                "shadow_quality": 0,
                "antialiasing": 0,
                "effects_quality": 0,
                "post_processing": 0,
                "view_distance": 0,
                "vsync": False,
                "frame_rate_limit": 0,
                "dynamic_resolution": True,
                "motion_blur": False,
                "depth_of_field": False,
                "bloom": False,
                "ambient_occlusion": 0,
                "reflections": 0
            },
            "low": {
                "resolution_scale": 0.75,
                "texture_quality": 1,
                "shadow_quality": 0,
                "antialiasing": 0,
                "effects_quality": 1,
                "post_processing": 1,
                "view_distance": 1,
                "vsync": False,
                "frame_rate_limit": 60,
                "dynamic_resolution": True,
                "motion_blur": False,
                "depth_of_field": False,
                "bloom": False,
                "ambient_occlusion": 0,
                "reflections": 0
            },
            "medium": {
                "resolution_scale": 1.0,
                "texture_quality": 2,
                "shadow_quality": 1,
                "antialiasing": 1,
                "effects_quality": 2,
                "post_processing": 2,
                "view_distance": 2,
                "vsync": False,
                "frame_rate_limit": 60,
                "dynamic_resolution": False,
                "motion_blur": False,
                "depth_of_field": False,
                "bloom": True,
                "ambient_occlusion": 1,
                "reflections": 1
            },
            "high": {
                "resolution_scale": 1.0,
                "texture_quality": 3,
                "shadow_quality": 2,
                "antialiasing": 2,
                "effects_quality": 3,
                "post_processing": 3,
                "view_distance": 3,
                "vsync": False,
                "frame_rate_limit": 120,
                "dynamic_resolution": False,
                "motion_blur": True,
                "depth_of_field": True,
                "bloom": True,
                "ambient_occlusion": 2,
                "reflections": 2
            },
            "ultra": {
                "resolution_scale": 1.0,
                "texture_quality": 4,
                "shadow_quality": 3,
                "antialiasing": 3,
                "effects_quality": 4,
                "post_processing": 4,
                "view_distance": 4,
                "vsync": True,
                "frame_rate_limit": 0,
                "dynamic_resolution": False,
                "motion_blur": True,
                "depth_of_field": True,
                "bloom": True,
                "ambient_occlusion": 3,
                "reflections": 3
            }
        }
        
        self.quality_levels = ["最低", "低", "中", "高", "极致"]
    
    def find_config_file(self):
        possible_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\ArenaBreakout\Saved\Config\WindowsNoEditor"),
            os.path.expandvars(r"%APPDATA%\ArenaBreakout\Saved\Config\WindowsNoEditor"),
            os.path.expandvars(r"%USERPROFILE%\Documents\ArenaBreakout\Config"),
            os.path.expandvars(r"%LOCALAPPDATA%\暗区突围\Saved\Config\WindowsNoEditor"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.config_path = path
                return path
        
        return None
    
    def load_settings(self):
        config_path = self.find_config_file()
        if not config_path:
            return False
        
        try:
            settings_file = os.path.join(config_path, "GameUserSettings.ini")
            if os.path.exists(settings_file):
                with open(settings_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                self.settings = self._parse_ini(content)
                self.original_settings = self.settings.copy()
                return True
        except Exception as e:
            print(f"Failed to load settings: {e}")
        
        return False
    
    def _parse_ini(self, content):
        settings = {}
        current_section = None
        
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith(";") or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                settings[current_section] = {}
            elif "=" in line and current_section:
                key, value = line.split("=", 1)
                settings[current_section][key.strip()] = value.strip()
        
        return settings
    
    def _serialize_ini(self, settings):
        lines = []
        for section, values in settings.items():
            lines.append(f"[{section}]")
            for key, value in values.items():
                lines.append(f"{key}={value}")
            lines.append("")
        return "\n".join(lines)
    
    def save_settings(self):
        if not self.config_path or not self.settings:
            return False
        
        try:
            settings_file = os.path.join(self.config_path, "GameUserSettings.ini")
            content = self._serialize_ini(self.settings)
            with open(settings_file, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Failed to save settings: {e}")
            return False
    
    def apply_preset(self, level):
        level_name = level.name.lower() if hasattr(level, 'name') else str(level).lower()
        
        if level_name == "optimizationlevel.minimum":
            level_name = "minimum"
        elif level_name == "optimizationlevel.low":
            level_name = "low"
        elif level_name == "optimizationlevel.medium":
            level_name = "medium"
        elif level_name == "optimizationlevel.high":
            level_name = "high"
        elif level_name == "optimizationlevel.ultra":
            level_name = "ultra"
        
        preset = self.presets.get(level_name)
        if not preset:
            return False
        
        self.settings = self.settings or {}
        
        if "/Script/Engine.GameUserSettings" not in self.settings:
            self.settings["/Script/Engine.GameUserSettings"] = {}
        
        gs = self.settings["/Script/Engine.GameUserSettings"]
        
        gs["ResolutionQuality"] = str(int(preset["resolution_scale"] * 100))
        gs["OverallQualityLevel"] = str(preset["texture_quality"])
        gs["ShadowQuality"] = str(preset["shadow_quality"])
        gs["AntiAliasingQuality"] = str(preset["antialiasing"])
        gs["EffectsQuality"] = str(preset["effects_quality"])
        gs["PostProcessingQuality"] = str(preset["post_processing"])
        gs["ViewDistanceQuality"] = str(preset["view_distance"])
        gs["bUseVSync"] = "True" if preset["vsync"] else "False"
        gs["FrameRateLimit"] = str(preset["frame_rate_limit"])
        
        return self.save_settings()
    
    def set_setting(self, category, key, value):
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = str(value)
    
    def get_setting(self, category, key, default=None):
        if category in self.settings and key in self.settings[category]:
            return self.settings[category][key]
        return default
    
    def optimize_for_performance(self):
        return self.apply_preset("minimum")
    
    def optimize_for_quality(self):
        return self.apply_preset("ultra")
    
    def apply_balanced(self):
        return self.apply_preset("medium")
    
    def restore_original(self):
        if self.original_settings:
            self.settings = self.original_settings.copy()
            return self.save_settings()
        return False
    
    def get_current_quality_description(self):
        if not self.settings:
            return "未知"
        
        gs = self.settings.get("/Script/Engine.GameUserSettings", {})
        overall = gs.get("OverallQualityLevel", "2")
        
        try:
            level = int(overall)
            if 0 <= level < len(self.quality_levels):
                return self.quality_levels[level]
        except ValueError:
            pass
        
        return "中等"
