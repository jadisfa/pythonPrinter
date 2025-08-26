from PyQt6.QtGui import QIcon,QAction,QPageLayout, QPageSize,QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QTimer,Qt,QEventLoop,QSizeF,QMarginsF,QByteArray,QRectF,QUrl
from PyQt6.QtWidgets import QApplication,QMainWindow,QTextEdit, QVBoxLayout,QMessageBox,QProgressDialog
from PyQt6.QtWidgets import QWidget, QPushButton,QSystemTrayIcon,QMenu,QToolButton,QCheckBox
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog,QPrintPreviewDialog,QPrinterInfo
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QFontDatabase,QDesktopServices

import base64,gzip,json,tempfile,time,fitz,requests
from urllib.parse import unquote
from globals import getAllPrintTasks,getPrintTask,addPrintTask,removePrintTask,release_all,preview_queue,print_queue,direct_print_queue,parent_conn,run_path
from src.webs.manager import startWebServer,stopWebServer,checkWatchCrtFile,isWebServerRunning,destroyWebServer
from src.ui.autoStartup import *
from src.ui.TagPrinter import *
from src.ui.EscPosPrinter import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.previewCmd = ""
        self.fonts = {}  # 存储已加载的字体家族名称
        self.initFonts()  # 新增字体初始化方法
        # system_fonts = QFontDatabase.families()
        # print("Available fonts:", system_fonts)
        
        self.initUI()
    
         # 确保系统托盘支持可用
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.createTrayIcon()
    def initFonts(self):
        # 字体URL列表（示例）
        font_urls = [
            "https://file.dianplus.cn/assets/fonts/UNIFY%20TEXTILE%20CARE.ttf"
        ]
        
        for url in font_urls:
            try:
                # 从网络下载字体文件
                response = requests.get(url, stream=True)
                response.raise_for_status()  # 检查请求是否成功
                
                # 创建临时文件保存字体
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(url)[1]) as tmp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        tmp_file.write(chunk)
                    font_path = tmp_file.name
                
                # 获取字体名称（从URL提取）
                font_name = os.path.splitext(os.path.basename(url))[0]
                
                # 加载字体文件
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id == -1:
                    print(f"字体加载失败：{url}")
                    continue
                
                # 获取字体家族名称
                families = QFontDatabase.applicationFontFamilies(font_id)
                self.fonts.update({font_name: families[0]})
                print(f"已加载字体：{', '.join(families)}")
                
                # 删除临时文件（可选）
                os.unlink(font_path)
                
            except Exception as e:
                print(f"下载或加载字体 {url} 时出错：{e}")
        # '"仿宋","STFangsong","FangSong"', '"宋体","Songti SC","STSong"', '"微软雅黑","Microsoft YaHei","PingFang SC"', '"新宋体","NSimSun","Songti SC"', '"楷体","Kaiti SC","STKaiti"', '"黑体","Heiti SC","STHeiti"','"Resource Han Rounded CN","幼圆体","Yuanti SC","Microsoft YaHei UI"'
    def initUI(self):
        self.setFixedWidth(300)
        self.setFixedHeight(200)
        self.timerPreview = QTimer(self)  # 预览指令监听器
        self.timerPreview.timeout.connect(self.checkPreviewQueue)
        self.timerPreview.start(1000) 
        self.timerPrint = QTimer(self)  # 打印指令监听器
        self.timerPrint.timeout.connect(self.checkPrintQueue)
        self.timerPrint.start(1000) 

        self.timerDirectPrint = QTimer(self)  # 直接打印指令监听器
        self.timerDirectPrint.timeout.connect(self.checkDirectPrintQueue)
        self.timerDirectPrint.start(1000) 

        self.timerPrinterStatus = QTimer(self)  # 打印机状态监听器
        self.timerPrinterStatus.timeout.connect(self.checkPrintStatuses)
        self.timerPrinterStatus.start(1000) 

        self.timerWatchCrtFile = QTimer(self)  # http证书文件监控
        self.timerWatchCrtFile.timeout.connect(lambda : checkWatchCrtFile(self))
        # 2小时监控一次
        self.timerWatchCrtFile.start(2*60*60*1000) 

        self.timerCmds = QTimer(self)  # 其他指令监听器
        self.timerCmds.timeout.connect(self.cmds)
        self.timerCmds.start(100) 

        # 创建一个 QTimer 实例
        self.delay_timer = QTimer(self)
        self.delay_timer.setSingleShot(True)  # 设置为单次触发

        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        centralWidget = QWidget()  # 中心部件a# 设置中心部件
        layout = QVBoxLayout(centralWidget)
        self.startWebButton = QPushButton('开启服务', self)
        self.startWebButton.clicked.connect(self.onStartWebButtonClicked)
        self.startWebButton.setEnabled(False)  # 初始时禁用停止按钮

        self.stopWebButton = QPushButton('停止服务', self)
        self.stopWebButton.clicked.connect(self.onStopWebButtonClicked)

        self.textEdit = QTextEdit()
        self.textEdit.setText("正在等待打印请求...")
        self.textEdit.setReadOnly(True)
        self.textEdit.setFixedHeight(50)
        if platform.system() == "Windows" or platform.system() == "Darwin":
            self.startupCheckBox = QCheckBox('开机自启动', self)
            self.startupCheckBox.setChecked(get_startup())
            self.startupCheckBox.stateChanged.connect(onStartupCheckBoxChanged)
            layout.addWidget(self.startupCheckBox)
        layout.addWidget(self.textEdit)
        layout.addWidget(self.startWebButton)
        layout.addWidget(self.stopWebButton)

        # 创建一个链接按钮，点击后打开浏览器访问
        self.visitWebsiteButton = QPushButton("调试", self)
        self.visitWebsiteButton.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://localhost.dianplus.cn:5443")))  # 替换为实际官网地址
        layout.addWidget(self.visitWebsiteButton) 

        self.loop=QEventLoop()
        webView = QWebEngineView()

        webView.setFixedWidth(1)
        webView.setFixedHeight(1)
        webView.loadFinished.connect(lambda success: self.onWebViewLoadFinished(success))
        self.webView=webView
        self.printer=None
        self.pdfDoc=None
        layout.addWidget(webView)
        self.mainLayout = layout
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        version = '1.2.1'
        # 获取当前运行环境是64位还是32位
        if platform.architecture()[0] == '64bit':
            self.setWindowTitle(f'店家小助手V{version}(64位)')
        else:
            self.setWindowTitle(f'店家小助手V{version}(32位)')
        self.show()
        self.trayIcon=None
        self.isQuit=False
    # 打印页面属性配置，页面单位、大小、边距等
    def getQPageLayout(self,pageInfos):
        pageLayout=QPageLayout()
        margins=pageInfos.get('margins')
        contentOrientation=pageInfos.get('contentOrientation','portrait')
        pageLayout.setUnits(pageInfos.get('layoutUnit'))
        pageLayout.setOrientation(pageInfos.get('orientation'))
        pageLayout.setMargins(QMarginsF(margins.get('left'), margins.get('top'), margins.get('right'), margins.get('bottom')))
        width = pageInfos.get('width')
        height =pageInfos.get('height')
        if self.printer:
            printerType = self.printer.printerType
            if printerType == 'tag':
                height = height + 0.3
                width = width + 0.3
       
        if contentOrientation=='landscape':
            pageLayout.setPageSize(QPageSize(QSizeF(height,width), pageInfos.get('unit')))
        else:
            pageLayout.setPageSize(QPageSize(QSizeF(width,height), pageInfos.get('unit')))
       
        return pageLayout
    def onWebViewLoadFinished(self,success):
        if success:
            if self.printer is not None:
                try:
                    self.webView.printToPdf(self.onWebViewPdfPrintFinished, self.getQPageLayout(self.printer.pageInfos))
                except Exception as e:
                    logging.error(f"Error closing previewQueue: {e}")
                    self.loop.exit()
        else:
            self.loop.exit()
    def onWebViewPdfPrintFinished(self,pdfDate:QByteArray):
        if self.printer.onlyPdf:
            doc = fitz.open("pdf",pdfDate.data())
            for page in doc:
                self.pdfDoc.insert_pdf(doc, from_page=page.number, to_page=page.number)
                if self.printer.printerType=='tag' or self.printer.printerType=='tag_script':
                    break
            self.loop.exit()
            return
        
        doc = fitz.open("pdf",pdfDate.data())
        count =doc.page_count
        index=0
        svgs = []
        for page in doc:
            matrix = fitz.Matrix(self.printer.resolution() / 72, self.printer.resolution() / 72)
            text = page.get_svg_image(matrix=matrix, text_as_path=True)
            svgs.append(gzip.compress(text.encode('utf-8'),compresslevel=5))
            if self.printer.printerType=='tag' or self.printer.printerType=='tag_script':
                self.loop.exit()
                break
            # 判断是否最后一页
            if index < count - 1:
                pass
            else:
                self.loop.exit()
            index+=1

        self.printer.svgs=svgs
    # 创建系统托盘图标
    def createTrayIcon(self):
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(QIcon(run_path+"/static/logo.png"))  # 提供一个默认图标路径
        # 创建右键菜单
        trayMenu = QMenu(self)
        
        quitAction = QAction("退出", self)
        
        def quitSure():
              # 显示确认对话框
            reply = QMessageBox.question(self, '退出应用程序', '确定要退出应用程序吗？',
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.quitApplication()
            
        # 鼠标左键单击才触发退出事件
        quitAction.triggered.connect(quitSure)

        trayMenu.addAction(quitAction)
        # 设置菜单到托盘图标
        self.trayIcon.setContextMenu(trayMenu)
        
        # 当用户点击托盘图标时显示消息
        self.trayIcon.activated.connect(self.trayIconActivated)
        # 显示托盘图标
        self.trayIcon.show()

    # 当用户点击托盘图标时显示消息
    def trayIconActivated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show()
    #当用户点击窗口的关闭按钮时，隐藏窗口，而不是关闭它
    def closeEvent(self, event):
        try:
            if self.isQuit == True:
                event.accept()
                return
            if not(self.trayIcon == None) and self.trayIcon.isVisible():
                self.hide()
                event.ignore()
        except Exception as e:
            logging.error(f"Error closing previewQueue: {e}")
    # 退出应用程序，释放各类资源，关停Web服务
    def quitApplication(self):
        try:
            destroyWebServer()
            release_all()
            QApplication.instance().quit()
        except Exception as e:
            logging.error(f"Error in quitApplication: {e}")
        finally:
            self.isQuit = True
            QApplication.instance().quit()
    # 启动Web服务器
    def onStartWebButtonClicked(self):
        self.textEdit.setText("正在启动服务...")
        if (isWebServerRunning()):
            # 启用停止按钮
            self.startWebButton.setEnabled(False)
            self.stopWebButton.setEnabled(True)
            return
        startWebServer()
        # 启用停止按钮
        self.startWebButton.setEnabled(False)

        def startDelayActions():
            self.textEdit.setText("启动成功，正在等待打印请求...")
            self.stopWebButton.setEnabled(True)
        try:
            self.delay_timer.timeout.disconnect()  
        except Exception as e:
            logging.error(f"Failed to disconnect previous timer: {e}")
        self.delay_timer.timeout.connect(startDelayActions)  # 连接槽函数
        self.delay_timer.start(5000)  # 启动定时器，延时 5000 毫秒（5 秒）
    
    # 停止Web服务器
    def onStopWebButtonClicked(self):
        self.textEdit.setText("正在关闭服务...")
        stopWebServer()
        def stopDelayActions():
            # 在这里执行延时后的操作
            self.textEdit.setText("关闭成功")
            # 禁用停止按钮，启用启动按钮（可选，取决于您的需求）
            self.startWebButton.setEnabled(True)
            self.stopWebButton.setEnabled(False)

        try:
            self.delay_timer.timeout.disconnect()  
        except Exception as e:
            logging.error(f"Failed to disconnect previous timer: {e}")
        self.delay_timer.timeout.connect(stopDelayActions)  # 连接槽函数
        self.delay_timer.start(5000)  # 启动定时器，延时 5000 毫秒（5 秒）
    
    # 准备打印机
    def prepareQPrinter(self,taskKey,options):
        try:
            printerName = options.get('printerName')
            pageRect = options.get('pageRect')
            margins = options.get('margins')
            resolution = options.get('resolution')
            orientation = options.get('orientation')
            contentOrientation = options.get('contentOrientation')
            duplex = options.get('duplex')
            colorMode = options.get('colorMode')
            pageScopes = options.get('pageScopes')
            printCount = options.get('printCount', 1)  # 默认为1份
            printerType = options.get('printerType')  # 打印机类型
            printUnit = options.get('printUnit')  # 打印单位
            printMode = options.get('printMode')  # 
            printFullPage = options.get('printFullPage')  # 全屏铺满
            printCurrentNum = options.get('currentNum') # 分页后第几份

            printer = QPrinter(QPrinter.PrinterMode.PrinterResolution)
            printer.onlyPdf=False
            printer.pdfData=None
            printer.painter=None
            printer.printerType=None
            pageInfos={}
            if printUnit == 'inch':
                pageInfos['unit'] = QPageSize.Unit.Inch
                pageInfos['layoutUnit'] = QPageLayout.Unit.Inch
            elif printUnit == 'pt':
                pageInfos['unit'] = QPageSize.Unit.Point
                pageInfos['layoutUnit'] = QPageLayout.Unit.Point
            elif printUnit == 'didot':
                pageInfos['unit'] = QPageSize.Unit.Didot
                pageInfos['layoutUnit'] = QPageLayout.Unit.Didot
            else:
                pageInfos['unit'] = QPageSize.Unit.Millimeter
                pageInfos['layoutUnit'] = QPageLayout.Unit.Millimeter
            pageInfos['contentOrientation']=contentOrientation
            
            if printMode:
                printer.printMode = printMode
            else:
                printer.printMode = 'HighQuality'
            if printerType is not None:
                printer.printerType = printerType
            # 指定打印机
            if printerName:
                printer.setPrinterName(printerName)
                
            if printFullPage:
                printer.setFullPage(True)
            
            # 设置页面大小
            if pageRect:
                if pageInfos.get('unit') == QPageSize.Unit.Point: 
                    # 单位为pt
                    width=pageRect.get('width') if pageRect.get('width') != None else (80 / 0.352777778)
                    height=pageRect.get('height') if pageRect.get('height') != None else (90 / 0.352777778)
                elif pageInfos.get('unit') == QPageSize.Unit.Inch: 
                    # 单位为inch mm 转英寸 1英寸=2.54厘米
                    width=pageRect.get('width') if pageRect.get('width') != None else (80 / 25.4)
                    height=pageRect.get('height') if pageRect.get('height') != None else (90 / 25.4)
                elif pageInfos.get('unit') == QPageSize.Unit.Didot: 
                    # 单位为Didot mm 转Didot 1Didot=1.2Didot
                    width=pageRect.get('width') if pageRect.get('width') != None else (80 * 2.659)
                    height=pageRect.get('height') if pageRect.get('height') != None else (90 * 2.659)
                else : 
                    # 单位为毫米
                    width=pageRect.get('width') if pageRect.get('width') != None else 210
                    height=pageRect.get('height') if pageRect.get('height') != None else 297
                    
                pageInfos['width'] = width 
                pageInfos['height'] = height 
                pageSize = QPageSize(QSizeF(width, height), pageInfos.get('unit'))
                printer.setPageSize(pageSize)
            # 设置边距
            if margins:
                left=margins.get('left') if margins.get('left') != None else 0
                top=margins.get('top') if margins.get('top') != None else 0
                right=margins.get('right') if margins.get('right') != None else 0
                bottom=margins.get('bottom') if margins.get('bottom') != None else 0
                pageMargin = QMarginsF(left, top, right, bottom)
                pageInfos['margins']={"left": left, "top": top, "right": right, "bottom": bottom}
                # *****特别提醒这里的边距单位和页面的单位用的不是一个页面用的是 QPageSize.Unit 而这里要用QPageLayout.Unit
                printer.setPageMargins(pageMargin, pageInfos.get('layoutUnit'))
            else:
                pageInfos['margins']={"left": 0, "top": 0, "right": 0, "bottom": 0}
                printer.setPageMargins(QMarginsF(0, 0, 0, 0), pageInfos.get('layoutUnit'))
            # 设置打印方向
            if orientation:
                if(orientation=='landscape'):
                    printer.setPageOrientation(QPageLayout.Orientation.Landscape)
                    pageInfos['orientation']=QPageLayout.Orientation.Landscape
                else:
                    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
                    pageInfos['orientation']=QPageLayout.Orientation.Portrait

            printer.setPageLayout(self.getQPageLayout(pageInfos))

            # 设置打印机分辨率
            if resolution:
                printer.setResolution(resolution)  
            else:
                if printerType == 'ticket' or printerType == 'tag': 
                    printer.setResolution(203)
                    pageInfos['resolution']=203
                else:
                    printer.setResolution(300)
                    pageInfos['resolution']=300
                    
            printer.pageInfos=pageInfos
            # 设置双面打印
            if duplex:
                if(duplex=='long'):
                    printer.setDuplex(QPrinter.DuplexMode.DuplexLongSide)
                elif (duplex=='short'):
                    printer.setDuplex(QPrinter.DuplexMode.DuplexShortSide)
                elif (duplex=='auto'):
                    printer.setDuplex(QPrinter.DuplexMode.DuplexAuto)
                else:
                    printer.setDuplex(QPrinter.DuplexMode.DuplexNone)

            # 设置打印颜色模式
            if colorMode:
                if(colorMode=='color'):
                    printer.setColorMode(QPrinter.ColorMode.Color)
                else:
                    printer.setColorMode(QPrinter.ColorMode.GrayScale)

            # 设置打印起止页码
            if pageScopes:
                startPage = pageScopes.get('from') if pageScopes.get('from') != None else 1
                endPage = pageScopes.get('to') if pageScopes.get('to') != None else 1
                printer.setFromTo(startPage, endPage)
            else: 
                printer.setFromTo(1, 0)
            # 打印份数
            printer.setCopyCount(printCount)
            
            addPrintTask(taskKey,task={
                "taskKey":taskKey,
                "active":False,
                "status":'init',
                "printer":printer,
                "time":time.time()
            })
            return printer
        except Exception as e:
            logging.error(f"Error in prepareQPrinter: {e}")
            return None
    def getProcessWindows(self,label,count):
        progress = QProgressDialog("进度", "终止", 0, count)
        progress.setWindowTitle(label)
        progress.setWindowModality(Qt.WindowModality.NonModal) 
        progress.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowCloseButtonHint  
        )
        progress.setFixedWidth(400)
        progress.setAutoClose(True)  # 添加自动关闭
        return progress
    def getPrintDatas(self,printer,cmd):
        htmls = cmd.get('htmls')
        scripts = cmd.get('scripts')
        pdfUrl = cmd.get('pdfUrl')
        datas=[]
        if scripts:
            count = len(scripts)
            for index, script in enumerate(scripts):
                datas.append(script)
        if htmls:
            count = len(htmls)
            options = cmd.get('options')
            currentNum = options.get('currentNum')
            # 创建进度对话框
            progress:QProgressDialog=self.getProcessWindows("渲染进度",count)
            progress.show()
            for index, html in enumerate(htmls):
                if progress.wasCanceled():
                    break
                progress.setValue(index+1)
                if currentNum:
                    progress.setLabelText(f"正在渲染第 {currentNum} 份,第 {index+1}/{count} 页...")
                else:
                    progress.setLabelText(f"正在渲染第 {index+1}/{count} 页...")
                progress.repaint()  # 强制重绘
                self.webView.setHtml(unquote(html))
                self.loop.exec()
                for svg in printer.svgs:
                    datas.append(svg)

            progress.close()
            progress.deleteLater()
        if pdfUrl:
            response = requests.get(pdfUrl, stream=True)
            pdf_data = response.content
            doc = fitz.open("pdf", pdf_data)
            count =doc.page_count
            # 创建进度对话框
            progress:QProgressDialog=self.getProcessWindows("渲染进度",count)
            progress.show()
            for index, page in enumerate(doc):
                if progress.wasCanceled():
                    break
                text = page.get_svg_image()
                datas.append(gzip.compress(text.encode('utf-8'),compresslevel=5))
                progress.setValue(index+1)
                progress.setLabelText(f"正在渲染第 {index+1}/{count} 页...")
                progress.repaint()  # 强制重绘

            progress.close()
            progress.deleteLater()

        return datas
    def printSingleSvgPage(self,painter:QPainter,printer:QPrinter,data:dict,options:dict):
       
        pageRect = printer.pageRect(QPrinter.Unit.DevicePixel)
       
        svgR = QSvgRenderer(QByteArray(gzip.decompress(data)))
        svg_size = svgR.defaultSize()
       
         # 设置了内容跟随翻转
        if options.get("contentOrientation","portrait") == "landscape":
            svg_size.scale(pageRect.size().toSize().height(),pageRect.size().toSize().width(),Qt.AspectRatioMode.KeepAspectRatio)
            painter.save()  # 保存当前状态
            # 重置坐标系原点
            painter.resetTransform()
            painter.translate(0, pageRect.size().toSize().height())
            painter.rotate(-90) 
            svgR.render(painter, QRectF(0, 0,svg_size.width(), svg_size.height()))
            painter.restore()  
        else:
            svg_size.scale(pageRect.size().toSize(),Qt.AspectRatioMode.KeepAspectRatio)
            svgR.render(painter, QRectF(0, 0,svg_size.width(), svg_size.height()))
    # 打印预览
    def handlePrintPreview(self,cmd):
        try:
            taskKey = cmd.get('taskKey')
            options = cmd.get('options')
            printer:QPrinter=self.prepareQPrinter(taskKey,options)
            if not printer:
                return
            self.printer=printer
            
            previewDialog = QPrintPreviewDialog(printer, self)
            previewDialog.setEnabled(False)

            # 设置窗口支持最大化最小化
            previewDialog.setWindowFlags(previewDialog.windowFlags() | Qt.WindowType.WindowMinMaxButtonsHint)
            previewDialog.setWindowFlags(previewDialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            
            buttons = previewDialog.findChildren(QToolButton)

            previewDialog.triggerBtn = None
            # 遍历按钮寻找横竖排切换按钮
            for btn in buttons:
                if btn.text() in ["Portrait", "Landscape"]:  
                    def onOrientationChanged(e):
                        previewDialog.triggerBtn="Preview"
                    # 连接点击事件
                    btn.toggled.connect(onOrientationChanged)

                if btn.text() in ["Print"]:  
                    def handle_print_button_clicked():
                        try:
                            self.textEdit.setText("正在等待打印请求...")
                            getPrintTask(taskKey)['active'] = True
                        except Exception as e:
                            pass
                    btn.clicked.connect(handle_print_button_clicked)

            datas=self.getPrintDatas(printer,cmd)
            count=len(datas)
            scriptsPrint=cmd.get("scripts") != None
            def handlePaintRequested(printer:QPrinter):
                previewDialog.setEnabled(False)
                previewDialog.triggerBtn=None
                painter=QPainter()
                painter.begin(printer)
                
                # 获取当前设置的起止页码
                from_page = 0
                to_page = 0
                if printer.fromPage()==0 and printer.toPage()==0:
                    from_page=0
                    to_page=count
                else:
                    from_page=printer.fromPage()-1
                    if printer.toPage()>count:
                        to_page=count
                    else:
                        to_page=printer.toPage()

                actualDatas=[]
                for index in range(from_page, to_page):
                    actualDatas.append(datas[index])
                for index, data in enumerate(actualDatas):
                    data = actualDatas[index]
                    if scriptsPrint:
                        tagPrinter = TagPrinter(data, options)
                        tagPrinter.render(printer,painter)
                    else:
                        self.printSingleSvgPage(painter, printer, data, options)
                    if index < (len(actualDatas) - 1):  # 根据实际页码范围判断是否需要分页
                        printer.newPage()
                
                painter.end()
                previewDialog.setEnabled(True)

            previewDialog.paintRequested.connect(handlePaintRequested)
            previewDialog.exec()
            previewDialog.raise_()
            previewDialog.activateWindow()
            previewDialog.deleteLater()
        except Exception as e:
            logging.error(f"Error in prepareQPrinter: {e}")
    # 打印
    def handlePrint(self,cmd):
        try:
            taskKey = cmd.get('taskKey')
            options = cmd.get('options')
            printer:QPrinter=self.prepareQPrinter(taskKey,options)
            if not printer:
                return
            self.printer=printer
            dialog = QPrintDialog(printer, self)
            # 设置对话框置顶显示
            dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            dialog.raise_()
            dialog.activateWindow()
            
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                datas=self.getPrintDatas(printer,cmd)
                scriptsPrint=cmd.get("scripts") != None
                count=len(datas)
                painter=QPainter()
                painter.begin(printer)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                # 新增高质量渲染选项
                painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering, True)
                progress:QProgressDialog=self.getProcessWindows("打印进度",count)
                progress.show()
                for index, data in enumerate(datas):
                    if scriptsPrint:
                        tagPrinter = TagPrinter(data, options)
                        tagPrinter.render(printer,painter)
                    else:
                        self.printSingleSvgPage(painter, printer, data, options)
                    if index < count - 1:
                        self.printer.newPage()
                    getPrintTask(taskKey)['active'] = True
                    progress.setValue(index+1)
                    progress.setLabelText(f"正在打印第 {index+1}/{count} 页...")
                    progress.repaint()  # 强制重绘
                painter.end()
                progress.close()
                progress.deleteLater()
        except Exception as e:
            logging.error(f"Error in prepareQPrinter: {e}")
    # 直接打印
    def handleDirectPrint(self,cmd):
        try:
            taskKey = cmd.get('taskKey')
            options = cmd.get('options')
            # 小票打印
            if options.get("printerType","normal") == "ticket":
                datas=self.getPrintDatas(None,cmd)
                for index, data in enumerate(datas):
                    posPrinter = EscPosPrinter(data, options)
                    posPrinter.render()
                return
            
            printer:QPrinter=self.prepareQPrinter(taskKey,options)
            if not printer:
                return
            self.printer=printer
            datas=self.getPrintDatas(printer,cmd)
            scriptsPrint=cmd.get("scripts") != None
            count=len(datas)
             # 创建进度对话框
            painter=QPainter()
            painter.begin(printer)
            print(printer.copyCount())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            # 新增高质量渲染选项
            painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering, True)
            currentNum = options.get('currentNum')
            progress:QProgressDialog=self.getProcessWindows("打印进度",count)
            progress.show()
            for index, data in enumerate(datas):
                if scriptsPrint:
                    scriptR = TagPrinter(data, options)
                    scriptR.render(printer,painter)
                else:
                    self.printSingleSvgPage(painter, printer, data, options)
                if index < count - 1:
                    self.printer.newPage()
                getPrintTask(taskKey)['active'] = True
                progress.setValue(index+1)
                if currentNum:
                    progress.setLabelText(f"正在打印第 {currentNum} 份,第 {index+1}/{count} 页...")
                else:
                    progress.setLabelText(f"正在打印第 {index+1}/{count} 页...")
                progress.repaint()  # 强制重绘
            painter.end()
            progress.close()
            progress.deleteLater()
                
        except Exception as e:
            logging.error(f"Error in prepareQPrinter: {e}")

    # 生成PDF
    def handleExportPdf(self,cmd):
        try:
            taskKey = cmd.get('taskKey')
            options = cmd.get('options')
            htmls = cmd.get('htmls')
            printer=self.prepareQPrinter(taskKey,options)
            printer.onlyPdf=True
            if not printer:
                return None
            count = len(htmls)
            self.printer=printer
            self.pdfDoc=fitz.open()
             # 创建进度对话框
            progress:QProgressDialog=self.getProcessWindows("导出进度",count)
            progress.show()
            for index, html in enumerate(htmls):
                if progress.wasCanceled():
                    break
                progress.setValue(index+1)
                progress.setLabelText(f"正在渲染第 {index+1}/{count} 页...")
                progress.repaint()  # 强制重绘

                self.webView.setHtml(unquote(html))
                self.loop.exec()
            pdfData:bytes=self.pdfDoc.tobytes()
            self.pdfDoc.close()
            self.pdfDoc=None
            if not pdfData:
                return None
            progress.close()
            progress.deleteLater()
            return base64.b64encode(pdfData).decode('utf-8')
        except Exception as e:
            logging.error(f"Error in prepareQPrinter: {e}")
        return None
    #检测预览队列
    def checkPreviewQueue(self):
        try:
            if not preview_queue.empty():
                cmd = preview_queue.get()
                self.textEdit.setText("接收到预览指令")
                self.handlePrintPreview(cmd)
                self.textEdit.setText("正在等待打印请求...")
        except Exception as e:
            logging.error(f"Error in prepareQPrinter: {e}")
     #检测打印队列
    def checkPrintQueue(self):
        try:
            if not print_queue.empty():
                cmd = print_queue.get()
                self.textEdit.setText("接收到打印指令")
                self.handlePrint(cmd)
                self.textEdit.setText("正在等待打印请求...")
        except Exception as e:
            logging.error(f"Error in prepareQPrinter: {e}")
     #检测直接打印队列
    def checkDirectPrintQueue(self):
        try:
            if not direct_print_queue.empty():
                cmd = direct_print_queue.get()
                self.textEdit.setText("接收到直接打印指令")
                self.handleDirectPrint(cmd)
                self.textEdit.setText("正在等待打印请求...")
        except Exception as e:
            logging.error(f"Error in prepareQPrinter: {e}")

    # 检查已激活的打印机状态
    def checkPrintStatuses(self):
        try:
            tasks= getAllPrintTasks()
            # 变量所有任务列表
            for task in tasks:
                # 删除超时的
                if time.time() - task['time'] > 180:
                    removePrintTask(task['taskKey'])
                    continue
                if task['active']:
                    printer:QPrinter=task['printer']
                    if printer.printerState() == QPrinter.PrinterState.Idle:
                        task['status'] = "success"
                    elif printer.printerState() == QPrinter.PrinterState.Aborted:
                        task['status'] = "aborted"
                    elif printer.printerState() == QPrinter.PrinterState.Error:
                        task['status']  = "error"
                    elif printer.printerState() == QPrinter.PrinterState.Active:
                        # 更新时间
                        task['status']  = "active"
                        task['time'] = time.time()
        except Exception as e:
            logging.error(f"Error in prepareQPrinter: {e}")
    # 接收http服务子进程指令
    def cmds(self):
        try:
            cmd:str = parent_conn.poll()
            # 判断子进程是否有信息，如果没有则退出
            if cmd==False:
                return
            # 发现了信号
            cmd = parent_conn.recv()

            # 打印机状态
            if cmd=='printer_status':
                    printers = QPrinterInfo.availablePrinters()
                    printerInfos = []
                    for printer in printers:
                        info = {
                            "name": printer.printerName(),
                            "description": printer.description(),
                            "location": printer.location(),
                            "is_default": printer.isDefault(),
                            "is_remote": printer.isRemote(),
                            "supported_resolutions": [printer.supportedResolutions()]
                        }
                        printerInfos.append(info)
                    parent_conn.send(json.dumps(printerInfos))
            elif cmd=='print_tasks':
                    tasks=getAllPrintTasks()
                    printInfos=[]
                    for task in tasks:
                        printInfos.append({
                            "taskKey":task['taskKey'],
                            "status":task['status'],
                            "active":task['active'],
                            "printer":task['printer'].printerName()
                        })
                    parent_conn.send(json.dumps(printInfos))
             # 打印机状态
            elif cmd.startswith("export_pdf:"):
                    reportText=cmd.replace("export_pdf:", "")
                    result=self.handleExportPdf(json.loads(reportText))
                    parent_conn.send(result)
            else:
                parent_conn.send(cmd)
        except Exception as e:
            logging.error(f"Error in prepareQPrinter: {e}")

   
