# API文档

# 访问根路径:
- http://127.0.0.1:5100/
- http://localhost:5100/
- http://localhost.dianplus.cn:5100/
- https://localhost.dianplus.cn:5443/

# 打印机状态
1. 获取打印机列表
- printer_status  POST
- 请求示例：https://localhost.dianplus.cn:5443/printer_status
- 返回示例:

```json 
{
    "exceptionLevel": null,
    "exceptionMessage": null,
    "message": null,
    "resultCode": "success",
    "resultObject": {
        "printerInfos": [
            {
                "description": "Canon TS3300 series",
                "is_default": true,
                "is_remote": false,
                "location": "景天的MacBook Pro",
                "name": "Canon_TS3300_series",
                "supported_resolutions": [
                    [
                        300
                    ]
                ]
            },
            {
                "description": "HP LaserJet 400 M401dne (AFFC44)",
                "is_default": false,
                "is_remote": false,
                "location": "",
                "name": "HP_LaserJet_400_M401dne__AFFC44__2",
                "supported_resolutions": [
                    [
                        300
                    ]
                ]
            }
        ]
    },
    "status": "success"
}
```

2.获取打印任务列表
- print_tasks  POST
- 请求示例：https://localhost.dianplus.cn:5443/print_tasks
- 返回示例:
```json 
{
    "message": null,
    "resultCode": "success",
    "resultObject": {
        "printTasks": [
            {
                "active": false,
                "printer": "Canon_TS3300_series",
                "status": "init",
                "taskKey": "b328c554469511f094398ea095d6301a"
            }
        ]
    },
    "success": "success"
}
```

# 打印指令
1. 打印      print POST 打印前会弹出打印机选择窗口 
- 请求示例：https://localhost.dianplus.cn:5443/print
2. 直接打印  direct_print POST 直接打印选择默认打印机打印 
- 请求示例：https://localhost.dianplus.cn:5443/direct_print
3. 打印预览  preview POST 先预览再打印 
- 请求示例：https://localhost.dianplus.cn:5443/preview

- {{-}}这样的负号代表需要替换成自己的代码
- 请求消息体:
```json 
{
    "taskKey": "1749627095208",//任务编号 可自行生成,可以使用业务的唯一标识，用于查询打印状态
    "contents": [{{encodeURIComponent(html1)}},{{encodeURIComponent(html2)}}],//打印内容，contents scripts pdfUrl 3个参数至少选一个, 如果同时存在执行顺序为contents scripts pdfUrl，仅处理最先遇到的一项其他的会忽略
    //使用encodeURIComponent对html进行编码,如果开启了zip压缩，请使用gzip压缩 压缩方法假设是gzip 那么伪代码示例为: "contents":gzip(JSON.stringify([encodeURIComponent(html1),encodeURIComponent(html2)]))
    //"scripts":scripts,//脚本格式请参见 脚本打印指令介绍
    //scripts是JSON数组,如果开启了zip压缩，请使用gzip压缩 压缩方法假设是gzip 那么伪代码示例为:"scripts":gzip(JSON.stringify(scripts))
    //pdfUrl: "https://file.dianplus.cn/jingtian/dome.pdf",
    "options": {
        "printerName":"HP_LaserJet_400_M401dne__AFFC44__2",//打印机名称可以通过调用printer_status接口获取
        "printUnit": "mm",//支持单位 mm 毫米
        // "printerType": 'tag', //打印类型，默认为空，tag是标签
         "zip": false,//true问开启压缩,contents scripts内容请使用gzip压缩 
        "pageRect": {
            "width": 210,//纸张宽度 单位mm
            "height": 297//纸张宽度 单位mm
        },
        "margins": {
            "left": 0,//纸张左边距 单位mm
            "top": 0,//纸张顶边距 单位mm
            "right": 0,//纸张右边距 单位mm
            "bottom": 0//纸张底边距 单位mm
        },
        "printCount": 1,//打印份数，默认为1
        "printFullPage": true,//全屏打印
        // "contentOrientation": "portrait",//内容方向 portrait纵向 landscape横向,默认为纵向
        // "orientation": "landscape", // 页面方向 portrait纵向 landscape横向,默认为纵向
        // "duplex": "none",// 双面打印 none单面打印，auto双面打印，long长边翻转，short短边翻转
        // "colorMode": "grayScale",// 打印颜色模式 GrayScale灰度模式，Color彩色模式，默认为灰度模式
        // pageScopes: {
        //     from: 1,//打印页码范围，默认为1
        //     to: 1
        // }
    }
}
```

- 返回示例:
```json 
{
  "resultCode": "success",
  "resultObject": {},
  "status": "success"
}
```

# PDF导出
- export_pdf  POST
- 请求示例：https://localhost.dianplus.cn:5443/export_pdf
- 请求消息体:
```json 
{
    "taskKey": "1749627095208",//任务编号 可自行生成,可以使用业务的唯一标识，用于查询打印状态
    "contents": [{{encodeURIComponent(html1)}},{{encodeURIComponent(html2)}}],//导出内容，contents 
    "options": {
        "printUnit": "mm",//支持单位 mm 毫米
        "pageRect": {
            "width": 210,//纸张宽度 单位mm
            "height": 297//纸张宽度 单位mm
        },
        "margins": {
            "left": 0,//纸张左边距 单位mm
            "top": 0,//纸张顶边距 单位mm
            "right": 0,//纸张右边距 单位mm
            "bottom": 0//纸张底边距 单位mm
        },
        "printCount": 1,//打印份数，默认为1
        "printFullPage": true,//全屏打印
        // "contentOrientation": "portrait",//内容方向 portrait纵向 landscape横向,默认为纵向
        // "orientation": "landscape", // 页面方向 portrait纵向 landscape横向,默认为纵向
        // pageScopes: {
        //     from: 1,//打印页码范围，默认为1
        //     to: 1
        // }
    }
}
```
- 返回示例:
```json 
{
  "resultCode": "success",
  "resultObject": "{{BASE64字符串}}",
  "status": "success"
}
```

# 标签打印指令介绍:
- 以下是一个完整的标签示例：
- 请求示例
- print  POST 也支持 direct_print 直接打印 preview 预览
- 请求示例：https://localhost.dianplus.cn:5443/print
- 请求消息体:
```json 
{
    "taskKey": "1749627095208",//任务编号 可自行生成,可以使用业务的唯一标识，用于查询打印状态
    "scripts": [{{指令集}},{{指令集}}],
    "options": {
        "printerName":{{打印机名称}},//打印机名称可以通过调用printer_status接口获取
        "printUnit": "mm",//支持单位 mm 毫米
        "printerType": "tag", //打印类型，默认为空，tag是标签
         "zip": false,//true问开启压缩,contents scripts内容请使用gzip压缩 
        "pageRect": {
            "width": 210,//纸张宽度 单位mm
            "height": 297//纸张宽度 单位mm
        },
        "margins": {
            "left": 0,//纸张左边距 单位mm
            "top": 0,//纸张顶边距 单位mm
            "right": 0,//纸张右边距 单位mm
            "bottom": 0//纸张底边距 单位mm
        },
        "printCount": 1,//打印份数，默认为1
        "printFullPage": true,//全屏打印
        // "contentOrientation": "landscape",//内容方向 portrait纵向 landscape横向,默认为纵向
        // "orientation": "landscape", // 页面方向 portrait纵向 landscape横向,默认为纵向
        // "duplex": "none",// 双面打印 none单面打印，auto双面打印，long长边翻转，short短边翻转
        // "colorMode": "grayScale",// 打印颜色模式 GrayScale灰度模式，Color彩色模式，默认为灰度模式
        // pageScopes: {
        //     from: 1,//打印页码范围，默认为1
        //     to: 1
        // }
    }
}
```
- 指令集内容：
```json 
{
    "unit": "mm",//单位设定为mm 毫米时，以下x y x1 x2 y1 y2 width height fontSize 都为为毫米单位
    "labels": [
        { "type": "image", "x": 2, "y": 2, "width": 4.4, "height": 3, "rotateOrigin": "top-right", "rotate":-15 ,
          "imagePath": "https://file.dianplus.cn/assets/images/logo.png"},
        { "type": "text", "text": "合格证", "x": 14, "y": 1, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 4, "bold": true, "rotate": 180 },
        { "type": "line", "x1": 1, "y1": 5.8, "x2": 39, "y2": 5.8, "colorRgba": [0, 0, 0, 255], "border": 0.2 },
        {
            "type": "text", "text": "品牌：六六六", "x": 3, "y": 6, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 3, "underline": true,
            "position": "relative","rotate": 5, "rotateOrigin": "bottom-left",
            "rect": {  "x": 0, "y": 6, "width": 40, "height": 4, "display": true, "border": 1, "textAlign": "center", "verticalAlign": "bottom"}
        },
        { "type": "text", "text": "品名：女裤", "x": 3, "y": 10, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 3, "strikeOut": true },
        { "type": "text", "text": "附件：xxxxxxx", "x": 3, "y": 14, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 3, "italic": true },
        { "type": "text", "text": "货号：GM61272S", "x": 3, "y": 18, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 3, "overline": true },
        { "type": "text", "text": "号型：S/160", "x": 3, "y": 22, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 3 },
        { "type": "text", "text": "颜色：黑色", "x": 3, "y": 26, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 3 },
        { "type": "text", "text": "执行标准：%%%%%%", "x": 3, "y": 30, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 3 },
        { "type": "text", "text": "安全类别：叠叠叠叠叠叠", "x": 3, "y": 34, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 3 },
        { "type": "text", "text": "等级：S", "x": 3, "y": 38, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 3 },
        { "type": "text", "text": "检验员：天", "x": 20, "y": 38, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 3 },
        { "type": "text", "text": "成分：xxxxxxxxxx", "x": 3, "y": 42, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 3 },
        {  
            "type": "barcode", "barcodeType": "code128",  "format": "image","text": "6936353432531", "showText": true, "textDistance": 0.4,"moduleWidth": 0.25, "moduleHeight": 5,
            "x": 0, "y": 0, "rotate": 0,"position": "relative",
            "rect": {  "x": 0, "y": 49, "width": 40, "height": 8, "border": 1,  "textAlign": "center", "verticalAlign": "bottom", "truncate": true}
        },
        { "type": "rect", "x": 2, "y": 46, "width": 36, "height": 11.3, "colorRgba": [0, 0, 0, 128], "border": 0.2 },
        { "type": "text", "text": "(不含辅料及拼接线)", "x": 11.2, "y": 46, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 2, "bold": true },
        { "type": "text", "text": "单价：699.00", "x": 14, "y": 57, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 2 },
        { "type": "text", "text": "广州致XXXXXX管理有限公司", "x": 3, "y": 60, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 2 },
        { "type": "text", "text": "广州市XXXXXXXX道中669号3", "x": 3, "y": 63, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 2 },
        { "type": "text", "text": "房C118室 电话:18000000083", "x": 3, "y": 66, "fontFamilys": ["Microsoft YaHei", "Arial"], "fontSize": 2 }
    ]
}
```

# >>labels详解

1. 旋转参数介绍
-   圆心 rotateOrigin:->中心点:center,左上角:top-left,左下角:bottom-left,右上角:top-right,右下角:bottom-right 不填默认为center
-   角度 rotate 浮点数 0-360
-  所有标签都支持旋转

2. 文本
```json 
{
    "type": "text",//文本类型
    "text": "合格证",//打印内容
    "x": 14,//x坐标
    "y": 1,//y坐标
    "colorRgba":[0,0,0,255],//文本颜色
    "fontFamilys": [//字体列表 默认第一个 看系统有哪个，使用第一个存在的
        "Microsoft YaHei",
        "Arial"
    ],
    "fontSize": 4,//字体大小
    "bold": true,//是否加粗
    "overline": true,//上划线
    "strikeOut": true,//中划线
    "underline": true,//下划线
    "italic": true//斜体
    //其他属性，如居中，旋转，对齐方式等，参见 1 和 9
}
```

3. 线条
```json 
{
    "type": "line",//线条
    "x1": 1,//起点x坐标
    "y1": 5.8,//起点y坐标
    "x2": 39,//终点x坐标
    "y2": 5.8,//终点y坐标
    "colorRgba": [//线条颜色
        0,
        0,
        0,
        255
    ],
    "border": 0.2,//线条宽度
    "lineStyle": "solid" // 线条类型(solid,dash, dot)
     //其他属性，如旋转等，参见 1
}
```

4. 矩形
```json 
{
    "type": "rect",//矩形
    "x": 2,//左上角x坐标
    "y": 46,//左上角y坐标
    "width": 36,//宽度
    "height": 11.3,//高度
    "border": 0.2,//边框宽度
    "lineStyle": "solid", // 线条类型(solid,dash, dot)
    "colorRgba": [//边框颜色
        0,
        0,
        0,
        128
    ],
    "fillColorRgba": [//填充颜色
        0,
        0,
        0,
        128
    ]
     //其他属性，如旋转等，参见 1
}
```

5. 图片
```json 
{
    "type": "image",//图片
    "x": 2,//x坐标
    "y": 2,//y坐标
    "width": 4.4,//图片宽度
    "height": 3,//图片高度
    "imageData": "{{base64ImageData}}",//图片base64数据 imageData和imagePath 参数有一个即可
    "imagePath": "https://file.dianplus.cn/assets/images/logo.png",//图片路径
    "rotateOrigin": "top-right",//图片旋转原点
    "rotate": -15,
    "scaleType" : "equalRate",//缩放类型：原始大小 等比缩放 拉伸 分别对应的值是 initial equalRate stretching,缩放仅在有rect属性时生效
     //其他属性，如居中，旋转，对齐方式等，参见 1 和 9
}
```

6. SVG
```json 
{
    "type": "svg",
    "x": 3.5,//x坐标
    "y": 47,//y坐标
    "width": 34,//SVG宽度
    "height": 12,//SVG高度
    "svgData": "{{svgXML}}",//svgXML数据 svgData和svgPath 参数有一个即可
    "svgPath": "https://file.dianplus.cn/assets/images/logo.svg",//链接
    "scaleType" : "equalRate",//缩放类型：原始大小 等比缩放 拉伸 分别对应的值是 initial equalRate stretching,缩放仅在有rect属性时生效
     //其他属性，如居中，旋转，对齐方式等，参见 1 和 9
}
```

7. 条码
```json 
{
    "type": "barcode",//条码
    "text": "6936353432531","fontSize": 2,
    "showText": true, //  条码内容 是否显示文字 注意图片模式不支持直接显示文本
    "barcodeType": "code128", // 条码类型:条码类型:Codabar', 'Code11', 'Code128', 'Code128Auto', 'EAN13', 'EAN5', 'EAN8', 'ECC200DataMatrix', 'Extended39', 'Extended93', 'FIM', 'I2of5', 'ISBN', 'MSI', 'POSTNET', 'Standard39', 'Standard93', 'UPCA', 'USPS_4State'"code128" "itf" "gs1_128" "codabar" "nw-7"
    "format": "image", // 条码格式 image/svg 默认 svg 
    "x": 0,//条码内容区x坐标
    "y": 49,//条码内容区y坐标
    "moduleWidth": 0.25,//条码宽度
    "moduleHeight": 5, //条码线条宽高
    "rotate": 0,//旋转角度
    "rect": { //条码外矩形 详见 矩形容器参数介绍
        "x": 0,
        "y": 49,
        "width": 40,
        "height": 8,
        "border": 1,
        "textAlign": "center",
        "verticalAlign": "bottom" 
    }
     //其他属性，如居中，旋转，对齐方式等，参见 1 和 9
}
```

8. 二维码
```json 
{
    "type": "qrcode",//二维码
    "format": "svg", // svg 只支持SVG
    "text": "https://file.dianplus.cn/assets/images/logo.png",
    "x": 5, //x坐标(mm或px)
    "y": 20, // y坐标(mm或px)
    "size": 30, // 二维码尺寸(mm或px)
    "border": 1, // 二维码边框大小（默认为4个模块）
    "error_correction": "H", // 容错级别 L/M/Q/H
    "module_width": 0.4, // 单个模块宽度(mm)
    "logoData": "{{base64ImageData}}",//二维码中间的logo图片base64数据 logoData和logoPath 参数有一个即可
    "logoPath": "https://file.dianplus.cn/assets/images/logo.png",//二维码中间的logo图片路径
    "colorRgba": [
        0,
        0,
        0,
        255
    ], // 前景色RGBA
    "fillColorRgba": [
        255,
        255,
        255,
        255
    ] // 背景色RGBA
     //其他属性，如居中，旋转，对齐方式等，参见 1 和 9
}
```
9. 表格打印参数介绍
```json
{
    "type": "table",
    "x": 0,
    "y": 0,
    "fontSize": 3,//字体大小 单位mm
    "width": 40,// 表格宽度 单位mm
    "height": 40,// 表格高度 单位mm
    "borderColorRgba": [0, 0, 0, 128],// 边框颜色RGBA
    "showBorder": true,// 是否显示边框
    "colWidths": [10, 20, 10],//list 表格列宽
    "rowHeights": [5, 10, 5],//list 表格行高
    "ths": [
        {
            "text": "标题1",//标题内容
            // "image": "http://www.baidu.com/logo.png",//图片内容
            "rowIndex": 0,//行索引
            "colIndex": 0,//列索引
            "rowSpan": 1,//行合并
            "colSpan": 2,//列合并
            "autoWrap": true,//是否自动换行
            "autoSize": true,//自适应字体
            "textAlign": "center",//文本对齐方式
            "verticalAlign": "middle",//垂直对齐方式
            "colorRgba": [0, 0, 0, 255],// 矩形框的边框颜色
            "fillColorRgba": [128, 128, 128, 128]// 矩形框的填充颜色
        },
        {
            "text": "标题3",
            "rowIndex": 0,
            "colIndex": 2,
            "rowSpan": 1,
            "colSpan": 1,
            "autoWrap": true,
            "autoSize": true,
            "textAlign": "center",
            "verticalAlign": "middle",
            "colorRgba": [0, 0, 0, 255],
            "fillColorRgba": [128, 128, 128, 128]
        }
    ],
    "trs": [[
        {
            "text": "值1-1",
            // "image": "http://www.baidu.com/logo.png",//图片内容
            "rowIndex": 1,
            "colIndex": 0,
            "rowSpan": 2,
            "colSpan": 1,
            "autoWrap": true,
            "autoSize": true,
            "textAlign": "center",
            "verticalAlign": "middle",
            "colorRgba": [0, 0, 0, 255],
            "fillColorRgba": [0, 255, 255, 255]
        },
        {
            "text": "值1-2",
            "rowIndex": 1,
            "colIndex": 1,
            "rowSpan": 1,
            "colSpan": 1,
            "autoWrap": true,
            "autoSize": true,
            "textAlign": "center",
            "verticalAlign": "middle",
            "colorRgba": [0, 0, 0, 255],
            "fillColorRgba": [100, 0, 100, 255]
        },
        {
            "text": "值1-3",
            "rowIndex": 1,
            "colIndex": 2,
            "rowSpan": 1,
            "colSpan": 1,
            "autoWrap": true,
            "autoSize": true,
            "textAlign": "center",
            "verticalAlign": "middle",
            "colorRgba": [0, 0, 0, 255],
            "fillColorRgba": [255, 120, 0, 255]
        }
    ],
    [
        {
            "text": "值2-2",
            "rowIndex": 2,
            "colIndex": 1,
            "rowSpan": 1,
            "colSpan": 1,
            "autoWrap": true,
            "autoSize": true,
            "textAlign": "center",
            "verticalAlign": "middle",
            "colorRgba": [0, 0, 0, 255],
            "fillColorRgba": [255, 0, 0, 255]
        },
        {
            "text": "值2-3",
            "rowIndex": 2,
            "colIndex": 2,
            "rowSpan": 1,
            "colSpan": 1,
            "autoWrap": true,
            "autoSize": true,
            "textAlign": "center",
            "verticalAlign": "middle",
            "colorRgba": [255, 255, 255, 255],
            "fillColorRgba": [128, 0, 0, 255]
        }
    ]
    ]
}
```

10. 矩形容器参数介绍
- 矩形容器是一个矩形框，只支持图片，SVG，文本，条码，二维码，表格这几个label，一般用于不确定长度的内容在一个区间内停靠方式，如居中
```json 
    "position": "relative",//rect的参数textAlign设置值后，x值失效 rect的参数verticalAlign设置值后，y值失效
    "x": 2, //x坐标(mm或px) position为relative时，x为相对rect的x的坐标
    "y": 2, // y坐标(mm或px) position为relative时 y为绝对rect的y的坐标
    "rect": {  
        "x": 0,// 矩形框的左上角x坐标
        "y": 49,// 矩形框的左上角y坐标
        "width": 40,// 矩形框的宽度
        "height": 8,// 矩形框的高度
        "border": 1,// 矩形框的边框宽度
        "textAlign": "center",// 内容横向停靠 标签参数position设置为relative时才生效 textAlign: left center right
        "verticalAlign": "middle", // 内容纵向停靠 标签参数position设置为relative时才生效 verticalAlign:top bottom middle
        "colorRgba": [0, 0, 0, 255],// 矩形框的边框颜色
        "fillColorRgba": [255, 255, 255, 0],// 矩形框的填充颜色
        "truncate": true, // 内容截断（false情况下换行和缩小字体自动判断内容是否超出边界，只保留边界内内容）
        "autoWrap": true,// 自动换行,可与autoSize配合使用，自动通过换行和调整字体大小来适应矩形框大小
        "autoSize": true,// 是否自动调整字体大小，以适应矩形框大小，最小字体4像素默认为false
    }
```




# 票据打印介绍
- 以下是一个完整的票据示例：
- 请求示例
- direct_print  POST 仅支持直接打印
- 请求示例：https://localhost.dianplus.cn:5443/direct_print
- 请求消息体:
```json 
{
    "scripts": [{{指令集}},{{指令集}}],
    "options": {
        "taskKey": {{new Date().getTime()}}, //可以使用业务的唯一标识，用于查询打印状态
        "printerName": "HP_LaserJet_400_M401dne__AFFC44_",//打印机名称可以通过调用printer_status接口获取
        "printUnit": "mm",//支持单位 mm 毫米、inch 英寸、pt 颗粒、didot 印刷粒度
        "printerType": "ticket",
        "printerCount": 1,//打印份数
        "lineSpacing": 3, //行间距 单位点
        "feedPaper": 1, //打印前走纸行数 1
        "printSpeed": 2, //走纸速度 设置打印速度（1=慢速，2=中速，3=快速）
        "printDensity": 10,//打印浓度（0-15）
         //macos 专用 可以通过命令查看: system_profiler SPUSBDataType | grep -A 11 "Printer"
        "vendorId": "厂商ID",
        "productId": "产品ID"
    }
}
```
- 票据指令集示例
- 使用以下内容替换请求消息体中的{{指令集}}
```json 
 {
    "rows": [
        { "type": "br" },
        {
            "type": "image",
            "style": {
                "align": "center",
                "width": 150,//像素
                "height": 150//像素
            },
            "src": "https://file.dianplus.cn/assets/images/logo2.png",
            "imageMode": "bitImageColumn" //bitImageColumn 高清，不是所有机器都支持 bitImageRaster标准基本都支持
        },
        { "type": "br" },
        {
            "type": "text", "text": "店家小助手",
            "style": { "align": "center", "bold": true, "inverse_printing": false, "upside_down": false }
        },
        { "type": "br" },
        { "type": "text", "text": "地址: 某某市某某区某某路", "style": { "align": "center" } },
        { "type": "br" },
        { "type": "text", "text": "--------------------------------", "style": { "align": "center" } },
        { "type": "br" },
        {
            "type": "table",
            "width": 42,//字数
            "style": {
                "align": "center"
            },
            "header_style": {
                "font": "A",
                "bold": true,
                "underline": false,
                "double_height": true,
                "double_width": false,
                "align": "left"
            },
            "row_style": {
                "font": "A",
                "bold": false,
                "underline": false,
                "double_height": false,
                "double_width": false,
                "align": "left",
                "wrapBottom": false
            },
            "header_cell_styles": [
                {
                    "width": 17,
                    "align": "left"
                },
                {
                    "width": 5
                },
                {
                    "width": 10
                },
                {
                    "width": 10,
                    "align": "right"
                }
            ],
            "row_cell_styles": [
                {
                    "width": 17,
                    "align": "left"
                },
                {
                    "width": 5
                },
                {
                    "width": 10
                },
                {
                    "width": 10,
                    "align": "right"
                }
            ],
            "headers": ["品名", "数量", "价格", "总价"],
            "rows": [
                ["商品AA", "2", "0.00", "0.00"],
                ["Item 2", "2", "0.00", "0.00"],
                ["Item 3", "2", "0.00", "0.00"],
                ["Item 2", "2", "0.00", "0.00"],
                ["Item 3", "2", "0.00", "0.00"]
            ]
        },
        { "type": "br" },
        {
            "type": "text_grid",
            "width": 42,//字数
            "style": { "align": "center", "spacing": 2 },
            "cells": [
                {
                    "text": "储值余额:888", "width": 20, "align": "left"
                },
                {
                    "text": "折扣:88", "width": 20, "align": "right"
                },
                {
                    "text": "------", "width": 20, "align": "center"
                }
            ]
        },
        { "type": "br" },
        {
            "type": "text_grid",
            "width": 42,//字数
            "style": { "align": "center" },
            "spacing": 2,
            "cells": [
                {
                    "text": "会员:VIP11", "width": 20, "align": "left"
                },
                {
                    "text": "合计:50.00", "width": 20, "align": "right"
                }
            ]
        },
        { "type": "br" },
        { "type": "text", "text": "感谢惠顾!", "style": { "align": "center" } },
        { "type": "br" },
        { "type": "text", "text": "欢迎下次光临!", "style": { "align": "center" } },
        { "type": "br" },
        { "type": "barcode", "code": "6912345678901", "style": { "align": "center" }, "width": 3, "format": "EAN13", "showText": true },
        { "type": "br" },
        { "type": "qrcode", "text": "http://www.example.com", "style": { "align": "center" }, "size": 6 },
        { "type": "br", "line_spacing": 80 },
        { "type": "cut" },
        { "type": "box" }
    ]
}
```

# >>rows详解

1. text: 添加文本，参数为字符串，可选参数：
- text: 文本内容，必填参数
- style: 样式，可选参数：
    - align: 文本对齐方式，可选值：left, center, right，默认为center
    - fontSize: 字体大小，默认为10
    - bold: 是否加粗，默认为false
    - underline: 下划线，默认为false
    - double_height: 放大字体高度，默认为false
    - double_width: 放大字体宽度，默认为false
    - character: "CHINA|USA|JAPAN|EUROPE", // 可选
    - inverse_printing": true|false, // 黑白交换
    - upside_down": true|false   //倒置
```json
{
  "type": "text",
  "text": "文本内容",
  "style": {
    "align": "left|center|right",   // 可选
    "bold": true|false,             // 可选
    "underline": true|false,        // 可选
    "double_height": true|false,    // 可选
    "double_width": true|false,     // 可选
    "character": "CHINA|USA|JAPAN|EUROPE", // 可选
    "inverse_printing": true|false, // 可选
    "upside_down": true|false       // 可选
  }
}
```

2. image: 添加图片，参数为图片路径，可选参数：
- src:图片路径|base64(data:image/png;base64,xxx)，必填
- style: 样式，可选参数：
    - align: 图片对齐方式，可选值：left, center, right，默认为center
    - width: 图片宽度，可选值：auto, number，默认auto
    - height: 图片高度，可选值：auto, number，默认auto
- imageMode: 图片指令集 bitImageColumn 高清，不是所有机器都支持 bitImageRaster标准基本都支持
```json
{
  "type": "image",
  "src": "图片URL或本地路径",
  "style": {
    "align": "left|center|right",   // 可选
    "width": 200,                   // 可选（像素）
    "height": 200,                   // 可选（像素）
  },
  "imageMode": "bitImageColumn|bitImageRaster"
}
```

3. text_grid: 添加两列文本，可选参数：
- width: 文本总宽度 48个字符约等于80mm
- style: 样式，可选参数：
    - align: 文本对齐方式，可选值：left, center, right，默认为center
    - fontSize: 字体大小，默认为10
    - spacing: 两列的空隙，默认为0
    - bold: 是否加粗，默认为false
    - underline: 下划线，默认为false
    - double_height: 放大字体高度，默认为false
    - double_width: 放大字体宽度，默认为false
    - character: "CHINA|USA|JAPAN|EUROPE", // 可选
    - inverse_printing": true|false, // 黑白交换
    - upside_down": true|false   //倒置
- cells: 单元格数组 ，可选参数：
    - text: 文本内容
    - width: 单元格宽度, 必填参数
    - align: 文本对齐方式，可选值：left, center, right，默认为left

```json
{
    "type": "text_grid",
    "width": 42,
    "style": {
        "align": "left|center|right",  // 可选
        "spacing": 1
    },
    "cells": [
        {
            "text": "储值余额:888", "width": 20, "align": "left"
        },
        {
            "text": "折扣:88", "width": 20, "align": "right"
        },
        {
            "text": "------", "width": 20, "align": "center"
        }
    ]
}
```
4. image_grid: 添加栅格图片，可选参数：
- width: 文本总宽度 48个字符约等于80mm
- style: 样式，可选参数：
    - align: 文本对齐方式，可选值：left, center, right，默认为center
    - spacing: 两列的空隙，默认为0
- cells: 单元格数组 ，可选参数：
    - src: 图片链接或者base64图片数据
    - width: 单元格宽度, 必填参数
    - align: 文本对齐方式，可选值：left, center, right，默认为left
- imageMode:图片模式，可选参数：bitImageColumn, bitImageRaster
```json
 {
    "type": "image_grid",
    "width": 44,//字数
    "style": { 
        "align": "center", 
        "spacing": 1 
    },
    "cells": [
        {"src": "https://img.alicdn.com/tfs/TB1.Y.qhYr1gK0jSZFhXXaAtVXa-100-100.png", "width": 14, "align": "left"},
        {"src": "https://img.alicdn.com/tfs/TB1.Y.qhYr1gK0jSZFhXXaAtVXa-100-100.png", "width": 14, "align": "center"},
        {"src": "https://img.alicdn.com/tfs/TB1.Y.qhYr1gK0jSZFhXXaAtVXa-100-100.png", "width": 14, "align": "right"},
    ],
    "imageMode": "bitImageColumn"
}
```

5. table: 添加表格，参数为表格数据，可选参数：
- width: 表整度，可选值：auto, number，默认auto
- headers: 表头数据
- rows: 表明细数据
- style: 整表样式，可选参数：
    - align: 文本对齐方式，可选值：left, center, right，默认为center
    - fontSize: 字体大小，默认为10
    - bold: 是否加粗，默认为false
    - underline: 下划线，默认为false
    - double_height: 放大字体高度，默认为false
    - double_width: 放大字体宽度，默认为false
    - character: "CHINA|USA|JAPAN|EUROPE", // 可选
    - inverse_printing": true|false, // 黑白交换
    - upside_down": true|false   //倒置
- header_style: 表头样式，可选参数：
    - align: 文本对齐方式，可选值：left, center, right，默认为center
    - fontSize: 字体大小，默认为10
    - bold: 是否加粗，默认为false
    - underline: 下划线，默认为false
    - double_height: 放大字体高度，默认为false
    - double_width: 放大字体宽度，默认为false
    - character: "CHINA|USA|JAPAN|EUROPE", // 可选
    - inverse_printing": true|false, // 黑白交换
    - upside_down": true|false   //倒置
    - split: 分割线
        - bold: true|false 是否黑体
        - char: 分割线字符
        - line_spacing:分割线高度
        - shows: [false, true, false] 分别标识上中下三条分割线是否显示
- row_style: 数据行样式，可选参数：
    - align: 文本对齐方式，可选值：left, center, right，默认为center
    - fontSize: 字体大小，默认为10
    - bold: 是否加粗，默认为false
    - underline: 下划线，默认为false
    - double_height: 放大字体高度，默认为false
    - double_width: 放大字体宽度，默认为false
    - character: "CHINA|USA|JAPAN|EUROPE", // 可选
    - inverse_printing": true|false, // 黑白交换
    - upside_down": true|false   //倒置
    - line_spacing:行高
    - split: 分割线
        - bold: true|false 是否黑体
        - char: 分割线字符
        - show: true|false 分割线是否显示
- header_cell_styles: 表头单元格样式，可选参数, 对象数组：
    - align: 文本对齐方式，可选值：left, center, right，默认为center
    - width: 字数
- row_cell_styles: 数据单元格样式，可选参数, 对象数组：
    - align: 文本对齐方式，可选值：left, center, right，默认为center
    - width: 字数
```json
{
    "type": "table",
    "width": 42,                    // 必选（字符宽度）
    "headers": ["列1", "列2", "列3"],// 必选
    "rows": [                       // 必选
        ["值1", "值2", "值3"],      // 每行个数一样
        ["值4", "值5", "值6"]
    ],
    "style": {
        "align": "left|center|right"// 可选 默认center
    },
    "header_style": {               //可选 表头行样式
        "font": "A|B",
        "bold": true|false,
        "underline": true|false,
        "double_height": true|false,
        "double_width": true|false,
        "character": "CHINA|USA|JAPAN|EUROPE",
        "inverse_printing": true|false,
        "upside_down": true|false,
        "wrapBottom": true|false, // 文字过长，换行模式 false 置顶换行，true 置底换行
        "split": {
            "bold": false,
            "char": "-",
            "shows": [false, true, false] // 三条分割线，true 显示，false 不显示
        }
    },
    "row_style": {                  //可选 表明细行样式
        "font": "A|B",
        "bold": true|false,
        "underline": true|false,
        "double_height": true|false,
        "double_width": true|false,
        "character": "CHINA|USA|JAPAN|EUROPE",
        "inverse_printing": true|false,
        "upside_down": true|false,
        "wrapBottom": true|false, // 文字过长，换行模式 false 置顶换行，true 置底换行
        "split": {
            "bold": false,//是否加粗
            "char": "-",//分割线字符
            "show": true|false //显示分割线
        }
    },
    "header_cell_styles": [          //必选 单元格样式，所有width加起来要等于表格的width，此处width设定的是42，那么最后的和应当就是42
        {
            "width": 17,//字数
            "align": "left|center|right"   // 可选
        },
        {
            "width": 15,//字数
            "align": "left|center|right"   // 可选
        },
        {
            "width": 10,//字数
            "align": "left|center|right"   // 可选
        }
    ],
    "row_cell_styles": [
        {
            "width": 17,//字数
            "align": "left|center|right"   // 可选
        },
        {
            "width": 15,//字数
            "align": "left|center|right"   // 可选
        },
        {
            "width": 10,//字数
            "align": "left|center|right"   // 可选
        }
    ]
}
```

6. barcode: 添加条形码，参数为条形码内容，可选参数：
- code: 条形码内容
- format: 条形码格式，可选值：EAN13, EAN8, UPC_A, UPC_E, CODE128, CODE39, CODE93 特别提醒：CODE128, CODE39, CODE93 不是所有打印机都支持的，大部分打印机只支持EAN13,可以使用替代方案，使用图片代替
- width: 条形码宽度，可选值：auto, number，默认auto
- height: 条形码高度，可选值：auto, number，默认auto
- style: 样式，可选参数：
    - align: 对齐方式，可选值：left, center, right，默认为center
    - fontSize: 字体大小，默认为10
    - bold: 是否加粗，默认为false
    - underline: 下划线，默认为false
    - double_height: 放大字体高度，默认为false
    - double_width: 放大字体宽度，默认为false
    - character: "CHINA|USA|JAPAN|EUROPE", // 可选
    - inverse_printing": true|false, // 黑白交换
    - upside_down": true|false   //倒置
```json
{
  "type": "barcode",
  "code": "12345678",
  "style": {
    "align": "left|center|right"   // 可选
  },
  "width": 200,                   // 可选（像素）
  "height": 50                    // 可选（像素）
}
```

7. qrcode: 添加二维码，参数为二维码内容，可选参数：
- size: 二维码大小，可选值：auto, number，默认auto
- style: 样式，可选参数：
    - align: 文本对齐方式，可选值：left, center, right，默认为center
```json
{
    "type": "qrcode",
    "text": "内容",
    "style": {
        "align": "left|center|right"   // 可选 默认center
    },
    "size": 6                     // 可选，二维码小方块的大小
}
```

8. 换行指令
```json
{
  "type": "br",//br 换行 
  "line_spacing": 10 //br 换行时设置行间距
}
```

9. 控制指令
```json
{
  "type": "cut",//cut 全切刀 partial_cut 部分切刀，会留个连接点 box 开启钱箱
}
```