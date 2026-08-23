package render

import (
	"context"
	"fmt"
	"html/template"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

// Engine HTML/PDF渲染引擎（基于无头Chromium）
type Engine struct {
	outDir      string
	chromePath  string
}

// NewEngine 创建渲染引擎，outDir为PDF输出目录
func NewEngine(outDir string) *Engine {
	chrome := findChrome()
	return &Engine{
		outDir:     outDir,
		chromePath: chrome,
	}
}

// RenderTicket 渲染气球小票，返回PDF路径
func (e *Engine) RenderTicket(team, problem, passTime string) (string, error) {
	html := ticketHTML(team, problem, passTime)
	return e.renderHTML(html, "ticket")
}

// RenderCode 渲染代码打印，返回PDF路径
func (e *Engine) RenderCode(source, lang string) (string, error) {
	html := codeHTML(source, lang)
	return e.renderHTML(html, "code")
}

// renderHTML 通用渲染：写临时HTML -> Chrome headless -> PDF
func (e *Engine) renderHTML(htmlContent, prefix string) (string, error) {
	// 1. 写临时HTML（用纳秒时间戳保证唯一，避免并发冲突）
	ts := time.Now().UnixNano()
	tmpHTML := filepath.Join(e.outDir, fmt.Sprintf("%s_%d.html", prefix, ts))
	if err := os.WriteFile(tmpHTML, []byte(htmlContent), 0644); err != nil {
		return "", fmt.Errorf("写HTML失败: %w", err)
	}
	defer os.Remove(tmpHTML)

	// 2. Chrome headless 生成PDF（30秒超时，防止Chrome僵死阻塞worker）
	pdfPath := filepath.Join(e.outDir, fmt.Sprintf("%s_%d.pdf", prefix, ts))
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, e.chromePath,
		"--headless",
		"--disable-gpu",
		"--no-sandbox",
		"--disable-software-rasterizer",
		fmt.Sprintf("--print-to-pdf=%s", pdfPath),
		"--run-all-compositor-stages-before-draw",
		"--virtual-time-budget=5000",
		"file:///"+strings.ReplaceAll(tmpHTML, "\\", "/"),
	)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("chrome渲染失败: %w, output: %s", err, string(out))
	}
	return pdfPath, nil
}

// findChrome 查找Chrome/Chromium路径
func findChrome() string {
	candidates := []string{
		`C:\Program Files\Google\Chrome\Application\chrome.exe`,
		`C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`,
	}
	if runtime.GOOS == "linux" {
		candidates = []string{
			"/usr/bin/chromium",
			"/usr/bin/chromium-browser",
			"/usr/bin/google-chrome",
		}
	}
	for _, c := range candidates {
		if _, err := os.Stat(c); err == nil {
			return c
		}
	}
	// 尝试从PATH找
	if p, err := exec.LookPath("chromium"); err == nil {
		return p
	}
	if p, err := exec.LookPath("google-chrome"); err == nil {
		return p
	}
	return "chrome"
}

// ticketHTML 生成气球小票HTML（58mm窄纸宽）
func ticketHTML(team, problem, passTime string) string {
	if passTime == "" {
		passTime = "--" // 接口约定：pass_time 为空时渲染为 --
	}
	const tpl = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body { width: 58mm; margin: 0; padding: 4mm; font-family: "Microsoft YaHei", "SimHei", sans-serif; font-size: 14px; }
.header { text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 4mm; border-bottom: 1px dashed #000; padding-bottom: 2mm; }
.row { margin: 2mm 0; }
.label { font-weight: bold; }
.footer { margin-top: 4mm; text-align: center; font-size: 12px; color: #666; border-top: 1px dashed #000; padding-top: 2mm; }
</style>
</head>
<body>
<div class="header">气球小票</div>
<div class="row"><span class="label">队名：</span>{{.Team}}</div>
<div class="row"><span class="label">题号：</span>{{.Problem}}</div>
<div class="row"><span class="label">通过时间：</span>{{.PassTime}}</div>
<div class="footer">CCPC Print Service</div>
</body>
</html>`
	t, _ := template.New("ticket").Parse(tpl)
	var buf strings.Builder
	t.Execute(&buf, map[string]string{
		"Team": team, "Problem": problem, "PassTime": passTime,
	})
	return buf.String()
}

// codeHTML 生成代码打印HTML（80mm窄纸宽，语法高亮）
func codeHTML(source, lang string) string {
	if lang == "" {
		lang = "text" // 接口约定：lang 为空时渲染为 text
	}
	// 源码由 html/template 在 {{.Source}} 处自动转义，保证特殊字符安全显示
	const tpl = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body { width: 80mm; margin: 0; padding: 4mm; font-family: "Consolas", "Courier New", monospace; font-size: 10px; }
.header { font-size: 12px; font-weight: bold; margin-bottom: 2mm; border-bottom: 1px solid #000; }
pre { white-space: pre-wrap; word-wrap: break-word; margin: 0; line-height: 1.4; }
.keyword { font-weight: bold; color: #0000aa; }
</style>
</head>
<body>
<div class="header">代码打印 ({{.Lang}})</div>
<pre>{{.Source}}</pre>
</body>
</html>`
	t, _ := template.New("code").Parse(tpl)
	var buf strings.Builder
	t.Execute(&buf, map[string]string{
		"Source": source, "Lang": lang,
	})
	return buf.String()
}
