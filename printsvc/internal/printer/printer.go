package printer

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"time"
)

// Adapter 打印机适配器（默认打印机 / PDF兜底）
type Adapter struct{}

// NewAdapter 创建适配器
func NewAdapter() *Adapter {
	return &Adapter{}
}

// Print 驱动系统默认打印机输出PDF；无实体打印机时PDF本身即为产物
// 超时10秒，防止阻塞worker（PowerShell -Wait可能因无打印机而挂起）
func (a *Adapter) Print(pdfPath string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if runtime.GOOS == "windows" {
		// Windows：用Start-Process -Verb Print 调用默认打印
		cmd := exec.CommandContext(ctx, "powershell", "-Command",
			fmt.Sprintf("Start-Process -FilePath '%s' -Verb Print -Wait", pdfPath))
		out, err := cmd.CombinedOutput()
		if err != nil {
			// 打印失败时，仅记录警告，PDF已生成作为兜底
			fmt.Fprintf(os.Stderr, "[printer] 打印到实体打印机失败（可能无默认打印机），PDF已保留: %s, err=%v, output=%s\n", pdfPath, err, string(out))
			return nil // 不视为失败，PDF兜底
		}
	} else {
		// Linux：使用 lp 或 lpr 命令
		cmd := exec.CommandContext(ctx, "lp", pdfPath)
		out, err := cmd.CombinedOutput()
		if err != nil {
			fmt.Fprintf(os.Stderr, "[printer] Linux打印失败，PDF已保留: %s, err=%v, output=%s\n", pdfPath, err, string(out))
			return nil
		}
	}
	return nil
}
