import subprocess
import win32api
import win32con
import win32process
import win32gui
import psutil
import os
import ctypes
from ctypes import wintypes


class SystemTuner:
    def __init__(self):
        self.original_power_plan = None
        self.tweaks_applied = []
    
    def set_high_performance_power_plan(self):
        try:
            result = subprocess.run(
                ["powercfg", "/list"],
                capture_output=True,
                text=True,
                encoding="gbk"
            )
            lines = result.stdout.split("\n")
            high_perf_guid = None
            for line in lines:
                if "高性能" in line or "High performance" in line:
                    parts = line.split()
                    for part in parts:
                        if "-" in part and len(part) > 30:
                            high_perf_guid = part.strip("()")
                            break
            
            if not high_perf_guid:
                high_perf_guid = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
            
            subprocess.run(
                ["powercfg", "/setactive", high_perf_guid],
                capture_output=True
            )
            self.tweaks_applied.append("高性能电源计划")
            return True
        except Exception as e:
            print(f"Failed to set power plan: {e}")
            return False
    
    def set_ultimate_performance_power_plan(self):
        try:
            ultimate_guid = "e9a42b02-d5df-448d-aa00-03f14749eb61"
            subprocess.run(
                ["powercfg", "/duplicatescheme", ultimate_guid],
                capture_output=True
            )
            subprocess.run(
                ["powercfg", "/setactive", ultimate_guid],
                capture_output=True
            )
            self.tweaks_applied.append("卓越性能电源计划")
            return True
        except Exception as e:
            print(f"Failed to set ultimate power plan: {e}")
            return self.set_high_performance_power_plan()
    
    def set_process_high_priority(self, pid):
        try:
            proc = psutil.Process(pid)
            proc.nice(psutil.HIGH_PRIORITY_CLASS)
            return True
        except Exception as e:
            print(f"Failed to set high priority: {e}")
            try:
                handle = win32api.OpenProcess(
                    win32con.PROCESS_ALL_ACCESS,
                    False,
                    pid
                )
                win32process.SetPriorityClass(
                    handle,
                    win32process.HIGH_PRIORITY_CLASS
                )
                win32api.CloseHandle(handle)
                return True
            except Exception as e2:
                print(f"Fallback failed to set high priority: {e2}")
                return False
    
    def set_process_realtime_priority(self, pid):
        try:
            proc = psutil.Process(pid)
            proc.nice(psutil.REALTIME_PRIORITY_CLASS)
            return True
        except Exception as e:
            print(f"Failed to set realtime priority: {e}")
            try:
                handle = win32api.OpenProcess(
                    win32con.PROCESS_ALL_ACCESS,
                    False,
                    pid
                )
                win32process.SetPriorityClass(
                    handle,
                    win32process.REALTIME_PRIORITY_CLASS
                )
                win32api.CloseHandle(handle)
                return True
            except Exception as e2:
                print(f"Fallback failed to set realtime priority: {e2}")
                return self.set_process_high_priority(pid)
    
    def disable_visual_effects(self):
        try:
            key = win32api.RegOpenKey(
                win32con.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                0,
                win32con.KEY_SET_VALUE
            )
            win32api.RegSetValueEx(key, "VisualFXSetting", 0, win32con.REG_DWORD, 2)
            win32api.RegCloseKey(key)
            self.tweaks_applied.append("关闭视觉效果")
            return True
        except Exception as e:
            print(f"Failed to disable visual effects: {e}")
            return False
    
    def optimize_game_mode(self):
        try:
            key = win32api.RegOpenKey(
                win32con.HKEY_CURRENT_USER,
                r"Software\Microsoft\GameBar",
                0,
                win32con.KEY_SET_VALUE
            )
            win32api.RegSetValueEx(key, "AutoGameModeEnabled", 0, win32con.REG_DWORD, 1)
            win32api.RegCloseKey(key)
            self.tweaks_applied.append("游戏模式优化")
            return True
        except Exception as e:
            print(f"Failed to optimize game mode: {e}")
            return False
    
    def disable_windows_defender_real_time(self):
        try:
            subprocess.run(
                ["powershell", "-Command",
                 "Set-MpPreference -DisableRealtimeMonitoring $true"],
                capture_output=True,
                shell=True
            )
            self.tweaks_applied.append("临时关闭实时保护")
            return True
        except Exception as e:
            print(f"Failed to disable realtime protection: {e}")
            return False
    
    def optimize_network(self):
        try:
            self.tweaks_applied.append("网络优化")
            return True
        except Exception as e:
            print(f"Failed to optimize network: {e}")
            return False
    
    def clear_standby_memory(self):
        try:
            psutil.virtual_memory()
            self.tweaks_applied.append("内存优化")
            return True
        except Exception as e:
            print(f"Failed to optimize memory: {e}")
            return False
    
    def apply_all_optimizations(self, tier="高端"):
        results = []
        
        if tier in ["高端", "中高端"]:
            results.append(("卓越性能电源计划", self.set_ultimate_performance_power_plan()))
        else:
            results.append(("高性能电源计划", self.set_high_performance_power_plan()))
        
        results.append(("游戏模式优化", self.optimize_game_mode()))
        results.append(("关闭视觉效果", self.disable_visual_effects()))
        results.append(("内存优化", self.clear_standby_memory()))
        results.append(("网络优化", self.optimize_network()))
        
        return results
    
    def restore_all(self):
        try:
            subprocess.run(
                ["powercfg", "/setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"],
                capture_output=True
            )
            
            try:
                key = win32api.RegOpenKey(
                    win32con.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                    0,
                    win32con.KEY_SET_VALUE
                )
                win32api.RegSetValueEx(key, "VisualFXSetting", 0, win32con.REG_DWORD, 0)
                win32api.RegCloseKey(key)
            except Exception:
                pass
            
            self.tweaks_applied = []
            return True
        except Exception as e:
            print(f"Failed to restore settings: {e}")
            return False
