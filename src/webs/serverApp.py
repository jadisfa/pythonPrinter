import os
import logging
from flask import Flask, request, jsonify, render_template,send_file
from flask_cors import CORS
import uuid
import json
import time
from urllib.parse import unquote
import gzip
import base64

# Flask Web服务器定义
flaskApp = Flask(__name__)

CORS(flaskApp)

@flaskApp.route('/')
def index():
    try:
        return render_template('index.html', contextPath="")
    except Exception as e:
        logging.error(f"Error rendering index.html: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
@flaskApp.route('/apidocs')
def apidocs():
    try:
         # 获取模板目录路径
        template_dir = flaskApp.template_folder
        # 构建Markdown文件完整路径
        md_path = os.path.join(template_dir, 'API.md')
        # 直接发送Markdown文件内容
        return send_file(md_path, mimetype='text/markdown')
    except Exception as e:
        logging.error(f"Error rendering API.md: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
@flaskApp.route('/api-html')
def apiHtml():
    try:
        return render_template('api.html', contextPath="")
    except Exception as e:
        logging.error(f"Error rendering api.html: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
@flaskApp.route('/ticket-scripts')
def pageTicketScripts():
    try:
        return render_template('ticket-scripts.html', contextPath="")
    except Exception as e:
        logging.error(f"Error rendering ticket-scripts.html: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@flaskApp.route('/landscape')
def page80L():
    try:
        return render_template('landscape.html', contextPath="")
    except Exception as e:
        logging.error(f"Error rendering landscape.html: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
@flaskApp.route('/tag-html')
def pagetagHtml():
    try:
        return render_template('tag-html.html', contextPath="")
    except Exception as e:
        logging.error(f"Error rendering tag-html.html: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
@flaskApp.route('/tag-scripts')
def pageTagScripts():
    try:
        return render_template('tag-scripts.html', contextPath="")
    except Exception as e:
        logging.error(f"Error rendering tag-scripts.html: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
@flaskApp.route('/wash-printer')
def pageWashPrinter():
    try:
        return render_template('wash-printer.html', contextPath="")
    except Exception as e:
        logging.error(f"Error rendering wash-printer.html: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
@flaskApp.route('/pdf-printer')
def pagePdfPrinter():
    try:
        return render_template('pdf-printer.html', contextPath="")
    except Exception as e:
        logging.error(f"Error rendering pdf-printer.html: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
@flaskApp.route('/pdf')
def pagepdf():
    try:
        return render_template('pdf.html', contextPath="")
    except Exception as e:
        logging.error(f"Error rendering pdf.html: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    


# 指令组装
def createCmd(request):
    try:
        # 获取请求体中的数据
        unique_id = uuid.uuid1().hex
        # zip = request.json.get('zip')
        # 打印的唯一口令，如果用户没传入就自动用uuid生成一个
        taskKey = request.json.get('taskKey') if request.json.get('taskKey') != None else unique_id
        # 打印的内容
        contents = request.json.get('contents') if request.json.get('contents') != None else None
        # 打印脚本内容
        scripts = request.json.get('scripts') if request.json.get('scripts') != None else None
        # 打印的选项
        options = request.json.get('options') if request.json.get('options') != None else {}
        zip = options.get('zip')
        pdfUrl = request.json.get('pdfUrl')
        if zip:
            if contents:
                content_bytes = base64.b64decode(unquote(contents).encode('utf-8'))
                decompressed = gzip.decompress(content_bytes)
                contents = decompressed.decode('utf-8')
                contents=json.loads(contents)
            if scripts:
                content_bytes = base64.b64decode(unquote(scripts).encode('utf-8'))
                decompressed = gzip.decompress(content_bytes)
                scripts = decompressed.decode('utf-8')
                scripts=json.loads(scripts)
        
        
        # 返回的指令
        cmd = {"taskKey": taskKey, "htmls": contents,"scripts":scripts, "pdfUrl":pdfUrl, "options": options}
        return cmd
    except Exception as e:
        print(e)
        logging.error(f"Error creating command: {e}")
        return None

# 预览
@flaskApp.route('/preview', methods=['POST'])
def preview():
    try:
        cmd = createCmd(request)
        if cmd:
            preview_queue.put(cmd)  # 将数据放入队列中
            return jsonify({
                "status": "success", 
                "resultCode": "success", 
                "resultObject" : { },
            }), 200
        else:
            return jsonify({
                "status": "error", 
                "resultCode": "error",
                "message": "Failed to create command"
            }), 400
    except Exception as e:
        logging.error(f"Error handling preview request: {e}")
        return jsonify({
            "status": "error", 
            "resultCode": "error",
            "message": "Internal Server Error"
        }), 500
        # return jsonify({"error": "Internal Server Error"}), 500

# 打印
@flaskApp.route('/print', methods=['POST'])
def prints():
    try:
        cmd = createCmd(request)
        if cmd:
            print_queue.put(cmd)  # 将数据放入队列中
            return jsonify({
                "status": "success", 
                "resultCode": "success", 
                "resultObject" : { },
            }), 200
        else:
            return jsonify({
                "status": "error", 
                "resultCode": "error",
                "message": "Failed to create command"
            }), 400
    except Exception as e:
        logging.error(f"Error handling print request: {e}")
        return jsonify({
            "status": "error", 
            "resultCode": "error",
            "message": "Internal Server Error"
        }), 500

# 直接打印
@flaskApp.route('/direct_print', methods=['POST'])
def direct_print():
    try:
        cmd = createCmd(request)
        if cmd:
            direct_print_queue.put(cmd)  # 将数据放入队列中
            return jsonify({
                "status": "success", 
                "resultCode": "success", 
                "resultObject" : { },
            }), 200
        else:
            return jsonify({
                "status": "error", 
                "resultCode": "error",
                "message": "Failed to create command"
            }), 400
    except Exception as e:
        logging.error(f"Error handling direct_print request: {e}")
        return jsonify({
            "status": "error", 
            "resultCode": "error",
            "message": "Internal Server Error"
        }), 500
# 向主进程发送通信指令
def sendCmd(cmd):
    times=100
    try:
        while p_doing.value==1 and times > 0:
            time.sleep(0.3)
            times=times-1
            # 指令超时
            if times==0:
                return jsonify({"error": "Internal Server Error"}), 500
        
        p_doing.value=1
        child_conn.send(cmd)
        maxWait = 1000
        while not child_conn.poll() and maxWait>0:
            time.sleep(0.3)
            maxWait=maxWait-1
        data = child_conn.recv()
        p_doing.value=0
        return data
    except Exception as e:
        logging.error(f"Error sending command: {e}")
        return None

# 展示打印机列表
@flaskApp.route('/printer_status', methods=['GET', 'POST'])
def printer_status():
    try:
        result = sendCmd("printer_status")
        if result:
            return jsonify({
                "status": "success", 
                "resultCode": "success", 
                "resultObject" : { "printerInfos": json.loads(result) },
                "message": None,
                "exceptionMessage": None,
                "exceptionLevel": None
                }
            ), 200
        else:
            return jsonify({
                "status": "error", 
                "resultCode": "error",
                "message": "Failed to get printer status"
            }), 500
    except Exception as e:
        logging.error(f"Error handling printer_status request: {e}")
        return jsonify({
            "status": "error", 
            "resultCode": "error",
            "message": "Internal Server Error"
        }), 500

# 获取打印进度
@flaskApp.route('/print_tasks', methods=['GET', 'POST'])
def print_tasks():
    try:
        result = sendCmd("print_tasks")
        if result:
            return jsonify({
                "success": "success",
                "resultCode": "success",
                "message": None,
                "resultObject": {
                    "printTasks": json.loads(result)
                }
            }), 200
            # return jsonify({"success": True, "printTasks": json.loads(result)}), 200
        else:
            return jsonify({
                "status": "error",
                "resultCode": "error",
                "message": "Failed to get print tasks"
            }), 500
    except Exception as e:
        logging.error(f"Error handling print_tasks request: {e}")
        return jsonify({
            "status": "error",
            "resultCode": "error",
            "message": "Internal Server Error"
        }), 500

# 导出PDF
@flaskApp.route('/export_pdf', methods=['POST'])
def export_pdf():
    try:
        cmd = createCmd(request)
        result = sendCmd("export_pdf:"+json.dumps(cmd))
        if result:
            return jsonify({
                "status": "success", 
                "resultCode": "success", 
                "resultObject" : result,
                "message": None,
                "exceptionMessage": None,
                "exceptionLevel": None
                }
            ), 200
        else:
            return jsonify({
                "status": "error", 
                "resultCode": "error",
                "message": "Failed to get printer status"
            }), 500
    except Exception as e:
        logging.error(f"Error handling printer_status request: {e}")
        return jsonify({
            "status": "error", 
            "resultCode": "error",
            "message": "Internal Server Error"
        }), 500

# 写入当前进程的 PID 到 PID 文件
def write_pid(temp_dir):
    with open(temp_dir+'/dplus-app.pid', 'a') as f:
        f.write(f"{os.getpid()}\n")
# 启动 HTTP 服务（端口 5100）
def runHttpServer(rootPath,tempDir,previewQueue, printQueue, directPrintQueue, conn,pDoing):
    global temp_dir,preview_queue, print_queue, direct_print_queue, child_conn,root_path,p_doing
    preview_queue = previewQueue
    print_queue = printQueue
    temp_dir = tempDir
    direct_print_queue = directPrintQueue
    child_conn = conn
    root_path = rootPath
    p_doing = pDoing

    try:
        write_pid(temp_dir)
        flaskApp.root_path=root_path
        flaskApp.template_folder=root_path + '/templates'
        flaskApp.static_folder=root_path + '/static'
        flaskApp.run(host='0.0.0.0', port=5100)
    except Exception as e:
        logging.error(f"Error running HTTP server: {e}")

# 启动 HTTPS 服务（端口 5443）
def runHttpsServer(rootPath,tempDir,previewQueue, printQueue, directPrintQueue, conn,pDoing, keyPath, certPath):
    global temp_dir,root_path,preview_queue, print_queue, direct_print_queue, child_conn,p_doing, key_temp_path, cert_temp_path
    preview_queue = previewQueue
    print_queue = printQueue
    direct_print_queue = directPrintQueue
    child_conn = conn
    temp_dir = tempDir
    root_path = rootPath
    p_doing = pDoing
    key_temp_path = keyPath
    cert_temp_path = certPath
    try:
        write_pid(temp_dir)
        flaskApp.root_path=root_path
        flaskApp.template_folder=root_path + '/templates'
        flaskApp.static_folder=root_path + '/static'
        flaskApp.run(host='0.0.0.0', ssl_context=(cert_temp_path, key_temp_path), port=5443)
    except Exception as e:
        logging.error(f"Error running HTTPS server: {e}")