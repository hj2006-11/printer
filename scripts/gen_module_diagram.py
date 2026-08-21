"""Generate a refined module diagram for the local print service (D2 report).

Run: python scripts/gen_module_diagram.py
Output: module_diagram_d2.png (workspace root)
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont

OUT_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "module_diagram_d2.png"))

# ---------------- canvas ----------------
W, H = 1700, 1150
BG_TOP = (245, 248, 252)
BG_BOTTOM = (255, 255, 255)

# ---------------- palette ----------------
# layer theme: (label, container_bg, container_border, accent)
THEME = {
    "web":    ("Web 展示层",    (232, 241, 251), (46, 117, 182),  (46, 117, 182)),
    "api":    ("HTTP 接入层",   (230, 247, 247), (31, 138, 140),  (31, 138, 140)),
    "task":   ("任务与状态层",  (253, 240, 231), (197, 90, 17),   (197, 90, 17)),
    "render": ("渲染与打印层",  (242, 237, 250), (112, 48, 160),  (112, 48, 160)),
    "ext":    ("外部系统",      (234, 247, 236), (76, 154, 42),   (76, 154, 42)),
}

# ---------------- fonts ----------------
def get_font(size):
    for name in ["Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "msyh.ttc", "Arial Unicode MS"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

F_TITLE = get_font(34)
F_SUBTITLE = get_font(16)
F_LAYER = get_font(17)
F_NAME = get_font(19)
F_SUB = get_font(13)
F_LABEL = get_font(12)
F_NOTE = get_font(13)

# single RGBA canvas + one draw object
img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
draw = ImageDraw.Draw(img)

# ---------------- helpers ----------------
def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

def text_size(text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0], b[3] - b[1]

def draw_gradient_bg():
    for y in range(H):
        color = lerp_color(BG_TOP, BG_BOTTOM, y / H) + (255,)
        draw.line((0, y, W, y), fill=color)

def rounded_rect(xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill,
                           outline=outline, width=width)

def draw_badge(cx, cy, r, text, font, bg, fg=(255, 255, 255)):
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=bg)
    tw, th = text_size(text, font)
    draw.text((cx - tw / 2, cy - th / 2 - 1), text, font=font, fill=fg)

def wrap_text(text, max_w, font, separator=" / "):
    """Split sub-description into up to 2 lines by ' / '."""
    words = text.split(separator)
    lines = []
    line = ""
    for wd in words:
        candidate = line + separator + wd if line else wd
        if text_size(candidate, font)[0] <= max_w:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = wd
    if line:
        lines.append(line)
    return lines[:2]

def draw_module(cx, cy, w, h, num, name, sub, theme_key):
    """Draw a module card with shadow, accent strip, badge, name and description."""
    x1, y1, x2, y2 = cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2
    _, _, _, accent = THEME[theme_key]
    # soft shadow
    draw.rounded_rectangle((x1 + 4, y1 + 7, x2 + 4, y2 + 7), 14, fill=(30, 40, 60, 45))
    # card
    draw.rounded_rectangle((x1, y1, x2, y2), 14, fill=(255, 255, 255),
                           outline=accent, width=2)
    # accent top strip
    draw.rounded_rectangle((x1 + 10, y1 + 8, x2 - 10, y1 + 14), 3, fill=accent)
    # number badge
    if isinstance(num, int):
        draw_badge(x1 + 34, y1 + 40, 16, str(num), F_LABEL, accent)
    # name
    draw.text((x1 + 58, y1 + 27), name, font=F_NAME, fill=(25, 30, 38))
    # sub description
    lines = wrap_text(sub, w - 80, F_SUB)
    ty = y1 + 56
    for ln in lines:
        draw.text((x1 + 30, ty), ln, font=F_SUB, fill=(105, 112, 122))
        ty += 21

def draw_layer_container(x1, y1, x2, y2, theme_key):
    label, bg, border, accent = THEME[theme_key]
    draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=bg,
                           outline=border, width=2)
    tw, th = text_size(label, F_LAYER)
    px1, py1 = x1 + 18, y1 - 15
    px2, py2 = px1 + tw + 36, py1 + 30
    draw.rounded_rectangle((px1, py1, px2, py2), 15, fill=(255, 255, 255),
                           outline=border, width=2)
    draw.text((px1 + 18, py1 + 5), label, font=F_LAYER, fill=accent)

def draw_arrow(start, end, label=None, curved=False, color=(90, 96, 106)):
    """Straight or curved arrow with arrowhead and optional label."""
    x1, y1 = start
    x2, y2 = end
    if curved:
        mx = (x1 + x2) / 2
        cx = mx + (44 if x2 < x1 else -44)
        cy = (y1 + y2) / 2 + (36 if y2 > y1 else -36)
        steps = 48
        pts = []
        for i in range(steps + 1):
            t = i / steps
            ix = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t ** 2 * x2
            iy = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t ** 2 * y2
            pts.append((ix, iy))
        draw.line(pts, fill=color, width=2)
        label_pos = pts[len(pts) // 2]
    else:
        draw.line((x1, y1, x2, y2), fill=color, width=2)
        label_pos = ((x1 + x2) / 2, (y1 + y2) / 2)
    angle = math.atan2(y2 - y1, x2 - x1)
    hl = 11
    a1 = angle + math.radians(28)
    a2 = angle - math.radians(28)
    draw.polygon([
        (x2, y2),
        (x2 - hl * math.cos(a1), y2 - hl * math.sin(a1)),
        (x2 - hl * math.cos(a2), y2 - hl * math.sin(a2)),
    ], fill=color, outline=color)
    if label:
        lw, lh = text_size(label, F_LABEL)
        lx, ly = label_pos
        pad = 4
        draw.rounded_rectangle((lx - lw / 2 - pad, ly - lh / 2 - pad - 2,
                                lx + lw / 2 + pad, ly + lh / 2 + pad - 2),
                               6, fill=(255, 255, 255, 230), outline=color, width=1)
        draw.text((lx - lw / 2, ly - lh / 2 - 2), label, font=F_LABEL, fill=color)

def draw_person_icon(cx, cy, scale=1.0, color=(46, 117, 182)):
    r = 16 * scale
    draw.ellipse((cx - r, cy - r - 8 * scale, cx + r, cy + r - 8 * scale), fill=color)
    draw.pieslice((cx - 22 * scale, cy - 6 * scale, cx + 22 * scale, cy + 34 * scale),
                  180, 360, fill=color)

# ---------------- render ----------------
draw_gradient_bg()

# title
title = "本地打印服务完整模块图（D2）"
tw, th = text_size(title, F_TITLE)
draw.text(((W - tw) / 2, 26), title, font=F_TITLE, fill=(25, 45, 70))
sub = "课题 CCP-2026-001 · 浏览器调用本地打印机 · 基于 Golang 的跨平台本地打印服务（MVP） · 2026-08-20"
sw, sh = text_size(sub, F_SUBTITLE)
draw.text(((W - sw) / 2, 74), sub, font=F_SUBTITLE, fill=(110, 120, 132))

# actor card (browser user)
ax, ay = 210, 300
draw_person_icon(ax - 62, ay - 8, scale=1.1)
draw.rounded_rectangle((ax - 100, ay - 52, ax + 100, ay + 52), 16,
                       fill=(255, 250, 242), outline=(196, 118, 48), width=2)
draw.text((ax - 58, ay - 30), "浏览器用户", font=F_NAME, fill=(80, 55, 25))
draw.text((ax - 58, ay - 2), "工作人员 / 裁判", font=F_SUB, fill=(150, 110, 60))

# layer 1: web
draw_layer_container(400, 180, 1560, 330, "web")
draw_module(980, 255, 560, 100, 1, "Web Frontend", "提交页 / 状态页 / 自动获取端口", "web")

# layer 2: api
draw_layer_container(80, 360, 1620, 560, "api")
draw_module(980, 460, 460, 120, 2, "HTTP API Server", "路由 / 入参校验 / 任务分发", "api")
draw_module(280, 430, 260, 100, 3, "Port Manager", "18210 监听 / 占用递增回退", "api")
draw_module(1420, 430, 260, 100, 4, "Health Check", "GET /healthz 探活", "api")

# layer 3: task
draw_layer_container(160, 590, 1540, 740, "task")
draw_module(620, 665, 380, 100, 5, "Task Queue", "入队 / 调度 / 状态联动", "task")
draw_module(1080, 665, 380, 100, 6, "Status Manager", "排队中 / 已完成 / 失败及原因", "task")

# layer 4: render
draw_layer_container(160, 770, 1540, 920, "render")
draw_module(620, 845, 380, 100, 7, "Render Engine", "HTML → PDF / 无头 Chromium", "render")
draw_module(1060, 845, 380, 100, 8, "Printer Adapter", "默认打印机 / PDF 兜底", "render")

# external printer
draw_module(1510, 845, 220, 100, None, "默认打印机 / PDF", "CUPS / 打印子系统", "ext")

# ---------------- arrows ----------------
draw_arrow((310, 290), (700, 255), "打开页面")
draw_arrow((980, 305), (980, 400), "提交 / 查询")
draw_arrow((1240, 290), (1350, 380), "探活", curved=True)
draw_arrow((830, 520), (620, 615), "创建任务")
draw_arrow((1130, 520), (1080, 615), "读 / 写状态")
draw_arrow((810, 665), (885, 665), "更新状态")
draw_arrow((620, 715), (620, 795), "调度渲染")
draw_arrow((810, 845), (865, 845), "PDF")
draw_arrow((1250, 845), (1400, 845), "打印输出")

# ---------------- legend / notes ----------------
draw.rounded_rectangle((40, 955, 1660, 1110), 16, fill=(255, 255, 255, 255),
                       outline=(200, 208, 218), width=2)
notes = [
    "说明：1) 浏览器用户通过服务托管的本地页面提交打印任务，页面自动获取实际端口。",
    "2) Port Manager 负责 18210 默认监听及 18210~18220 占用回退；Health Check 供页面先确认服务在线。",
    "3) Render Engine 用无头 Chromium 将 HTML 渲染为 PDF，Printer Adapter 优先驱动默认打印机，无打印机时打印到 PDF。",
    "4) Status Manager 在内存中维护任务状态（排队中 / 已完成 / 失败），服务重启后清空。",
]
ny = 980
for n in notes:
    draw.text((60, ny), n, font=F_NOTE, fill=(80, 88, 98))
    ny += 26
draw.text((60, ny + 2), "模块编号即开发顺序，模块 1~8 均可对应到第 1 天核心故事。",
          font=F_NOTE, fill=(46, 117, 182))

img.convert("RGB").save(OUT_PATH, "PNG")
print("Saved:", OUT_PATH)
