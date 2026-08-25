# Harness — ccpc-printsvc 六类约束验证基准

> 本文件是 ccpc-printsvc 的完整 Harness，由 D1~D6 各天的真实决策汇总而成，
> 分为 **六类约束**：文件约束（F）、工具/API 约束（T）、流程约束（W）、
> 输出 Schema 约束（S）、安全 & 资源约束（C）、验收校验约束（R/P）。
> 全部内容均摘自各天报告、范围控制、接口书面约定与 .gitignore，无新增虚构决策。
>
> 规则编号保持 R1~R9 / P1~P7 不变，`run_checks.ps1` / `run_checks.sh` 直接对应。
> 每次提交/发布前运行检查脚本，全部通过才算符合规范。

---

## 一、文件约束（F）— 限定允许修改 / 读取的文件路径，glob 白 / 黑名单

### 白名单（允许修改 / 新增）

| 编号 | 允许路径（glob） | 说明与依据 |
|------|------------------|-----------|
| F1 | `printsvc/**` | 代码 + 契约 + 操作文档；仓库形态 = 代码 + 接口契约 + 操作文档（D4 仓库收敛决策） |
| F2 | `scripts/**` | 文档生成 / git 提交工具脚本 |
| F3 | `第*天报告_*.md`、`*_项目备忘_*.md`、`范围控制_*.md`、`技术知识点_*.md`、`数据模型_*.md`（仓库根目录） | 本机可读可改，但**禁止入库**（D4/.gitignore 第 5 节） |

### 黑名单（禁止修改 / 删除）

| 编号 | 禁止路径（glob） | 说明与依据 |
|------|------------------|-----------|
| F4 | `printsvc/output/**` | 运行产物（PDF/HTML），每次任务重新生成（.gitignore 第 2 节） |
| F5 | `printsvc/port.txt`、`printsvc/pid.txt` | 运行期自动写入，每次不同（.gitignore 第 2 节） |
| F6 | `printsvc/printsvc.exe*`、`printsvc/dist/**` | 构建产物，`go build` 可再生成（.gitignore 第 1 节） |
| F7 | `.codebuddy/**` | IDE 工程数据目录，不得删除（.gitignore 第 7 节） |
| F8 | `接口书面约定_20260821.md` / docx | 契约 v1.0 **已冻结**：只读，不得改字段/状态码；变更须走变更记录追加 + 立项人定案（D3） |

### 模块改动边界（D6 执行清单，一脉相承）

| 编号 | 约束 | 依据 |
|------|------|------|
| F9 | 单次任务只改白名单内与任务相关的模块，**不触碰无关模块** | D6 范围控制：模块 B 仅限 `internal/task`、`internal/port`、`cmd/printsvc/main.go`，不触碰 server / render / printer / static |

---

## 二、工具 / API 约束（T）— 工具白名单、ACL、禁止高危工具

### 工具白名单

| 编号 | 允许工具 | 用途 | 依据 |
|------|---------|------|------|
| T1 | `go build / go vet / go test / gofmt / go list` | 构建、静态检查、测试（**标准库 only**） | D3：不引外部依赖（P2） |
| T2 | `python scripts/git_store.py <add\|commit\|push\|status>` | git 操作（本机无 git 工具链，用 dulwich） | D5/D6 提交纪律 |
| T3 | `powershell -File harness/run_checks.ps1` / `bash harness/run_checks.sh` | 执行验收校验 | D6 Harness |
| T4 | `python scripts/md_to_docx_v2.py` 等文档工具 | 生成 docx 交付 | D4 文档流程 |

### 禁止 / 不适用项

| 编号 | 禁止项 | 处理 |
|------|-------|------|
| T5 | 破坏性 shell 命令（`rm -rf` 工作目录外路径、格式化等） | 禁止；仅允许删除脚本生成的临时文件 |
| T6 | 网络外联拉取依赖 | 禁止（离线环境）；chroma 未接入即因此，G6 离线保留 CSS 模拟 |
| T7 | 数据库删除 / 数据审批 | **不适用**：本项目无数据库，任务仅存内存（D1"不做队列持久化"） |
| T8 | 云服务 / 远程主机 / 生产环境操作 | **不适用**：仅本机演示服务（D1"不做云打印/远程打印"） |
| T9 | 修改冻结契约 / 范围外文件 | 高危操作，必须人工确认：先问立项人，定案后执行（D3 方案 B 定案流程、D6 三分歧点对齐） |

---

## 三、流程（工作流）约束（W）— 状态机编排，强制步骤顺序，不允许跳步骤

### 流程状态机（D5"D计划→执行→核对" + D6"排错五项" + D4"自审"）

```
需求/任务明确
   │  分歧存在？──是──> 先问立项人，立项人定案（W1）
   ▼
契约/设计定案（接口 v1.0 已冻结；新功能须先定案再编码）（W2）
   ▼
编码（仅白名单路径，F1/F9）
   ▼
自审（对照契约逐项自查，D4 审查三项缺陷为前车之鉴）（W3）
   ▼
单元测试（go test -race，禁止竞态）（W4）
   ▼
Harness 全量校验（run_checks.ps1 / run_checks.sh 全绿）（W5）
   │  校验失败 ──> 按失败上下文修正 ──> 重新跑 W3~W5（不允许直接输出结果）
   ▼
归档（报告 / 项目备忘 / 联调记录 / 排错记录，内容可复现）（W6）
   ▼
小步提交（1 次提交 = 1 件任务，docs / fix 分开）（W7）
```

| 编号 | 约束 | 依据 |
|------|------|------|
| W1 | 接口、范围、选型出现分歧，必须先询问立项人意见，以立项人决定为主 | D3 方案 B 定案；D6 三个分歧点（G1 执行方式 / 报告格式 / Harness 定义） |
| W2 | 设计未定案不得进入编码；契约 v1.0 冻结后不得偏离 | D3 契约冻结；D5 四要素任务（约束/需求/范围/输出） |
| W3 | 编码完成必须先自审，再跑单元测试，才能输出结果 | D4 审查结论（go:embed 修复、双重转义修复、test_api.py 删除） |
| W4 | 单元测试必须含 `-race`，数据竞态视为失败 | D6 G2 竞态修复；P6 |
| W5 | 验收校验失败，返回错误上下文，驱动修正后重试，不直接输出结果 | D6 Harness 运行机制（见第六节） |
| W6 | fatal 问题当日清掉；排错记录写齐五项（现象/层次/根因/修复/验证） | D6 本日排错记录；D7 讲解模板 |
| W7 | 提交纪律：小步提交，1 次提交 = 1 件任务 | D4 仓库收敛 |
| W8 | 判断故障所在层次后再改代码（接口层 / 并发层 / 渲染层 / 打印层 / 前端层） | D6 排错记录"层次判断"；D7 讲解模板 |

---

## 四、输出 Schema 约束（S）— 强制输出 JSON 结构、字段格式，不符合直接打回重跑

> 依据：接口书面约定 v1.0（D3 冻结），全部为已实现契约，非虚构。

| 编号 | 接口 | 强制 Schema |
|------|------|------------|
| S1 | `GET /api/v1/healthz`（200） | `{"service":"ccpc-printsvc","status":"ok","version":"v0.2.0"}`，字段 snake_case |
| S2 | `POST /api/v1/tasks` 请求体 | `{"type":"ticket\|code","data":{...}}`；ticket：`team`、`problem` 必填，`pass_time` 空→渲染 `--`；code：`source` 必填，`lang` 空→渲染 `text` |
| S3 | `POST /api/v1/tasks` 成功（202） | `{"task_id":"T{4位序号}-{unix秒}","status":"pending","created_at":RFC3339}` |
| S4 | `GET /api/v1/tasks/{id}` 成功（200） | `{"task_id","type","status","output_path","created_at","data"}`；状态机 `pending→completed\|failed` |
| S5 | 异步失败 | 任务 `status=failed`，`message` 带 `RENDER_FAILED:` / `PRINT_FAILED:` 前缀，不占用同步状态码 |
| S6 | 统一错误（400/404/405） | `{"error":{"code":"INVALID_ARGUMENT\|NOT_FOUND\|METHOD_NOT_ALLOWED","message":"<可读信息>"}}` |
| S7 | 时间格式 | `created_at`：RFC3339（如 `2026-08-21T10:30:00+08:00`）；`pass_time`：`YYYY-MM-DD HH:MM:SS` |
| S8 | 字段命名 | 一律 snake_case；UTF-8 JSON，`Content-Type: application/json`；CORS 本机来源白名单（D8 G7：`Origin` ∈ `127.0.0.1`/`::1`/`localhost`，其余不设 CORS 头） |

校验方式：契约冒烟（run_checks 内置 healthz 探活）+ 契约用例逐条对照；不符合即打回重跑，不进入下一阶段。

---

## 五、安全 & 资源约束（C）— 单次操作上限、沙箱隔离、资源配额、敏感信息禁止输出

| 编号 | 约束 | 依据 |
|------|------|------|
| C1 | 服务仅监听 `127.0.0.1`（本地打印服务，不暴露外网） | D1 必做 1：默认监听 `127.0.0.1:18210` |
| C2 | 端口 18210~18220 递增回退；全占用时优雅报错退出（error 上抛），不 panic | D2 选型 2 + D6 G3 修复 |
| C3 | 渲染超时 30s、打印超时 10s（防 Chrome 僵死 / PowerShell 阻塞） | D2 超时决策 |
| C4 | 无实体打印机时"打印到 PDF"兜底，不视为失败；PDF 路径 + 任务状态为核验依据 | D1 交付边界 |
| C5 | 队列仅存内存，服务重启即清空；演示数据 3~5 队，不做全量导入 | D1 不做队列持久化 / 不做大并发优化 |
| C6 | 敏感信息禁止输出：不输出密钥/令牌/内部配置；日志仅含服务运行信息；报告不得虚构数据 | D6 P7 + D1 本地边界 |
| C7 | 资源配额：单任务一次渲染 + 一次打印；队列单 worker 串行，不并发放大 | D2 单 worker 串行决策 |
| C8 | 运行产物 / 构建产物不入库（output/、port.txt、pid.txt、dist/、exe） | D4/.gitignore 第 1、2 节（P4） |

---

## 六、验收校验约束（R / P）— lint、单元测试、业务规则校验，失败返回上下文驱动重试

### 规则（必须满足）

| 编号 | 规则 | 验证方式 |
|------|------|----------|
| R1 | 所有包 Windows amd64 构建通过 | `go build ./...` |
| R2 | 所有包 Linux amd64 交叉编译通过 | `GOOS=linux GOARCH=amd64 go build ./...` |
| R3 | 静态检查通过 | `go vet ./...` |
| R4 | 全部单元测试通过（含 -race，禁止数据竞态） | `go test -race ./...` |
| R5 | HTTP API 符合契约 v1.0：healthz / POST tasks / GET tasks/{id}，错误码 400/404/405 | 契约用例（S1~S8） |
| R6 | 端口协商 18210→18220 回退；全占用时优雅报错退出，不 panic | `port` 包测试 |
| R7 | 任务状态机 pending→completed/failed；异步失败 message 带 RENDER_FAILED:/PRINT_FAILED: 前缀 | `task` 包测试 |
| R8 | 队列严格串行（单 worker），并发提交不交错、不丢任务 | `task` 包测试 |
| R9 | 渲染转义只执行一次（`&&`→`&amp;&amp;`，不产生 `&amp;amp;`） | `render` 包测试 |

### 禁令（禁止事项，违反即失败）

| 编号 | 禁令 | 检查方式 |
|------|------|----------|
| P1 | 禁止 panic 退出（运行期错误一律 error 上抛，由 main 优雅处理） | 代码审查 + port/task 测试 |
| P2 | 禁止引入外部依赖（保持标准库 only） | `go list -m all` 仅含 std + 本模块 |
| P3 | 禁止 HTML 双重转义 | `render` 包回归测试 |
| P4 | 禁止运行产物入库：`output/`、`port.txt`、`pid.txt`、`dist/`、`printsvc.exe` | `.gitignore` 覆盖 + `git status` 复核 |
| P5 | 禁止实验报告/数据模型/项目备忘入库（仓库仅代码+接口契约+操作文档） | `.gitignore` 第 5 节 + `git status` 复核 |
| P6 | 禁止数据竞态（锁外读共享指针） | `go test -race ./...` |
| P7 | 禁止虚构测试数据/无依据结论（报告内容必须可复现） | 人工复核 + 检查脚本输出留档 |

### 失败处理流程（驱动重试，不直接输出结果）

1. 检查脚本打印失败项编号 + 失败明细（exit code 非 0）；
2. 依据失败上下文定位层次（W8），修正代码；
3. 重跑对应包测试 → 全量 `run_checks.ps1`，直到 0 退出；
4. 全部通过后才允许归档与提交。

---

## 七、检查脚本执行

```powershell
cd printsvc
powershell -ExecutionPolicy Bypass -File harness/run_checks.ps1   # Windows
bash harness/run_checks.sh                                        # Linux / D7 真机
```

- 退出码 0 = 全部通过；非 0 = 存在失败项（脚本打印失败明细与上下文）。
- 文件约束（F 类）与仓库洁净度（P4/P5）由 `.gitignore` + `git status` 人工复核，脚本输出提示。

## 八、与各天决策的对应关系（索引）

| 本 Harness 章节 | 来源 |
|----------------|------|
| 一、文件约束 | D4 仓库收敛 / D6 执行清单 / .gitignore |
| 二、工具 / API 约束 | D1 边界 / D2 选型 / D3 标准库 only / D5~D6 提交纪律 |
| 三、流程约束 | D3 契约冻结 / D4 自审 / D5 四要素与计划-执行-核对 / D6 排错五项 |
| 四、输出 Schema | 接口书面约定 v1.0（D3 冻结） |
| 五、安全 & 资源 | D1 边界 / D2 超时与串行 / D6 G3 / .gitignore |
| 六、验收校验 | D6 规则 R1~R9 / 禁令 P1~P7 |
