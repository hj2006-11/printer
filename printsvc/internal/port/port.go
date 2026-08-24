package port

import (
	"fmt"
	"log"
	"net"
	"os"
	"path/filepath"
)

// FindAvailablePort 从 start~end 范围内找一个可用端口监听，
// 并把实际地址写入当前目录的 port.txt 和日志。
// 格式: 127.0.0.1:port
// 全范围占用时返回 error（D6 G3：原实现 panic，改为优雅降级，由调用方决定退出策略）。
func FindAvailablePort(start, end int) (string, error) {
	for p := start; p <= end; p++ {
		addr := fmt.Sprintf("127.0.0.1:%d", p)
		ln, err := net.Listen("tcp", addr)
		if err == nil {
			ln.Close()
			// 写入 port.txt
			wd, _ := os.Getwd()
			f, err := os.Create(filepath.Join(wd, "port.txt"))
			if err == nil {
				fmt.Fprintf(f, "%s\n", addr)
				f.Close()
			}
			log.Printf("[port] 选定端口: %s", addr)
			return addr, nil
		}
		log.Printf("[port] 端口 %d 被占用，尝试下一个", p)
	}
	return "", fmt.Errorf("端口 %d~%d 全部被占用，无可用端口", start, end)
}
