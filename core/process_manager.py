import psutil
import win32api
import win32con
import win32process
import os
from collections import defaultdict


class ProcessManager:
    def __init__(self):
        pass
    
    def get_all_processes(self):
        processes = []
        for proc in psutil.process_iter(["pid", "name", "exe", "cpu_percent", "memory_percent", "memory_info", "status", "create_time", "nice"]):
            try:
                info = proc.info
                mem_info = info.get("memory_info")
                mem_rss = mem_info.rss if mem_info else 0
                
                processes.append({
                    "pid": info["pid"],
                    "name": info["name"],
                    "exe": info.get("exe", ""),
                    "cpu_percent": info.get("cpu_percent", 0) or 0,
                    "memory_percent": info.get("memory_percent", 0) or 0,
                    "memory_rss": mem_rss,
                    "status": info.get("status", ""),
                    "create_time": info.get("create_time", 0),
                    "nice": info.get("nice", 0),
                    "username": self._get_proc_username(proc)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return sorted(processes, key=lambda x: x["cpu_percent"], reverse=True)
    
    def _get_proc_username(self, proc):
        try:
            return proc.username()
        except Exception:
            return ""
    
    def get_top_cpu_processes(self, limit=10):
        procs = self.get_all_processes()
        return procs[:limit]
    
    def get_top_memory_processes(self, limit=10):
        procs = sorted(self.get_all_processes(), key=lambda x: x["memory_rss"], reverse=True)
        return procs[:limit]
    
    def kill_process(self, pid):
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            return True, "进程已终止"
        except psutil.NoSuchProcess:
            return False, "进程不存在"
        except psutil.AccessDenied:
            return False, "权限不足"
        except Exception as e:
            return False, str(e)
    
    def kill_process_tree(self, pid):
        try:
            proc = psutil.Process(pid)
            children = proc.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except Exception:
                    pass
            proc.terminate()
            return True, f"已终止进程及其 {len(children)} 个子进程"
        except Exception as e:
            return False, str(e)
    
    def set_process_priority(self, pid, priority_class):
        try:
            proc = psutil.Process(pid)
            proc.nice(priority_class)
            return True, "优先级已设置"
        except Exception as e:
            return False, str(e)
    
    def set_process_affinity(self, pid, cpu_list):
        try:
            proc = psutil.Process(pid)
            proc.cpu_affinity(cpu_list)
            return True, "CPU 亲和性已设置"
        except Exception as e:
            return False, str(e)
    
    def suspend_process(self, pid):
        try:
            proc = psutil.Process(pid)
            proc.suspend()
            return True, "进程已挂起"
        except Exception as e:
            return False, str(e)
    
    def resume_process(self, pid):
        try:
            proc = psutil.Process(pid)
            proc.resume()
            return True, "进程已恢复"
        except Exception as e:
            return False, str(e)
    
    def get_process_by_name(self, name):
        processes = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if name.lower() in proc.info["name"].lower():
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
    
    def get_system_resource_summary(self):
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count(logical=True)
        cpu_physical = psutil.cpu_count(logical=False)
        
        return {
            "cpu_percent": cpu_percent,
            "cpu_count": cpu_count,
            "cpu_physical": cpu_physical,
            "cpu_freq_current": cpu_freq.current if cpu_freq else 0,
            "cpu_freq_max": cpu_freq.max if cpu_freq else 0,
            "memory_total": mem.total,
            "memory_used": mem.used,
            "memory_available": mem.available,
            "memory_percent": mem.percent,
            "process_count": len(list(psutil.process_iter()))
        }
    
    def find_resource_hogs(self):
        hogs = {
            "cpu": [],
            "memory": [],
            "suspicious": []
        }
        
        procs = self.get_all_processes()
        
        hogs["cpu"] = [p for p in procs if p["cpu_percent"] > 20][:5]
        hogs["memory"] = sorted(
            [p for p in procs if p["memory_percent"] > 10],
            key=lambda x: x["memory_rss"],
            reverse=True
        )[:5]
        
        suspicious_names = ["miner", "coin", "bitcoin", "trojan", "hack"]
        for p in procs:
            name_lower = p["name"].lower() if p["name"] else ""
            for kw in suspicious_names:
                if kw in name_lower:
                    hogs["suspicious"].append(p)
                    break
        
        return hogs
    
    def format_bytes(self, bytes_val):
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024**2:
            return f"{bytes_val/1024:.1f} KB"
        elif bytes_val < 1024**3:
            return f"{bytes_val/(1024**2):.1f} MB"
        else:
            return f"{bytes_val/(1024**3):.2f} GB"
