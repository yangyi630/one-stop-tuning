import subprocess
import sys
import os
import time

REQUIRED_MODULES = {
    "PyQt6": "PyQt6",
    "psutil": "psutil",
    "win32api": "pywin32",
    "wmi": "wmi",
    "screeninfo": "screeninfo",
}


def check_module(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def get_missing_modules():
    missing = []
    for import_name, pip_name in REQUIRED_MODULES.items():
        if not check_module(import_name):
            missing.append(pip_name)
    return missing


def install_requirements():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    req_file = os.path.join(script_dir, "requirements.txt")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_file],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        return result.returncode == 0
    except Exception:
        return False


def launch_main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_file = os.path.join(script_dir, "main.py")
    
    if not os.path.exists(main_file):
        print("ERROR: main.py not found")
        time.sleep(3)
        return False
    
    try:
        if sys.platform == "win32":
            subprocess.Popen(
                [sys.executable, main_file],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=script_dir
            )
        else:
            subprocess.Popen(
                [sys.executable, main_file],
                cwd=script_dir
            )
        return True
    except Exception as e:
        print("ERROR: Failed to launch main.py:", e)
        time.sleep(3)
        return False


def main():
    print("=" * 50)
    print("  System Performance Tuner - Launcher")
    print("=" * 50)
    print()
    
    print("[1/3] Checking dependencies...")
    missing = get_missing_modules()
    
    if missing:
        print("  Missing:", ", ".join(missing))
        print()
        print("[2/3] Installing dependencies (this may take a few minutes)...")
        success = install_requirements()
        
        if not success:
            print("  WARNING: Some packages may have failed to install.")
            print("  Retrying with individual packages...")
            for pkg in missing:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", pkg],
                        capture_output=True
                    )
                except Exception:
                    pass
        
        missing_after = get_missing_modules()
        if missing_after:
            print("  ERROR: Failed to install:", ", ".join(missing_after))
            print("  Please run: pip install -r requirements.txt")
            time.sleep(5)
            sys.exit(1)
        
        print("  Dependencies installed successfully.")
    else:
        print("  All dependencies are ready.")
    
    print()
    print("[3/3] Starting application...")
    print()
    
    success = launch_main()
    
    if success:
        print("Application started successfully.")
        print("This window will close automatically.")
        time.sleep(2)
    else:
        print("Failed to start application.")
        time.sleep(5)
        sys.exit(1)


if __name__ == "__main__":
    main()
