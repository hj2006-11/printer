package printer

import (
	"testing"
)

// TestWindowsDefaultPrinter 仅验证 windowsDefaultPrinter 解析逻辑（Windows 下取注册表 Device 键第一段）。
// 解析逻辑是纯字符串处理，独立于真实注册表，可跨平台测试。
func TestWindowsDefaultPrinter(t *testing.T) {
	cases := []struct{ name, want string }{
		{"Microsoft Print to PDF,winspool,Ne02:", "Microsoft Print to PDF"},
		{"Microsoft XPS Document Writer,winspool,Ne01:", "Microsoft XPS Document Writer"},
		{"  ,  ", ""},
		{"", ""},
	}
	for _, c := range cases {
		if got := parsePrinterName(c.name); got != c.want {
			t.Errorf("parsePrinterName(%q) = %q, want %q", c.name, got, c.want)
		}
	}
}
