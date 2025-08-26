import platform
import sys
import os
import logging

#判定程序是windows系统
if platform.system() == "Windows":
    import winreg
# 判断是否是mac系统
if platform.system() == "Darwin":
    import plistlib
    import subprocess
# 判断是否已经是开机自启动了
def get_startup():
    #判定程序是windows系统
    if platform.system() == "Windows":
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_READ)
            value = winreg.QueryValueEx(key, "DplusAsst")[0]
            return value == sys.executable
        except Exception as e:
            logging.error(e)
            return False
    # 判断是否是mac系统
    elif platform.system() == "Darwin":
        try:
            # 定义 LaunchAgent 的路径
            agent_path = os.path.expanduser('~/Library/LaunchAgents/cn.dianplus.DplusAsst.plist')
            
            # 检查文件是否存在
            if os.path.exists(agent_path):
                # 读取文件内容
                with open(agent_path, 'rb') as f:
                    agent_dict = plistlib.load(f)
                
                # 验证内容是否正确
                if agent_dict.get('Label') == 'cn.dianplus.DplusAsst' and \
                agent_dict.get('ProgramArguments') == ['/Applications/DplusAsst.app/Contents/MacOS/DplusAsst'] and \
                agent_dict.get('RunAtLoad') is True:
                    return True
            return False
        except Exception as e:
            logging.error(e)
            return False
    else:
        return False
def set_startup(enable):
    try:
        # 判定程序是windows系统
        if platform.system() == "Windows":
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_SET_VALUE)
            if enable:
                winreg.SetValueEx(key, "DplusAsst", 0, winreg.REG_SZ, sys.executable)
            else:
                winreg.DeleteValue(key, "DplusAsst")
            winreg.CloseKey(key)
        # 判断是否是mac系统
        elif platform.system() == "Darwin":
            app_path = '/Applications/DplusAsst.app/Contents/MacOS/DplusAsst'
            if enable:
                # 定义 LaunchAgent 的路径
                agent_path = os.path.expanduser('~/Library/LaunchAgents/cn.dianplus.DplusAsst.plist')
                # 定义 LaunchAgent 的内容
                agent_dict = {
                    'Label': 'cn.dianplus.DplusAsst',
                    'ProgramArguments': [app_path],
                    'RunAtLoad': True
                }
                
                # 创建或更新 LaunchAgent 文件
                with open(agent_path, 'wb') as f:
                    plistlib.dump(agent_dict, f)
                
                # 加载 LaunchAgent
                subprocess.run(['launchctl', 'load', agent_path])
                logging.info(f"LaunchAgent created and loaded: {agent_path}")
            else:
                # 定义 LaunchAgent 的路径
                agent_path = os.path.expanduser('~/Library/LaunchAgents/cn.dianplus.DplusAsst.plist')
                
                # 卸载 LaunchAgent
                subprocess.run(['launchctl', 'unload', agent_path])
                
                # 删除 LaunchAgent 文件
                if os.path.exists(agent_path):
                    os.remove(agent_path)
                logging.info(f"LaunchAgent removed: {agent_path}")
    except Exception as e:
        logging.error(e)
        pass

def onStartupCheckBoxChanged(checked):
    try:
        if checked != 0:
            set_startup(True)
        else:
            set_startup(False)
    except Exception as e:
        logging.error(e)
    
