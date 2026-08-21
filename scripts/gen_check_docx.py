# -*- coding: utf-8 -*-
"""生成《技术路径核查与D2执行计划》docx，零第三方依赖。"""
import zipfile, os, xml.sax.saxutils as sx

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "路径核查与D2执行计划_20260820.docx")

def esc(s): return sx.escape(s, {'"': "&quot;"})

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CNT_W = 9026

xml = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
       f'<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>']

def run(text, bold=False, size=None, color=None, italic=False):
    rpr = '<w:rPr>'
    if bold: rpr += '<w:b/>'
    if italic: rpr += '<w:i/>'
    if size: rpr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    if color: rpr += f'<w:color w:val="{color}"/>'
    rpr += '</w:rPr>'
    return f'<w:r>{rpr}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'

def para(text="", style=None, bold=False, size=None, color=None, italic=False,
         align=None, spacing_before=None, spacing_after=None):
    ppr = '<w:pPr>'
    if style: ppr += f'<w:pStyle w:val="{style}"/>'
    if align: ppr += f'<w:jc w:val="{align}"/>'
    sp = '<w:spacing '
    if spacing_before is not None: sp += f'w:before="{spacing_before}" '
    if spacing_after is not None: sp += f'w:after="{spacing_after}" '
    sp += '/>'
    ppr += sp + '</w:pPr>'
    return f'<w:p>{ppr}{run(text, bold=bold, size=size, color=color, italic=italic)}</w:p>'

def h1(t): return para(t, style="Heading1")
def h2(t): return para(t, style="Heading2")
def p(t, **kw): return para(t, **kw)

def bullet(t):
    return (f'<w:p><w:pPr><w:ind w:left="360" w:hanging="360"/></w:pPr>'
            + run("• ", bold=False) + run(t) + '</w:p>')

def numbered(t, num):
    return (f'<w:p><w:pPr><w:ind w:left="540" w:hanging="540"/></w:pPr>'
            + run(f"{num}. ", bold=False) + run(t) + '</w:p>')

def table(headers, rows, widths, header_fill="2E75B6", header_color="FFFFFF", font_size=20):
    assert sum(widths) == CNT_W, f"table widths {sum(widths)} != {CNT_W}"
    out = ['<w:tbl><w:tblPr>'
           f'<w:tblW w:w="{CNT_W}" w:type="dxa"/>'
           '<w:tblBorders>'
           + "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/>'
                     for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
           + '</w:tblBorders>'
           '<w:tblLayout w:type="fixed"/></w:tblPr>'
           + '<w:tblGrid>' + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + '</w:tblGrid>']
    out.append('<w:tr><w:trPr><w:tblHeader/></w:trPr>')
    for i, htxt in enumerate(headers):
        out.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[i]}" w:type="dxa"/>'
                   f'<w:shd w:val="clear" w:color="auto" w:fill="{header_fill}"/>'
                   '<w:vAlign w:val="center"/></w:tcPr>'
                   f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr>{run(htxt, bold=True, color=header_color, size=21)}</w:p></w:tc>')
    out.append('</w:tr>')
    for row in rows:
        out.append('<w:tr>')
        for i, cell in enumerate(row):
            cell_lines = cell.split("\n")
            out.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[i]}" w:type="dxa"/>'
                       '<w:vAlign w:val="top"/></w:tcPr>')
            for j, ln in enumerate(cell_lines):
                sp_after = "60" if j < len(cell_lines) - 1 else "20"
                out.append(f'<w:p><w:pPr><w:spacing w:before="20" w:after="{sp_after}"/></w:pPr>{run(ln, size=font_size)}</w:p>')
            out.append('</w:tc>')
        out.append('</w:tr>')
    out.append('</w:tbl>')
    return "".join(out)

# ============ 内容 ============
xml.append(para("技术路径核查与 D2 执行计划", size=44, bold=True, align="center", spacing_before=200, spacing_after=80))
xml.append(para("2026-08-20（第 2 天）", size=24, align="center", color="595959", spacing_after=200))
xml.append(p("目的：核查《第 1 天报告》《立项书》中的技术路径是否真实可行，修正发现的问题，并把“明日安排”细化为可执行、可核对的 D2 计划。"))

xml.append(h1("一、环境实测结论（Windows 本机，2026-08-20 实测）"))
xml.append(table(
    ["项目", "实测结果", "结论"],
    [
        ["Go 工具链", "go1.26.6 windows/amd64", "可用，支持交叉编译 Linux"],
        ["无头渲染浏览器", "Chrome 已安装（C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe）", "可用"],
        ["无头渲染最小验证", "chrome --headless=new --no-pdf-header-footer --print-to-pdf 实测生成 42 KB PDF 成功", "Windows 渲染路径验证通过"],
        ["默认打印机", "Microsoft Print to PDF（虚拟）", "无实体打印机，打印动作实际输出 PDF"],
        ["Linux 运行环境", "WSL 未安装（wsl 命令不存在）", "风险确认：本机暂无 Linux 演示环境"],
    ],
    [2000, 4326, 2700],
))

xml.append(h1("二、核查发现的问题（原方案需修正 4 处）"))
xml.append(h2("问题 1（关键）：Linux 演示环境缺失，原方案未落实来源"))
xml.append(p("原方案只写“Linux 各演示 ≥1 次”，但本机没有 WSL / Docker / 虚拟机。修正：D2 起把“Linux 演示环境”当作硬性任务处理，三选一并在 D2 定案："))
xml.append(numbered("安装 WSL2（wsl --install，需管理员权限，通常要重启）；", 1))
xml.append(numbered("借用/申请一台 Linux 机器（远程 SSH，部署交叉编译产物）；", 2))
xml.append(numbered("本机装虚拟机（VirtualBox + Ubuntu ISO，下载约 4~5 GB，需提前）。", 3))
xml.append(p("若三选一均不可行（如无管理员权限、无网络下载），降级演示口径：交叉编译 Linux 版产物 + 在可用 Linux 环境跑通同一渲染命令并截图存档，并提前告知验收方调整验收 3 的演示方式。"))

xml.append(h2("问题 2（关键）：默认打印机是虚拟 PDF，原“打印出纸”表述不真实"))
xml.append(p("本机默认打印机 = Microsoft Print to PDF，无实体打印机；且向该虚拟打印机发起“打印”会弹出“另存为”对话框，自动化会被卡住。修正：MVP 的“打印”动作拆为两步并如实描述："))
xml.append(numbered("自动生成 PDF 产物（Chrome 无头，已实测可行）；", 1))
xml.append(numbered("送默认打印机（Windows：PowerShell Start-Process -Verb Print；Linux：lp）——虚拟打印机场景会弹窗，需人工确认或跳过；", 2))
xml.append(numbered("任务 done 状态必须返回 PDF 产物路径，作为演示与验收的第一核验结果；实体打印机出纸为可选加分项。", 3))
xml.append(p("验收 1 前提改为“默认打印机可用（含 Microsoft Print to PDF）”，结果以“PDF 产物 + 任务状态已完成”为核验点。"))

xml.append(h2("问题 3（端口/防火墙）：原方案未定监听地址，可能被防火墙拦截"))
xml.append(p("若监听 0.0.0.0，Windows 防火墙首次会弹窗、拦截风险高；本课题定位“本机打印”，无需对外暴露。修正：服务明确监听 127.0.0.1，回环流量不触发防火墙拦截；端口协商仅在 18210 被占用时在 18210~18220 内递增回退。"))

xml.append(h2("问题 4（简化）：Web 页面与 API 同端口托管，去掉页面端“端口协商”复杂度"))
xml.append(p("原方案让 Web 页面探活多个端口，复杂且易错。修正：本地服务同时托管 Web 静态页面，用户直接打开 http://127.0.0.1:<port>/；页面从 location.port 拿端口，同源调用 API，无 CORS 问题。端口协商只发生在服务启动时一次（固定→回退→写 port.txt + 日志）。"))

xml.append(h2("附带修正（实现细节确认可行）"))
xml.append(numbered("语法高亮：改用 Go 库 github.com/alecthomas/chroma/v2 服务端生成高亮 HTML（避免前端 JS 依赖）；需网络拉取依赖，离线时改用 vendor 或内置最小高亮。", 1))
xml.append(numbered("窄纸：CSS @page { size: 80mm }（58mm 同理），Chrome --print-to-pdf 遵守该尺寸；中文依赖系统中文字体，Linux 需 fonts-noto-cjk。", 2))
xml.append(numbered("Go 交叉编译：CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build（纯 Go + 系统命令 exec，无 CGO 依赖），可行。", 3))

xml.append(h1("三、D2（2026-08-20）执行计划（细化版）"))
xml.append(h2("上午（9:00–12:00）"))
xml.append(table(
    ["时间", "任务", "具体动作与命令", "完成标志"],
    [
        ["9:00–9:30", "Linux 环境定案", "查权限/网络 → 决定 WSL2 / 借机 / 虚拟机；可行则立即启动安装", "方案定案并记录，WSL 安装已启动（需重启则记录重启安排）"],
        ["9:30–10:30", "Go 项目骨架", "go mod init printsvc；目录 cmd/printsvc/、internal/{server,render,printer,task,port}；main.go + GET /healthz", "本地 go build 通过"],
        ["10:30–11:00", "双平台构建", "CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o bin/printsvc-linux；Windows 构建 bin/printsvc.exe", "bin 下两个产物存在且可执行"],
        ["11:00–12:00", "端口协商最小闭环", "net.Listen(127.0.0.1:18210) → 失败递增至 18220 → 写 port.txt+日志；用另一进程占住 18210 验证回退", "占用时自动回退，port.txt 与实际端口一致"],
    ],
    [1500, 2000, 3926, 1600],
))
xml.append(h2("下午（14:00–18:00）"))
xml.append(table(
    ["时间", "任务", "具体动作与命令", "完成标志"],
    [
        ["14:00–15:30", "渲染子模块 v0", "render.Render(tpl, data) 生成 HTML 临时文件 → exec Chrome --headless=new --no-pdf-header-footer --print-to-pdf → 返回 PDF 路径（复用已验证命令封装成 Go 函数）；用最小小票模板实测", "Go 函数可生成小票 PDF，中文正常（目检样张）"],
        ["15:30–16:30", "打印命令适配层", "抽 printer.Print(pdfPath)：Windows 走 PowerShell 打印 verb；Linux 走 lp；虚拟打印机弹窗行为记录为已知限制", "适配层编译通过，Windows 调用行为已记录"],
        ["16:30–17:00", "Linux 依赖清单", "编写 docs/linux-deps.md：chromium / fonts-noto-cjk / cups（lp）安装脚本；若 WSL2 就绪则实际安装并跑同一渲染命令", "文档入库；WSL 内渲染验证记录"],
        ["17:00–17:30", "当日简报", "今日完成 / 阻塞项 / 明日计划，附 PDF 样张与双平台产物清单", "简报发出"],
    ],
    [1500, 1900, 4126, 1500],
))
xml.append(h2("D2 结束可核对清单（对照验收说明）"))
xml.append(numbered("bin/printsvc.exe 与 bin/printsvc-linux 双平台产物存在；", 1))
xml.append(numbered("curl http://127.0.0.1:18210/healthz 返回 200 + JSON；", 2))
xml.append(numbered("占住 18210 后服务自动回退，port.txt 可见实际端口；", 3))
xml.append(numbered("render 函数生成的小票 PDF 存在且中文无乱码（目检样张）；", 4))
xml.append(numbered("Linux 演示环境方案已定案并有执行记录。", 5))

xml.append(h1("四、对原验收说明的微调"))
xml.append(numbered("验收 1 前提：改为“默认打印机可用（含 Microsoft Print to PDF）”，结果核验以“PDF 产物路径 + 状态已完成 + 字段正确”为准，出纸为加分。", 1))
xml.append(numbered("验收 3 前提：Linux 环境来源按问题 1 的三选一定案后执行；若降级为“远程环境跑渲染命令”，需提前告知验收方调整演示方式。", 2))
xml.append(numbered("验收 2 不变（端口协商行为本身不受上述问题影响）。", 3))

xml.append('<w:sectPr>'
           '<w:pgSz w:w="11906" w:h="16838"/>'
           '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>'
           '</w:sectPr>')
xml.append('</w:body></w:document>')
document_xml = "".join(xml)

styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W}">
  <w:docDefaults><w:rPrDefault><w:rPr>
    <w:rFonts w:ascii="微软雅黑" w:eastAsia="微软雅黑" w:hAnsi="微软雅黑" w:cs="微软雅黑"/>
    <w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="en-US" w:eastAsia="zh-CN"/>
  </w:rPr></w:rPrDefault>
  <w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="300" w:lineRule="auto"/></w:pPr></w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/><w:next w:val="Normal"/>
    <w:pPr><w:keepNext/><w:spacing w:before="280" w:after="140" w:line="320" w:lineRule="auto"/>
    <w:outlineLvl w:val="0"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="1F4E79"/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/><w:next w:val="Normal"/>
    <w:pPr><w:keepNext/><w:spacing w:before="200" w:after="100" w:line="300" w:lineRule="auto"/>
    <w:outlineLvl w:val="1"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="2E74B5"/><w:sz w:val="27"/><w:szCs w:val="27"/></w:rPr>
  </w:style>
</w:styles>'''

content_types = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''

rels = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''

document_rels = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

core = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>技术路径核查与 D2 执行计划</dc:title>
  <dc:creator>侯俊</dc:creator>
  <cp:lastModifiedBy>侯俊</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">2026-08-20T00:00:00Z</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">2026-08-20T00:00:00Z</dcterms:modified>
</cp:coreProperties>'''

app = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>CodeBuddy Document Generator</Application>
</Properties>'''

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", content_types)
    z.writestr("_rels/.rels", rels)
    z.writestr("docProps/core.xml", core)
    z.writestr("docProps/app.xml", app)
    z.writestr("word/document.xml", document_xml)
    z.writestr("word/_rels/document.xml.rels", document_rels)
    z.writestr("word/styles.xml", styles)

print("OK ->", OUT, os.path.getsize(OUT), "bytes")
