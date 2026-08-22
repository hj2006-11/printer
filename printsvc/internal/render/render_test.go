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
