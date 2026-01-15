
import os
import sys
import subprocess
import time
import signal
import threading

def run_terminal_server(python_exe, base_dir):
    """在单独线程中启动终端WebSocket服务器"""
    terminal_script = os.path.join(base_dir, "core", "script", "terminal_server.py")
    subprocess.Popen([python_exe, terminal_script])

def run():
    # 1. Start Backend
    print("Starting backend...")
    base_dir = os.path.dirname(__file__)
    is_windows = sys.platform.startswith('win')

    if is_windows:
        python_exe = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
    else:
        python_exe = os.path.join(base_dir, ".venv", "bin", "python")

    if not os.path.exists(python_exe):
        python_exe = sys.executable

    backend_script = os.path.join(base_dir, "backend", "server.py")
    backend_proc = subprocess.Popen([python_exe, backend_script])

    # 1.5. Start Terminal WebSocket Server
    print("Starting terminal server...")
    terminal_script = os.path.join(base_dir, "core", "script", "terminal_server.py")
    terminal_proc = subprocess.Popen([python_exe, terminal_script])

    # 2. Wait for servers to start
    time.sleep(2)

    # 3. Start Frontend (Electron)
    print("Starting frontend...")
    try:
        # If packaged, we would run the executable in dist/
        # For now, we use npm to start (while we wait for packaging)
        npm_cmd = "npm.cmd" if is_windows else "npm"
        frontend_proc = subprocess.Popen([npm_cmd, "run", "start"], cwd=base_dir)
        
        # Wait for either to close
        while True:
            if backend_proc.poll() is not None:
                break
            if frontend_proc.poll() is not None:
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Cleanup
        backend_proc.terminate()
        if 'terminal_proc' in locals():
            terminal_proc.terminate()
        if 'frontend_proc' in locals():
            frontend_proc.terminate()

if __name__ == "__main__":
    run()
