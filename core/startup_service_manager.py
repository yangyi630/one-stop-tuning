import win32api
import win32con
import win32process
import psutil
import os
import winreg
from dataclasses import dataclass


@dataclass
class StartupItem:
    name: str
    path: str
    command: str
    location: str
    enabled: bool
    impact: str = "未知"


class StartupManager:
    def __init__(self):
        self.reg_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunServices", "HKLM RunServices"),
        ]
    
    def get_startup_items(self):
        items = []
        
        for root_key, sub_key, location in self.reg_paths:
            try:
                key = winreg.OpenKey(root_key, sub_key, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        items.append(StartupItem(
                            name=name,
                            path=value.split('"')[1] if '"' in value else value.split()[0] if value else "",
                            command=value,
                            location=location,
                            enabled=True,
                            impact=self._estimate_impact(value)
                        ))
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except Exception:
                continue
        
        startup_folders = [
            os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup"),
            os.path.join(os.environ.get("PROGRAMDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup"),
        ]
        
        for folder in startup_folders:
            if os.path.exists(folder):
                for file in os.listdir(folder):
                    file_path = os.path.join(folder, file)
                    items.append(StartupItem(
                        name=os.path.splitext(file)[0],
                        path=file_path,
                        command=file_path,
                        location="启动文件夹",
                        enabled=True,
                        impact="低"
                    ))
        
        return items
    
    def _estimate_impact(self, command):
        if not command:
            return "未知"
        
        low_keywords = ["updater", "update", "tray", "notification", "helper"]
        high_keywords = ["antivirus", "security", "firewall", "driver", "service"]
        
        cmd_lower = command.lower()
        for kw in high_keywords:
            if kw in cmd_lower:
                return "高"
        for kw in low_keywords:
            if kw in cmd_lower:
                return "低"
        return "中"
    
    def disable_startup_item(self, item):
        try:
            if "启动文件夹" in item.location:
                if os.path.exists(item.path):
                    disabled_folder = os.path.join(os.path.dirname(item.path), "StartupDisabled")
                    os.makedirs(disabled_folder, exist_ok=True)
                    new_path = os.path.join(disabled_folder, os.path.basename(item.path))
                    os.rename(item.path, new_path)
                    return True, "已禁用"
            else:
                for root_key, sub_key, location in self.reg_paths:
                    if location == item.location:
                        key = winreg.OpenKey(root_key, sub_key, 0, winreg.KEY_SET_VALUE)
                        winreg.DeleteValue(key, item.name)
                        winreg.CloseKey(key)
                        return True, "已禁用"
        except Exception as e:
            return False, str(e)
        return False, "未找到"
    
    def enable_startup_item(self, item):
        try:
            if "启动文件夹" in item.location:
                disabled_folder = os.path.join(os.path.dirname(item.path), "StartupDisabled")
                disabled_path = os.path.join(disabled_folder, os.path.basename(item.path))
                if os.path.exists(disabled_path):
                    os.rename(disabled_path, item.path)
                    return True, "已启用"
            else:
                for root_key, sub_key, location in self.reg_paths:
                    if location == item.location:
                        key = winreg.OpenKey(root_key, sub_key, 0, winreg.KEY_SET_VALUE)
                        winreg.SetValueEx(key, item.name, 0, winreg.REG_SZ, item.command)
                        winreg.CloseKey(key)
                        return True, "已启用"
        except Exception as e:
            return False, str(e)
        return False, "未找到"
    
    def get_boot_time(self):
        try:
            boot_time = psutil.boot_time()
            return boot_time
        except Exception:
            return None
    
    def optimize_startup(self):
        items = self.get_startup_items()
        recommendations = []
        
        for item in items:
            cmd_lower = item.command.lower() if item.command else ""
            
            if any(kw in cmd_lower for kw in ["updater", "updatecheck", "telemetry"]):
                recommendations.append({
                    "item": item,
                    "action": "建议禁用",
                    "reason": "更新检查/遥测程序，不影响核心功能"
                })
            elif "tray" in cmd_lower or "toolbar" in cmd_lower:
                recommendations.append({
                    "item": item,
                    "action": "可禁用",
                    "reason": "工具栏/托盘程序，需要时可手动启动"
                })
        
        return recommendations


class ServiceManager:
    def __init__(self):
        pass
    
    def get_services(self):
        services = []
        try:
            for service in psutil.win_service_iter():
                try:
                    info = service.as_dict()
                    services.append({
                        "name": info.get("name", ""),
                        "display_name": info.get("display_name", ""),
                        "status": info.get("status", ""),
                        "start_type": info.get("start_type", ""),
                        "username": info.get("username", ""),
                        "pid": info.get("pid", None),
                        "description": info.get("description", "")
                    })
                except Exception:
                    continue
        except Exception:
            pass
        return services
    
    def get_running_services(self):
        return [s for s in self.get_services() if s["status"] == "running"]
    
    def get_disableable_services(self):
        safe_to_disable = [
            "Fax",
            "RemoteRegistry",
            "seclogon",
            "TabletInputService",
            "tzautoupdate",
            "wisvc",
        ]
        
        services = self.get_services()
        return [s for s in services if s["name"] in safe_to_disable and s["status"] == "running"]
    
    def stop_service(self, service_name):
        try:
            service = psutil.win_service_get(service_name)
            if service.status() == "running":
                service.stop()
                return True, "服务已停止"
            return True, "服务已停止"
        except Exception as e:
            return False, str(e)
    
    def start_service(self, service_name):
        try:
            service = psutil.win_service_get(service_name)
            if service.status() != "running":
                service.start()
                return True, "服务已启动"
            return True, "服务已运行"
        except Exception as e:
            return False, str(e)
    
    def set_service_start_type(self, service_name, start_type):
        try:
            import win32serviceutil
            win32serviceutil.ChangeServiceConfig(
                service_name,
                startType=start_type
            )
            return True, "启动类型已修改"
        except Exception as e:
            return False, str(e)
    
    def optimize_services(self):
        results = []
        recommendations = [
            ("Fax", "禁用", "传真服务，大多数用户不需要"),
            ("RemoteRegistry", "禁用", "远程注册表服务，有安全风险"),
            ("seclogon", "禁用", "二次登录服务，普通用户不需要"),
            ("tzautoupdate", "禁用", "时区自动更新，可手动设置"),
            ("wisvc", "禁用", "Windows 预览体验服务"),
        ]
        
        services = self.get_services()
        service_names = {s["name"]: s for s in services}
        
        for svc_name, action, reason in recommendations:
            if svc_name in service_names:
                results.append({
                    "name": svc_name,
                    "display_name": service_names[svc_name]["display_name"],
                    "current_status": service_names[svc_name]["status"],
                    "recommended_action": action,
                    "reason": reason
                })
        
        return results
