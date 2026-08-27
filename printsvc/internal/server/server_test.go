package server

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"ccpc-printsvc/internal/task"
)

// newTestServer 构造测试服务器（不启动 worker，任务保持 pending，只验证 HTTP 层）
func newTestServer(t *testing.T) *httptest.Server {
	t.Helper()
	q := task.NewQueue(nil, nil, t.TempDir())
	s := New("127.0.0.1:0", q, t.TempDir())
	ts := httptest.NewServer(LogMiddleware(cors(s.mux())))
	t.Cleanup(ts.Close)
	return ts
}

func get(t *testing.T, url string, hdr map[string]string) *http.Response {
	t.Helper()
	req, _ := http.NewRequest(http.MethodGet, url, nil)
	for k, v := range hdr {
		req.Header.Set(k, v)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("GET %s: %v", url, err)
	}
	return resp
}

func post(t *testing.T, url, body string, hdr map[string]string) *http.Response {
	t.Helper()
	req, _ := http.NewRequest(http.MethodPost, url, bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	for k, v := range hdr {
		req.Header.Set(k, v)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("POST %s: %v", url, err)
	}
	return resp
}

func readBody(resp *http.Response) string {
	b, _ := io.ReadAll(resp.Body)
	return string(b)
}

// --- 契约回归（v1.0） ---

func TestHealthzOK(t *testing.T) {
	ts := newTestServer(t)
	resp := get(t, ts.URL+"/api/v1/healthz", nil)
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status = %d, want 200", resp.StatusCode)
	}
	var body map[string]string
	_ = json.NewDecoder(resp.Body).Decode(&body)
	if body["status"] != "ok" {
		t.Fatalf(`status field = %q, want "ok"`, body["status"])
	}
}

func TestHealthzMethodNotAllowed(t *testing.T) {
	ts := newTestServer(t)
	resp := post(t, ts.URL+"/api/v1/healthz", "", nil)
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusMethodNotAllowed {
		t.Fatalf("status = %d, want 405", resp.StatusCode)
	}
}

func TestCreateTicketContract(t *testing.T) {
	ts := newTestServer(t)
	resp := post(t, ts.URL+"/api/v1/tasks",
		`{"type":"ticket","data":{"team":"Alpha","problem":"A","pass_time":"2026-08-25 10:00:00"}}`, nil)
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusAccepted {
		t.Fatalf("status = %d, want 202; body=%s", resp.StatusCode, readBody(resp))
	}
	var body struct {
		TaskID string `json:"task_id"`
		Status string `json:"status"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if !strings.HasPrefix(body.TaskID, "T") || body.Status != "pending" {
		t.Fatalf("resp = %+v", body)
	}
}

func TestCreateTicketMissingTeam(t *testing.T) {
	ts := newTestServer(t)
	resp := post(t, ts.URL+"/api/v1/tasks", `{"type":"ticket","data":{"problem":"A"}}`, nil)
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusBadRequest {
		t.Fatalf("status = %d, want 400", resp.StatusCode)
	}
	if !strings.Contains(readBody(resp), "INVALID_ARGUMENT") {
		t.Fatalf("body lacks INVALID_ARGUMENT: %s", readBody(resp))
	}
}

func TestCreateTaskInvalidType(t *testing.T) {
	ts := newTestServer(t)
	resp := post(t, ts.URL+"/api/v1/tasks", `{"type":"bogus","data":{}}`, nil)
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusBadRequest {
		t.Fatalf("status = %d, want 400", resp.StatusCode)
	}
	if !strings.Contains(readBody(resp), "INVALID_ARGUMENT") {
		t.Fatalf("body lacks INVALID_ARGUMENT: %s", readBody(resp))
	}
}

func TestGetTaskNotFound(t *testing.T) {
	ts := newTestServer(t)
	resp := get(t, ts.URL+"/api/v1/tasks/T9999-0000000000", nil)
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusNotFound {
		t.Fatalf("status = %d, want 404", resp.StatusCode)
	}
	if !strings.Contains(readBody(resp), "NOT_FOUND") {
		t.Fatalf("body lacks NOT_FOUND: %s", readBody(resp))
	}
}

// --- G7 强化项 ---

func TestCreateTaskBodyTooLarge(t *testing.T) {
	ts := newTestServer(t)
	huge := fmt.Sprintf(`{"type":"code","data":{"source":%q}}`, strings.Repeat("x", 2<<20))
	resp := post(t, ts.URL+"/api/v1/tasks", huge, nil)
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusBadRequest {
		t.Fatalf("status = %d, want 400 (body too large)", resp.StatusCode)
	}
	if !strings.Contains(readBody(resp), "too large") {
		t.Fatalf("body lacks 'too large': %s", readBody(resp))
	}
}

func TestCORSLocalOrigin(t *testing.T) {
	ts := newTestServer(t)
	resp := get(t, ts.URL+"/api/v1/healthz", map[string]string{"Origin": "http://127.0.0.1:18210"})
	defer resp.Body.Close()
	if got := resp.Header.Get("Access-Control-Allow-Origin"); got != "http://127.0.0.1:18210" {
		t.Fatalf("ACAO = %q, want %q", got, "http://127.0.0.1:18210")
	}
}

func TestCORSRejectedOrigin(t *testing.T) {
	ts := newTestServer(t)
	for _, origin := range []string{"http://evil.example", "https://attacker.com", "file:///etc/passwd", "http://192.168.1.10:9999"} {
		resp := get(t, ts.URL+"/api/v1/healthz", map[string]string{"Origin": origin})
		resp.Body.Close()
		if got := resp.Header.Get("Access-Control-Allow-Origin"); got != "" {
			t.Fatalf("origin %q: ACAO = %q, want empty", origin, got)
		}
	}
}

func TestCORSNoOrigin(t *testing.T) {
	ts := newTestServer(t)
	resp := get(t, ts.URL+"/api/v1/healthz", nil)
	defer resp.Body.Close()
	if got := resp.Header.Get("Access-Control-Allow-Origin"); got != "" {
		t.Fatalf("no origin: ACAO = %q, want empty", got)
	}
}

func TestPreflightLocalOrigin(t *testing.T) {
	ts := newTestServer(t)
	req, _ := http.NewRequest(http.MethodOptions, ts.URL+"/api/v1/tasks", nil)
	req.Header.Set("Origin", "http://localhost:18210")
	req.Header.Set("Access-Control-Request-Method", "POST")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusNoContent {
		t.Fatalf("status = %d, want 204", resp.StatusCode)
	}
	if got := resp.Header.Get("Access-Control-Allow-Origin"); got != "http://localhost:18210" {
		t.Fatalf("ACAO = %q, want %q", got, "http://localhost:18210")
	}
}
