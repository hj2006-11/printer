#!/usr/bin/env bash
# run_checks.sh — ccpc-printsvc Harness 检查脚本（Linux / bash，D7 真机验证用）
# 对应 HARNESS.md 规则 R1~R4、R6~R9 与禁令 P1~P7。
# 用法: bash harness/run_checks.sh
# 退出码: 0 = 全部通过
set -o pipefail
cd "$(dirname "$0")/.." || exit 1   # 进入 printsvc/

PASS=0
FAIL=0

step() {
    local name="$1"; shift
    printf '==> %s\n' "$name"
    if "$@"; then
        printf '    [PASS] %s\n' "$name"
        PASS=$((PASS+1))
    else
        printf '    [FAIL] %s\n' "$name"
        FAIL=$((FAIL+1))
    fi
}

# ---- R1 本机构建 ----
step "R1 go build ./..." go build ./...

# ---- R2 Linux 交叉编译 ----
step "R2 go build (linux/amd64)" env GOOS=linux GOARCH=amd64 go build -o /tmp/ccpc-printsvc-linux-check ./cmd/printsvc
rm -f /tmp/ccpc-printsvc-linux-check

# ---- R3 go vet ----
step "R3 go vet ./..." go vet ./...

# ---- R4 go test -race ----
step "R4 go test -race ./..." go test -race -count=1 ./...

# ---- R6 端口协商测试 ----
step "R6 go test internal/port" go test -count=1 -v ./internal/port/

# ---- R7/R8 任务队列边界测试 ----
step "R7/R8 go test internal/task -race" go test -race -count=1 -v ./internal/task/

# ---- R9 渲染转义回归 ----
step "R9 go test internal/render" go test -count=1 -v ./internal/render/

# ---- 契约冒烟：启动服务探活（仅当可执行文件存在）----
if [ -f ./printsvc ]; then
    ./printsvc >/tmp/ccpc-printsvc.log 2>&1 &
    SPID=$!
    sleep 3
    ADDR=$(head -n1 ./port.txt 2>/dev/null)
    if [ -z "$ADDR" ]; then
        printf '    [FAIL] R5 smoke: port.txt not written\n'
        FAIL=$((FAIL+1))
    else
        if curl -fsS "http://$ADDR/api/v1/healthz" | grep -q '"status":"ok"'; then
            printf '    [PASS] R5 smoke: healthz contract\n'
            PASS=$((PASS+1))
        else
            printf '    [FAIL] R5 smoke: healthz contract\n'
            FAIL=$((FAIL+1))
        fi
    fi
    kill "$SPID" 2>/dev/null
    wait "$SPID" 2>/dev/null
else
    printf '    [SKIP] R5 smoke (printsvc 不存在，先 go build)\n'
fi

# ---- 汇总 ----
printf '\n========== 汇总 ==========\n'
if [ "$FAIL" -eq 0 ]; then
    printf 'ALL CHECKS PASSED (%d)\n' "$PASS"
    exit 0
else
    printf 'FAILED: %d item(s) (pass=%d)\n' "$FAIL" "$PASS"
    exit 1
fi
