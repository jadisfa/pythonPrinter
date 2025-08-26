import logging
import os
import signal
from multiprocessing import Process
from PyQt6.QtCore import QTimer,QObject
from src.webs.certMonitor import isCertFileChanged, key_temp_path, cert_temp_path
from src.webs.serverApp import runHttpServer, runHttpsServer
from globals import preview_queue, print_queue, direct_print_queue, child_conn,pDoing,run_path, temp_dir

# 定义 HTTP 和 HTTPS 服务的进程对象
httpProcess: Process = None
httpsProcess: Process = None

# 定义 PID 文件路径
PID_FILE = temp_dir + '/dplus-app.pid'

# 移除 PID 文件
def remove_pid():
    try:
        os.remove(PID_FILE) if os.path.exists(PID_FILE) else None
    except Exception:
        return None

# 写入当前进程的 PID 到 PID 文件
def write_pid():
    try:
        with open(PID_FILE, 'a') as f:
            f.write(f"{os.getpid()}\n")
    except Exception:
        pass
# 读取 PID 文件中的所有 PID
def read_pids():
    pids = []
    try:
        with open(PID_FILE, 'r') as file:
            for line in file:
                pid = line.strip()
                if pid.isdigit():
                    pids.append(int(pid))
    except Exception as e:
        logging.error(f"Error reading PID file: {e}")
    return pids

# 终止旧的进程
def kill_old_pids():
    old_pids = read_pids()
    for old_pid in old_pids:
        if old_pid:
            try:
                os.kill(old_pid, signal.SIGTERM)
                print(f"Killed old instance with PID {old_pid}")
            except Exception:
                pass

# 判断 WEB 服务是否在运行
def isWebServerRunning():
    return (httpProcess is not None and httpProcess.is_alive()) or (httpsProcess is not None and httpsProcess.is_alive())

# 启动 WEB 服务
def startWebServer():
    global httpProcess, httpsProcess
    try:
        # 启动 HTTP 服务
        httpProcess = Process(target=runHttpServer, args=(run_path, temp_dir, preview_queue, print_queue, direct_print_queue, child_conn,pDoing,))
        httpProcess.daemon = True  # 设置为守护进程
        httpProcess.start()
    except Exception as e:
        logging.error(f"Failed to start HTTP server: {e}")

    try:
        # 启动 HTTPS 服务
        httpsProcess = Process(target=runHttpsServer, args=(run_path, temp_dir, preview_queue, print_queue, direct_print_queue, child_conn,pDoing, key_temp_path, cert_temp_path,))
        httpsProcess.daemon = True  # 设置为守护进程
        httpsProcess.start()
    except Exception as e:
        logging.error(f"Failed to start HTTPS server: {e}")

# 停止 WEB 服务
def stopWebServer():
    global httpProcess, httpsProcess
    try:
        if httpProcess is not None and httpProcess.is_alive():
            httpProcess.kill()  # 强制终止子进程
    except Exception as e:
        logging.error(f"Failed to stop HTTP server: {e}")

    try:
        if httpsProcess is not None and httpsProcess.is_alive():
            httpsProcess.kill()  # 强制终止子进程
    except Exception as e:
        logging.error(f"Failed to stop HTTPS server: {e}")

# 监听证书更新
def checkWatchCrtFile(self):
    global httpsProcess
    delayTimer:QTimer=self.delay_timer
    if isCertFileChanged():
        try:
            # 重启 HTTPS 服务
            if httpsProcess is not None and httpsProcess.is_alive():
                httpsProcess.kill()  # 强制终止子进程
                httpsProcess = None
        except Exception as e:
            logging.error(f"Failed to stop HTTPS server during certificate update: {e}")

        try:
            def restartActions():
                global httpsProcess
                try:
                    # 启动 HTTPS 服务
                    httpsProcess = Process(target=runHttpsServer, args=(run_path, temp_dir, preview_queue, print_queue, direct_print_queue, child_conn,pDoing, key_temp_path, cert_temp_path,))
                    httpsProcess.daemon = True  # 设置为守护进程
                    httpsProcess.start()
                except OSError as e:
                    logging.error(f"Failed to restart HTTPS server: {e}")
            try:
                delayTimer.timeout.disconnect()  
            except Exception as e:
                logging.error(f"Failed to disconnect previous timer: {e}")

            delayTimer.timeout.connect(restartActions)  # 连接槽函数
            delayTimer.start(5000)  # 启动定时器，延时 5000 毫秒（5 秒）
        except Exception as e:
            logging.error(f"Failed to set up timer for certificate update: {e}")

# 销毁 WEB 服务
def destroyWebServer():
    global httpProcess, httpsProcess
    try:
        if httpProcess is not None and httpProcess.is_alive():
            httpProcess.kill()  # 强制终止子进程
    except ProcessLookupError as e:
        logging.error(f"Failed to destroy HTTP server: {e}")

    try:
        if httpsProcess is not None and httpsProcess.is_alive():
            httpsProcess.kill()  # 强制终止子进程
    except ProcessLookupError as e:
        logging.error(f"Failed to destroy HTTPS server: {e}")

    try:
        os.remove(key_temp_path)
        os.remove(cert_temp_path)
    except Exception as e:
        logging.error(f"Failed to destroy timer: {e}")