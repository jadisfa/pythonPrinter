from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPen, QBrush, QColor
from PyQt6.QtGui import QPainter, QColor,QImage,QFontMetricsF,QFont
from PyQt6.QtCore import QByteArray,QRectF,Qt,QSize
from PyQt6.QtPrintSupport import QPrinter,QPrinterInfo

import requests,logging,base64
import math
from xml.dom import minidom  
from reportlab.graphics.barcode import createBarcodeDrawing,qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import Color

def get_printer_by_name(printer_name: str) -> QPrinterInfo:
    printers = QPrinterInfo.availablePrinters()
    for printer in printers:
        if printer.printerName() == printer_name:
            return printer
    return None

# 脚本打印
class TagPrinter():
    isColor = False
    mm_to_px=1
    #设置线条样式
    style_map = {
        "solid": Qt.PenStyle.SolidLine,
        "dash": Qt.PenStyle.DashLine,
        "dot": Qt.PenStyle.DotLine,
        "dashdot": Qt.PenStyle.DashDotLine,
        "dashdotdot": Qt.PenStyle.DashDotDotLine,
        "none": Qt.PenStyle.NoPen
    }
    def __init__(self, json_data:dict,options:dict):
        self.labels = json_data.get("labels")
        self.unit = json_data.get("unit","px")
        self.options = options
        print_name = self.options.get("printerName")
        printer_info = get_printer_by_name(print_name)
        # 获取当前打印机信息，判断是否支持彩色打印，单色模式下动态修改填充色和文字颜色
        if printer_info is not None:
            supported_modes = printer_info.supportedColorModes()
            target_mode = QPrinter.ColorMode.Color
            if target_mode in supported_modes or printer_info.defaultColorMode().name == 'Color':
                self.isColor = True
            else:
                self.isColor = False       
    def render(self,printer:QPrinter, painter:QPainter):
        """绘制单个标签内容（需根据实际需求修改）"""
        painter.save()  # 保存当前状态
    
        pageRect = printer.pageRect(QPrinter.Unit.DevicePixel)

        width=pageRect.size().toSize().width()
        height=pageRect.size().toSize().height()
        # 转换为打印机坐标系统
        painter.setWindow(0, 0,width,height)
        painter.setViewport(0, 0, width, height)

        dpi = printer.resolution()  # 通常为300/600/720等
        self.dpi = dpi
        self.mm_to_px = dpi / 25.4  # 1英寸=25.4mm → 1mm= (dpi/25.4)像素
        # 设置了内容跟随翻转
        if self.options.get("contentOrientation","portrait") == "landscape":
            painter.translate(0, height)
            painter.rotate(-90) 
        # 绘制标签      
        for label in self.labels:
            try: 
                label_type = label["type"]
                if label_type == "text":
                    self.drawText(painter, label)
                if label_type == "table":
                    self.drawTable(painter, label)
                elif label_type == "image":
                    self.drawImage(painter, label)
                elif label_type == "svg":
                    self.drawSvg(painter, label)
                elif label_type == "line":
                    self.drawLine(painter, label)
                elif label_type == "rect":
                    self.drawRect(painter, label)
                elif label_type == "barcode":
                    self.drawBarCode(painter, label)
                elif label_type == "qrcode":
                    self.drawQrCode(painter, label)
            except Exception as e:
                print(e)
                logging.error(f"Error rendering label: {e}")
            
        painter.restore()  # 恢复状态
    
    # 绘制线条
    def drawLine(self, painter:QPainter,data):
        x1 = self.getPxValue(data.get("x1", 0))
        y1 =  self.getPxValue(data.get("y1", 0))
        x2 =  self.getPxValue(data.get("x2", 0))
        y2 =  self.getPxValue(data.get("y2", 0))
        rotate = data.get("rotate", None)
        rotateOrigin = data.get("rotateOrigin", None)
        colorRgba = data.get("colorRgba", [0,0,0,255])
        border = self.getPxValue(data.get("border", 1))
        pen:QPen=painter.pen()
        line_style = data.get("lineStyle", "solid")
        color = QColor(colorRgba[0], colorRgba[1], colorRgba[2], colorRgba[3])
        myPen = QPen(color, border)
        qstyle = self.style_map.get(line_style.lower(), Qt.PenStyle.SolidLine)
        myPen.setStyle(qstyle)
        painter.setPen(myPen)

        if rotate:
            painter.save()
            if rotateOrigin == "top-left" or rotateOrigin == "bottom-left":
                # 计算中心点坐标
                center_x = x1
                center_y = y1
                # 坐标变换三部曲
                painter.translate(center_x, center_y)  # 1.平移坐标系到中心点
                if rotate==180:
                    painter.rotate(rotate+0.0000000001)
                else:
                    painter.rotate(rotate)             # 2.执行旋转
                # 计算相对坐标并绘制
                painter.drawLine(0, 0, x2 - x1, y2 - y1)  # 3.绘制相对坐标线条
            elif rotateOrigin == "top-right" or rotateOrigin == "bottom-right":
                # 计算中心点坐标
                center_x = x2
                center_y = y2
                # 坐标变换三部曲
                painter.translate(center_x, center_y)  # 1.平移坐标系到中心点
                if rotate==180:
                    painter.rotate(rotate+0.0000000001)
                else:
                    painter.rotate(rotate)
                relative_x1 = x1 - center_x
                relative_y1 = y1 - center_y
                relative_x2 = x2 - center_x
                relative_y2 = y2 - center_y               # 2.执行旋转
                # 计算相对坐标并绘制
                painter.drawLine(relative_x1,relative_y1, relative_x2, relative_y2)  # 3.绘制相对坐标线条
            else:
                # 计算中心点坐标
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                # 坐标变换三部曲
                painter.translate(center_x, center_y)  # 1.平移坐标系到中心点
                if rotate==180:
                    painter.rotate(rotate+0.0000000001)
                else:
                    painter.rotate(rotate)               # 2.执行旋转
                # 计算相对坐标并绘制
                painter.drawLine(x1 - center_x, y1 - center_y, 
                                x2 - center_x, y2 - center_y)  # 3.绘制相对坐标线条
            painter.restore()
        else:
            painter.drawLine(x1, y1, x2, y2)
        # 恢复画笔
        painter.setPen(pen)
    # 绘制矩形
    def drawRect(self, painter:QPainter,data):
        x =  self.getPxValue(data.get("x", 0))
        y =  self.getPxValue(data.get("y", 0))
        w =  self.getPxValue(data.get("width", 0))
        h =  self.getPxValue(data.get("height", 0))
        border =  self.getPxValue(data.get("border", 0))
        colorRgba = data.get("colorRgba", None)
        fillColorRgba = data.get("fillColorRgba", None)
        rotate = data.get("rotate", None)
        rotate_origin= data.get("rotateOrigin", None)
        pen:QPen=painter.pen()
        brush:QPen=painter.brush()
        if colorRgba and border != 0:
            color = QColor(colorRgba[0], colorRgba[1], colorRgba[2], colorRgba[3])
            myPen = QPen(color, border)
            line_style = data.get("lineStyle", "solid")
            qstyle = self.style_map.get(line_style.lower(), Qt.PenStyle.SolidLine)
            myPen.setStyle(qstyle)
            painter.setPen(myPen)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
        # 彩色模式或填充色为白色采用数据颜色，单色模式下采用黑底
        if fillColorRgba:
            Y = 0.299*fillColorRgba[0] + 0.587*fillColorRgba[1] + 0.114*fillColorRgba[2]
            if self.isColor:
                fillColor = QColor(fillColorRgba[0], fillColorRgba[1], fillColorRgba[2], fillColorRgba[3])
                painter.setBrush(QBrush(fillColor))
            else:
                if Y and Y > 128:
                    fillColor = QColor(255, 255, 255, 255)
                    painter.setBrush(QBrush(fillColor))
                else:
                    fillColor = QColor(0, 0, 0, 255)
                    painter.setBrush(QBrush(fillColor))
        
        if rotate:
            painter.save()
            center_x, center_y=self.findRotationOrigPoint(x, y, w, h, rotate_origin)
            painter.translate(center_x, center_y)
            if rotate==180:
                painter.rotate(rotate+0.0000000001)
            else:
                painter.rotate(rotate)
            drawX,drawY= self.findRotationDrawPoint(0, 0, w, h, rotate_origin)
            # 根据原点类型调整绘制位置
            painter.drawRect(drawX, drawY, w, h)
            painter.restore()
        else:
            painter.drawRect(x, y, w, h)
         # 恢复画笔
        painter.setPen(pen)
        painter.setBrush(brush)
    # 绘制文本
    def drawText(self, painter:QPainter,data):
        rect =  data.get("rect", None)
        text = data.get("text", "")

        self.setFont(painter,data)
        fontSize = painter.font().pixelSize()
        if rect is not None:
            autoWrap = rect.get("autoWrap", False)
            autoSize = rect.get("autoSize", False)
            truncate = rect.get("truncate", False)
            #  自动换行
            if autoWrap:
                return self.drawAutoWarpText(painter,data)
             # 开启了自动调整字体大小
            if autoSize:
                self.textAutoSize(painter,data)
                # 重置文字大小
                fontSize = painter.font().pixelSize()
            # 文字截断
            if truncate:
                # 计算截断后的文本
                text=self.textTruncate(painter,data,rect)
       
        if text is None:
            return
       
        rotate = data.get("rotate", None)
        rotate_origin= data.get("rotateOrigin", None)
        x2 =  self.getPxValue(data.get("x", 0))
        y2 =  self.getPxValue(data.get("y", 0))
       
        position = data.get("position", "absolute")
        if rect is not None:
            rectX =  self.getPxValue(rect.get("x", 0))
            rectY =  self.getPxValue(rect.get("y", 0))
            rectW =  self.getPxValue(rect.get("width", 0))
            rectH =  self.getPxValue(rect.get("height", 0))
            # 绘制外框
            self.drawWapperRect(painter,data)
           
            if position == "relative":
                x2=x2+rectX
                y2=y2+rectY
                rectTextAlign = rect.get("textAlign", None)
                rectVerticalAlign = rect.get("verticalAlign", None)
        text_rect = painter.fontMetrics().boundingRect(text)
        w= text_rect.width()
        h= text_rect.height()

        if position == "relative":
            x2, y2 = self.findRelativePoint(rectX, rectY, rectW, rectH, w,h,rectTextAlign, rectVerticalAlign)

        if rotate:
            painter.save()
            if rect:
                w= rectW 
                h= rectH 
                x1= rectX 
                y1= rectY 
            else:
                w= text_rect.width()
                h= text_rect.height()
                x1= x2
                y1= y2
            center_x, center_y=self.findRotationOrigPoint(x1, y1, w, h, rotate_origin)
            offsetX, offsetY = x2-x1, y2-y1+fontSize
            painter.translate(center_x, center_y)
            if rotate==180:
                painter.rotate(rotate+0.0000000001)
            else:
                painter.rotate(rotate)

            drawX,drawY= self.findRotationDrawPoint(offsetX, offsetY, w, h, rotate_origin)

            painter.drawText(drawX, drawY, text)

            painter.restore()
        else:
            painter.drawText(int(x2), int(y2+fontSize), text)
            
    # 绘制自动换行文本
    def drawAutoWarpText(self, painter:QPainter,data):
        text = data.get("text", "")
        if text is None:
            return
        
        rotate = data.get("rotate", None)
        rotate_origin= data.get("rotateOrigin", None)
        x2 =  self.getPxValue(data.get("x", 0))
        y2 =  self.getPxValue(data.get("y", 0))
        rect =  data.get("rect", None)
        rectX =  self.getPxValue(rect.get("x", 0))
        rectY =  self.getPxValue(rect.get("y", 0))
        rectW =  self.getPxValue(rect.get("width", 0))
        rectH =  self.getPxValue(rect.get("height", 0))

        x2=x2+rectX
        y2=y2+rectY
        rectTextAlign = rect.get("textAlign", None)
        rectVerticalAlign = rect.get("verticalAlign", None)
        autoSize = rect.get("autoSize", False)
        truncate = rect.get("truncate", False)
        # 绘制外框
        self.drawWapperRect(painter,data)
        #  设置字体
        self.setFont(painter,data)

         # 设置文本对齐标志
        flags = 0
        if rectTextAlign == "right":
            flags |= Qt.AlignmentFlag.AlignRight
        elif rectTextAlign == "center":
            flags |= Qt.AlignmentFlag.AlignHCenter
        else:  # left
            flags |= Qt.AlignmentFlag.AlignLeft
            
        if rectVerticalAlign == "bottom":
            flags |= Qt.AlignmentFlag.AlignBottom
        elif rectVerticalAlign == "middle":
            flags |= Qt.AlignmentFlag.AlignVCenter
        else:  # top
            flags |= Qt.AlignmentFlag.AlignTop
        flags |= Qt.TextFlag.TextWordWrap  # 启用自动换行
        
        if autoSize:
            min_font_size_mm = 1.5 # 设置最小字体大小为 1.5mm
            min_font_size_px = max(1, int(min_font_size_mm * self.mm_to_px))  # 转换为像素
            font = painter.font()
            original_font_size = font.pixelSize()
            current_font_size = original_font_size
            natural_lines = text.split('\n') if text else ['']

            # 提前初始化 fm，避免 UnboundLocalError
            font.setPixelSize(int(round(current_font_size)))
            painter.setFont(font)
            fm = painter.fontMetrics()
            line_height = fm.lineSpacing()

            # 尝试找到合适的字号
            while current_font_size >= min_font_size_px:
                font.setPixelSize(int(round(current_font_size)))
                painter.setFont(font)
                fm = painter.fontMetrics()  # 更新 fm
                line_height = fm.lineSpacing()

                # 新增：先判断原始文本宽度是否超过容器宽度
                raw_text_width = 0
                for natural_line in natural_lines:
                    raw_line_width = fm.horizontalAdvance(natural_line)
                    if raw_line_width > raw_text_width:
                        raw_text_width = raw_line_width

                fits_width = True

                # 如果原始文本宽度大于容器宽度，则不满足
                if raw_text_width > rectW:
                    fits_width = False
                else:
                    # 再检查换行后的每一行是否适配
                    for natural_line in natural_lines:
                        sub_lines = self.wrapText(natural_line, rectW, painter)
                        for line in sub_lines:
                            if fm.horizontalAdvance(line) > rectW * 1.03:
                                fits_width = False
                                break
                        if not fits_width:
                            break

                if not fits_width:
                    current_font_size -= 0.25
                    continue

                # 检查总高度是否适配
                total_height = len(natural_lines) * line_height
                if total_height <= rectH:
                    break  # 宽高都适配成功
                else:
                    current_font_size -= 0.25  # 高度不够，继续缩小

            # ⭐️ 特别注意：如果循环结束后仍未找到合适字号，强制使用最小字号
            final_font_size = max(current_font_size, min_font_size_px)

            # ⭐️ 兜底：如果最终字号仍然小于最小字号，设为最小字号
            if final_font_size < min_font_size_px:
                final_font_size = min_font_size_px
            # font.setPixelSize(13.5)
            font.setPixelSize(max(round(final_font_size), 1.5))
            painter.setFont(font)

            # 重新获取字体度量（因为字体已改变）
            fm = painter.fontMetrics()
            line_height = fm.lineSpacing()

            # 重新换行并裁剪超出内容
            wrapped_lines = []
            total_height = 0
            for natural_line in natural_lines:
                sub_lines = self.wrapText(natural_line, rectW, painter)
                for line in sub_lines:
                    if total_height + line_height > rectH:
                        break  # 超出高度，停止添加
                    wrapped_lines.append(line)
                    total_height += line_height
                if total_height + line_height > rectH:
                    break  # 总高度已超限，跳出外层循环

            wrapped_text = "\n".join(wrapped_lines)
        else:
            # 换行拆解
            natural_lines = text.split('\n') if text else ['']
            wrapRows=[]
            line_height = painter.fontMetrics().height()
            for line_str in natural_lines:
                wrappedLines = self.wrapText(line_str, rectW, painter)
                wrapRows.extend(wrappedLines)  # 添加所有换行后的字符串
            if len(natural_lines) > 1: 
                max_lines = int(rectH // line_height)
                # wrapRows = wrapRows[:max_lines]  # 截断超出高度的行
                # total_height = 0
                # limited_rows = []
                # fm = painter.fontMetrics()
                
                # for line in wrapRows:
                #     # 使用 boundingRect 获取实际行高
                #     line_rect = fm.boundingRect(QRect(0, 0, int(rectW), int(rectH)), 
                #                             Qt.TextFlag.TextWordWrap, line)
                #     line_height = line_rect.height()
                    
                #     # 如果加上当前行会超出高度限制，则停止添加
                #     if total_height + line_height > rectH:
                #         break
                        
                #     limited_rows.append(line)
                #     total_height += line_height
                
                # wrapRows = limited_rows
            wrapped_text="\n".join(wrapRows)
        text_rect = painter.fontMetrics().boundingRect(text)

        if truncate==False:
            if text_rect.height()>rectH:
                rectH=text_rect.height()

        if rotate:
            painter.save()
            #获取原点
            center_x, center_y=self.findRotationOrigPoint(x2, y2, rectW, rectH, rotate_origin)
            # 计算相对偏移量
            offsetX = x2 - center_x
            offsetY = y2 - center_y

            # 执行旋转
            painter.translate(center_x, center_y)
            if rotate==180:
                painter.rotate(rotate+0.0000000001)
            else:
                painter.rotate(rotate)
        
            rotatedRect = QRectF(offsetX, offsetY, rectW, rectH)
            
            # 绘制文本
            painter.drawText(rotatedRect, flags, wrapped_text)
            painter.restore()
        else:
            # 创建文本矩形区域
            textRect = QRectF(x2, y2, rectW, rectH)
            
            # 直接使用 painter.drawText 方法，这是最稳定可靠的方案
            self.drawReliableText(painter, wrapped_text, textRect, data, rect)

    def drawReliableText(self, painter, text, textRect, data, rect):
        """使用可靠的方式绘制文本，确保与HTML/CSS渲染一致"""
        # 保存当前字体状态
        original_font = painter.font()
        
        # # 设置字体
        # self.setFont(painter, data)
        
        # 获取字体度量信息
        fm = painter.fontMetrics()
        # 解析文本为行
        lines = text.split('\n')
        
        # 计算行高 - 使用 lineSpacing 确保与CSS的line-height一致
        line_height = fm.lineSpacing()
        
        # 如果设置了lineHeight属性，使用该值
        # if 'lineHeight' in data and data['lineHeight'] is not None:
        # line_height = self.getPxValue(data['fontSize'])
        
        # 计算总高度
        total_height = len(lines) * line_height
        
        # 垂直对齐计算
        start_y = textRect.y()
        rectVerticalAlign = rect.get("verticalAlign", "top")
        
        if rectVerticalAlign == "middle":
            start_y = textRect.y() + (textRect.height() - total_height) / 2
        elif rectVerticalAlign == "bottom":
            start_y = textRect.y() + textRect.height() - total_height
        
        # 确保起始Y位置不会小于文本区域顶部
        start_y = max(start_y, textRect.y())
        
        # 绘制每一行
        current_y = start_y
        rectTextAlign = rect.get("textAlign", "left")
        for i, line in enumerate(lines):
            # 避免绘制超出文本区域
            if current_y + line_height > textRect.y() + textRect.height() and (
                current_y + line_height - textRect.y() + textRect.height() <= 2
            ) :
                break
                
            # 计算每行的X坐标（水平对齐）
            line_width = fm.horizontalAdvance(line)
            current_x = textRect.x()
            
            if rectTextAlign == "center":
                current_x = textRect.x() + (textRect.width() - line_width) / 2
            elif rectTextAlign == "right":
                current_x = textRect.x() + textRect.width() - line_width
                
            # 确保绘制位置在有效范围内
            current_x = max(current_x, textRect.x())
            
            # 使用 ascent 精确定位基线，确保与CSS的vertical-align一致
            baseline_y = current_y + fm.ascent()
            
            # 确保baseline_y在有效范围内
            if baseline_y <= textRect.y() + textRect.height():
                painter.drawText(int(current_x), int(baseline_y), line)
                
            current_y += line_height
        
        # 恢复原始字体
        painter.setFont(original_font)
     # 绘制表格
    def drawTable(self, painter:QPainter,data):
        x2 =  data.get("x", 0)
        y2 =  data.get("y", 0)
        w =  data.get("width", 0)
        h =  data.get("height", 0)
        colWidths = data.get("colWidths", [])
        rowHeights = data.get("rowHeights", [])
        ths = data.get("ths", [])
        trs = data.get("trs", [])
        rotate = data.get("rotate", None)
        rotate_origin= data.get("rotateOrigin", None)
        position = data.get("position", "absolute")
        rect =  data.get("rect", None)
        self.setFont(painter,data)
        if rect is not None:
            rectX =  rect.get("x", 0)
            rectY =  rect.get("y", 0)
            rectW =  rect.get("width", 0)
            rectH =  rect.get("height", 0)
            if position == "relative":
                x2=x2+rectX
                y2=y2+rectY
                rectTextAlign = rect.get("textAlign", None)
                rectVerticalAlign = rect.get("verticalAlign", None)
             # 绘制外框
            self.drawWapperRect(painter,data)

        if position == "relative":
            x2, y2 = self.findRelativePoint(rectX, rectY, rectW, rectH, w,h,rectTextAlign, rectVerticalAlign)
       
        def drawBody(offsetX,offsetY):
            rows=[]
            if len(ths) > 0:
                rows.extend([ths])
            rows.extend(trs)
            for row in rows:
                for td in row:
                    border =  td.get("border", 0)
                    text = td.get("text", None)
                    image = td.get("image", None)
                    if text is None and image is None:
                        continue
                   
                    rowIndex,colIndex=td.get("rowIndex", 0),td.get("colIndex", 0)
                    colSpan,rowSpan=td.get("colSpan", 0),td.get("rowSpan", 0)
                    textAlign,verticalAlign=td.get("textAlign", 0),td.get("verticalAlign", 0)
                    tX,tW,tY,tH=0,0,0,0
                    for i in range(0,colIndex):
                        tX+=colWidths[i]
                    for i in range(colIndex,colIndex+colSpan):
                        tW+=colWidths[i]
                    for i in range(0,rowIndex):
                        tY+=rowHeights[i]
                    for i in range(rowIndex,rowIndex+rowSpan):
                        tH+=rowHeights[i]
                    drawX,drawY = tX+offsetX, tY+offsetY

                    if text is not None:
                        self.setFont(painter,td)
                        autoWrap,autoSize=td.get("autoWrap", True),td.get("autoSize", True)
                        textWrapData={
                            "text":text,
                            "bold":td.get("bold", data.get("bold", False)),
                            "overline":td.get("overline", data.get("overline", False)),
                            "italic":td.get("italic", data.get("italic", False)),
                            "strikeOut":td.get("strikeOut", data.get("strikeOut", False)),
                            "underline":td.get("underline", data.get("underline", False)),
                            "fontSize":td.get("fontSize", data.get("fontSize", 12)),
                            "colorRgba":td.get("colorRgba", data.get("colorRgba",  [0, 0, 0, 255])),
                            "fontFamilys":td.get("fontFamilys", data.get("fontFamilys",["Microsoft YaHei", "Arial"])),
                            "position":"relative",
                            "rect":{
                                "x": drawX,
                                "y": drawY,
                                "width": tW,
                                "height": tH,
                                "textAlign":textAlign,
                                "verticalAlign":verticalAlign,
                                "autoWrap": autoWrap,
                                "autoSize": autoSize,
                                "border": border,
                                "lineStyle": td.get("lineStyle", "solid"),
                                "display": True,
                                "colorRgba": data.get("borderColorRgba", [0, 0, 0, 255]),
                                "fillColorRgba": td.get("fillColorRgba", [255, 255, 255, 0]),
                            }
                        }
                        self.drawAutoWarpText(painter,textWrapData)
                        self.setFont(painter,data)
                    else:
                        imageData={
                            "type": "image",
                            "x": 0,
                            "y": 0,
                            "imagePath": td.get("imagePath"),
                            "position":"relative",
                            "rect":{
                                "x": drawX,
                                "y": drawY,
                                "width": tW,
                                "height": tH,
                                "textAlign":textAlign,
                                "verticalAlign":verticalAlign,
                                "border": border,
                                "display": True,
                                "colorRgba": data.get("borderColorRgba", [0, 0, 0, 255]),
                                "fillColorRgba": td.get("fillColorRgba", [255, 255, 255, 0]),
                            }
                        }
                        self.drawImage(painter, imageData)

        if rotate:
            painter.save()
            if rect:
                w= rectW 
                h= rectH 
                x1= rectX 
                y1= rectY 
            else:
                x1= x2
                y1= y2
            center_x, center_y=self.findRotationOrigPoint(x1, y1, w, h, rotate_origin)
            offsetX, offsetY = x2-x1, y2-y1
            painter.translate(center_x*self.mm_to_px, center_y*self.mm_to_px)
            if rotate==180:
                painter.rotate(rotate+0.0000000001)
            else:
                painter.rotate(rotate)
            drawX,drawY= self.findRotationDrawPoint(offsetX, offsetY, w, h, rotate_origin)
            drawBody(drawX, drawY)
            painter.restore()
        else:
            drawBody(x2,y2)
        
    # 绘制图片
    def drawImage(self, painter:QPainter,data:dict):
        imagePath = data.get("imagePath", None)
        imageData = data.get("imageData", None)
        imageRender = data.get("imageRender", None)
        # 判断图片数据
        if not any([imagePath, imageData, imageRender]):
            logging.error("No valid image source provided")
            return
        rotate = data.get("rotate", None)
        rotate_origin= data.get("rotateOrigin", None)
        x2 =  self.getPxValue(data.get("x", 0))
        y2 =  self.getPxValue(data.get("y", 0))
        w =  self.getPxValue(data.get("width", 0))
        h =  self.getPxValue(data.get("height", 0))
        position = data.get("position", "absolute")
        scaleType=data.get("scaleType",None)
        rect =  data.get("rect", None)
        if rect is not None:
            rectBorder =  self.getPxValue(rect.get("border", 0))
            rectX =  self.getPxValue(rect.get("x", 0))
            rectY =  self.getPxValue(rect.get("y", 0))
            rectW =  self.getPxValue(rect.get("width", 0))
            rectH =  self.getPxValue(rect.get("height", 0))
            if position == "relative":
                x2=x2+rectX
                y2=y2+rectY
                rectTextAlign = rect.get("textAlign", None)
                rectVerticalAlign = rect.get("verticalAlign", None)
             # 绘制外框
            self.drawWapperRect(painter,data)

        
        if imagePath:
           with requests.get(imagePath, stream=True) as response:
            if response.status_code == 200:
                image_data = QByteArray(response.content)
                img = QImage()
                try:
                    img.loadFromData(image_data)
                except:
                    del img
                
        if imageData:
            # 1. 提取 base64 数据（去除 data URL 前缀）
            if imageData.startswith('data:image/'):
                parts = imageData.split(',', 2)
                if len(parts) < 2:
                    logging.error("Invalid data URL format: missing comma")
                    return
                imageData = parts[1]

            # 2. 修复 URL 编码字符（%2B → +, %2F → /, %3D → =）
            # 这些字符在 HTML 中自动解码，但在 Python 中需手动还原
            imageData = imageData.replace('%2B', '+').replace('%2F', '/').replace('%3D', '=')

            # 3. Base64 解码
            image_data = QByteArray.fromBase64(imageData.encode('utf-8'))
            if image_data.isEmpty():
                logging.error("Base64 decoding resulted in empty data")
                return

            # 4. 加载到 QImage
            img = QImage()
            if not img.loadFromData(image_data):
                logging.error("Failed to load image from base64 data")
                return

        if imageRender:
            img = imageRender

        if not img.isNull():
            # 获取图片的默认宽高
            img_width, img_height = img.width(), img.height()
            w=w != None and w or img_width
            h=h != None and h or img_height
            if rect is not None:
                size = QSize(rectW-rectBorder*2, rectH-rectBorder*2)
                # 等比缩放
                if scaleType=="equalRate":
                    img = img.scaled(size, aspectRatioMode= Qt.AspectRatioMode.KeepAspectRatio)
                # 拉伸填满
                elif scaleType=="stretching":
                    img = img.scaled(size.width(), size.height())
            
            w, h = img.width(), img.height()
            
            if position == "relative":
                x2, y2 = self.findRelativePoint(rectX+rectBorder, rectY+rectBorder, rectW-rectBorder*2, rectH-rectBorder*2, w, h, rectTextAlign, rectVerticalAlign)

            if rotate:
                painter.save()
                if rect:
                    w= rectW
                    h= rectH
                    x1= rectX 
                    y1= rectY 
                else:
                    x1= x2
                    y1= y2
                center_x, center_y=self.findRotationOrigPoint(x1, y1, w, h, rotate_origin)
                offsetX, offsetY = x2-x1, y2-y1
                painter.translate(int(center_x), int(center_y))
                if rotate==180:
                    painter.rotate(rotate+0.0000000001)
                else:
                    painter.rotate(rotate)
                drawX,drawY= self.findRotationDrawPoint(offsetX, offsetY, w, h, rotate_origin)
                painter.drawImage(int(drawX), int(drawY),img)
                painter.restore()
            else:
                painter.drawImage(int(x2), int(y2), img)
    # 绘制SVG
    def drawSvg(self, painter:QPainter,data:dict):
        svgPath = data.get("svgPath")
        svgRenderer = data.get("svgRenderer",None)
        svgData = data.get("svgData")
        rotate = data.get("rotate", None)
        rotate_origin= data.get("rotateOrigin", None)
        x2 =  self.getPxValue(data.get("x", 0))
        y2 =  self.getPxValue(data.get("y", 0))
        w =  self.getPxValue(data.get("width", 0))
        h =  self.getPxValue(data.get("height", 0))
        position = data.get("position", "absolute")
        scaleType=data.get("scaleType",None)
        rect =  data.get("rect", None)
        if rect is not None:
            rectBorder =  self.getPxValue(rect.get("border", 0))
            rectX =  self.getPxValue(rect.get("x", 0))
            rectY =  self.getPxValue(rect.get("y", 0))
            rectW =  self.getPxValue(rect.get("width", 0))
            rectH =  self.getPxValue(rect.get("height", 0))
            if position == "relative":
                x2=x2+rectX
                y2=y2+rectY
                rectTextAlign = rect.get("textAlign", None)
                rectVerticalAlign = rect.get("verticalAlign", None)

             # 绘制外框
            self.drawWapperRect(painter,data)
            
        if svgRenderer == None:
            if svgData == None:
                svgData = open(svgPath, 'r').read()
            # 加载SVG
            svgRenderer = QSvgRenderer(QByteArray(svgData.encode("utf-8")))
        
        if svgRenderer.isValid():
            svgW=svgRenderer.defaultSize().width()
            svgH=svgRenderer.defaultSize().height()
            w = w if w else svgW
            h = h if h else svgH
            svg_size = svgRenderer.defaultSize()
            if rect is not None:
                size = QSize(rectW-rectBorder*2, rectH-rectBorder*2)
                # 等比缩放
                if scaleType=="equalRate":
                    svg_size.scale(size, aspectRatioMode= Qt.AspectRatioMode.KeepAspectRatio)
                # 拉伸填满
                elif scaleType=="stretching":
                    svg_size.scale(size.width(), size.height())

            w,h = svg_size.width(), svg_size.height()
            svgW,svgH=w,h

            if position == "relative":
                x2, y2 = self.findRelativePoint(rectX+rectBorder, rectY+rectBorder, rectW-rectBorder*2, rectH-rectBorder*2, w,h,rectTextAlign, rectVerticalAlign)

            if rotate:
                painter.save()
                if rect:
                    w= rectW
                    h= rectH
                    x1= rectX 
                    y1= rectY 
                else:
                    x1= x2
                    y1= y2

                center_x, center_y = self.findRotationOrigPoint(x1, y1, w, h, rotate_origin)
                offsetX, offsetY = x2-x1, y2-y1
                painter.translate(center_x, center_y)
                if rotate==180:
                    painter.rotate(rotate+0.0000000001)
                else:
                    painter.rotate(rotate)

                drawX,drawY= self.findRotationDrawPoint(offsetX, offsetY, w, h, rotate_origin)

                svgRenderer.render(painter, QRectF(drawX, drawY,svgW, svgH))

                painter.restore()
            else:
                svgRenderer.render(painter, QRectF(x2, y2, svgW, svgH))
    # 绘制条形码
    def drawBarCode(self, painter:QPainter, data:dict):
        x= data.get("x", 0)
        y= data.get("y", 0)
        # 条码类型
        barcode_type:str = data.get("barcodeType", "code128")
        format = data.get("format", "svg")
        # 条码内容  
        text = data.get("text", "")
        # 条码宽度
        moduleWidth =data.get("moduleWidth", 0.3)
        # 条码高度
        moduleHeight = data.get("moduleHeight", 5)
        position = data.get("position", "absolute")
        fontSize = data.get("fontSize", 2)
        # fontFamilys = data.get("fontFamilys", ["Microsoft YaHei", "Arial"])

        # 是否显示文本
        showText = data.get("showText", True)
        rect =  data.get("rect", None)
        if rect is not None:
            rectW =  self.getPxValue(rect.get("width", 0))
            rectH =  self.getPxValue(rect.get("height", 0))
            if position == "relative":
                x=x+rect.get("x", 0)
                y=y+rect.get("y", 0)
                rectTextAlign = rect.get("textAlign", None)
                rectVerticalAlign = rect.get("verticalAlign", None)
             # 绘制外框
            self.drawWapperRect(painter,data)

        rectObj = {
            "x": rect.get("x", 0),
            "y": rect.get("y", 0),
            "width": rect.get("width", 0),
            "height": rect.get("height", 0)
        }
        
        barcode = createBarcodeDrawing(barcode_type, value=text,fontSize=self.getPxValue(fontSize),
                        barWidth=moduleWidth*self.mm_to_px,barHeight=moduleHeight*self.mm_to_px,
                        fillColor=Color(0,0,0,1),humanReadable=showText)
        dom = minidom.parseString(barcode.asString(format="svg"))
        #预加载查看大小
        preRenderer = QSvgRenderer(QByteArray(dom.toxml().encode("utf-8")))
        pre_svg_size=preRenderer.defaultSize()
        scaleRate=1.0
        if pre_svg_size.width()>rectW or pre_svg_size.height()>rectH:
            scaleRate=rectW/pre_svg_size.width()
            #尺寸超出 重新在框内生成
            barcode = createBarcodeDrawing(barcode_type, value=text,fontSize=self.getPxValue(fontSize),
                        barWidth=scaleRate*moduleWidth*self.mm_to_px,barHeight=moduleHeight*self.mm_to_px,
                        fillColor=Color(0,0,0,1),humanReadable=showText)
            
            dom = minidom.parseString(barcode.asString(format="svg"))
        
        # 遍历所有元素
        for node in dom.getElementsByTagName('clipPath'):
            for rnode in node.getElementsByTagName('rect'):
                try:
                    rnode.setAttribute("style", "stroke: none; stroke-linecap: butt; stroke-width: 0; fill: none; fill-rule: evenodd;")
                except:
                    pass
        texts=[]
        for node in dom.getElementsByTagName('text'):
            node.setAttribute("style", "fill: transparent;")
            text_params = {
                "type": "text",
                "x": float(node.attributes.get('x').firstChild.data),
                "y": float(node.attributes.get('y').firstChild.data),
                "rotate": data.get("rotate", 0),
                "rotateOrigin": data.get("rotateOrigin", "center"),
                "fontFamilys": data.get("fontFamilys", [
                    "Microsoft YaHei",
                    "Arial"
                ]),
                "colorRgba": data.get("colorRgba", [0,0,0, 255]),
                "text": node.firstChild.data,
                "fontSize": data.get("fontSize", 3),
                "bold": data.get("bold", False),
                "rect":  rectObj
            }
            texts.append(text_params)

        barcode_svg=dom.toxml()
        # print(dom.toprettyxml(indent='', newl=''))
        renderer = QSvgRenderer(QByteArray(barcode_svg.encode("utf-8")))
        if renderer.isValid():
            svg_size=renderer.defaultSize()
            imgW = svg_size.width()
            imgH = svg_size.height()
            imgX = x
            imgY = y
            if position == "relative":
                w1,h1,w2,h2 =rectW/self.mm_to_px, rectH/self.mm_to_px, imgW/self.mm_to_px, imgH/self.mm_to_px
                imgX, imgY = self.findRelativePoint(x, y, w1, h1, w2, h2, rectTextAlign, rectVerticalAlign)
        if rect is None:
            rectObj={
                "x":x,
                "y":y,
                "w":imgW/self.mm_to_px,
                "h":imgH/self.mm_to_px
            }

        # 构造SVG数据
        if format == "image":
            image_params = {
                "type": "image",
                "x": imgX,
                "y": imgY,
                "rotate": data.get("rotate", 0),
                "rotateOrigin": data.get("rotateOrigin", "center"),
                "imageRender": self.svg_to_png(renderer,imgW,imgH),
                "rect":  rectObj
            }
                # 复用现有图像绘制逻辑
            self.drawImage(painter, image_params)
        else:
            svg_data = {
                "type": "svg",
                "x": imgX,
                "y": imgY,
                "rotate": data.get("rotate", 0),
                "rotateOrigin": data.get("rotateOrigin", "center"),
                "svgRenderer":renderer,
                "rect": rectObj
            }
            # 复用现有SVG绘制逻辑
            self.drawSvg(painter, svg_data)

        for text_params in texts:
            yOffet = 0
            if not (barcode_type.startswith('EAN') and barcode_type.startswith('UPC')):
               yOffet=0.3
            text_params.update({
                "x": text_params.get("x", 0)/self.mm_to_px+imgX,
                "y": imgH/self.mm_to_px-fontSize+imgY+yOffet,
                "fontSize": fontSize,
            })
            self.drawText(painter, text_params)
    # 绘制二维码
    def drawQrCode(self, painter:QPainter, data:dict):
        # 解析参数
        text=data.get("text", "")
        x=data.get("x", 0)
        y=data.get("y", 0)
        size=data.get("size", 0)
        position = data.get("position", "absolute")
        rect =  data.get("rect", None)

        if rect is not None:
            rectW =  self.getPxValue(rect.get("width", 0))
            rectH =  self.getPxValue(rect.get("height", 0))

            if position == "relative":
                x=x+rect.get("x", 0)
                y=y+rect.get("y", 0)
                rectTextAlign = rect.get("textAlign", None)
                rectVerticalAlign = rect.get("verticalAlign", None)

             # 绘制外框
            self.drawWapperRect(painter,data)

        qr_code:qr.QrCodeWidget=qr.QrCodeWidget(text)
        colorRgba = data.get("colorRgba", None)
        fillColorRgba = data.get("fillColorRgba", None)
        if colorRgba:
            qr_code.barFillColor=Color(colorRgba[0],colorRgba[1],colorRgba[2],colorRgba[3]/255)
        if fillColorRgba:
            qr_code.barStrokeColor=Color(fillColorRgba[0],fillColorRgba[1],fillColorRgba[2],fillColorRgba[3]/255)

        bounds = qr_code.getBounds()
        w=bounds[2]-bounds[0]
        h=bounds[3]-bounds[1]
        qr_size = self.getPxValue(size)
        d = Drawing(qr_size,qr_size,transform=[qr_size/w,0,0,qr_size/h,0,0])
        d.add(qr_code)
        svg_data=d.asString(format="svg")
        dom = minidom.parseString(svg_data)
        # 遍历所有元素
        for node in dom.getElementsByTagName('clipPath'):
            for rnode in node.getElementsByTagName('rect'):
                try:
                    rnode.setAttribute("style", "stroke: none; stroke-linecap: butt; stroke-width: 0; fill: none; fill-rule: evenodd;")
                except:
                    pass
        logo_path = data.get("logoPath",None)  # 从参数获取logo路径
        logo_data = data.get("logoData",None)  # base64编码的logo数据
        if logo_path or logo_data:
            # 计算插入位置和大小（占二维码1/5大小）
            logo_size = qr_size // 8
            logo_x = (qr_size - logo_size) / 2
            logo_y = (qr_size - logo_size) / 2
            if logo_path:
                try:
                     # 网络图片
                    response = requests.get(logo_path)
                    if response.status_code == 200:
                        image_data = response.content
                        base64_data = base64.b64encode(image_data).decode("utf-8")
                        mime_type = "image/png"  # 默认类型
                        if logo_path.lower().endswith(".jpg") or logo_path.lower().endswith(".jpeg"):
                            mime_type = "image/jpeg"
                        elif logo_path.lower().endswith(".gif"):
                            mime_type = "image/gif"
                        elif logo_path.lower().endswith(".svg"):
                            mime_type = "image/svg+xml"
                    else:
                        logging.error(f"Failed to download logo: {logo_data}")
                except Exception as e:
                    print(e)
                    logging.error(f"Failed to download logo: {e}")
               

            logo_data = f"data:{mime_type};base64,{base64_data}"
            # 创建<image>元素
            svg_root = dom.documentElement
            rect_elem = dom.createElement("rect")
            rect_elem.setAttribute("x", str(logo_x-3))
            rect_elem.setAttribute("y", str(logo_y-3))
            rect_elem.setAttribute("width", str(logo_size+6))
            rect_elem.setAttribute("height", str(logo_size+6))
            rect_elem.setAttribute("style", "fill: #ffffff;")

            image_elem = dom.createElement("image")
            image_elem.setAttribute("x", str(logo_x))
            image_elem.setAttribute("y", str(logo_y))
            image_elem.setAttribute("transform", f"scale(1,-1) translate(0,-{qr_size})")  # 翻转Y轴方向
            image_elem.setAttribute("width", str(logo_size))
            image_elem.setAttribute("height", str(logo_size))
            # image_elem.setAttribute("href", logo_path)  # 支持base64/dataURL
            image_elem.setAttributeNS("http://www.w3.org/1999/xlink", "xlink:href", logo_data)


            # 添加到SVG中（插入到所有元素之后）
            first_group = svg_root.getElementsByTagName("g")[0]
            first_group.appendChild(rect_elem)
            first_group.appendChild(image_elem)
        svg_data=dom.toxml()
        # print(dom.toprettyxml(indent='', newl=''))
        renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))

        if renderer.isValid():
            imgW = qr_size
            imgH = qr_size
            imgX = x
            imgY = y
            if position == "relative":
                w1,w2,h1,h2 =rectW/self.mm_to_px, rectH/self.mm_to_px, imgW/self.mm_to_px, imgH/self.mm_to_px
                imgX, imgY = self.findRelativePoint(x, y, w1, w2, h1, h2, rectTextAlign, rectVerticalAlign)
            if rect is None:
                rectObj = {
                    "x": imgX,
                    "y": imgY,
                    "width": size,
                    "height": size
                }
            else:
                rectObj = {
                    "x": rect.get("x", 0),
                    "y": rect.get("y", 0),
                    "width": rect.get("width", 0),
                    "height": rect.get("height", 0)
                }
            # 构造svgData参数
            svg_params = {
                "type": "svg",
                "x": imgX,
                "y": imgY,
                "width": data.get("size", 50),
                "height": data.get("size", 50),
                "rotate": data.get("rotate", 0),
                "rotateOrigin": data.get("rotateOrigin", "center"),
                "svgRenderer":renderer,
                "rect": rectObj
            }
            
            # 复用现有svg绘制逻辑
            self.drawSvg(painter, svg_params)
    # 绘制外包矩形
    def drawWapperRect(self, painter:QPainter,data):
        rect =  data.get("rect", None)
        if rect.get("display", False):
            rect_params ={
                "x": rect.get("x", 0),
                "y": rect.get("y", 0),
                "width": rect.get("width", 0),
                "height": rect.get("height", 0),
                "border" : rect.get("border", 0.3),
                "colorRgba" : rect.get("colorRgba", None),
                "fillColorRgba" : rect.get("fillColorRgba", None),
                "rotate":data.get("rotate", None),
                "rotateOrigin":data.get("rotateOrigin", None),
                "lineStyle": rect.get("lineStyle", "solid"),
            }
            self.drawRect(painter,rect_params)
    #文字自动换行
    def wrapText(self, text, max_width, painter):
        fm = QFontMetricsF(painter.font())
        wrapped_lines = []
        current_line = ""
        current_width = 0
        
        # 按字符遍历文本
        for char in text:
            char_str = char if isinstance(char, str) else str(char)
            # char_width = painter.fontMetrics().horizontalAdvance(char_str)
            char_width = fm.horizontalAdvance(char_str)
            # 当前行宽度检查
            if current_width + char_width <= max_width:
                current_line += char
                current_width += char_width
            else:
                wrapped_lines.append(current_line)
                current_line = char
                current_width = char_width
        
        if current_line:
            wrapped_lines.append(current_line)
        
        return wrapped_lines
     # 文本截断处理
    def textTruncate(self, painter:QPainter,data,rect):
        # 获取矩形宽高
        rectW = self.getPxValue(rect.get("width", 0))
        rectH = self.getPxValue(rect.get("height", 0))

        # 设置字体以确保正确计算文本大小
        self.setFont(painter, data)
        text = data.get("text", "")
        text_lines = text.split('\n') if text else ['']
        truncated_lines = []
        total_height = 0

        fm = painter.fontMetrics()

        for line in text_lines:
            current_line = ""
            current_width = 0

            for char in line:
                char_str = char if isinstance(char, str) else str(char)
                char_advance = fm.horizontalAdvance(char_str)

                if current_width + char_advance <= rectW:
                    current_line += char
                    current_width += char_advance
                else:
                    break  # 当前行已满

            # 如果当前行有内容且总高度未超限，则保留该行
            if current_line:
                truncated_lines.append(current_line)
                total_height += fm.lineSpacing()
                if total_height >= rectH:
                    break  # 超出高度，停止处理
        # 拼接为带有换行符的字符串
        text = "\n".join(truncated_lines)     
        return text
    #自动缩小字体
    def textAutoSize(self, painter:QPainter,data):
        text = data.get("text", "")
        if text is None:
            return
        rect =  data.get("rect", None)
        rectW =  self.getPxValue(rect.get("width", 0))
        rectH =  self.getPxValue(rect.get("height", 0))
        min_font_size = 17  # 最小字号限制
        # 获取当前字体和行高
        font = painter.font()
        original_font_size = font.pixelSize()
        current_font_size = original_font_size
        while current_font_size >= min_font_size:
            # 设置当前字号
            font.setPixelSize(int(current_font_size))
            painter.setFont(font)
            text_rect = painter.fontMetrics().boundingRect(text)
            w= text_rect.width()
            h= text_rect.height()
            if w <= rectW and h <= rectH:
                break
            # 减小字号继续尝试
            current_font_size -= 1  # 每次减小1像素
        # 应用最终字号
        font.setPixelSize(max(current_font_size, min_font_size))
        painter.setFont(font)

    # 查找相对坐标
    def findRelativePoint(self, x, y, w1, h1, w2, h2, rectTextAlign, rectVerticalAlign):
        if rectTextAlign=="right":
            relativeX = x + (w1-w2)
        elif rectTextAlign=="center":
            relativeX = x + (w1-w2)/2
        elif rectTextAlign=="left":
            relativeX = x 
            
        if rectVerticalAlign=="bottom":
            relativeY = y + (h1-h2)
        elif rectVerticalAlign=="middle":
            relativeY = y + (h1-h2)/2
        elif rectVerticalAlign=="top":
            relativeY = y 
        return relativeX, relativeY
    # 查找旋转原点
    def findRotationOrigPoint(self, x, y, w, h, rotate_origin):
        # 根据旋转原点计算中心点
        if rotate_origin == "top-left":
            center_x, center_y = x, y
        elif rotate_origin == "top-right":
            center_x, center_y = x + w, y
        elif rotate_origin == "bottom-left":
            center_x, center_y = x, y + h
        elif rotate_origin == "bottom-right":
            center_x, center_y = x + w, y + h
        else:  # 默认中心点
            center_x, center_y = x + w/2, y + h/2
        return center_x, center_y
    # 查找绘制点
    def findRotationDrawPoint(self, offsetX, offsetY, w, h, rotate_origin):
        # 根据原点类型调整绘制位置
        if rotate_origin == "top-left":
            return int(offsetX), int(offsetY)
        elif rotate_origin == "top-right":
            return int(-w+offsetX), int(offsetY)
        elif rotate_origin == "bottom-left":
            return int(offsetX), int(-h+offsetY)
        elif rotate_origin == "bottom-right":
            return int(-w+offsetX), int(-h+offsetY)
        else:  # 中心点
            return int(-w/2+offsetX), int(-h/2+offsetY)

    # 获取像素值
    def getPxValue(self, value):
        if(self.unit  == "mm"):
            return int(self.mm_to_px*value)
        return value
    #字体设置公用方法
    def setFont(self, painter:QPainter,data):
        bold=data.get("bold", False)
        italic=data.get("italic", False)
        underline=data.get("underline", False)
        overline=data.get("overline", False)
        strikeOut=data.get("strikeOut", False)
        letterSpacing = data.get("letterSpacing", 0)
        wordSpacing = data.get("wordSpacing", 0)
        lineHeight = data.get("lineHeight", 0)
        font = painter.font()
        if data.get("fontSize", None):
            fontSize = self.getPxValue(data.get("fontSize", 12))
            font.setPixelSize(fontSize)
        fontFamilys = data.get("fontFamilys", ["Microsoft YaHei", "Arial"])
        is_microsoft_yahei = "Microsoft YaHei" in fontFamilys
        colorRgba = data.get("colorRgba", None)
        rect = data.get("rect", None)
        fillColorRgba = None
        if rect:
            fillColorRgba = rect.get("fillColorRgba", None)

        if colorRgba:
            if self.isColor or fillColorRgba is None:
               color = QColor(colorRgba[0], colorRgba[1], colorRgba[2], colorRgba[3])
            else: 
                Y = 0.299*colorRgba[0] + 0.587*colorRgba[1] + 0.114*colorRgba[2]
                if Y and Y > 128:
                    color = QColor(255, 255, 255, 255)
                else:
                    color = QColor(0, 0, 0, 255)
            painter.setPen(QPen(color, 1))
        else:
            color = QColor(0, 0, 0, 255)
            painter.setPen(QPen(color, 1))
        font.setFamilies(fontFamilys)
        font.setBold(bold)
        font.setItalic(italic)
        font.setStrikeOut(strikeOut)
        font.setUnderline(underline)
        font.setOverline(overline)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, float(letterSpacing))
        font.setWordSpacing(float(wordSpacing))
        try:
            if is_microsoft_yahei:
                font.setStyleHint(QFont.StyleHint.AnyStyle, QFont.StyleStrategy.PreferTypoLineMetrics)
            else:
                font.setStyleHint(QFont.StyleHint.AnyStyle, QFont.StyleStrategy.PreferTypoLineMetrics)
        except Exception as e:
            pass

        painter.setFont(font)

    def svg_to_png(self, renderer: QSvgRenderer, width, height) -> QImage:
        scale_factor = 2  # 放大倍数，可调整为 3 或更高
        large_image = QImage(int(width * scale_factor), int(height * scale_factor), QImage.Format.Format_ARGB32)
        large_image.fill(0x00000000)

        painter = QPainter(large_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        renderer.render(painter, QRectF(0, 0, int(width * scale_factor), int(height * scale_factor)))
        painter.end()

        return large_image.scaled(int(width), int(height), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)