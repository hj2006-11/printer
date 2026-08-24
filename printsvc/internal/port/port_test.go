package port

import (
	"fmt"
	"net"
	"strings"
	"testing"
)

// 测试用端口段（避开常用端口，避免与本机真实服务冲突）
const (
	base   = 28310
	base10 = 28320
)

// TestFindAvailablePortNormal 正常场景：范围未被占满，应返回首个可用地址。
func TestFindAvailablePortNormal(t *testing.T) {
	addr, err := FindAvailablePort(base, base10)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !strings.HasPrefix(addr, "127.0.0.1:") {
		t.Fatalf("addr = %q, want 127.0.0.1:port", addr)
	}
	// 返回的地址应真实可监听
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		t.Fatalf("addr %s not listenable: %v", addr, err)
	}
	ln.Close()
}

// TestFindAvailablePortFallback 起点被占用时回退到下一个端口。
func TestFindAvailablePortFallback(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:28341")
	if err != nil {
		t.Fatalf("setup: %v", err)
	}
	defer ln.Close()

	addr, err := FindAvailablePort(28341, 28350)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if addr != "127.0.0.1:28342" {
		t.Fatalf("addr = %s, want 127.0.0.1:28342", addr)
	}
}

// TestFindAvailablePortAllBusy G3 全范围占用：必须返回 error 而非 panic。
func TestFindAvailablePortAllBusy(t *testing.T) {
	// 占用整个范围
	var listeners []net.Listener
	for p := 28351; p <= 28360; p++ {
		ln, err := net.Listen("tcp", fmt.Sprintf("127.0.0.1:%d", p))
		if err != nil {
			t.Fatalf("setup port %d: %v", p, err)
		}
		listeners = append(listeners, ln)
	}
	defer func() {
		for _, l := range listeners {
			l.Close()
		}
	}()

	// 必须不 panic（原实现 panic），返回 error
	defer func() {
		if r := recover(); r != nil {
			t.Fatalf("FindAvailablePort panicked on all-busy, want graceful error: %v", r)
		}
	}()
	addr, err := FindAvailablePort(28351, 28360)
	if err == nil {
		t.Fatalf("expected error when all ports busy, got addr=%s", addr)
	}
	if !strings.Contains(err.Error(), "全部被占用") {
		t.Fatalf("error message = %q, want contains 全部被占用", err.Error())
	}
}
