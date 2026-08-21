# -*- coding: utf-8 -*-
"""生成《项目立项书（详细版）》docx，使用 Python 标准库直接构造 OOXML，零第三方依赖。"""
import zipfile, os, xml.sax.saxutils as sx

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "项目立项书_详细版_20260819.docx")

def esc(s): return sx.escape(s, {'"': "&quot;"})

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

CNT_W = 9026  # A4 11906 - 2*1440

xml = []
xml.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
xml.append(f'<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>')

def run(text, bold=False, size=None, color=None, italic=False):
    rpr = '<w:rPr>'
    if bold: rpr += '<w:b/>'
    if italic: rpr += '<w:i/>'
    if size: rpr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    if color: rpr += f'<w:color w:val="{color}"/>'
    rpr += '</w:rPr>'
    return f'<w:r>{rpr}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'

def para(text="", style=None, bold=False, size=None, color=None, italic=False,
         align=None, spacing_before=None, spacing_after=None, shade=None, border_bottom=None):
    ppr = '<w:pPr>'
    if style: ppr += f'<w:pStyle w:val="{style}"/>'
    if align: ppr += f'<w:jc w:val="{align}"/>'
    sp = '<w:spacing '
    if spacing_before is not None: sp += f'w:before="{spacing_before}" '
    if spacing_after is not None: sp += f'w:after="{spacing_after}" '
    sp += '/>'
    ppr += sp
    if shade: ppr += f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>'
    if border_bottom:
        ppr += f'<w:pBdr><w:bottom w:val="single" w:sz="{border_bottom[1]}" w:space="1" w:color="{border_bottom[0]}"/></w:pBdr>'
    ppr += '</w:pPr>'
    return f'<w:p>{ppr}{run(text, bold=bold, size=size, color=color, italic=italic)}</w:p>'

def h1(t): return para(t, style="Heading1")
def h2(t): return para(t, style="Heading2")
def h3(t): return para(t, style="Heading3")
def p(t, **kw): return para(t, **kw)

def bullet(t, level=0):
    ind = 360 + level * 360
    return (f'<w:p><w:pPr><w:ind w:left="{ind}" w:hanging="360"/></w:pPr>'
            + run("• ", bold=False) + run(t) + '</w:p>')

def numbered(t, num):
    return (f'<w:p><w:pPr><w:ind w:left="540" w:hanging="540"/></w:pPr>'
            + run(f"{num}. ", bold=False) + run(t) + '</w:p>')

def code_block(t):
    lines = t.split("\n")
    out = [f'<w:p><w:pPr><w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>'
           f'<w:ind w:left="180" w:right="180"/><w:spacing w:before="40" w:after="40"/></w:pPr>']
    for i, ln in enumerate(lines):
        out.append(run(ln, size=20))
        if i < len(lines) - 1:
            out.append('<w:r><w:br/></w:r>')
    out.append('</w:p>')
    return "".join(out)

def table(headers, rows, widths, header_fill="2E75B6", header_color="FFFFFF"):
    assert sum(widths) == CNT_W, f"table widths {sum(widths)} != {CNT_W}"
    out = ['<w:tbl><w:tblPr>'
           f'<w:tblW w:w="{CNT_W}" w:type="dxa"/>'
           '<w:tblBorders>'
           + "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/>'
                     for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
           + '</w:tblBorders>'
           '<w:tblLayout w:type="fixed"/></w:tblPr>'
           + '<w:tblGrid>' + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + '</w:tblGrid>']
    # header
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
            # 支持 cell 里多行（用 \n 分隔）
            cell_lines = cell.split("\n")
            out.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[i]}" w:type="dxa"/>'
                       '<w:vAlign w:val="top"/></w:tcPr>')
            for j, ln in enumerate(cell_lines):
                sp_after = "60" if j < len(cell_lines) - 1 else "20"
                out.append(f'<w:p><w:pPr><w:spacing w:before="20" w:after="{sp_after}"/></w:pPr>{run(ln, size=20)}</w:p>')
            out.append('</w:tc>')
        out.append('</w:tr>')
    out.append('</w:tbl>')
    return "".join(out)

def spacer(pts=120):
    return f'<w:p><w:pPr><w:spacing w:before="0" w:after="{pts}"/></w:pPr></w:p>'

# ============ 内容 ============
# 标题
xml.append(para("项目立项书（详细版）", size=48, bold=True, align="center", spacing_before=240, spacing_after=120))
xml.append(para("浏览器调用本地打印机 —— 基于 Golang 的跨平台本地打印服务（MVP）",
                size=28, bold=True, align="center", spacing_after=60))
xml.append(para("浏览器（Web 端）经 HTTP 调用本地打印服务，驱动本机默认打印机输出，并回传任务排队与完成状态",
                size=22, color="595959", align="center", spacing_after=240))

xml.append(table(
    ["项目信息", "内容"],
    [
        ["项目名称", "浏览器调用本地打印机（Web-to-Print Local Print Service）"],
        ["课题编号", "CCP-2026-001"],
        ["版本 / 状态", "V1.0 正式版"],
        ["起草日期 / 周期", "2026-08-19 起草；执行周期 7 天：2026-08-20 ~ 2026-08-26"],
        ["立项人", "侯俊"],
        ["开发方式", "独立开发（单人）"],
        ["验收人员", "侯俊（自评）+ 验收评审"],
        ["参考项目", "CCPCOJ（含现场打印队列场景）"],
        ["商用对照", "Lodop（网页打印控件）"],
        ["交付物", "本立项书、可运行代码仓库、双平台演示记录（Windows / Linux 各 ≥1 次）"],
    ],
    [2200, 6826],
))

xml.append(h1("一、课题概述（背景与目标）"))
xml.append(h2("1.1 这个课题要解决什么问题"))
xml.append(p("在 ACM/ICPC 等程序设计竞赛现场，有两类高频打印需求：", spacing_after=60))
xml.append(bullet("气球小票：队伍 AC（通过）某道题后，工作人员需要打印一张小票（包含队名、题号、通过时间等），"
                  "用于确认与派发气球。比赛现场节奏快，要求小票即点即打、排队有序、可追踪。"))
xml.append(bullet("代码打印：裁判或队伍需要打印选手提交的源代码用于核查。代码应带语法高亮、适配窄行小票纸宽，"
                  "避免折行截断。"))
xml.append(p("当前商用方案（如 Lodop 网页打印控件）依赖 IE/ActiveX 或特定浏览器插件，跨平台（Linux）支持弱、"
             "部署繁琐、存在授权成本；开源项目 CCPCOJ 虽包含现场打印队列场景，但其打印链路依赖特定环境。"
             "因此本项目自研一套轻量、跨平台的本地打印服务替代方案。", spacing_before=60))
xml.append(h2("1.2 项目目标（一句话）"))
xml.append(p("浏览器（Web 端）通过 HTTP 调用部署在本机的 Golang 打印服务，把两类打印任务渲染为 PDF 后交给"
             "系统默认打印机输出，并通过接口回传任务的排队 / 完成 / 失败状态；同一仓库代码可在 Windows 与 Linux "
             "双平台运行，各完成至少一次完整演示。"))
xml.append(h2("1.3 技术栈"))
xml.append(table(
    ["层次", "选型", "说明"],
    [
        ["本地服务", "Golang", "跨平台编译（GOOS=windows/linux 交叉编译），平台差异通过适配层隔离"],
        ["渲染方案", "无头 Chromium（headless）", "渲染 HTML → PDF，交由系统默认打印机输出；不可用时提供等价降级方案"],
        ["Web 对接", "HTTP / JSON 接口", "任务提交接口 + 任务状态查询接口"],
        ["端口协商", "固定默认端口 + 探活 + 自动回退", "默认端口被占用时自动寻找可用端口并上报给 Web 端"],
        ["打印驱动", "操作系统默认打印机", "Windows：系统默认打印机；Linux：CUPS 默认打印机"],
    ],
    [1800, 3000, 4226],
))

xml.append(h1("二、业务场景与系统流程详解（供验收理解）"))
xml.append(h2("2.1 场景一：气球小票打印"))
xml.append(p("队伍 AC 某题后，Web 端（裁判系统）向本地服务提交一条小票打印任务，入参为 JSON，示例："))
xml.append(code_block('POST /api/v1/print/ticket\n'
                      'Content-Type: application/json\n'
                      '{\n'
                      '  "team_name": "SkyNet",\n'
                      '  "team_id": "TEAM-07",\n'
                      '  "problem_id": "A",\n'
                      '  "problem_title": "A+B Problem",\n'
                      '  "passed_at": "2026-08-20 10:23:45",\n'
                      '  "balloon_color": "Red",\n'
                      '  "rank": 3\n'
                      '}'))
xml.append(p("服务端渲染为小票样式（标题行 + 字段表格 + 分割线），转 PDF 送默认打印机。"
             "小票纸宽按 58mm / 80mm 预设 CSS，保证折行整齐。", spacing_before=60))
xml.append(h2("2.2 场景二：代码打印"))
xml.append(p("打印选手提交的源代码：服务端对源码做语法高亮（自动识别语言，如 C/C++/Python/Java/Go），"
             "按窄行纸宽（建议 58/80mm，字符数上限可配）自动换行与缩进保留，渲染为 PDF 后打印。"
             "高亮目标：关键字、字符串、注释、数字、函数名以不同颜色区分；黑白打印机环境下通过加粗与下划线保证可读性。"))
xml.append(h2("2.3 端到端调用流程（Web → 本地服务 → 打印机 → 状态回传）"))
xml.append(numbered("Web 页面探活：页面加载时向本地服务 GET /healthz 探活，获取服务实际监听端口（若默认端口被占用，"
                    "服务会在启动日志与配置文件中上报实际端口）。", 1))
xml.append(numbered("提交任务：Web 端 POST /api/v1/print/ticket 或 /api/v1/print/code 提交打印任务。", 2))
xml.append(numbered("入队：服务端将任务加入内存队列，分配任务 ID，状态置为 queued（排队中），立即返回任务 ID 与当前状态。", 3))
xml.append(numbered("渲染：后台任务取出任务，将 JSON/源码渲染为 HTML，再经无头 Chromium 转为 PDF（失败则任务标记 failed 并记录原因）。", 4))
xml.append(numbered("打印：PDF 提交给操作系统默认打印机；Windows 与 Linux（CUPS）差异由适配层封装。", 5))
xml.append(numbered("回传状态：任务进入 printing → done（已完成）或 failed（失败 + 原因，如“无可用打印机”“渲染超时”“入参非法”）。", 6))
xml.append(numbered("查询：Web 端 GET /api/v1/tasks/{id} 或 GET /api/v1/tasks?status=queued 查询排队中/已完成/失败任务。", 7))
xml.append(h2("2.4 端口自动协商机制"))
xml.append(numbered("服务启动时先尝试监听固定默认端口（如 18210）。", 1))
xml.append(numbered("若被占用，自动回退到默认端口 + 递增区间内的空闲端口。", 2))
xml.append(numbered("服务把最终实际端口写入 stdout 日志与端口配置文件（port.txt），Web 端探活失败时按配置读取新端口。", 3))
xml.append(numbered("Web 端提供端口输入/自动探测，保证浏览器与本地服务始终能对接。", 4))
xml.append(h2("2.5 任务状态机"))
xml.append(table(
    ["状态", "含义", "可观测行为"],
    [
        ["queued（排队中）", "任务已入队，等待渲染/打印", "提交接口立即返回此状态，可通过队列接口查看排位"],
        ["printing（打印中）", "正在渲染或提交打印机", "状态查询可见，防止重复提交"],
        ["done（已完成）", "成功打印", "返回完成时间、打印页数等摘要"],
        ["failed（失败）", "打印失败", "必须返回可读失败原因（无打印机/渲染失败/入参非法/超时等）"],
    ],
    [2600, 3200, 3226],
))

xml.append(h1("三、必做与不做（范围边界，验收以此为准）"))
xml.append(table(
    ["必做（In Scope，MVP 验收范围）", "不做（Out of Scope，明确排除）"],
    [
        ["1. 气球小票打印：JSON 入参（队名、题号、通过时间等字段）渲染并打印",
         "1. 不实现云打印/远程服务端打印，打印必须发生在浏览器所在本机"],
        ["2. 代码打印：源码渲染、语法高亮、适配小票/窄行纸宽",
         "2. 不做与 Lodop 全量 API 兼容，仅参考其交互模型"],
        ["3. Web 端经 HTTP 调用本地服务提交任务",
         "3. 不做打印预览可视化编辑（仅极简确认/状态展示）"],
        ["4. 任务状态回传：排队中 / 已完成 / 失败及原因",
         "4. 不做账号体系、鉴权、多租户、任务优先级抢占"],
        ["5. 本地服务驱动默认打印机输出（无头 Chromium 渲染 HTML/PDF）",
         "5. 不做打印机驱动安装、打印机管理面板、选择打印机 UI"],
        ["6. Web 与本地服务自动协商端口（固定配置 + 探活 / 可用端口回退）",
         "6. 不做浏览器端实时推送（WebSocket 轮询留待二期）"],
        ["7. 任务查询接口：排队中 / 已完成 / 失败及原因",
         "7. 不做多语言界面、移动端适配"],
        ["8. 跨平台：Windows 与 Linux 双平台可运行，各演示 ≥1 次",
         "8. 不做打印队列持久化（服务重启即清空，任务存内存）"],
        ["9. 打印失败原因可读化（缺打印机、渲染失败、队列异常等）",
         "9. 不做并发大压力场景优化（现场并发量级预估可控）"],
    ],
    [4513, 4513],
))

xml.append(h1("四、人员配置：独立开发"))
xml.append(p("立项人：侯俊。本项目确定由侯俊独立开发完成。依据：", spacing_after=60))
xml.append(bullet("MVP 范围收敛、接口面小，单人可闭环全部技术环节（服务端 + 渲染 + 打印 + Web 对接）。"))
xml.append(bullet("双人收益主要体现在并行开发与相互评审，但会增加沟通成本与接口对齐成本。"))
xml.append(bullet("课题技术深度集中于「渲染 + 打印 + 状态机」，连续推进效率更高。"))
xml.append(bullet("立项人同时承担验收对接，按第五章节验收标准自评并提交演示记录。"))

xml.append(h1("五、风险与沟通方式"))
xml.append(h2("5.1 风险清单（R1–R8）"))
xml.append(table(
    ["编号", "风险描述", "等级", "应对措施"],
    [
        ["R1", "Linux 无头环境下 Chromium 依赖缺失（沙箱/字体/库）", "高",
         "首日（D1）在 Linux 做最小渲染验证；提供 fallback 渲染路径；文档化依赖安装清单"],
        ["R2", "打印机平台差异：Windows 打印 API 与 Linux（CUPS）行为不同", "高",
         "统一抽象 Printer 接口，平台适配层隔离；先打通「渲染→PDF」再切实体机"],
        ["R3", "端口协商失败（默认端口被占用 / 防火墙拦截）", "中",
         "固定端口 + 探活重试 + 自动回退端口 + 服务端上报实际端口（写 port.txt / stdout）"],
        ["R4", "中文与字体渲染：小票字段、代码中文字符乱码或截断", "中",
         "明确字体依赖；渲染前统一 UTF-8；双平台做字符级验收用例"],
        ["R5", "语法高亮与窄行纸宽适配效果差", "中",
         "采用成熟高亮库生成 HTML；CSS 按 58/80mm 纸宽预设；评审前置截图确认"],
        ["R6", "演示环境无实体打印机 / 型号不一致", "中",
         "准备「打印到 PDF」兜底演示方案；提前 1 天确认演示机打印机"],
        ["R7", "状态回传与 Web 端异步展示不同步", "低",
         "状态机单测覆盖；查询接口带时间戳与顺序保证"],
        ["R8", "提交代码含非法/超长内容导致渲染异常", "低",
         "入参长度与字符白名单校验；渲染超时保护"],
    ],
    [800, 3600, 800, 3826],
))
xml.append(h2("5.2 沟通方式"))
xml.append(table(
    ["事项", "方式", "频率"],
    [
        ["每日进度同步", "文字简报（今日完成 / 明日计划 / 阻塞项）", "每日 1 次，17:00 前"],
        ["里程碑评审", "会议 + 现场演示（M1–M6）", "每个里程碑结束"],
        ["问题升级", "阻塞超过 4 小时未解决 → 立即上报，不隔夜", "随时"],
        ["文档沉淀", "接口契约、部署文档随代码入库", "持续"],
    ],
    [2600, 4426, 2000],
))

xml.append(h1("六、主路线与验收说法"))
xml.append(h2("6.1 主路线（里程碑 M1–M6，7 天）"))
xml.append(table(
    ["里程碑", "内容", "可演示产物", "预计完成"],
    [
        ["M1", "Golang 服务骨架 + 健康检查 + 端口协商（探活/回退）", "curl /healthz 返回 OK，端口协商日志可查", "D1（08-20）"],
        ["M2", "打印任务队列 + 状态机（排队中→打印中→已完成/失败）", "提交任务后查询接口返回状态流转", "D2（08-21）"],
        ["M3", "气球小票：JSON 入参 → HTML/PDF 渲染 → 默认打印机输出", "实物小票（或 PDF 兜底）含队名/题号/通过时间", "D3（08-22）"],
        ["M4", "代码打印：语法高亮 + 窄行纸宽适配", "高亮 PDF / 打印样张（窄纸排版合规）", "D4~D5（08-23~24）"],
        ["M5", "任务查询接口完善 + Web 端页面集成（提交/状态展示）", "Web 页面全流程操作演示", "D5~D6（08-24~25）"],
        ["M6", "Windows + Linux 双平台演示各 ≥1 次 + 文档归档", "演示记录（截图/视频 + 实样）", "D7（08-26）"],
    ],
    [1100, 3900, 2926, 1100],
))
xml.append(h2("6.2 验收说法（验收标准，逐条可核验）"))
xml.append(numbered("功能验收：Web 端提交气球小票与代码两类任务，均能通过本机默认打印机输出，且查询接口正确返回"
                    "「排队中 / 已完成 / 失败及原因」。", 1))
xml.append(numbered("入参验收：气球小票 JSON 字段（队名、题号、通过时间等）完整正确落到打印件。", 2))
xml.append(numbered("渲染验收：代码打印含语法高亮，内容在 58/80mm 窄纸宽内不截断、不溢出。", 3))
xml.append(numbered("端口验收：默认端口占用时自动回退可用端口，Web 端探活后可正常对接。", 4))
xml.append(numbered("跨平台验收：同一仓库分别构建 Windows 与 Linux 版本，各完成 ≥1 次全流程演示。", 5))
xml.append(numbered("健壮性验收：无打印机 / 非法入参 / 渲染失败等场景，服务返回明确可读的错误原因，不崩溃。", 6))

xml.append(h1("七、近期风险与明日计划"))
xml.append(h2("7.1 当前重点风险（本周内）"))
xml.append(table(
    ["优先级", "风险", "处理动作", "责任人"],
    [
        ["P0", "R1：Linux 无头 Chromium 渲染链路是否可通（最大技术不确定性）", "明日立即做最小渲染验证", "侯俊"],
        ["P0", "R2：打印 API 平台差异", "明日先打通「渲染→PDF」，实体打印留 M3", "侯俊"],
        ["P1", "R3：端口协商方案可行性", "明日实现探活 + 回退的最小闭环", "侯俊"],
    ],
    [1100, 4000, 2826, 1100],
))
xml.append(h2("7.2 明日计划（2026-08-20，对应 M1 + 风险消解）"))
xml.append(table(
    ["序号", "事项", "验收标准", "完成标志"],
    [
        ["1", "搭建 Golang 项目骨架（cmd/、internal/ 分层，平台适配接口预留）", "go build 双平台（Windows/Linux）通过", "双平台可执行文件产出"],
        ["2", "实现 GET /healthz 健康检查", "curl 返回 200 + JSON", "日志/命令输出可见"],
        ["3", "实现端口协商最小闭环：固定端口探活 → 回退可用端口 → 实际端口上报", "占用默认端口时服务仍可被访问，实际端口可查", "日志输出 + curl 验证"],
        ["4", "Linux 无头 Chromium 最小渲染验证（HTML→PDF 或截图）", "渲染产物成功生成且中文正常", "样张文件产出"],
        ["5", "输出依赖清单文档（Linux 侧 Chromium/字体依赖、Windows 侧说明）", "文档入库，可直接按步骤复现", "文档 commit"],
        ["6", "每日进度简报（含阻塞项）", "17:00 前发出", "简报记录"],
    ],
    [800, 4100, 2926, 1200],
))

xml.append(h1("八、附则"))
xml.append(numbered("本立项书为 MVP 范围界定依据，范围变更须书面更新本文件并重新评审。", 1))
xml.append(numbered("全部代码、接口契约与部署文档随仓库保存，演示产出物（样张/截图/视频）归档。", 2))
xml.append(numbered("若 M1–M6 任一步骤评估超出预估周期 ≥1 天，立项人须第一时间上报并按评审结论调整范围。", 3))
xml.append(spacer(60))

xml.append('<w:sectPr>'
           '<w:pgSz w:w="11906" w:h="16838"/>'
           '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>'
           '</w:sectPr>')
xml.append('</w:body></w:document>')

document_xml = "".join(xml)

# ============ styles.xml ============
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
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/>
    <w:basedOn w:val="Normal"/><w:next w:val="Normal"/>
    <w:pPr><w:keepNext/><w:spacing w:before="160" w:after="80" w:line="300" w:lineRule="auto"/>
    <w:outlineLvl w:val="2"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="404040"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>
  </w:style>
</w:styles>'''

# ============ 打包 ============
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
  <dc:title>项目立项书（详细版）— 浏览器调用本地打印机</dc:title>
  <dc:creator>侯俊</dc:creator>
  <cp:lastModifiedBy>侯俊</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">2026-08-19T00:00:00Z</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">2026-08-19T00:00:00Z</dcterms:modified>
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
