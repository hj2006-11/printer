package server

import (
	"encoding/json"
	"log"
	"net/http"
	"time"

	"ccpc-printsvc/internal/static"
	"ccpc-printsvc/internal/task"
)

// Server HTTP API Server + 静态页面托管
// 接口契约 v1.0（方案B：REST 资源化 + 按类型分组）见《接口书面约定_20260821.md》
type Server struct {
	addr   string
	queue  *task.Queue
	outDir string
}

// New 创建服务器
func New(addr string, queue *task.Queue, outDir string) *Server {
	return &Server{
		addr:   addr,
		queue:  queue,
		outDir: outDir,
	}
}

// Run 启动HTTP服务
func (s *Server) Run() error {
	mux := http.NewServeMux()

	// API路由（契约 v1.0）
	mux.HandleFunc("/api/v1/healthz", s.handleHealthz)
	mux.HandleFunc("/api/v1/tasks", s.handleCreateTask)
	mux.HandleFunc("/api/v1/tasks/{task_id}", s.handleGetTask)

	// 静态页面（go:embed 内嵌二进制，运行不依赖工作目录）
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		_, _ = w.Write([]byte(static.IndexHTML))
	})

	return http.ListenAndServe(s.addr, LogMiddleware(cors(mux)))
}

// GET /api/v1/healthz 探活
func (s *Server) handleHealthz(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "method not allowed")
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{
		"status":  "ok",
		"service": "ccpc-printsvc",
		"version": "v0.2.0",
	})
}

// submitRequest 提交任务请求体（契约 v1.0：{type, data:{按类型分组}}）
type submitRequest struct {
	Type string          `json:"type"`
	Data json.RawMessage `json:"data"`
}

// ticketPayload 气球小票载荷
type ticketPayload struct {
	Team     string `json:"team"`
	Problem  string `json:"problem"`
	PassTime string `json:"pass_time"`
}

// codePayload 代码打印载荷
type codePayload struct {
	Lang   string `json:"lang"`
	Source string `json:"source"`
}

// POST /api/v1/tasks 提交打印任务
func (s *Server) handleCreateTask(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "method not allowed")
		return
	}

	var req submitRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "INVALID_ARGUMENT", "invalid JSON body: "+err.Error())
		return
	}
	if req.Type != "ticket" && req.Type != "code" {
		writeError(w, http.StatusBadRequest, "INVALID_ARGUMENT", "type must be ticket or code")
		return
	}

	t := &task.Task{Type: req.Type}

	if req.Type == "ticket" {
		var p ticketPayload
		if len(req.Data) == 0 {
			writeError(w, http.StatusBadRequest, "INVALID_ARGUMENT", "data required for ticket")
			return
		}
		if err := json.Unmarshal(req.Data, &p); err != nil {
			writeError(w, http.StatusBadRequest, "INVALID_ARGUMENT", "data invalid for ticket: "+err.Error())
			return
		}
		if p.Team == "" {
			writeError(w, http.StatusBadRequest, "INVALID_ARGUMENT", "data.team required for ticket")
			return
		}
		if p.Problem == "" {
			writeError(w, http.StatusBadRequest, "INVALID_ARGUMENT", "data.problem required for ticket")
			return
		}
		t.Data = task.TaskData{Team: p.Team, Problem: p.Problem, PassTime: p.PassTime}
	} else { // code
		var p codePayload
		if len(req.Data) == 0 {
			writeError(w, http.StatusBadRequest, "INVALID_ARGUMENT", "data required for code")
			return
		}
		if err := json.Unmarshal(req.Data, &p); err != nil {
			writeError(w, http.StatusBadRequest, "INVALID_ARGUMENT", "data invalid for code: "+err.Error())
			return
		}
		if p.Source == "" {
			writeError(w, http.StatusBadRequest, "INVALID_ARGUMENT", "data.source required for code")
			return
		}
		t.Data = task.TaskData{Lang: p.Lang, Source: p.Source}
	}

	id := s.queue.Submit(t)

	writeJSON(w, http.StatusAccepted, map[string]interface{}{
		"task_id":    id,
		"status":     task.StatusPending,
		"created_at": time.Now().Format(time.RFC3339),
	})
}

// GET /api/v1/tasks/{task_id} 查询任务
func (s *Server) handleGetTask(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "method not allowed")
		return
	}
	id := r.PathValue("task_id")
	if id == "" {
		writeError(w, http.StatusBadRequest, "INVALID_ARGUMENT", "task_id required")
		return
	}
	t, ok := s.queue.Get(id)
	if !ok {
		writeError(w, http.StatusNotFound, "NOT_FOUND", "task not found: "+id)
		return
	}
	writeJSON(w, http.StatusOK, t)
}

// writeJSON 输出JSON响应
func writeJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("[server] 写响应失败: %v", err)
	}
}

// writeError 统一错误结构（契约 v1.0）：{"error":{"code":...,"message":...}}
func writeError(w http.ResponseWriter, status int, code, message string) {
	writeJSON(w, status, map[string]interface{}{
		"error": map[string]string{"code": code, "message": message},
	})
}

// cors 简单的CORS中间件，允许本地页面跨域探活
func cors(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

// LogMiddleware 请求日志中间件
func LogMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("[http] %s %s %s", r.Method, r.URL.Path, time.Since(start))
	})
}
