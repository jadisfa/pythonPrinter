import sys,math
import logging
import requests,logging
from globals import temp_dir
from escpos.printer import Usb, Dummy
import usb.core

from io import BytesIO
from PIL import Image
import base64

# 打印指令举例
# rowText={"type":"text", "text":"14345678", "font":"A", "align":"center", "bold":True, "underline":True, "double_height":True, "double_width":True，"character":"CHINA", "inverse_printing":False, "upside_down":False}
# rowImage={"type":"image", "src":"http://image.dianplus.cn/logo.png",  "align":"center", "width":200, "height":200}
# rowTable={
#     "type":"table", 
#     "align":"center", "width":200,
#     "header_style" : {
#         "font": "A",
#         "bold": True,
#         "underline": False,
#         "double_height": True,
#         "double_width": False,"character":"CHINA", "inverse_printing":False, "upside_down":False
#     },
#     "row_style" : {
#         "font": "B",
#         "bold": False,
#         "underline": False,
#         "double_height": False,
#         "double_width": False,"character":"CHINA", "inverse_printing":False, "upside_down":False
#     },
#     "headers":["品名","数量","价格"],
#     "rows":[{"Item 1", "2", "0.00"},{"Item 2", "2", "0.00"},{"Item 3", "2", "0.00"}],
# }
# rowBarcode={"type":"barcode", "code":"14345678", "align":"center", "width":200, "height":50}
# rowQrCode={"type":"qrcode", "text":"http://www.example.com", "align":"center", "size":200}
# rowBr={"type":"br"}
# rowCut={"type":"cut"}
# rowPartialCut={"type":"partial_cut"}
# rowBox={"type":"box"}
# rows=[rowText, rowImage, rowTable, rowBarcode, rowQrCode,rowBr,rowCut,rowBox]
# options = {"line_spacing":30, "feed_paper":1, "print_speed":2, "print_density":10, }
def validate_params(required_params: list):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            for param in required_params:
                if param not in kwargs and param not in args[1:]:
                    raise ValueError(f"Missing required parameter: '{param}'")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

class EscPosPrinter():
    def __init__(self,print_cmd:dict,options:dict):
        self.printer_name = options.get("printerName")
        self.options = options
        self.print_cmds = print_cmd.get("rows",[])
  
    def render(self):
        settings = self.options
        
        self.dummy = Dummy()
        self.paper_width = settings.get("paper_width", 80) 
        self.dummy.print_and_feed(settings.get("printSpeed",1))
        self.set_line_spacing(settings.get("lineSpacing",3))  # 设置行间距
        printCount=settings.get('printCount', 1)
        for i in range(printCount):
            for row in self.print_cmds:
                try:
                    if "type" not in row:
                        raise ValueError("Print command missing 'type' field")
                    
                    if row["type"] == "text":
                        self.add_text(text= row.get("text"),style= row.get("style",{}))
                    elif row["type"] == "text_grid":
                        self.add_text_grid(
                            width=row.get("width", 42),
                            style=row.get("style", {}),
                            cells=row.get("cells", [])
                        )
                    elif row["type"] == "image_grid":
                        self.add_image_grid(
                            width=row.get("width", 44),
                            style=row.get("style", {}),
                            cells=row.get("cells", []),
                            imageMode=row.get("imageMode","bitImageColumn")
                        )
                    elif row["type"] == "table":  
                        self.add_table(
                            headers=row.get("headers",[]),
                            rows=row.get("rows",[]),
                            width=row.get("width", 42),
                            style=row.get("style", {}),
                            header_style=row.get("header_style", {}),
                            row_style=row.get("row_style", {}),
                            header_cell_styles=row.get("header_cell_styles",[]),
                            row_cell_styles=row.get("row_cell_styles",[]),
                        )
                    elif row["type"] == "image":
                        self.add_image(src=row["src"],style=row.get("style",{}),imageMode=row.get("imageMode","bitImageRaster"))
                    elif row["type"] == "barcode":  
                        self.add_barcode(code=row["code"],
                                         style = row.get("style",{}),
                                         format = row.get("format","EAN14"),
                                         showText =row.get("showText",False),
                                         width = row.get("width",3),
                                         height = row.get("height",64))
                    elif row["type"] == "qrcode":  
                        self.add_qr_code(text=row["text"], size = row.get("size",3), style = row.get("style",{}), )
                    elif row["type"] == "cut":  
                        self.cut()
                    elif row["type"] == "partial_cut":  
                        self.partial_cut()
                    elif row["type"] == "box":  
                        self.moneyBox()
                    elif row["type"] == "br":  
                        self.br(lineSpacing=row.get("line_spacing",10))
                    else:
                        raise ValueError("Print command 'type'"+ row["type"] + "unsupport")
                except Exception as e:
                    self.add_text(text=str(e), style={})
                    logging.error(e)

        self.reset_printer()
        
        # 在发送前添加
        if sys.platform== "Windows" or sys.platform== "win" or sys.platform == 'win32':
            import win32print
            if not self.printer_name:
                    raise ValueError("Missing printerName")
            hprinter = win32print.OpenPrinter(self.printer_name)
          
            if win32print.GetPrinter(hprinter, 2)['Status'] != 0:
                logging.error("打印机状态异常")
            try:
                win32print.StartDocPrinter(hprinter, 1, ("Receipt", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hprinter)
                    win32print.WritePrinter(hprinter, bytes(self.dummy.output))
                    win32print.EndPagePrinter(hprinter)
                finally:
                    win32print.EndDocPrinter(hprinter)
            finally:
                win32print.ClosePrinter(hprinter)
        elif sys.platform == "darwin":
            try:
                vendorId:str = self.options.get("vendorId")
                productId:str = self.options.get("productId")
                if not vendorId or not productId:
                    raise ValueError("Missing USB printer IDs (vendorId/productId)")
                # vendorId和productId是打印机的USB ID，可以通过system_profiler SPUSBDataType | grep -A 11 "Printer"查看
                # vendorId和productId是16进制字符串，需要转换成整数
                vendorId = int(vendorId,16)
                productId = int(productId,16)
                device = usb.core.find(idVendor=vendorId, idProduct=productId)
                if device is None:
                    raise ValueError("设备未找到，请检查 vendorId 和 productId")
                # 获取配置和接口
                cfg = device.get_active_configuration()
                interface_number = cfg[(0, 0)].bInterfaceNumber
                interface = usb.util.find_descriptor(cfg, bInterfaceNumber=interface_number)
                # 枚举端点
                endpoint_in = None
                endpoint_out = None
                for endpoint in interface:
                    if usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_IN:
                        endpoint_in = endpoint.bEndpointAddress
                    elif usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                        endpoint_out = endpoint.bEndpointAddress

                p=Usb(vendorId,productId, in_ep=endpoint_in, out_ep=endpoint_out)
                p.open()
                p.hw('INIT')
                print("=============================================================================")
                p._raw(self.dummy.output)
                p.close()
            except Exception as e:
                print(e)
                raise
        else:
            # Linux 打印方案
            with open(f"/dev/usb/lp0", "wb") as printer:
                printer.write(self.dummy.output)
                
    def get_style(self,style:dict):
        """样式提前器"""
        return {
            "align": style.get("align","center"),
            "character": style.get("character",'CHINA'),
            "font": style.get("font","A"),
            "bold": style.get("bold",False),
            "underline": style.get("underline",False),
            "double_height": style.get("double_height",False),
            "double_width": style.get("double_width",False),
            "inverse_printing": style.get("inverse_printing",False),
            "upside_down": style.get("upside_down",False),
        }
        
    def set_style(self,align='left',character='CHINA',font='A',
                bold=False, underline=False, 
                double_height=False, double_width=False,
                inverse_printing=False,upside_down=False):
        """样式设置统一方法"""
        self.set_font(font)
        self.set_character_set(character)  # 默认使用中文字符集
        if align == 'center':
            self.center_align()
        elif align == 'right':
            self.right_align()
        else:
            self.left_align()
        self.set_bold(bold)
        self.set_underline(underline)
        
        self.set_inverse_printing(inverse_printing)  # 设置反白打印（黑白反转）
        self.set_upside_down(upside_down)  # 设置倒置打印

        if double_height and double_width:
            self.set_double_height()
            self.set_double_width()
        elif double_height:
            self.set_double_height()
        elif double_width:
            self.set_double_width()
        else:
            self.set_normal_size()
            
    def calc_display_len(self,text):
        """文本长度计算"""
        return sum(2 if ord(char) > 147 else 1 for char in text)
    
    @validate_params(["text"])
    def add_text(self, text:str, style={}):
        """文本"""
        self.set_style(**self.get_style(style))
        self.dummy.textln(text)
        self.left_align()  # 恢复左对齐
        
    @validate_params(["cells"])
    def add_text_grid(self,width=42, style={}, cells=[]):
        """左右文本"""
        # 确定总宽度
        width = width or self.paper_width
        self.set_style(**self.get_style(style))
        spacing = style.get("spacing", 0)
        rows=[]
        row=[]
        row_width=0

        spacing_cell={
            "text": ' '*spacing,
            "width": spacing
        }

        for cell in cells:
            cell_width=cell.get("width", 0)

            if row_width>0 and (row_width+spacing) <= width:
                row_width += spacing 
                row.append(spacing_cell)

            if (row_width+cell_width) > width:
                row_width = 0
                rows.append(row)
                row=[]
            row_width += cell_width
            row.append(cell)

        if len(row)>0:
            rows.append(row)

        def get_cell_text(cell):
            align = cell.get("align", "center")
            cell_width = cell.get("width", 0)
            cell_text=cell.get("text", "")
            cell_text_width = self.calc_display_len(cell_text)
            # 左文本对齐处理
            if align == "left":
                rightPadding = max(0, cell_width - cell_text_width)
                content = cell_text + ' ' * rightPadding
            elif align == "center":
                leftPadding = max(0, (cell_width - cell_text_width)//2)
                rightPadding = max(0, cell_width-cell_text_width-leftPadding)
                content = ' ' * leftPadding + cell_text + ' ' * rightPadding
            elif align == "right":
                leftPadding = max(0, cell_width - cell_text_width)
                content = ' ' * leftPadding + cell_text
            return content

        for row in rows:
            row_text = ''.join([get_cell_text(cell) for cell in row])
            row_width = self.calc_display_len(row_text)
            row_text = row_text+' '*(width-row_width)
            self.dummy.textln(row_text)

         # 使用左对齐模式打印（实际布局通过空格控制）
        self.left_align()

    @validate_params(["cells"])
    def add_image_grid(self, width=42, style={}, cells=[],imageMode="bitImageColumn"):
        """左右图片"""
        # 确定总宽度
        width = width or self.paper_width
        self.set_style(**self.get_style(style))
        spacing = style.get("spacing", 0)
        align = style.get("align", "center")
        total_width = int(width * 14)
        spacing_width = int(spacing * 14)
        spacing_cell={
            "type": "text",
            "image":{
                "width": spacing_width,
                "height": spacing_width
            }
        }
        # 加载左右图片
        def load_image(src):
            if src.startswith('http') or src.startswith('data:image'):
                response = requests.get(src) if src.startswith('http') else None
                data = base64.b64decode(src.split(',', 1)[1]) if src.startswith('data:image') else response.content
                return Image.open(BytesIO(data)).convert("RGBA")
            else:
                return Image.open(src).convert("RGBA")
            
        for cell in cells:
            cell.update({"image": load_image(cell.get("src",""))})
        rows=[]
        row=[]
        row_width=0
        for cell in cells:
            cell_width=cell.get("width", 0)
            if row_width>0 and (row_width+spacing) <= width:
                row_width += spacing 
                row.append(spacing_cell)

            if (row_width+cell_width) > width:
                row_width = 0
                rows.append(row)
                row=[]
            row_width += cell_width
            row.append(cell)

        if len(row)>0:
            rows.append(row)

        def get_cell_img_pos(cell,offsetX,max_height):
            align = cell.get("align", "center")
            cell_width = cell.get("width", 0)*14
            image_width = cell.get("image",{}).width
            image_height = cell.get("image",{}).height
            # 图对齐处理
            if align == "left":
                pos = (0+int(offsetX), 0)
            elif align == "center":
                pos = (int(offsetX+(cell_width-image_width)/2), int((max_height - image_height) / 2))
            elif align == "right":
                pos = (int(offsetX+(cell_width-image_width)), int(max_height - image_height))
            return pos
        
        for row in rows:
            max_height=0
            for cell in row:
                if cell.get("type","image")=="text":
                    max_height = max(max_height, cell.get("image").get("height"))
                    continue
                img:Image=cell.get("image")
                cell_width = cell.get("width", 0)*14
                if img.width > cell_width:
                    # 调整图片大小，按宽度等比缩小
                    scale_ratio = cell_width / img.width
                    new_height = int(img.height * scale_ratio)
                    img = img.resize((cell_width, new_height))
                    cell.update({"image": img})
                max_height = max(max_height, img.height)
            # 创建新图（背景白色），大小足够容纳两张图片
            new_img = Image.new('RGBA', (total_width, max_height), (255, 255, 255,0))
            offset_x=0
            for cell in row:
                if cell.get("type")=="text":
                    offset_x+=cell.get("width",0)*14
                    continue
                img:Image=cell.get("image")
                pos= get_cell_img_pos(cell,offset_x,max_height)
                new_img.paste(img,pos)
                offset_x+=cell.get("width",0)*14

            # 打印拼接后的图像
            self.dummy.image(new_img, center=(align == "center"), impl=imageMode)
            # 恢复左对齐
            self.left_align()
            # 恢复行间距
            self.set_line_spacing(self.options.get("lineSpacing",3))  # 设置行间距
    @validate_params(["headers","rows","width","header_cell_styles","row_cell_styles"])
    def add_table(self, headers=[], rows=[], width=42,
                    style={}, header_style={}, 
                    row_style={},
                    header_cell_styles=[], 
                    row_cell_styles=[] ):
        """表格"""
        self.set_style(**self.get_style(style))
        def split_line(cols=[],cellStyles=[],style={}):
            wrapBottom = style.get("wrapBottom",True)  
            # 自适应单元格
            deep=1
            for index ,cellStyle in enumerate(cellStyles):
                col = cols[index]
                # 计算文本列宽
                actWidth = self.calc_display_len(col)
                # 实际列宽比列宽ceil向上取整
                needRow = math.ceil(actWidth/cellStyle.get("width",5))
                if deep<needRow:
                    deep=needRow
            lines = []
            for i in range(deep):
                columns=[]
                for col in enumerate(cols):
                    columns.append('')
                lines.append(columns)

            for index ,cellStyle in enumerate(cellStyles):
                col = cols[index]
                col_width = cellStyle.get("width",5)
                # 计算文本列宽
                actWidth = self.calc_display_len(col)
                # 计算和格子的差值
                diffWidth = col_width - actWidth
                # 格子够
                if diffWidth>0:
                    if wrapBottom:
                        lines[deep-1][index]=col
                    else:
                         lines[0][index]=col
                else:
                    # 格子不够 按 header_deep 拆行
                    cursor = ''
                    splitCols=[]
                    for c in col:
                        if self.calc_display_len(cursor+c) >= col_width:
                            splitCols.append(cursor)
                            cursor = '' + c
                        else:
                            cursor += c
                    if cursor:
                        splitCols.append(cursor)
                        
                    diffDeep = 0
                    if wrapBottom:
                        diffDeep = deep-len(splitCols)
                        
                    for sIndex,splitCol in enumerate(splitCols) :
                        lines[sIndex][diffDeep+index]= splitCol 

                    for i in range(len(splitCols),deep):
                        lines[i]+=' ' * col_width   
                        
            printLines=[]      
            for i ,line in enumerate(lines):
                printLine=''
                for j ,col in enumerate(line):
                    col_width = cellStyles[j].get("width",5)
                    align = cellStyles[j].get("align","center")
                    # 计算文本列宽
                    actWidth = self.calc_display_len(col)
                    # # 计算和格子的差值
                    diffWidth=col_width - actWidth
                    if align == "left":
                        col = col+' ' * diffWidth 
                    elif align == "center":
                        half = diffWidth//2
                        col = ' ' * half + col+' ' * (diffWidth-half) 
                    elif align == "right":
                        col = ' ' * diffWidth + col
                    printLine+=col
                printLines.append(printLine)
                  
            return printLines
        split_style=header_style.get("split",{})
        split_line_spacing=split_style.get("line_spacing",5)
        shows=split_style.get("shows",[False,True,False])
        if shows[0]:
            self.dummy.line_spacing(split_line_spacing)
            self.set_style(**self.get_style(split_style))
            self.dummy.textln(split_style.get("char","-") * width)
        # 处理成和表格一致的对齐
        headerAlign = header_style.get("align","center")
        header_style.update({"align":style.get("align","center")})
        # 应用表头样式
        self.set_style(**self.get_style(header_style))
        header_style.update({"align":headerAlign})
        # 表头
        header_lines = split_line(headers,header_cell_styles,style=header_style)
        # 数据打印
        for header_line in header_lines:
            self.dummy.textln(header_line)
        row_split_style=row_style.get("split",{})
        row_line_spacing=row_style.get("line_spacing",5)

        if shows[1]:
            self.set_style(**self.get_style(split_style))
            self.dummy.textln(split_style.get("char","-") * width)
            self.br(row_line_spacing)

        rowAlign = row_style.get("align","center")
        row_style.update({"align":style.get("align","center")})
         # 应用数据行样式
        self.set_style(**self.get_style(row_style))
        self.dummy.line_spacing(row_line_spacing)
        row_style.update({"align":rowAlign})
        # 构建数据行
        for index,row in enumerate(rows):
            # 数据行
            row_lines = split_line(row,row_cell_styles,style=row_style)
            # 打印数据行
            for row_line in row_lines:
                self.dummy.textln(row_line)
                if row_split_style.get("show",False):
                    if index<len(rows)-1:
                        self.dummy.textln(row_split_style.get("char","-") * width)
                        self.br(row_line_spacing)
                else:
                    self.br(row_line_spacing)
        if shows[2]:
            self.set_style(**self.get_style(split_style))
            self.dummy.line_spacing(split_line_spacing)
            # 分割线
            self.dummy.textln(split_style.get("char","-") * width)
        # 恢复
        self.dummy.line_spacing(self.options.get("lineSpacing",30))
    
    @validate_params(["src"])  
    def add_image(self, src="",style={}, imageMode="bitImageRaster"):
        """支持打印网络图片和本地图片"""
        try:
            self.set_style(**self.get_style(style))
            align=style.get("align","center")
            width=style.get("width",None)
            height=style.get("height",None)
            # 处理网络图片
            if src.startswith('http://') or src.startswith('https://'):
                response = requests.get(src)
                response.raise_for_status()  # 检查HTTP状态码
                # 使用BytesIO处理图片数据
                response = requests.get(src, timeout=5)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content)).copy()
                 # 自定义尺寸适配
                if width or height:
                    width,height=int(width),int(height)
                    img = img.resize((width or img.width, height or img.height))
                # 打印网络图片
                self.dummy.image(img, center=(align=="center"),impl=imageMode)
            elif src.startswith('data:image/'):
                # 处理base64图片数据
                if src.startswith('data:'):
                    # 找到base64数据的实际开始位置
                    comma_index = src.find(',')
                    if comma_index != -1:
                        src = src[comma_index + 1:]
                image_data = base64.b64decode(src)
                img = Image.open(BytesIO(image_data)).copy()
                if width or height:
                    width, height = int(width), int(height)
                    img = img.resize((width or img.width, height or img.height))
                self.dummy.image(img, center=(align == "center"), impl=imageMode)
            else:
                # 处理本地图片
                img = Image.open(src).copy()
                if width or height:
                    width,height=int(width),int(height)
                    img = img.resize((width or img.width, height or img.height))
                self.dummy.image(img, center=(align=="center"),impl=imageMode)
        except requests.exceptions.RequestException as e:
            logging.error(f"图片下载失败: {e}")
        except Exception as e:
            logging.error(f"图片打印失败: {e}")
        # 恢复行间距
        self.set_line_spacing(self.options.get("lineSpacing",3))  # 设置行间距
            
    @validate_params(["code"])
    def add_barcode(self, code="1",  style={}, format="EAN14", showText=True, width=3,height=64):
        """条形码"""
        self.set_style(**self.get_style(style))
        self.dummy.barcode(code, bc=format, align_ct=(style.get("align","center")=="center"), height=height, width=width,check=showText)
    
    @validate_params(["text"])
    def add_qr_code(self, text="1",size=3, style={}):
        """二维码"""
        self.dummy.qr(text, size=size,center=(style.get("align","center")=="center"))
        pass
    
    #================以下是基础指令================#
    def set_paper_width(self):
        """直接发送ESC/POS命令设置纸张宽度"""
        # ESC ( C 命令设置纸张宽度
        # 格式: ESC ( C nL nH
        width_mm = self.options.get("paperWidth",58)  # 58mm纸张
        nL = width_mm % 256
        nH = width_mm // 256
        self.dummy._raw(bytes([0x1B, 0x28, 0x43, 0x02, nL, nH]))
    
    def set_font(self, font="A"):
        """设置字体"""
        if font == "A":
            self.dummy.set(font="a")
        elif font == "B":
            self.dummy.set(font="b")
        pass
    def set_character_set(self, charset="USA"):
        """设置字符集"""
        # self.dummy.charcode(charset)
        pass
    def set_line_spacing(self, spacing=30):
        self.dummy.line_spacing(spacing)
    def reset_printer(self):
        """重置打印机到初始状态"""
        self.dummy.line_spacing(self.options.get("lineSpacing",30))
        self.left_align() 
    def set_inverse_printing(self, enable=True):
         self.dummy.set(invert=enable)
    def set_upside_down(self, enable=True):
         self.dummy.set(flip=enable)
    def center_align(self):
        """设置居中对齐"""
        self.dummy.set(align="center")
    def left_align(self):
        """设置左对齐（恢复默认）"""
        self.dummy.set(align="left")
    def right_align(self):
        """设置右对齐"""
        self.dummy.set(align="right")
    def set_double_height(self):
        """设置双倍高度"""
        self.dummy.set(double_height=True)
    def set_double_width(self):
        """设置双倍宽度"""
        self.dummy.set(double_width=True)
    def set_normal_size(self):
        """恢复标准字号"""
        self.dummy.set(normal_textsize=True)
    def set_bold(self, enable=True):
        """设置加粗"""
        self.dummy.set(bold=enable)
    def set_underline(self, enable=True):
        """设置下划线"""
        self.dummy.set(underline=enable)
    def br(self, lineSpacing=3):
        """换行"""
        self.dummy.ln(lineSpacing)
    def cut(self):
        """切刀"""
         # 添加切刀指令
        self.dummy.cut()  
    def partial_cut(self):
        """部分切纸（留连接点）"""
        self.dummy.cut(mode="partial") 
        
    def moneyBox(self):
        # 添加钱箱指令
        self.dummy.cashdraw(2)
        self.dummy.cashdraw(5)