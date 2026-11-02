import os
import shutil
import tempfile
import win32api
import win32con
import psutil
from datetime import datetime


class SystemCleaner:
    def __init__(self):
        self.cleaned_items = []
        self.total_freed_space = 0
    
    def get_cleanup_targets(self):
        targets = []
        
        temp_dir = os.environ.get("TEMP", tempfile.gettempdir())
        if os.path.exists(temp_dir):
            targets.append({
                "key": "temp_files",
                "name": "临时文件",
                "description": "系统和应用程序产生的临时文件",
                "path": temp_dir,
                "safe": True
            })
        
        win_temp = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Temp")
        if os.path.exists(win_temp):
            targets.append({
                "key": "windows_temp",
                "name": "Windows 临时文件",
                "description": "Windows 系统临时目录中的文件",
                "path": win_temp,
                "safe": True
            })
        
        prefetch = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Prefetch")
        if os.path.exists(prefetch):
            targets.append({
                "key": "prefetch",
                "name": "预读取文件",
                "description": "加快程序启动的预读取缓存，可安全清理",
                "path": prefetch,
                "safe": True
            })
        
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        if local_appdata:
            targets.append({
                "key": "crash_dumps",
                "name": "崩溃转储文件",
                "description": "程序崩溃时产生的内存转储文件",
                "path": os.path.join(local_appdata, "CrashDumps"),
                "safe": True
            })
            
            cache_path = os.path.join(local_appdata, "Microsoft", "Windows", "INetCache")
            if os.path.exists(cache_path):
                targets.append({
                    "key": "ie_cache",
                    "name": "IE 浏览器缓存",
                    "description": "Internet Explorer 浏览器缓存文件",
                    "path": cache_path,
                    "safe": True
                })
        
        recycle_bin = "::{645FF040-5081-101B-9F08-00AA002F954E}"
        targets.append({
            "key": "recycle_bin",
            "name": "回收站",
            "description": "清空回收站释放磁盘空间",
            "path": recycle_bin,
            "safe": True
        })
        
        thumbnails = os.path.join(local_appdata, "Microsoft", "Windows", "Explorer")
        if os.path.exists(thumbnails):
            targets.append({
                "key": "thumbnails",
                "name": "缩略图缓存",
                "description": "文件资源管理器的缩略图缓存",
                "path": thumbnails,
                "safe": True
            })
        
        return targets
    
    def scan_directory(self, path):
        total_size = 0
        file_count = 0
        
        if not os.path.exists(path):
            return 0, 0
        
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            size = os.path.getsize(file_path)
                            total_size += size
                            file_count += 1
                    except (PermissionError, OSError):
                        continue
                for dir_name in dirs:
                    try:
                        dir_path = os.path.join(root, dir_name)
                        if os.path.isdir(dir_path):
                            pass
                    except (PermissionError, OSError):
                        continue
        except Exception:
            pass
        
        return total_size, file_count
    
    def scan_all(self, targets=None):
        if targets is None:
            targets = self.get_cleanup_targets()
        
        results = []
        total_size = 0
        total_files = 0
        
        for target in targets:
            if target["key"] == "recycle_bin":
                size, count = self._scan_recycle_bin()
            else:
                size, count = self.scan_directory(target["path"])
            
            results.append({
                **target,
                "size": size,
                "file_count": count
            })
            total_size += size
            total_files += count
        
        return results, total_size, total_files
    
    def _scan_recycle_bin(self):
        total_size = 0
        file_count = 0
        
        try:
            drives = win32api.GetLogicalDriveStrings().split("\x00")[:-1]
            for drive in drives:
                recycle_path = os.path.join(drive, "$Recycle.Bin")
                if os.path.exists(recycle_path):
                    size, count = self.scan_directory(recycle_path)
                    total_size += size
                    file_count += count
        except Exception:
            pass
        
        return total_size, file_count
    
    def clean_directory(self, path, key=""):
        cleaned_size = 0
        cleaned_count = 0
        errors = []
        
        if not os.path.exists(path):
            return 0, 0, []
        
        try:
            for root, dirs, files in os.walk(path, topdown=False):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleaned_size += size
                            cleaned_count += 1
                    except (PermissionError, OSError) as e:
                        errors.append(str(e))
                        continue
                
                for dir_name in dirs:
                    try:
                        dir_path = os.path.join(root, dir_name)
                        if os.path.isdir(dir_path):
                            if not os.listdir(dir_path):
                                shutil.rmtree(dir_path, ignore_errors=True)
                    except (PermissionError, OSError):
                        continue
        except Exception as e:
            errors.append(str(e))
        
        self.cleaned_items.append({
            "key": key,
            "size": cleaned_size,
            "count": cleaned_count,
            "time": datetime.now()
        })
        self.total_freed_space += cleaned_size
        
        return cleaned_size, cleaned_count, errors
    
    def clean_all(self, targets=None):
        if targets is None:
            targets = [t for t in self.get_cleanup_targets() if t["safe"]]
        
        results = []
        total_cleaned = 0
        total_files = 0
        
        for target in targets:
            if target["key"] == "recycle_bin":
                size, count, errors = self._clean_recycle_bin()
            else:
                size, count, errors = self.clean_directory(target["path"], target["key"])
            
            results.append({
                **target,
                "cleaned_size": size,
                "cleaned_count": count,
                "errors": errors
            })
            total_cleaned += size
            total_files += count
        
        self.total_freed_space += total_cleaned
        
        return results, total_cleaned, total_files
    
    def _clean_recycle_bin(self):
        cleaned_size = 0
        cleaned_count = 0
        errors = []
        
        try:
            import winshell
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
        except Exception:
            try:
                drives = win32api.GetLogicalDriveStrings().split("\x00")[:-1]
                for drive in drives:
                    recycle_path = os.path.join(drive, "$Recycle.Bin")
                    if os.path.exists(recycle_path):
                        size, count, errs = self.clean_directory(recycle_path, "recycle_bin")
                        cleaned_size += size
                        cleaned_count += count
                        errors.extend(errs)
            except Exception as e:
                errors.append(str(e))
        
        return cleaned_size, cleaned_count, errors
    
    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.2f} GB"
    
    def get_disk_usage(self):
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                })
            except (PermissionError, OSError):
                continue
        return disks
    
    def get_memory_optimization_info(self):
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
            "cached": getattr(mem, 'cached', 0),
            "buffers": getattr(mem, 'buffers', 0)
        }
    
    def optimize_memory(self):
        try:
            mem = psutil.virtual_memory()
            
            try:
                import ctypes
                ctypes.windll.psapi.EmptyWorkingSet(-1)
            except Exception:
                pass
            
            return True, "内存优化已执行"
        except Exception as e:
            return False, f"内存优化失败: {str(e)}"
