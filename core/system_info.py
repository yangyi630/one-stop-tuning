import psutil
import platform
import wmi
import subprocess
from screeninfo import get_monitors

try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False


class SystemInfo:
    def __init__(self):
        self.wmi_client = wmi.WMI()
        self.refresh()
    
    def refresh(self):
        self.cpu_info = self._get_cpu_info()
        self.gpu_info = self._get_gpu_info()
        self.memory_info = self._get_memory_info()
        self.disk_info = self._get_disk_info()
        self.display_info = self._get_display_info()
        self.os_info = self._get_os_info()
    
    def _get_cpu_info(self):
        cpu = self.wmi_client.Win32_Processor()[0]
        return {
            "name": cpu.Name,
            "cores": cpu.NumberOfCores,
            "threads": cpu.NumberOfLogicalProcessors,
            "max_clock": cpu.MaxClockSpeed,
            "current_clock": cpu.CurrentClockSpeed,
            "load_percent": psutil.cpu_percent(interval=0.1),
            "architecture": platform.machine()
        }
    
    def _get_gpu_info(self):
        gpus = []
        virtual_gpu_keywords = ["virtual", "虚拟", "mumu", "nox", "ldplayer",
                                "hyper-v", "vmware", "virtualbox", "wddm",
                                "microsoft basic", "microsoft remote"]
        
        if HAS_GPUTIL:
            try:
                gpu_list = GPUtil.getGPUs()
                for gpu in gpu_list:
                    is_virtual = any(kw.lower() in gpu.name.lower() for kw in virtual_gpu_keywords)
                    if not is_virtual:
                        gpus.append({
                            "name": gpu.name,
                            "memory_total": gpu.memoryTotal,
                            "memory_used": gpu.memoryUsed,
                            "memory_free": gpu.memoryFree,
                            "load": gpu.load,
                            "temperature": gpu.temperature,
                            "driver": gpu.driver,
                            "is_virtual": False
                        })
            except Exception:
                pass
        
        if not gpus:
            try:
                all_gpus = list(self.wmi_client.Win32_VideoController())
                for gpu in all_gpus:
                    mem = 0
                    if gpu.AdapterRAM:
                        try:
                            raw_mem = int(gpu.AdapterRAM)
                            if raw_mem < 0:
                                raw_mem = raw_mem + 2**32
                            mem = raw_mem / (1024**2)
                        except Exception:
                            mem = 0
                    
                    is_virtual = any(kw.lower() in str(gpu.Name).lower() for kw in virtual_gpu_keywords)
                    
                    gpus.append({
                        "name": gpu.Name,
                        "memory_total": mem,
                        "memory_used": 0,
                        "memory_free": mem,
                        "load": 0,
                        "temperature": 0,
                        "driver": gpu.DriverVersion,
                        "is_virtual": is_virtual
                    })
                
                physical_gpus = [g for g in gpus if not g["is_virtual"]]
                if physical_gpus:
                    gpus = sorted(physical_gpus, key=lambda x: x["memory_total"], reverse=True)
            except Exception:
                pass
        
        if not gpus:
            gpus.append({
                "name": "未知显卡",
                "memory_total": 0,
                "memory_used": 0,
                "memory_free": 0,
                "load": 0,
                "temperature": 0,
                "driver": "未知",
                "is_virtual": False
            })
        
        return gpus
    
    def _get_memory_info(self):
        mem = psutil.virtual_memory()
        return {
            "total": mem.total / (1024**3),
            "available": mem.available / (1024**3),
            "used": mem.used / (1024**3),
            "percent": mem.percent,
            "speed": 0
        }
    
    def _get_disk_info(self):
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total / (1024**3),
                    "used": usage.used / (1024**3),
                    "free": usage.free / (1024**3),
                    "percent": usage.percent
                })
            except Exception:
                continue
        return disks
    
    def _get_display_info(self):
        monitors = []
        try:
            for monitor in get_monitors():
                monitors.append({
                    "name": monitor.name,
                    "width": monitor.width,
                    "height": monitor.height,
                    "is_primary": monitor.is_primary
                })
        except Exception:
            monitors.append({
                "name": "主显示器",
                "width": 1920,
                "height": 1080,
                "is_primary": True
            })
        return monitors
    
    def _get_os_info(self):
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine()
        }
    
    def get_performance_score(self):
        score = 0
        cpu_score = min(100, (self.cpu_info["threads"] * 5) + (self.cpu_info["max_clock"] / 100))
        gpu_score = 0
        if self.gpu_info:
            gpu = self.gpu_info[0]
            gpu_score = min(100, (gpu["memory_total"] / 100) + gpu["load"])
        mem_score = min(100, self.memory_info["total"] * 5)
        score = (cpu_score * 0.3 + gpu_score * 0.4 + mem_score * 0.3)
        return min(100, max(0, score))
    
    def get_tier(self):
        score = self.get_performance_score()
        if score >= 80:
            return "高端", "极致画质+高帧率"
        elif score >= 60:
            return "中高端", "高画质+稳定帧率"
        elif score >= 40:
            return "中端", "中等画质+流畅帧率"
        elif score >= 20:
            return "低端", "低画质+基本流畅"
        else:
            return "入门", "最低画质+优先流畅"
