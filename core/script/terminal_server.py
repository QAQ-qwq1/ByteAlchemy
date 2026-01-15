"""
Terminal Server - WebSocket PTY Terminal
提供完整的交互式终端功能 (跨平台: Linux/macOS/Windows)
"""

import asyncio
import os
import sys
import signal
import struct
import threading
import websockets
from websockets.exceptions import ConnectionClosed

# 平台检测
IS_WINDOWS = sys.platform == 'win32'

if IS_WINDOWS:
    # Windows 实现 - 使用 PtyProcess 高级API
    try:
        from winpty import PtyProcess
        HAS_WINPTY = True
    except ImportError:
        HAS_WINPTY = False
        print("[Warning] winpty not available, terminal functionality disabled on Windows")
else:
    # Unix 实现
    import pty
    import fcntl
    import termios
    import select
    HAS_WINPTY = False  # Not needed on Unix


class TerminalSessionUnix:
    """Unix 终端会话 (Linux/macOS)"""
    
    def __init__(self, shell: str = "/bin/bash"):
        self.shell = shell
        self.fd = None
        self.pid = None
        self.running = False
    
    def start(self, rows: int = 24, cols: int = 80):
        """启动PTY会话"""
        self.stop()
        
        self.pid, self.fd = pty.fork()
        
        if self.pid == 0:
            # 子进程 - 执行shell
            os.environ['TERM'] = 'xterm-256color'
            os.environ['COLORTERM'] = 'truecolor'
            os.execvp(self.shell, [self.shell])
        else:
            # 父进程
            self.running = True
            self.resize(rows, cols)
    
    def resize(self, rows: int, cols: int):
        """调整终端大小"""
        if self.fd:
            try:
                winsize = struct.pack('HHHH', rows, cols, 0, 0)
                fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
            except Exception:
                pass
    
    def write(self, data: str):
        """向终端写入数据"""
        if self.fd and self.running:
            try:
                os.write(self.fd, data.encode('utf-8'))
            except OSError:
                self.running = False
    
    def read(self, timeout: float = 0.1) -> str:
        """读取终端输出"""
        if not self.fd or not self.running:
            return ""
        
        try:
            readable, _, _ = select.select([self.fd], [], [], timeout)
            if readable:
                data = os.read(self.fd, 4096)
                if not data:
                    self.running = False
                    return ""
                return data.decode('utf-8', errors='replace')
        except OSError:
            self.running = False
        return ""
    
    def stop(self):
        """停止终端会话"""
        self.running = False
        if self.pid and self.pid > 0:
            try:
                os.kill(self.pid, signal.SIGTERM)
                os.waitpid(self.pid, os.WNOHANG)
            except (ProcessLookupError, ChildProcessError, OSError):
                pass
            self.pid = None
        if self.fd:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None


class TerminalSessionWindows:
    """Windows 终端会话 - 使用 PtyProcess 高级 API，带持续读取线程"""
    
    def __init__(self, shell: str = None):
        if shell is None:
            # 使用 cmd.exe 以获得更好的兼容性
            self.shell = 'cmd.exe'
        else:
            self.shell = shell
        
        self.process = None
        self.running = False
        self._output_buffer = []
        self._buffer_lock = threading.Lock()
        self._read_thread = None
    
    def start(self, rows: int = 24, cols: int = 80):
        """启动终端会话"""
        self.stop()
        
        if not HAS_WINPTY:
            print("[Error] winpty not available on Windows")
            return
        
        try:
            # 使用 PtyProcess.spawn 创建进程
            self.process = PtyProcess.spawn(self.shell, dimensions=(rows, cols))
            self.running = True
            print(f"[Terminal] Started {self.shell} with PtyProcess")
            
            # 启动后台读取线程
            self._read_thread = threading.Thread(target=self._background_reader, daemon=True)
            self._read_thread.start()
            
        except Exception as e:
            print(f"[Error] Failed to start PtyProcess: {e}")
            import traceback
            traceback.print_exc()
            self.running = False
    
    def _background_reader(self):
        """后台线程持续读取终端输出"""
        import time
        while self.running and self.process:
            try:
                if not self.process.isalive():
                    self.running = False
                    break
                
                # 读取可用数据
                try:
                    data = self.process.read(4096)
                    if data:
                        with self._buffer_lock:
                            self._output_buffer.append(data)
                except EOFError:
                    self.running = False
                    break
                except Exception:
                    pass
                
                time.sleep(0.01)  # 小延迟避免CPU占用过高
                
            except Exception as e:
                print(f"[Reader Error] {e}")
                break
    
    def resize(self, rows: int, cols: int):
        """调整终端大小"""
        if self.process and self.running:
            try:
                self.process.setwinsize(rows, cols)
            except Exception:
                pass
    
    def write(self, data: str):
        """向终端写入数据"""
        if self.process and self.running:
            try:
                self.process.write(data)
            except Exception as e:
                print(f"[Error] Write failed: {e}")
    
    def read(self, timeout: float = 0.1) -> str:
        """读取终端输出 (从缓冲区获取)"""
        if not self.running:
            return ""
        
        # 从缓冲区获取所有数据
        with self._buffer_lock:
            if self._output_buffer:
                result = ''.join(self._output_buffer)
                self._output_buffer.clear()
                return result
        return ""
    
    def stop(self):
        """停止终端会话"""
        self.running = False
        
        if self.process:
            try:
                if self.process.isalive():
                    self.process.terminate(force=True)
            except Exception:
                pass
            self.process = None
        
        # 清空缓冲区
        with self._buffer_lock:
            self._output_buffer.clear()


# 跨平台终端会话类
def create_terminal_session(shell: str = None):
    """创建适合当前平台的终端会话"""
    if IS_WINDOWS:
        return TerminalSessionWindows(shell)
    else:
        return TerminalSessionUnix(shell or "/bin/bash")


class TerminalServer:
    """WebSocket终端服务器 - 支持多连接"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 3336):
        self.host = host
        self.port = port
        self.sessions = {}
    
    async def handle_client(self, websocket):
        """处理WebSocket连接"""
        session = create_terminal_session()
        session_id = id(websocket)
        self.sessions[session_id] = session
        read_task = None
        
        try:
            # 等待初始化消息 (包含终端尺寸)
            try:
                init_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            except asyncio.TimeoutError:
                init_msg = ""
            
            if init_msg.startswith("INIT:"):
                parts = init_msg.split(":")
                rows = int(parts[1]) if len(parts) > 1 else 24
                cols = int(parts[2]) if len(parts) > 2 else 80
                session.start(rows, cols)
            else:
                session.start()
            
            # 检查会话是否成功启动
            if not session.running:
                await websocket.send("\033[1;31m[Error] Failed to start terminal session\033[0m\r\n")
                return
            
            # 发送欢迎消息
            platform_info = "Windows" if IS_WINDOWS else "Unix"
            await websocket.send(f"\033[1;32m[Terminal Ready - {platform_info}]\033[0m\r\n")
            
            # 启动读取任务
            read_task = asyncio.create_task(self._read_loop(websocket, session))
            
            # 处理输入
            async for message in websocket:
                if not session.running:
                    break
                if message.startswith("RESIZE:"):
                    # 处理resize消息
                    parts = message.split(":")
                    rows = int(parts[1]) if len(parts) > 1 else 24
                    cols = int(parts[2]) if len(parts) > 2 else 80
                    session.resize(rows, cols)
                elif message.startswith("CMD:"):
                    # 执行脚本命令 (快捷方式)
                    cmd = message[4:]
                    session.write(cmd + "\r\n")
                else:
                    # 普通输入
                    session.write(message)
            
        except ConnectionClosed:
            pass
        except Exception as e:
            print(f"Session error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 清理
            if read_task:
                read_task.cancel()
                try:
                    await read_task
                except asyncio.CancelledError:
                    pass
            session.stop()
            if session_id in self.sessions:
                del self.sessions[session_id]
    
    async def _read_loop(self, websocket, session):
        """持续读取终端输出并发送"""
        try:
            while session.running:
                output = await asyncio.get_event_loop().run_in_executor(
                    None, session.read, 0.05
                )
                if output:
                    try:
                        await websocket.send(output)
                    except ConnectionClosed:
                        break
                await asyncio.sleep(0.02)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Read loop error: {e}")
    
    async def start(self):
        """启动WebSocket服务器"""
        print(f"Terminal WebSocket server starting on ws://{self.host}:{self.port}")
        print(f"Platform: {'Windows' if IS_WINDOWS else 'Unix'}")
        if IS_WINDOWS:
            print(f"winpty (PtyProcess) available: {HAS_WINPTY}")
        async with websockets.serve(
            self.handle_client, 
            self.host, 
            self.port,
            ping_interval=20,
            ping_timeout=60
        ):
            await asyncio.Future()  # 永远运行


def run_terminal_server():
    """运行终端服务器"""
    server = TerminalServer()
    asyncio.run(server.start())


if __name__ == "__main__":
    run_terminal_server()
