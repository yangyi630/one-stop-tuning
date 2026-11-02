import os
import time
import subprocess
import win32api
import win32con
import win32gui
import win32process
import win32event
import psutil
import pythoncom
import ctypes
from ctypes import wintypes
from win32com.client import Dispatch


SHELLEXECUTE_MASK_RETURNIMMEDIATELY = 0x00000000
SEE_MASK_NOCLOSEPROCESS = 0x00000040


class SHELLEXECUTEINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("fMask", wintypes.ULONG),
        ("hwnd", wintypes.HWND),
        ("lpVerb", wintypes.LPCWSTR),
        ("lpFile", wintypes.LPCWSTR),
        ("lpParameters", wintypes.LPCWSTR),
        ("lpDirectory", wintypes.LPCWSTR),
        ("nShow", wintypes.INT),
        ("hInstApp", wintypes.HINSTANCE),
        ("lpIDList", ctypes.c_void_p),
        ("lpClass", wintypes.LPCWSTR),
        ("hkeyClass", wintypes.HKEY),
        ("dwHotKey", wintypes.DWORD),
        ("hIcon", wintypes.HANDLE),
        ("hProcess", wintypes.HANDLE),
    ]


class GameLauncher:
    def __init__(self):
        self.game_process = None
        self.game_path = None
        self.game_pid = None
        self.is_running = False
    
    def parse_shortcut(self, shortcut_path):
        try:
            pythoncom.CoInitialize()
            shell = Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            target_path = shortcut.Targetpath
            work_dir = shortcut.WorkingDirectory
            arguments = shortcut.Arguments
            pythoncom.CoUninitialize()
            return {
                "target": target_path,
                "work_dir": work_dir,
                "arguments": arguments,
                "icon_location": shortcut.IconLocation
            }
        except Exception as e:
            print(f"Failed to parse shortcut: {e}")
            return None
    
    def find_game_executable(self, game_name):
        common_paths = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            os.path.expandvars(r"%LOCALAPPDATA%"),
            os.path.expandvars(r"%APPDATA%"),
            "D:\\",
            "E:\\",
            "F:\\"
        ]
        
        for base_path in common_paths:
            if not os.path.exists(base_path):
                continue
            try:
                for root, dirs, files in os.walk(base_path):
                    for file in files:
                        if game_name.lower() in file.lower() and file.endswith(".exe"):
                            return os.path.join(root, file)
            except Exception:
                continue
        return None
    
    def launch_game(self, exe_path, work_dir=None, arguments=""):
        if not os.path.exists(exe_path):
            return False, f"游戏文件不存在: {exe_path}"
        
        self.game_path = exe_path
        
        success = False
        message = ""
        
        success, message, pid = self._launch_normal(exe_path, work_dir, arguments)
        
        if not success and ("740" in message or "需要提升" in message or "elevation" in message.lower()):
            print("Admin privileges required, trying admin launch...")
            success, message, pid = self._launch_as_admin(exe_path, work_dir, arguments)
        
        if success:
            self.game_pid = pid
            self.is_running = True
            
            time.sleep(2)
            
            if self.game_pid is None:
                found_pid = self._find_process_by_exe(exe_path)
                if found_pid:
                    self.game_pid = found_pid
            
            return True, f"游戏已启动，PID: {self.game_pid}"
        else:
            return False, f"启动游戏失败: {message}"
    
    def _launch_normal(self, exe_path, work_dir=None, arguments=""):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            cmd = [exe_path]
            if arguments:
                cmd.extend(arguments.split())
            
            self.game_process = subprocess.Popen(
                cmd,
                cwd=work_dir or os.path.dirname(exe_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            return True, "", self.game_process.pid
        except Exception as e:
            return False, str(e), None
    
    def _launch_as_admin(self, exe_path, work_dir=None, arguments=""):
        try:
            sei = SHELLEXECUTEINFO()
            sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
            sei.fMask = SEE_MASK_NOCLOSEPROCESS
            sei.hwnd = 0
            sei.lpVerb = "runas"
            sei.lpFile = exe_path
            sei.lpParameters = arguments if arguments else ""
            sei.lpDirectory = work_dir if work_dir else os.path.dirname(exe_path)
            sei.nShow = win32con.SW_SHOWNORMAL
            
            result = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
            if not result:
                error = ctypes.windll.kernel32.GetLastError()
                return False, f"ShellExecuteEx 失败，错误码: {error}", None
            
            if sei.hProcess:
                pid = win32process.GetProcessId(sei.hProcess)
                win32api.CloseHandle(sei.hProcess)
                
                try:
                    self.game_process = psutil.Process(pid)
                except Exception:
                    self.game_process = None
                
                return True, "", pid
            else:
                return True, "已以管理员身份启动（需手动确认UAC提示）", None
        except Exception as e:
            return False, str(e), None
    
    def _find_process_by_exe(self, exe_path):
        exe_name = os.path.basename(exe_path).lower()
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() == exe_name:
                    return proc.info["pid"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def launch_from_shortcut(self, shortcut_path):
        info = self.parse_shortcut(shortcut_path)
        if info:
            return self.launch_game(
                info["target"],
                info["work_dir"],
                info["arguments"]
            )
        return False, "无法解析快捷方式"
    
    def wait_for_game_window(self, window_title_keywords=None, timeout=60):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.game_process and self.game_process.poll() is not None:
                return None
            
            hwnd = self._find_game_window(window_title_keywords)
            if hwnd:
                return hwnd
            time.sleep(1)
        return None
    
    def _find_game_window(self, keywords=None):
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32gui.GetWindowThreadProcessId(hwnd)
                if pid == self.game_pid:
                    windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(callback, windows)
        
        if windows:
            return windows[0]
        
        if keywords:
            def callback2(hwnd, result):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    for kw in keywords:
                        if kw.lower() in title.lower():
                            result.append(hwnd)
                            break
                return True
            
            result = []
            win32gui.EnumWindows(callback2, result)
            if result:
                return result[0]
        
        return None
    
    def is_game_running(self):
        if self.game_process:
            try:
                return self.game_process.is_running()
            except Exception:
                pass
        
        if self.game_pid:
            try:
                return psutil.pid_exists(self.game_pid)
            except Exception:
                pass
        
        return False
    
    def terminate_game(self):
        try:
            if self.game_process:
                try:
                    if self.game_process.is_running():
                        self.game_process.terminate()
                        self.game_process.wait(timeout=5)
                except Exception:
                    pass
            elif self.game_pid:
                try:
                    proc = psutil.Process(self.game_pid)
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    pass
            
            self.is_running = False
            return True
        except Exception as e:
            print(f"Failed to terminate game: {e}")
            return False
    
    def get_game_pid(self):
        return self.game_pid
    
    def get_all_game_processes(self, game_name=None):
        processes = []
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                if game_name:
                    if game_name.lower() in proc.info["name"].lower():
                        processes.append(proc)
                else:
                    processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
