import sys
import os
import datetime
import portalocker
import logging
import tempfile
import threading
import multiprocessing
from multiprocessing import Queue, Pipe,Value

multiprocessing.freeze_support()  # 防止在 Windows 上无限递归

current_date = datetime.date.today().strftime("%Y%m%d")
run_path = os.path.dirname(os.path.abspath(__file__))

httpKeyPath = 'https://app.dianplus.cn/certs/localhost-tls.key'
httpCertPath = 'https://app.dianplus.cn/certs/localhost-tls.crt'

# 创建队列用于进程间通信
print_queue = Queue()
direct_print_queue = Queue()
preview_queue = Queue()
# 指令通道
parent_conn, child_conn = Pipe()
pDoing = Value('i',0)

# 打印任务
printTasks = {}
# 创建一个锁对象
printTasks_lock = threading.Lock()


def addPrintTask(task_id, task):
    with printTasks_lock:
        printTasks[task_id] = task


def getPrintTask(task_id):
    with printTasks_lock:
        return printTasks[task_id]


def getAllPrintTasks():
    with printTasks_lock:
        # 返回一个列表，只要值
        return list(printTasks.values())


def removePrintTask(task_id):
    with printTasks_lock:
        if task_id in printTasks:
            del printTasks[task_id]


# 获取临时目录路径
temp_dir = tempfile.gettempdir()
# 构建锁定文件的完整路径
lock_file = os.path.join(temp_dir, "dianplus.app.lock")

logging.basicConfig(
    # 设置日志文件路径,文件名加上日期
    filename=temp_dir + '/dianplus.app.'+current_date+'.log',  # 日志文件路径
    level=logging.DEBUG,  # 日志级别
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
    datefmt='%Y-%m-%d %H:%M:%S'  # 日期格式
)

def prevent_multiple_instances(lock_file):
    try:
        # 打开文件并尝试获取锁
        file = open(lock_file, 'w')
        portalocker.lock(file, portalocker.LOCK_EX | portalocker.LOCK_NB)
        logging.info("Lock acquired, starting the application...")
        return file
    except (IOError, portalocker.AlreadyLocked) as e:
        logging.error(f"Failed to acquire lock: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error while acquiring lock: {e}")
        sys.exit(1)


def release_lock(lock_file):
    try:
        # 释放锁并关闭文件
        portalocker.unlock(lock_file)
        lock_file.close()
        logging.info("Lock released.")
    except Exception as e:
        logging.error(f"Error releasing lock: {e}")


def release_all():
    for queue in [preview_queue, print_queue, direct_print_queue]:
        try:
            queue.close()
            queue.join_thread()
        except Exception as e:
            logging.error(f"Error closing queue: {e}")
    try:
        parent_conn.close()
    except Exception as e:
        logging.error(f"Error closing parent connection: {e}")
    try:
        child_conn.close()
    except Exception as e:
        logging.error(f"Error closing child connection: {e}")
    try:
        # 释放锁
        release_lock(lock_file)
        # 删除锁文件
        os.remove(lock_file)
    except Exception as e:
        logging.error(f"Error closing child connection: {e}")