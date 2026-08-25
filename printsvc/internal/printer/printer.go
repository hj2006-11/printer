package printer

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"time"
)

// Adapter 打印机适配器（默认打印机 / 指定打印机 / PDF兜底）
type Adapter struct{}

// NewAdapter 创建适配器
func NewAdapter() *Adapter {
	return &Adapter{}
}

// Print 驱动打印机输出PDF；无实体打印机时PDF本身即为产物。
// 可通过环境变量 CCPC_PRINTER 指定打印机名（D7 G4），未设置时使用系统默认打印机。
// 超时10秒，防止阻塞worker（PowerShell -Wait可能因无打印机/保存对话框而挂起）
func (a *Adapter) Print(pdfPath string) error {
	printerName := os.Getenv("CCPC_PRINTER")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if runtime.GOOS == "windows" {
		if printerName != "" {
			// Windows：指定打印机 —— printui 切换默认 -> 打印 -> 恢复原默认
			script := fmt.Sprintf(
				"$old = (Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Windows' -ErrorAction SilentlyContinue).Device; "+
					"$oldName = if ($old) { ($old -split ',')[0] } else { '' }; "+
					"& rundll32 printui.dll,PrintUIEntry /y /n '%s' | Out-Null; "+
					"Start-Process -FilePath '%s' -Verb Print -Wait; "+
					"if ($oldName -and $oldName -ne '%s') { & rundll32 printui.dll,PrintUIEntry /y /n $oldName | Out-Null }",
				printerName, pdfPath, printerName)
			cmd := exec.CommandContext(ctx, "powershell", "-Command", script)
			out, err := cmd.CombinedOutput()
			if err != nil {
				fmt.Fprintf(os.Stderr, "[printer] 打印到指定打印机[%s]失败（PDF已保留）: %s, err=%v, output=%s\n", printerName, pdfPath, err, string(out))
				return nil // 不视为失败，PDF兜底
			}
		} else {
			// Windows：默认打印机，用Start-Process -Verb Print 调用
			cmd := exec.CommandContext(ctx, "powershell", "-Command",
				fmt.Sprintf("Start-Process -FilePath '%s' -Verb Print -Wait", pdfPath))
			out, err := cmd.CombinedOutput()
			if err != nil {
				// 打印失败时，仅记录警告，PDF已生成作为兜底
				fmt.Fprintf(os.Stderr, "[printer] 打印到默认打印机失败（可能无默认打印机），PDF已保留: %s, err=%v, output=%s\n", pdfPath, err, string(out))
				return nil // 不视为失败，PDF兜底
			}
		}
	} else {
		// Linux：使用 lp 命令，指定打印机时加 -d
		args := []string{pdfPath}
		if printerName != "" {
			args = append([]string{"-d", printerName}, args...)
		}
		cmd := exec.CommandContext(ctx, "lp", args...)
		out, err := cmd.CombinedOutput()
		if err != nil {
			fmt.Fprintf(os.Stderr, "[printer] Linux打印失败（PDF已保留）: %s, err=%v, output=%s\n", pdfPath, err, string(out))
			return nil
		}
	}
	return nil
}
