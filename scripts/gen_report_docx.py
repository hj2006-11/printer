import glob, os, zipfile, re

def esc(t):
    t = str(t)
    t = t.replace("&", "&amp;")
    t = t.replace("<", "&lt;")
    t = t.replace(">", "&gt;")
    t = t.replace('"', "&quot;")
    return t

def run(t, bold=False, size=None, color=None):
    s = ""
    if bold:
        s += '<w:b/><w:bCs/>'
    if size:
        s += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    if color:
        s += f'<w:color w:val="{color}"/>'
    return f'<w:r><w:rPr>{s}</w:rPr><w:t xml:space="preserve">{esc(t)}</w:t></w:r>'

def heading(text, level=1):
    sz = {1: 36, 2: 28, 3: 24}.get(level, 24)
    return (f'<w:p><w:pPr><w:pStyle w:val="Heading{level}"/>'
            f'<w:spacing w:before="200" w:after="120"/>'
            f'<w:outlineLvl w:val="{level-1}"/></w:pPr>'
            f'{run(text, bold=True, size=sz)}</w:p>')

def para(text, first_indent=0, left_indent=0):
    ind = ""
    if first_indent or left_indent:
        ind = f'<w:ind w:firstLine="{first_indent}" w:left="{left_indent}"/>'
    return f'<w:p><w:pPr><w:spacing w:before="60" w:after="60"/>{ind}</w:pPr>{run(text)}</w:p>'

def bullet(t, level=0):
    ind = 360 + level * 360
    return (f'<w:p><w:pPr><w:pStyle w:val="ListBullet"/>'
            f'<w:ind w:left="{ind}" w:hanging="360"/>'
            f'<w:numPr><w:ilvl w:val="{level}"/></w:numPr></w:pPr>'
            f'{run(t)}</w:p>')

def numbered(t, num):
    return (f'<w:p><w:pPr><w:pStyle w:val="ListNumber"/>'
            f'<w:ind w:left="540" w:hanging="540"/>'
            f'<w:numPr><w:ilvl w:val="0"/></w:numPr></w:pPr>'
            f'{run(f"{num}. ")}{run(t)}</w:p>')

def bold_para(label, text):
    return (f'<w:p><w:pPr><w:spacing w:before="60" w:after="60"/></w:pPr>'
            f'{run(label, bold=True)}{run(text)}</w:p>')


def build_document():
    paragraphs = []
    
    paragraphs.append(heading('课程项目第 1 天报告', 1))
    paragraphs.append(heading('基本信息', 2))
    paragraphs.append(para('课题编号：CCP-2026-001'))
    paragraphs.append(para('课题名称：浏览器调用本地打印机——基于 Golang 的跨平台本地打印服务（MVP）'))
    paragraphs.append(para('开发方式：独立完成（单人）'))
    paragraphs.append(para('成员 / 立项人：侯俊'))
    paragraphs.append(para('报告日期：2026-08-19（第 1 天）'))
    paragraphs.append(para('工期安排：共 9 天，2026-08-19 至 2026-08-27'))
    
    paragraphs.append(heading('今日目标', 2))
    paragraphs.append(para('今天需要完成三件事：一是选定课题并确认独立开发方式；二是把 9 天内必须交付、可演示、可验收的最小功能范围划清楚，防止后续范围膨胀；三是给出可逐步核对的验收口径，以及主要风险与应对办法。边界一旦明确，后续 8 天按里程碑推进，不在这个范围之外新增功能。'))
    
    paragraphs.append(heading('课题与使用场景', 2))
    paragraphs.append(heading('课题说明', 3))
    paragraphs.append(para('本课题要做一个浏览器调用本地打印机的最小可用服务（MVP）。参考 ACM/ICPC 类竞赛现场的打印队列场景（开源项目 CCPCOJ 含现场打印功能），对标商用方案 Lodop，但走自研轻量路线。核心思路是：用户在浏览器里打开一个本地页面，通过 HTTP 把打印任务提交给本机运行的一个 Golang 服务，服务负责渲染排版并送到默认打印机输出，同时把任务状态回传给页面。'))
    paragraphs.append(heading('选用理由', 3))
    paragraphs.append(para('竞赛现场有两类高频打印需求目前依赖外部方案：一是气球小票（队伍通过某题后打印小票，含队名、题号、通过时间），工作人员凭票派发气球；二是代码打印（打印选手提交的源代码，供裁判核查）。现有商用方案 Lodop 跨平台支持弱、部署复杂、授权费用高，而自研一个轻量 MVP 可以低成本解决这两类需求，同时积累跨平台本地服务的技术经验。'))
    paragraphs.append(heading('主要使用者与场景', 3))
    paragraphs.append(para('主要使用者是竞赛现场的工作人员和裁判。使用场景为：工作人员在浏览器打开本地页面，选择气球小票或代码打印，填写内容后提交；本地服务接收任务、渲染排版、驱动默认打印机输出；页面可随时查询任务状态（排队中 / 已完成 / 失败）。'))
    paragraphs.append(heading('课内交付边界', 3))
    paragraphs.append(para('由于课内环境受限，本课题明确以下交付边界：'))
    paragraphs.append(bullet('无实体打印机时，以打印到 PDF 作为兜底演示方式，PDF 产物路径和任务状态作为核验依据；'))
    paragraphs.append(bullet('Linux 演示环境若本机无法搭建（经实测本机无 WSL），优先采用交叉编译产物 + 远程 Linux 环境验证并截图存档；'))
    paragraphs.append(bullet('演示数据仅使用 3~5 支队伍的模拟数据，不做全库导入；'))
    paragraphs.append(bullet('状态查询采用轮询而非实时推送，降低 Web 端复杂度。'))
    
    paragraphs.append(heading('必做与不做', 2))
    paragraphs.append(heading('必做（9 天结束必须能演示、能验收）', 3))
    paragraphs.append(numbered('本地打印服务：用 Golang 实现，提供 HTTP 接口；默认监听 127.0.0.1:18210，端口被占用时自动回退到可用端口，并把实际端口写入日志与 port.txt。', 1))
    paragraphs.append(numbered('气球小票打印：Web 端提交 JSON（队名、题号、通过时间等字段），本地服务渲染小票排版并输出到系统默认打印机（或打印到 PDF 作为兜底）。', 2))
    paragraphs.append(numbered('代码打印：Web 端提交源代码，本地服务做语法高亮，按 58mm 或 80mm 窄纸宽自动换行，输出打印（或 PDF 兜底）。', 3))
    paragraphs.append(numbered('任务队列与状态：任务提交后返回任务 ID 与排队中状态；提供查询接口，可查排队中 / 已完成 / 失败及失败原因。', 4))
    paragraphs.append(numbered('渲染链路：用无头 Chromium 渲染 HTML 到 PDF，Windows 与 Linux 双平台均能跑通该链路。', 5))
    paragraphs.append(numbered('跨平台演示：Windows 完成至少 1 次端到端演示；Linux 完成至少 1 次渲染链路验证（有实体打印机则出纸，无则以 PDF 产物为准）。', 6))
    paragraphs.append(heading('不做（明确排除，防止范围扩大）', 3))
    paragraphs.append(numbered('不做云打印 / 远程打印，打印必须发生在浏览器所在本机。', 1))
    paragraphs.append(numbered('不做与 Lodop 的全量 API 兼容，仅参考其交互模型。', 2))
    paragraphs.append(numbered('不做账号体系、鉴权、多租户、任务优先级抢占。', 3))
    paragraphs.append(numbered('不做打印预览可视化编辑器，Web 端仅保留提交页和状态展示页。', 4))
    paragraphs.append(numbered('不做打印机管理面板、选择打印机 UI、驱动安装功能。', 5))
    paragraphs.append(numbered('不做 WebSocket 实时推送，用轮询查询代替。', 6))
    paragraphs.append(numbered('不做队列持久化，服务重启即清空，任务仅存内存。', 7))
    paragraphs.append(numbered('不做移动端适配与多语言界面。', 8))
    paragraphs.append(numbered('不做大并发优化与全量数据导入，演示仅用 3~5 支队伍模拟数据。', 9))
    
    paragraphs.append(heading('主路径与验收', 2))
    paragraphs.append(heading('主路径', 3))
    paragraphs.append(para('用户在浏览器打开本地 Web 页面（服务同时托管页面和 API，页面从 location.port 直接获取端口，无需额外协商）→ 页面探活本地服务确认在线 → 选择气球小票或代码打印并填写内容 → 提交 → 本地服务校验入参、入队并返回任务 ID（状态=排队中）→ 后台渲染 HTML 到 PDF → 调用系统默认打印机输出 → 状态流转为已完成或失败+原因 → 用户在页面查询接口看到状态与结果摘要。'))
    paragraphs.append(heading('验收说明（可按步骤核对）', 3))
    paragraphs.append(bold_para('验收 1：小票打印端到端', ''))
    paragraphs.append(para('前提：本机已配置默认打印机（或启用打印到 PDF 虚拟打印机）。操作：在 Web 页选择气球小票，填写队名 Team A、题号 A、通过时间 2026-08-20 10:23:45 并提交。应当看到：页面立即返回任务 ID 且状态为排队中；随后查询该任务状态变为已完成；PDF 产物中完整出现队名、题号、通过时间三个字段且内容正确。实体打印机出纸为加分项，非必达。'))
    paragraphs.append(bold_para('验收 2：端口自动回退', ''))
    paragraphs.append(para('前提：默认端口 18210 已被其他进程占用。操作：启动本地服务，再打开 Web 页。应当看到：服务自动回退到空闲端口（如 18211），并在日志与 port.txt 中上报实际端口；Web 页面探活后成功连接，可正常提交打印任务并返回排队中状态。'))
    paragraphs.append(bold_para('验收 3：代码打印与 Linux 验证', ''))
    paragraphs.append(para('前提：Linux 环境（本地或远程均可）、未安装实体打印机。操作：提交一段含中文注释的 C++ 源码执行代码打印。应当看到：服务渲染出带语法高亮的 PDF，中文注释不乱码，按窄纸宽自动换行不截断，任务状态为已完成（以 PDF 产物路径验证）。'))
    
    paragraphs.append(heading('风险与依赖', 2))
    paragraphs.append(bold_para('1. 环境风险——Linux 无头 Chromium 依赖缺失：', 'Linux 环境下 Chromium 的沙箱、字体、动态库可能缺失，导致渲染失败。应对办法：D2 首日做最小渲染验证，输出依赖安装清单；若依赖缺失严重，启用降级渲染路径（如先用纯文本或截图方式验证）。'))
    paragraphs.append(bold_para('2. 真机风险——无实体打印机或型号不一致：', '演示机可能无实体打印机，或打印机型号不同导致行为差异。应对办法：统一以打印到 PDF 为兜底演示方式；实体打印机出纸作为加分项而非必达项；提前 1 天确认演示机环境。'))
    paragraphs.append(bold_para('3. 渲染风险——中文乱码与窄纸折行截断：', '小票和代码中可能含中文，窄纸宽（58mm/80mm）下折行截断会影响可读性。应对办法：统一 UTF-8 编码；固定字体依赖（Windows 用系统字体，Linux 安装 fonts-noto-cjk）；CSS 按窄纸宽预设；评审前先出截图确认排版效果。'))
    paragraphs.append(bold_para('4. 网络/端口风险——防火墙拦截、端口被占用：', '服务监听地址选择不当会被防火墙拦截，或端口被占用导致服务无法启动。应对办法：服务明确监听 127.0.0.1（回环流量不触发防火墙）；端口协商仅在 18210 被占用时在 18210~18220 内递增回退；服务启动时把实际端口写入 port.txt 和日志。'))
    paragraphs.append(bold_para('5. 数据风险——模拟数据量过大：', '若演示数据过多，会导致报告冗长且演示耗时。应对办法：仅用 3~5 支队伍的模拟数据演示，不做全库下载或批量导入。'))
    
    paragraphs.append(heading('今日完成与自检', 2))
    paragraphs.append(heading('今天实际确定的内容', 3))
    paragraphs.append(bullet('课题编号 CCP-2026-001 与课题名称已确定'))
    paragraphs.append(bullet('独立开发方式已确认，成员为侯俊'))
    paragraphs.append(bullet('9 天最小范围已划定，必做 6 项、不做 9 项'))
    paragraphs.append(bullet('主路径已写清，从浏览器打开页面到查询状态的完整流程'))
    paragraphs.append(bullet('3 条可按步骤核对的验收说明已写清，每条都包含前提→操作→结果'))
    paragraphs.append(bullet('5 项主要风险与应对办法已列出'))
    paragraphs.append(heading('对照验收说明自检', 3))
    paragraphs.append(bullet('验收 1 的前提（Windows 环境 + 浏览器 + 默认打印机）已具备；但操作→结果依赖的本地服务、Web 页面、渲染功能尚未实现，为空。'))
    paragraphs.append(bullet('验收 2 的前提（可占用 18210 的测试条件）可手动模拟；但端口协商代码尚未实现，为空。'))
    paragraphs.append(bullet('验收 3 的前提（Linux 环境）尚未落实，需 D2 定案；渲染与代码打印功能尚未实现，为空。'))
    paragraphs.append(para('以上操作→结果均留待 D2~D8 完成，D9 统一按验收说明逐条核验。'))
    
    paragraphs.append(heading('问题、计划与 AI 沟通', 2))
    paragraphs.append(heading('与 AI 助手协作记录', 3))
    paragraphs.append(heading('不成功的沟通（及改进过程）', 4))
    paragraphs.append(para('第一次给 AI 的指令只描述了起草立项书，没有附带工期天数。AI 默认按 7 天排了里程碑，后来发现本课程要求 9 天（第 1 天定范围，后续 8 天实施），不得不重新调整排期。改进：后续给 AI 的任务描述必须自带工期约束，如第 1 天定范围，后续 8 天实施，共 9 天。'))
    paragraphs.append(para('询问 AI 关于 Linux 演示环境时，AI 默认假设本机有 WSL 或虚拟机，没有先做环境核查。后来在本机实测发现 WSL 未安装，原方案中 Linux 演示的技术路径不真实。改进：AI 给出的技术方案需要本人在实际环境中做最小验证，不能默认假设环境存在。'))
    paragraphs.append(heading('比较有效的沟通', 4))
    paragraphs.append(para('向 AI 明确给出课题背景（竞赛现场打印）、技术栈（Golang + 无头 Chromium + HTTP）、MVP 范围（仅气球小票 + 代码打印）后，AI 产出了可直接使用的立项书结构和验收口径模板，经人工核对字段后采用，节省了从零写文档的时间。'))
    paragraphs.append(para('要求 AI 对技术路径做真实核查后，AI 协助编写了环境检测命令（查 Go 版本、查 Chrome 路径、查默认打印机、WSL 状态），并执行了 Chrome 无头渲染的最小验证，确认了 Windows 侧渲染路径可行。这部分有效是因为指令明确到了执行具体命令并报告结果。'))
    paragraphs.append(heading('明日安排（D2）', 3))
    paragraphs.append(numbered('Linux 演示环境定案：本机实测无 WSL，需在安装 WSL2 / 借用 Linux 机器 / 装虚拟机三选一，D2 上午必须定案。若三选一均不可行，降级为交叉编译 Linux 产物 + 远程环境跑渲染命令并截图存档，并提前告知验收方调整验收 3 的演示方式。', 1))
    paragraphs.append(numbered('Go 服务骨架搭建：初始化项目目录（cmd/printsvc/、internal/{server,render,printer,task,port}/），实现 GET /healthz 健康检查，完成双平台构建（Windows 可执行文件 + Linux 交叉编译产物）。', 2))
    paragraphs.append(numbered('端口协商最小闭环：实现默认端口 18210 监听，被占用时回退到 18210~18220 内可用端口，实际端口写入日志与 port.txt。用另一进程占住 18210 验证回退行为。', 3))
    paragraphs.append(numbered('渲染子模块 v0：把已实测验证的 Chrome 无头渲染命令封装为 Go 函数，生成小票 PDF 样张，人工目检中文是否正常。同时编写 Linux 依赖清单（chromium、fonts-noto-cjk、cups）。', 4))
    
    return ''.join(paragraphs)


base = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(os.path.dirname(base), '第1天报告_20260819.docx')

body_xml = build_document()

wml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    ' xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"'
    ' mc:Ignorable="w14 w15 w16se w16cid w16 w16cex w16sdtdh wp14">'
    '<w:body>' + body_xml + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
    '<w:pgMar w:top="1440" w:right="1800" w:bottom="1440" w:left="1800" w:header="720" w:footer="720" w:gutter="0"/>'
    '<w:cols w:space="720"/>' + '</w:sectPr></w:body></w:document>'
)

styles_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="宋体" w:eastAsia="宋体" w:hAnsi="宋体" w:cs="宋体"/>'
    '<w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="en-US" w:eastAsia="zh-CN"/></w:rPr></w:rPrDefault>'
    '<w:pPrDefault><w:pPr><w:spacing w:line="360" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
    '<w:name w:val="Normal"/><w:qFormat/><w:rPr><w:rFonts w:ascii="宋体" w:eastAsia="宋体" w:hAnsi="宋体" w:cs="宋体"/>'
    '<w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading1">'
    '<w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:spacing w:before="360" w:after="200"/><w:outlineLvl w:val="0"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="黑体" w:eastAsia="黑体" w:hAnsi="黑体"/>'
    '<w:b/><w:bCs/><w:sz w:val="36"/><w:szCs w:val="36"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading2">'
    '<w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:spacing w:before="280" w:after="160"/><w:outlineLvl w:val="1"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="黑体" w:eastAsia="黑体" w:hAnsi="黑体"/>'
    '<w:b/><w:bCs/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading3">'
    '<w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:spacing w:before="200" w:after="120"/><w:outlineLvl w:val="2"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="黑体" w:eastAsia="黑体" w:hAnsi="黑体"/>'
    '<w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading4">'
    '<w:name w:val="heading 4"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:spacing w:before="160" w:after="80"/><w:outlineLvl w:val="3"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="黑体" w:eastAsia="黑体" w:hAnsi="黑体"/>'
    '<w:b/><w:bCs/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="ListBullet">'
    '<w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:pStyle w:val="ListBullet"/>'
    '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
    '<w:spacing w:before="40" w:after="40"/></w:pPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="ListNumber">'
    '<w:name w:val="List Number"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:pStyle w:val="ListNumber"/>'
    '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr>'
    '<w:spacing w:before="40" w:after="40"/></w:pPr></w:style>'
    '<w:num w:numId="1"><w:abstractNumId w:val="1"/></w:num>'
    '<w:num w:numId="2"><w:abstractNumId w:val="2"/></w:num>'
    '<w:abstractNum w:abstractNumId="1" w:multiLevelType="hybridMultilevel">'
    '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
    '<w:lvlText w:val="\u2022"/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="360" w:hanging="360"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/></w:rPr></w:lvl>'
    '<w:lvl w:ilvl="1"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
    '<w:lvlText w:val="\u2013"/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/></w:rPr></w:lvl>'
    '<w:lvl w:ilvl="2"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
    '<w:lvlText w:val="\u25aa"/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="1080" w:hanging="360"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/></w:rPr></w:lvl>'
    '</w:abstractNum>'
    '<w:abstractNum w:abstractNumId="2" w:multiLevelType="hybridMultilevel">'
    '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/>'
    '<w:lvlText w:val="%1."/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="540" w:hanging="540"/></w:pPr></w:lvl>'
    '<w:lvl w:ilvl="1"><w:start w:val="1"/><w:numFmt w:val="decimal"/>'
    '<w:lvlText w:val="%1.%2."/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="1080" w:hanging="540"/></w:pPr></w:lvl>'
    '<w:lvl w:ilvl="2"><w:start w:val="1"/><w:numFmt w:val="decimal"/>'
    '<w:lvlText w:val="%1.%2.%3."/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="1620" w:hanging="540"/></w:pPr></w:lvl>'
    '</w:abstractNum>'
    '</w:styles>'
)

rels_doc_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
    'Target="styles.xml"/>'
    '</Relationships>'
)

rels_pkg_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
    'Target="docProps/core.xml"/>'
    '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
    'Target="docProps/app.xml"/>'
    '</Relationships>'
)

core_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
    'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
    '<dc:title>课程项目第 1 天报告</dc:title>'
    '<dc:subject>浏览器调用本地打印机</dc:subject>'
    '<dc:creator>侯俊</dc:creator>'
    '<cp:lastModifiedBy>侯俊</cp:lastModifiedBy>'
    '<cp:revision>1</cp:revision>'
    '<dcterms:created xsi:type="dcterms:W3CDTF">2026-08-19T00:00:00Z</dcterms:created>'
    '<dcterms:modified xsi:type="dcterms:W3CDTF">2026-08-19T00:00:00Z</dcterms:modified>'
    '</cp:coreProperties>'
)

app_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
    '<Template>Normal.dotm</Template>'
    '<TotalTime>0</TotalTime>'
    '<Pages>1</Pages>'
    '<Words>0</Words>'
    '<Characters>0</Characters>'
    '<Application>Microsoft Office Word</Application>'
    '<DocSecurity>0</DocSecurity>'
    '<Lines>0</Lines>'
    '<Paragraphs>0</Paragraphs>'
    '<ScaleCrop>false</ScaleCrop>'
    '<Company></Company>'
    '<LinksUpToDate>false</LinksUpToDate>'
    '<CharactersWithSpaces>0</CharactersWithSpaces>'
    '<SharedDoc>false</SharedDoc>'
    '<HyperlinksChanged>false</HyperlinksChanged>'
    '<AppVersion>16.0000</AppVersion>'
    '</Properties>'
)

content_types = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
    '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
    '</Types>'
)

with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('[Content_Types].xml', content_types)
    zf.writestr('_rels/.rels', rels_pkg_xml)
    zf.writestr('word/document.xml', wml)
    zf.writestr('word/styles.xml', styles_xml)
    zf.writestr('word/_rels/document.xml.rels', rels_doc_xml)
    zf.writestr('docProps/core.xml', core_xml)
    zf.writestr('docProps/app.xml', app_xml)

print('OK', out_path)
