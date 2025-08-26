import os
import tempfile
import requests
import logging
from globals import httpKeyPath, httpCertPath,temp_dir

# 缓存
certFileCaches = {}
# 下载文件到临时文件
def downloadFileToTempfile(url:str):
    try:
        file_name = url.split('/')[-1]
        # 替换可能的非法字符
        file_name = ''.join(c if c.isalnum() or c in '._-' else '_' for c in file_name)
        file_path = os.path.join(temp_dir, file_name)

        # 发送 HTTP GET 请求下载文件
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()  # 如果响应状态码不是200，抛出异常
        with open(file_path, 'wb') as file:
            # 将文件内容写入临时文件
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
            # 返回临时文件的路径
            return file.name
    except Exception as e:
        logging.error(f"Failed to download file from {url}: {e}")
        raise

# 读取文件到字符串
def downloadFileToString(url):
    try:
        # 发送 HTTP GET 请求下载文件
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()  # 如果响应状态码不是200，抛出异常
        # 将文件内容读取为字符串
        return response.text
    except Exception as e:
        logging.error(f"Failed to download file from {url}: {e}")
        raise

# 将文本内容写到文件，覆盖原有的内容
def writeStringToFile(file_path, content):
    try:
        with open(file_path, 'w') as file:
            file.write(content)
    except IOError as e:
        logging.error(f"Failed to write to file {file_path}: {e}")
        raise

# 下载文件并将文件存储到临时目录
def readTempFileToString(url):
    try:
        path = downloadFileToTempfile(url)
        # 打开临时文件并读取内容为字符串
        with open(path, 'r') as file:
            fileContent = file.read()
        if certFileCaches.get(url) is None:
            certFileCaches[url] = fileContent
        return path
    except Exception as e:
        logging.error(f"Failed to read temp file from {url}: {e}")
        raise

key_temp_path = readTempFileToString(httpKeyPath)
cert_temp_path = readTempFileToString(httpCertPath)

# 判定文件是否更新了
def isCertFileChanged():
    try:
        keyContent = downloadFileToString(httpKeyPath)
        certContent = downloadFileToString(httpCertPath)
        # 检测文件是否有变化
        if (certFileCaches.get(httpKeyPath) != keyContent) or (certFileCaches.get(httpCertPath) != certContent):
            writeStringToFile(key_temp_path, keyContent)
            writeStringToFile(cert_temp_path, certContent)
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error checking certificate file changes: {e}")
        return False