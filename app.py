import sys
import os
import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTranslator, QLocale
from globals import prevent_multiple_instances,release_lock,lock_file
from src.ui.MainWindow import MainWindow
from src.webs.manager import startWebServer,destroyWebServer,kill_old_pids,write_pid,remove_pid

if __name__ == '__main__':
    # 尝试获取锁
    file = prevent_multiple_instances(lock_file)
    # 杀死老进程
    kill_old_pids()
    # 删除pid文件
    remove_pid()
    # 写入pid文件
    write_pid()
    try:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(os.path.dirname(os.path.abspath(__file__))+'/static/logo.png'))
        app.setQuitOnLastWindowClosed(False)
        locale = QLocale(QLocale.Language.Chinese, QLocale.Country.China)
        QLocale.setDefault(locale)
        
        # 设置当前使用的语言
        translator = QTranslator()
        translator.load(os.path.dirname(os.path.abspath(__file__))+'/static/qtbase_zh_CN.qm')  # 假设翻译文件名为 app_zh_CN.qm
        translator.load(os.path.dirname(os.path.abspath(__file__))+'/static/qt_zh_CN.qm')  # 假设翻译文件名为 app_zh_CN.qm
        app.installTranslator(translator)

        # 启动PyQt6主应用
        ex = MainWindow()
        # 启动Web服务器
        startWebServer()
        
        sys.exit(app.exec())
    except Exception as e:
        sys.exit(1)
    finally:
        try:
            # 停止Web服务器
            destroyWebServer()
            # 释放锁
            release_lock(file)
            # 删除锁文件
            os.remove(lock_file)
        except Exception:
            pass
    