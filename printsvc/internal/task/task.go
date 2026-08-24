package task

import (
	"fmt"
	"log"
	"path/filepath"
	"sync"
	"time"
)

// Status 任务状态
type Status string

const (
	StatusPending   Status = "pending"   // 排队中
	StatusCompleted Status = "completed" // 已完成
	StatusFailed    Status = "failed"    // 失败
)

// Task 打印任务（接口约定 v1.0：data 按 type 分组）
type Task struct {
	ID         string    `json:"task_id"`
	Type       string    `json:"type"`        // "ticket" | "code"
	Status     Status    `json:"status"`
	Message    string    `json:"message,omitempty"`     // 失败原因
	OutputPath string    `json:"output_path,omitempty"` // PDF产物路径
	CreatedAt  time.Time `json:"created_at"`
	Data       TaskData  `json:"data"` // 按 type 分组的具体载荷
}

// TaskData 按类型分组的载荷：ticket 用 Team/Problem/PassTime，code 用 Lang/Source
type TaskData struct {
	// ticket 载荷
	Team     string `json:"team,omitempty"`
	Problem  string `json:"problem,omitempty"`
	PassTime string `json:"pass_time,omitempty"`
	// code 载荷
	Lang   string `json:"lang,omitempty"`
	Source string `json:"source,omitempty"`
}

// Renderer 渲染器接口：ticket 58mm / code 80mm，返回PDF路径。
// render.Engine 实现该接口（D6 为可测试性抽象，行为不变）。
type Renderer interface {
	RenderTicket(team, problem, passTime string) (string, error)
	RenderCode(source, lang string) (string, error)
}

// Printer 打印机接口：输出PDF到默认打印机，PDF兜底。
// printer.Adapter 实现该接口（D6 为可测试性抽象，行为不变）。
type Printer interface {
	Print(pdfPath string) error
}

// Queue 任务队列与状态管理器
type Queue struct {
	ch      chan *Task
	tasks   map[string]*Task
	mu      sync.RWMutex
	rdr     Renderer
	prn     Printer
	outDir  string
	counter int
}

// NewQueue 创建队列，rdr=渲染引擎, prn=打印机适配器
func NewQueue(rdr Renderer, prn Printer, outDir string) *Queue {
	return &Queue{
		ch:     make(chan *Task, 10),
		tasks:  make(map[string]*Task),
		rdr:    rdr,
		prn:    prn,
		outDir: outDir,
	}
}

// Start 启动后台worker处理队列
func (q *Queue) Start() {
	go q.worker()
}

// Submit 提交任务，返回taskID
func (q *Queue) Submit(t *Task) string {
	q.mu.Lock()
	q.counter++
	t.ID = fmt.Sprintf("T%04d-%d", q.counter, time.Now().Unix())
	t.Status = StatusPending
	t.CreatedAt = time.Now()
	q.tasks[t.ID] = t
	q.mu.Unlock()

	q.ch <- t
	log.Printf("[task] 提交任务 %s, 类型=%s", t.ID, t.Type)
	return t.ID
}

// Get 查询任务状态。
// 返回任务副本而非内部指针：调用方在锁外读取字段不会与 worker 的 update 写冲突（D6 竞态修复，
// 由 go test -race 在 G2 边界测试中发现：原实现返回 *Task 导致 Get 读与 worker 写同一对象）。
func (q *Queue) Get(id string) (Task, bool) {
	q.mu.RLock()
	defer q.mu.RUnlock()
	t, ok := q.tasks[id]
	if !ok {
		return Task{}, false
	}
	return *t, true
}

func (q *Queue) worker() {
	for t := range q.ch {
		log.Printf("[task] 开始处理 %s", t.ID)
		var pdfPath string
		var err error

		switch t.Type {
		case "ticket":
			pdfPath, err = q.rdr.RenderTicket(t.Data.Team, t.Data.Problem, t.Data.PassTime)
		case "code":
			pdfPath, err = q.rdr.RenderCode(t.Data.Source, t.Data.Lang)
		default:
			err = fmt.Errorf("未知任务类型: %s", t.Type)
		}

		if err != nil {
			// 接口约定错误码表：异步失败经 status=failed + message 呈现，RENDER_FAILED 标识渲染失败
			q.update(t.ID, StatusFailed, "RENDER_FAILED: "+err.Error(), "")
			log.Printf("[task] %s 渲染失败: %v", t.ID, err)
			continue
		}

		// 打印/PDF输出
		if err := q.prn.Print(pdfPath); err != nil {
			// 契约错误码 PRINT_FAILED（无实体打印机时 PDF 兜底，正常情况下不可达）
			q.update(t.ID, StatusFailed, "PRINT_FAILED: "+err.Error(), pdfPath)
			log.Printf("[task] %s 打印失败: %v", t.ID, err)
			continue
		}

		q.update(t.ID, StatusCompleted, "", pdfPath)
		log.Printf("[task] %s 完成, 输出: %s", t.ID, pdfPath)
	}
}

func (q *Queue) update(id string, st Status, msg, out string) {
	q.mu.Lock()
	defer q.mu.Unlock()
	if t, ok := q.tasks[id]; ok {
		t.Status = st
		t.Message = msg
		if out != "" {
			// 确保输出路径是绝对路径
			if !filepath.IsAbs(out) {
				out = filepath.Join(q.outDir, out)
			}
			t.OutputPath = out
		}
	}
}
