# run_checks.ps1 — ccpc-printsvc Harness 检查脚本（Windows / PowerShell）
# 对应 HARNESS.md 规则 R1~R4、R6~R9 与禁令 P1~P7。
# 用法: powershell -ExecutionPolicy Bypass -File harness/run_checks.ps1
# 退出码: 0 = 全部通过

$ErrorActionPreference = "Continue"
$failed = @()
$pass = @()
$root = Split-Path -Parent $PSScriptRoot   # printsvc/
Set-Location $root

function Check-Step {
    param([string]$Name, [scriptblock]$Body)
    Write-Host "==> $Name" -ForegroundColor Cyan
    try {
        & $Body
        if ($LASTEXITCODE -eq 0) {
            $script:pass += $Name
            Write-Host "    [PASS] $Name" -ForegroundColor Green
        } else {
            $script:failed += $Name
            Write-Host "    [FAIL] $Name (exit=$LASTEXITCODE)" -ForegroundColor Red
        }
    } catch {
        $script:failed += $Name
        Write-Host "    [FAIL] $Name : $_" -ForegroundColor Red
    }
}

# ---- R1 Windows 构建 ----
Check-Step "R1 go build (windows/amd64)" {
    $env:GOOS="windows"; $env:GOARCH="amd64"
    go build ./... 
}

# ---- R2 Linux 交叉编译 ----
Check-Step "R2 go build (linux/amd64)" {
    $env:GOOS="linux"; $env:GOARCH="amd64"
    go build -o $env:TEMP\ccpc-printsvc-linux-check ./cmd/printsvc
    Remove-Item $env:TEMP\ccpc-printsvc-linux-check -ErrorAction SilentlyContinue
}
# 恢复本机环境
$env:GOOS=""; $env:GOARCH=""

# ---- R3 go vet ----
Check-Step "R3 go vet ./..." { go vet ./... }

# ---- R4 go test -race ----
Check-Step "R4 go test -race ./..." { go test -race -count=1 ./... }

# ---- R6 端口协商测试（含 G3 全占用优雅降级）----
Check-Step "R6 go test internal/port -v" { go test -count=1 -v ./internal/port/ }

# ---- R7/R8 任务队列边界测试（串行/状态机/竞态）----
Check-Step "R7/R8 go test internal/task -race -v" { go test -race -count=1 -v ./internal/task/ }

# ---- R9 渲染转义回归 ----
Check-Step "R9 go test internal/render -v" { go test -count=1 -v ./internal/render/ }

# ---- 契约冒烟：启动服务探活（仅当可执行文件存在）----
if (Test-Path "$root\printsvc.exe") {
    Check-Step "R5 smoke: healthz contract" {
        $p = Start-Process -FilePath "$root\printsvc.exe" -WorkingDirectory $root -PassThru -WindowStyle Hidden
        try {
            Start-Sleep -Seconds 3
            $addr = (Get-Content "$root\port.txt" -ErrorAction SilentlyContinue | Select-Object -First 1)
            if (-not $addr) { throw "port.txt not written" }
            $resp = Invoke-RestMethod -Uri "http://$addr/api/v1/healthz" -TimeoutSec 5
            if ($resp.status -ne "ok") { throw "healthz status=$($resp.status)" }
        } finally {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
        }
    }
} else {
    Write-Host "    [SKIP] R5 smoke (printsvc.exe 不存在，先 go build)" -ForegroundColor Yellow
}

# ---- 禁令 P4/P5：仓库洁净度（git 由 scripts/git_store.py 负责，此处提示）----
Write-Host "==> P4/P5 检查提示" -ForegroundColor Cyan
Write-Host "    运行产物不入库：.gitignore 已覆盖 output/, port.txt, pid.txt, dist/, printsvc.exe"
Write-Host "    实验报告不入库：.gitignore 已覆盖 第N天报告/数据模型/项目备忘/技术知识点/范围控制/验收自测表/审查与安全清单（D8 起）"
Write-Host "    提交前请人工复核: python scripts/git_store.py status"

# ---- 汇总 ----
Write-Host ""
Write-Host "========== 汇总 ==========" -ForegroundColor Magenta
foreach ($s in $pass) { Write-Host "  [PASS] $s" -ForegroundColor Green }
foreach ($s in $failed) { Write-Host "  [FAIL] $s" -ForegroundColor Red }
if ($failed.Count -eq 0) {
    Write-Host "ALL CHECKS PASSED" -ForegroundColor Green
    exit 0
} else {
    Write-Host "FAILED: $($failed.Count) item(s)" -ForegroundColor Red
    exit 1
}
