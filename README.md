# CCPC 本地打印服务（printsvc）

浏览器调用本地打印机——基于 Golang 的跨平台本地打印服务（MVP）。
参考竞赛现场打印队列场景（[CCPCOJ](https://github.com/CSGrandeur/CCPCOJ)，含现场打印功能），对标商用方案 Lodop，自研轻量实现。

## 功能

- 气球小票打印：Web 提交「队名 / 题号 / 通过时间」，渲染 58mm 窄纸小票。
- 代码打印：Web 提交源代码，渲染 80mm 窄纸（自动折行），供裁判核查。
- 任务队列与状态：提交即入队，返回任务 ID；可查询排队中 / 已完成 / 失败及原因。
- 端口协商：默认监听 127.0.0.1:18210，被占用时在 18210~18220 内自动回退，实际端口写入 `port.txt` 与日志。
- 无实体打印机时打印到 PDF 兜底，PDF 产物路径即验证依据。

## 目录结构

```
printsvc/                   # 服务代码（Go module: ccpc-printsvc）
  cmd/printsvc/main.go      # 主入口：端口协商、装配模块、启动 HTTP 服务
  internal/port/            # 端口协商（18210~18220 回退，全占用优雅报错，写入 port.txt）
  internal/server/          # HTTP API（v1.0）与静态页面托管
  internal/task/            # 内存任务队列（单 worker 串行）+ 状态机 + 边界测试（D6）
  internal/render/          # 无头 Chromium 渲染 HTML → PDF（ticket 58mm / code 80mm）
  internal/printer/         # 系统默认打印机（Win: PowerShell / Linux: lp），PDF 兜底
  internal/static/          # Web 前端（提交表单 + 探活 + 状态轮询）
  harness/                  # Harness（D6）：规则 R1~R9 / 禁令 P1~P7 / 检查脚本
    HARNESS.md              #   验证基准文档
    run_checks.ps1          #   Windows PowerShell 检查脚本
    run_checks.sh           #   Linux bash 检查脚本（真机验证用）
  DEMO.md                   # 主路径演示说明（D5，D6 已更新）：环境前提 + 编号步骤 + 预期现象
scripts/                    # 文档转换/校验/提交脚本（md→docx、git 提交等）
README.md                   # 本文件：安装、启动、停止、验证
接口书面约定_20260821.md    # 接口契约 v1.0（REST 资源化 + 按类型分组）
module_diagram_d2.png       # 模块图（第 2 天产出）
```

## 测试与验证（D6 Harness）

```bash
cd printsvc
go vet ./...                                # 静态检查
go test -race -count=1 ./...                # 全部单元测试（含竞态检测）
powershell -ExecutionPolicy Bypass -File harness/run_checks.ps1   # 一键检查（R1~R9）
# Linux 真机（D7）：bash harness/run_checks.sh
```

覆盖范围：端口全占用优雅降级（`internal/port`）、队列串行/状态机/并发竞态（`internal/task`）、渲染转义只执行一次（`internal/render`）。规则 R1~R9 与禁令 P1~P7 见 `printsvc/harness/HARNESS.md`。

## 依赖安装

1. Go 1.22+（开发用 1.26）：<https://go.dev/dl/>，装完后命令行执行 `go version` 确认。
2. Google Chrome 或 Chromium（渲染 HTML→PDF 用）。Windows 默认探测 `C:\Program Files\Google\Chrome\Application\chrome.exe` 与 `C:\Program Files (x86)\...`；Linux 探测 `chromium` / `chromium-browser` / `google-chrome`（PATH）。若探测不到会退回 `chrome` 命令名。
   - Linux 额外建议：`apt install chromium fonts-noto-cjk`（缺中文字体会乱码）。

## 启动

```bash
cd printsvc
go build -o printsvc.exe ./cmd/printsvc
./printsvc.exe
```

启动后日志会打印实际监听地址（默认 `http://127.0.0.1:18210`，被占用则递增）。`port.txt` 同步记录实际端口。

浏览器打开 `http://127.0.0.1:<port>` 即进入提交页面；页面通过 `location.port` 自动取端口探活。

## 停止

- 前台运行：在运行窗口按 `Ctrl+C`。
- 后台运行（Windows PowerShell 示例）：

```powershell
Stop-Process -Name printsvc
```

## 验证

服务启动后，可用以下命令核对主路径（Windows PowerShell）：

```powershell
# 1. 探活
curl.exe http://127.0.0.1:18210/api/v1/healthz
# 2. 提交气球小票任务
curl.exe -X POST http://127.0.0.1:18210/api/v1/tasks -H "Content-Type: application/json" -d "{\"type\":\"ticket\",\"data\":{\"team\":\"Alpha\",\"problem\":\"A+B\",\"pass_time\":\"2026-08-22 10:00:00\"}}"
# 3. 查询任务（<task_id> 替换为上一步返回的 ID）
curl.exe http://127.0.0.1:18210/api/v1/tasks/<task_id>
```

任务完成后可在 `printsvc/output/` 下看到 PDF 产物，响应中的 `output_path` 即绝对路径。

## 接口契约（v1.0）

- `GET  /api/v1/healthz` 探活
- `POST /api/v1/tasks` 提交任务，请求体 `{type: "ticket"|"code", data:{...}}`，返回 `{task_id, status, created_at}`
- `GET  /api/v1/tasks/{task_id}` 查询任务状态

详细字段与错误码见《接口书面约定_20260821.md》。

## .gitignore 说明

忽略规则按「密钥 / 依赖目录 / 构建产物 / 本机环境文件 / 可再生成内容」分类，逐条说明见 `.gitignore` 文件内注释。要点：构建产物（`printsvc.exe`）、运行产物（`output/`、`port.txt`、`pid.txt`）、Python 缓存（`__pycache__/`、`*.pyc`）、全部实验报告（第 1~5 天报告、数据模型、项目备忘——本机保留、仓库不收）一律不入库。仓库形态参考 [CCPCOJ](https://github.com/CSGrandeur/CCPCOJ)：只含代码、接口契约与操作文档，不含实验报告。
