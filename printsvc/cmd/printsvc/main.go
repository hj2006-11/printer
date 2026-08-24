package main

import (
	"log"
	"os"
	"path/filepath"

	"ccpc-printsvc/internal/port"
	"ccpc-printsvc/internal/printer"
	"ccpc-printsvc/internal/render"
	"ccpc-printsvc/internal/server"
	"ccpc-printsvc/internal/task"
)

func main() {
	// 1. 端口协商：默认18210，回退18210~18220
	listenAddr, err := port.FindAvailablePort(18210, 18220)
	if err != nil {
		// G3 优雅降级：全范围占用时明确报错退出，不再 panic
		log.Fatalf("[main] %v", err)
	}
	log.Printf("[main] 服务监听地址: %s", listenAddr)

	// 2. 工作目录（用于存放PDF输出和port.txt）
	wd, err := os.Getwd()
	if err != nil {
		log.Fatalf("[main] 获取工作目录失败: %v", err)
	}
	outDir := filepath.Join(wd, "output")
	os.MkdirAll(outDir, 0755)

	// 3. 初始化各模块
	rdr := render.NewEngine(outDir)
	prn := printer.NewAdapter()
	queue := task.NewQueue(rdr, prn, outDir)
	queue.Start()

	// 4. 启动HTTP服务（同时托管静态页面和API）
	srv := server.New(listenAddr, queue, outDir)
	log.Printf("[main] 启动服务，访问 http://%s", listenAddr)
	if err := srv.Run(); err != nil {
		log.Fatalf("[main] 服务启动失败: %v", err)
	}
}
