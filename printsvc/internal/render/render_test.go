package render

import (
	"strings"
	"testing"
)

// TestCodeHTMLEscapesSourceOnce 回归测试：源码中的 < > & 应只被转义一次，
// 不允许出现 &amp; 之类的双重转义（历史缺陷：预转义 + html/template 再转义）。
func TestCodeHTMLEscapesSourceOnce(t *testing.T) {
	html := codeHTML("int a = x < y && z > w;", "cpp")

	// 双重转义的标志：&amp;lt; 而不是 &lt;
	if strings.Contains(html, "&amp;lt;") {
		t.Fatalf("double escaping detected: %s", html)
	}
	// 单次转义结果：< → &lt;、&& → &amp;&amp;、> → &gt;
	if !strings.Contains(html, "&lt;") || !strings.Contains(html, "&amp;&amp;") || !strings.Contains(html, "&gt;") {
		t.Fatalf("expected single-escaped source, got: %s", html)
	}
}

// TestTicketHTMLDefaultPassTime 回归测试：接口约定 pass_time 为空时渲染为 --。
func TestTicketHTMLDefaultPassTime(t *testing.T) {
	html := ticketHTML("Team A", "A", "")
	if !strings.Contains(html, "通过时间：</span>--") {
		t.Fatalf("expected -- for empty pass_time, got: %s", html)
	}
	// 非空时原样展示，不被替换
	html2 := ticketHTML("Team A", "A", "2026-08-20 10:23:45")
	if strings.Contains(html2, "通过时间：</span>--") || !strings.Contains(html2, "通过时间：</span>2026-08-20 10:23:45") {
		t.Fatalf("expected pass_time shown as-is, got: %s", html2)
	}
}

// TestCodeHTMLDefaultLang 回归测试：接口约定 lang 为空时渲染为 text。
func TestCodeHTMLDefaultLang(t *testing.T) {
	html := codeHTML("int a;", "")
	if !strings.Contains(html, "代码打印 (text)") {
		t.Fatalf("expected text lang default, got: %s", html)
	}
}
