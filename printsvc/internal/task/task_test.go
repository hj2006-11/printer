package task

import (
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

// ============ fake 实现（不依赖 Chrome/打印机，D6 为可测试性注入） ============

// fakeRenderer 记录调用并模拟渲染耗时（默认 20ms），可配置失败。
type fakeRenderer struct {
	mu      sync.Mutex
	calls   []string            // 按调用顺序记录 "type:payload"
	active  int32               // 当前正在渲染的任务数（验证串行）
	maxConc int32               // 渲染期间观测到的最大并发数
	delay   time.Duration
	fail    map[string]error    // 按 payload 前缀匹配的失败注入
}

func newFakeRenderer(delay time.Duration) *fakeRenderer {
	return &fakeRenderer{delay: delay}
}

func (f *fakeRenderer) begin(key string) {
	atomic.AddInt32(&f.active, 1)
	if n := atomic.LoadInt32(&f.active); n > f.maxConc {
		atomic.StoreInt32(&f.maxConc, n)
	}
	f.mu.Lock()
	f.calls = append(f.calls, key)
	f.mu.Unlock()
}

func (f *fakeRenderer) end() { atomic.AddInt32(&f.active, -1) }

func (f *fakeRenderer) errFor(key string) error {
	if f.fail == nil {
		return nil
	}
	for prefix, e := range f.fail {
		if strings.HasPrefix(key, prefix) {
			return e
		}
	}
	return nil
}

func (f *fakeRenderer) RenderTicket(team, problem, passTime string) (string, error) {
	key := "ticket:" + team
	f.begin(key)
	defer f.end()
	if f.delay > 0 {
		time.Sleep(f.delay)
	}
	if e := f.errFor(key); e != nil {
		return "", e
	}
	return "/tmp/" + team + ".pdf", nil
}

func (f *fakeRenderer) RenderCode(source, lang string) (string, error) {
	key := "code:" + lang
	f.begin(key)
	defer f.end()
	if f.delay > 0 {
		time.Sleep(f.delay)
	}
	if e := f.errFor(key); e != nil {
		return "", e
	}
	return "/tmp/code_" + lang + ".pdf", nil
}

// fakePrinter 记录打印调用，模拟耗时（默认 20ms），可配置失败。
type fakePrinter struct {
	mu      sync.Mutex
	pdfPaths []string
	active  int32
	maxConc int32
	delay   time.Duration
	failErr error
}

func newFakePrinter(delay time.Duration) *fakePrinter {
	return &fakePrinter{delay: delay}
}

func (f *fakePrinter) Print(pdfPath string) error {
	atomic.AddInt32(&f.active, 1)
	if n := atomic.LoadInt32(&f.active); n > f.maxConc {
		atomic.StoreInt32(&f.maxConc, n)
	}
	defer atomic.AddInt32(&f.active, -1)
	if f.delay > 0 {
		time.Sleep(f.delay)
	}
	f.mu.Lock()
	f.pdfPaths = append(f.pdfPaths, pdfPath)
	f.mu.Unlock()
	return f.failErr
}

// ============ 测试用例 ============

// TestQueueSerialOrder 并发提交多个任务，验证 worker 严格串行（渲染/打印互不交错）且按提交顺序处理。
func TestQueueSerialOrder(t *testing.T) {
	rdr := newFakeRenderer(20 * time.Millisecond)
	prn := newFakePrinter(10 * time.Millisecond)
	q := NewQueue(rdr, prn, "/tmp")
	q.Start()

	const n = 6
	ids := make([]string, 0, n)
	for i := 0; i < n; i++ {
		ids = append(ids, q.Submit(&Task{Type: "ticket", Data: TaskData{Team: "TeamA", Problem: "A"}}))
	}
	waitAll(t, q, ids)

	// 串行断言：任何时刻最多 1 个渲染任务、1 个打印任务在跑
	if rdr.maxConc != 1 {
		t.Fatalf("renderer concurrency = %d, want 1 (strictly serial)", rdr.maxConc)
	}
	if prn.maxConc != 1 {
		t.Fatalf("printer concurrency = %d, want 1 (strictly serial)", prn.maxConc)
	}
	// 按提交顺序处理（渲染调用序 = 提交序）
	rdr.mu.Lock()
	defer rdr.mu.Unlock()
	if len(rdr.calls) != n {
		t.Fatalf("render calls = %d, want %d", len(rdr.calls), n)
	}
	for i, c := range rdr.calls {
		if c != "ticket:TeamA" {
			t.Fatalf("render call[%d] = %q, want ticket:TeamA", i, c)
		}
	}
	// 打印次数 = 渲染次数
	if len(prn.pdfPaths) != n {
		t.Fatalf("print count = %d, want %d", len(prn.pdfPaths), n)
	}
	// 状态机：全部 completed
	for _, id := range ids {
		got, ok := q.Get(id)
		if !ok {
			t.Fatalf("task %s missing", id)
		}
		if got.Status != StatusCompleted {
			t.Fatalf("task %s status = %s, want completed", id, got.Status)
		}
		if got.OutputPath == "" {
			t.Fatalf("task %s output_path empty", id)
		}
	}
}

// TestQueueMixedTypes 混入 ticket 与 code 两种类型，验证按提交顺序执行、两种载荷都正确处理。
func TestQueueMixedTypes(t *testing.T) {
	rdr := newFakeRenderer(5 * time.Millisecond)
	prn := newFakePrinter(2 * time.Millisecond)
	q := NewQueue(rdr, prn, "/tmp")
	q.Start()

	ids := []string{
		q.Submit(&Task{Type: "ticket", Data: TaskData{Team: "T1", Problem: "A"}}),
		q.Submit(&Task{Type: "code", Data: TaskData{Lang: "cpp", Source: "int a;"}}),
		q.Submit(&Task{Type: "ticket", Data: TaskData{Team: "T2", Problem: "B"}}),
	}
	waitAll(t, q, ids)

	rdr.mu.Lock()
	got := append([]string(nil), rdr.calls...)
	rdr.mu.Unlock()
	want := []string{"ticket:T1", "code:cpp", "ticket:T2"}
	if strings.Join(got, ",") != strings.Join(want, ",") {
		t.Fatalf("execution order = %v, want %v", got, want)
	}
}

// TestQueueRenderFailure 渲染失败 → failed + RENDER_FAILED 前缀（契约），且后续任务不受影响。
func TestQueueRenderFailure(t *testing.T) {
	rdr := newFakeRenderer(5 * time.Millisecond)
	rdr.fail = map[string]error{"ticket:Bad": &renderError{"simulated chrome crash"}}
	prn := newFakePrinter(2 * time.Millisecond)
	q := NewQueue(rdr, prn, "/tmp")
	q.Start()

	bad := q.Submit(&Task{Type: "ticket", Data: TaskData{Team: "Bad", Problem: "X"}})
	good := q.Submit(&Task{Type: "ticket", Data: TaskData{Team: "Good", Problem: "Y"}})
	waitAll(t, q, []string{bad, good})

	if got, _ := q.Get(bad); got.Status != StatusFailed || !strings.HasPrefix(got.Message, "RENDER_FAILED:") {
		t.Fatalf("bad task = %+v, want failed+RENDER_FAILED", got)
	}
	if got, _ := q.Get(good); got.Status != StatusCompleted {
		t.Fatalf("good task = %+v, want completed", got)
	}
	if len(prn.pdfPaths) != 1 {
		t.Fatalf("print count = %d, want 1 (failed task must not print)", len(prn.pdfPaths))
	}
}

// TestQueueConcurrentSubmit 并发提交大量任务，验证无竞态（配合 -race）、任务数完整、ID 唯一。
func TestQueueConcurrentSubmit(t *testing.T) {
	rdr := newFakeRenderer(0)
	prn := newFakePrinter(0)
	q := NewQueue(rdr, prn, "/tmp")
	q.Start()

	const n = 50
	var wg sync.WaitGroup
	ids := make([]string, n)
	for i := 0; i < n; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			ids[i] = q.Submit(&Task{Type: "ticket", Data: TaskData{Team: "T", Problem: "A"}})
		}(i)
	}
	wg.Wait()
	waitAll(t, q, ids)

	// 唯一性
	seen := make(map[string]bool, n)
	for _, id := range ids {
		if id == "" || seen[id] {
			t.Fatalf("duplicate or empty task id: %q", id)
		}
		seen[id] = true
	}
	// 完整性：全部可查询且 completed
	for _, id := range ids {
		got, ok := q.Get(id)
		if !ok {
			t.Fatalf("task %s missing after wait", id)
		}
		if got.Status != StatusCompleted {
			t.Fatalf("task %s status = %s, want completed", id, got.Status)
		}
	}
}

// waitAll 轮询等待所有任务脱离 pending（最多 5s 兜底）。
func waitAll(t *testing.T, q *Queue, ids []string) {
	t.Helper()
	deadline := time.Now().Add(5 * time.Second)
	for _, id := range ids {
		for {
			got, ok := q.Get(id)
			if !ok {
				t.Fatalf("task %s not found", id)
			}
			if got.Status != StatusPending {
				break
			}
			if time.Now().After(deadline) {
				t.Fatalf("task %s still pending after 5s", id)
			}
			time.Sleep(2 * time.Millisecond)
		}
	}
}

// renderError 测试用错误类型。
type renderError struct{ msg string }

func (e *renderError) Error() string { return e.msg }
