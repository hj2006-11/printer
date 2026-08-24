# Harness — 规则 / 禁令 / 检查脚本（D6）

本文件是 ccpc-printsvc 的验证基准（Harness），由"规则 + 禁令 + 检查脚本"三部分组成。
每次提交/发布前运行 `run_checks.ps1`（Windows）或 `run_checks.sh`（Linux），
全部通过才算符合规范。D7 起新增真机验证步骤沿用同一基准。

## 一、规则（必须满足）

| 编号 | 规则 | 验证方式 |
|------|------|----------|
| R1 | 所有包 Windows amd64 构建通过 | `go build ./...` |
| R2 | 所有包 Linux amd64 交叉编译通过 | `GOOS=linux GOARCH=amd64 go build ./...` |
| R3 | 静态检查通过 | `go vet ./...` |
| R4 | 全部单元测试通过（含 -race，禁止数据竞态） | `go test -race ./...` |
| R5 | HTTP API 符合契约 v1.0：healthz / POST tasks / GET tasks/{id}，错误码 400/404/405 | 契约用例（见下） |
| R6 | 端口协商 18210→18220 回退；全占用时优雅报错退出，不 panic | `port` 包测试 |
| R7 | 任务状态机 pending→completed/failed；异步失败 message 带 RENDER_FAILED:/PRINT_FAILED: 前缀 | `task` 包测试 |
| R8 | 队列严格串行（单 worker），并发提交不交错、不丢任务 | `task` 包测试 |
| R9 | 渲染转义只执行一次（`&&`→`&amp;&amp;`，不产生 `&amp;amp;`） | `render` 包测试 |

## 二、禁令（禁止事项，违反即失败）

| 编号 | 禁令 | 检查方式 |
|------|------|----------|
| P1 | 禁止 panic 退出（运行期错误一律 error 上抛，由 main 优雅处理） | 代码审查 + port/task 测试 |
| P2 | 禁止引入外部依赖（保持标准库 only） | `go list -m all` 仅含 std + 本模块 |
| P3 | 禁止 HTML 双重转义 | `render` 包回归测试 |
| P4 | 禁止运行产物入库：`output/`、`port.txt`、`pid.txt`、`dist/`、`printsvc.exe` | `.gitignore` 覆盖 + `git status` 复核 |
| P5 | 禁止实验报告/数据模型/项目备忘入库（仓库仅代码+接口契约+操作文档） | `.gitignore` 第5节 + `git status` 复核 |
| P6 | 禁止数据竞态（锁外读共享指针） | `go test -race ./...` |
| P7 | 禁止虚构测试数据/无依据结论（报告内容必须可复现） | 人工复核 + 检查脚本输出留档 |

## 三、检查脚本

- `run_checks.ps1` — Windows / PowerShell：R1~R4 + R9 + 契约冒烟 + ELF 静态验证（G1 部分完成项）
- `run_checks.sh`  — Linux / bash：R1~R4 + R9（D7 真机验证时在目标机执行）

执行方式：
```powershell
cd printsvc
powershell -ExecutionPolicy Bypass -File harness/run_checks.ps1
```

退出码：0 = 全部通过；非 0 = 存在失败项（脚本会打印失败明细）。
