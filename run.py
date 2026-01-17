import os
import sys
import subprocess
import time
import signal
import threading
import socket
import psutil

def kill_process_on_port(port):
    """如果端口被占用，尝试杀掉占用端口的进程"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    print(f"Port {port} is in use by {proc.info['name']} (PID: {proc.info['pid']}). Killing...")
                    proc.kill()
                    return
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def run():
    # 0. Pre-start cleanup
    print("Checking ports...")
    kill_process_on_port(3335)  # Backend
    kill_process_on_port(3336)  # Terminal
    
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
        npm_cmd = "npm.cmd" if is_windows else "npm"
        frontend_proc = subprocess.Popen([npm_cmd, "run", "start"], cwd=base_dir)
        
        # Monitor processes
        while True:
            if backend_proc.poll() is not None:
                print("Backend exited unexpectedly.")
                break
            if terminal_proc.poll() is not None:
                print("Terminal server exited unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                # Frontend closed, normal exit
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Cleanup
        print("Cleaning up processes...")
        
        if 'backend_proc' in locals() and backend_proc.poll() is None:
            backend_proc.terminate()
            
        if 'terminal_proc' in locals() and terminal_proc.poll() is None:
            terminal_proc.terminate()
            
        if 'frontend_proc' in locals() and frontend_proc.poll() is None:
            frontend_proc.terminate()
            
        # Ensure deep cleanup if they don't die
        time.sleep(1)
        kill_process_on_port(3335)
        kill_process_on_port(3336)

if __name__ == "__main__":
    run()
