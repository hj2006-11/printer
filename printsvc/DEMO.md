# printsvc 主路径演示说明（第 5 天）

> 目标：让一个**陌生环境/第二人**仅凭本说明即可复现「Web 提交 → 任务排队 → 渲染 PDF → 打印/PDF 兜底 → 状态查询」主路径。
> 适用于 Windows；Linux 差异在第 8 步注明。

## 环境前提

| 项 | 要求 | 检查命令（Windows） |
|---|---|---|
| Go | 1.22+ | `go version` |
| Chrome | 已安装 | 默认探测 `C:\Program Files\Google\Chrome\Application\chrome.exe` 与 `(x86)` |
| 实体打印机 | **可选** | 无打印机时自动走 PDF 兜底，PDF 即为产物 |

> 临时假实现说明：当前版本未接实体打印机验证出纸（D8 仍未借到实机，如实标注），无打印机时打印模块自动回退为 PDF 兜底并视作成功——这是**有意的临时行为**，非 bug。注意无打印机时打印阶段会失败后走 PDF 兜底，任务从提交到 `completed` 约需 9~14s（D7 实测，详见 S5）。D7 起可用环境变量 `CCPC_PRINTER` 指定打印机（Windows 用 printui 切换默认后打印并恢复，Linux 用 `lp -d`），未设置时使用系统默认打印机。气球小票/代码渲染均为真实实现。D8 起服务做了安全强化（G7）：CORS 仅放行本机来源、请求体上限 1MB、HTTP Server 显式超时，详见 `审查与安全清单_20260826.md`。

## 编号步骤

### S1 构建

```bash
cd printsvc
go build -o printsvc.exe ./cmd/printsvc
```

**预期现象**：命令无报错，生成 `printsvc.exe`。

**失败检查**：`go version` 报错 → Go 未装或 PATH 未配；`undefined: ...` → 源码与 go.mod 版本不匹配，先 `go mod tidy`。

### S2 启动服务

```bash
./printsvc.exe
```

**预期现象**：控制台打印监听地址 `http://127.0.0.1:18210`（18210 被占用则递增到 18220 内任意可用端口），同目录生成 `port.txt` 记录实际地址。

**失败检查**：18210~18220 全被占用 → 进程打印 `端口 18210~18220 全部被占用，无可用端口` 后以退出码 1 优雅退出（D6 G3 已实现，不再 panic）。

### S3 探活

```bash
curl.exe http://127.0.0.1:18210/api/v1/healthz
```

**预期现象**：返回 `{"service":"ccpc-printsvc","status":"ok","version":"v0.2.0"}`。

### S4 打开提交页

浏览器访问 `http://127.0.0.1:18210/`。

**预期现象**：页面标题「CCPC 本地打印服务」，顶部绿色状态条显示「服务在线」，下方两个页签「气球小票 / 代码打印」。

### S5 提交气球小票任务

在「气球小票」页签填入队名 `Team A`、题号 `A`、通过时间 `2026-08-23 10:00:00`，点击「提交打印」。

**预期现象**：
1. 下方结果区显示「提交成功」，含 `task_id`（形如 `T0001-1787454312`）与 `status: "pending"`；
2. 自动轮询（1.5s/次），约 12 秒后状态变为 `"completed"`，响应含 `output_path`。

> 耗时说明：渲染约 2s；本机无实体打印机，打印阶段会阻塞至 10s 超时后走 PDF 兜底（视为成功），故总计约 12s。期间查询为 `pending` 属正常异步时序，不是卡死。

**失败检查**：提交后约 30 秒仍停在 `pending`、或状态变 `failed` → 查看服务端日志是否有 render 报错（Chrome 未找到、渲染超时 30s）。

### S6 提交代码打印任务

切到「代码打印」页签，语言选 `C++`，源代码框粘贴：

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    // 你好，世界
    cout << "Hello && World" << endl;
    return 0;
}
```

点击「提交打印」。

**预期现象**：同上，提交成功 → 轮询 → `completed`，返回 `output_path` 指向 `code_*.pdf`。

**说明**：源码中的 `&&` 只做一次 HTML 转义（`&amp;&amp;`），PDF 内显示原文 `&&`，不会双重转义（D4 回归测试覆盖）。

### S7 查询任务状态（接口直查）

```bash
curl.exe http://127.0.0.1:18210/api/v1/tasks/<上一步返回的task_id>
```

**预期现象**：返回完整任务对象：`task_id / type / status / output_path / created_at / data`。

### S8 核对 PDF 产物

查看 `printsvc/output/` 目录，应存在 `ticket_*.pdf` 与 `code_*.pdf` 两个文件（大小约 40~60KB）。

**预期现象**：用任意 PDF 阅读器打开：
- `ticket_*.pdf`：58mm 窄纸小票样式，含队名、题号、通过时间；
- `code_*.pdf`：80mm 窄纸，代码自动折行，含简单语法着色（CSS 模拟，chroma 换真列入差距清单）。

**失败检查**：`output/` 为空 → 检查 S5/S6 是否真的 `completed`；PDF 中文乱码（Linux）→ 装 `fonts-noto-cjk`。

### S9 错误输入拒绝（可选核验）

```bash
# 非法类型
curl.exe -X POST http://127.0.0.1:18210/api/v1/tasks -H "Content-Type: application/json" -d "{\"type\":\"bogus\",\"data\":{}}"
# 缺字段
curl.exe -X POST http://127.0.0.1:18210/api/v1/tasks -H "Content-Type: application/json" -d "{\"type\":\"ticket\",\"data\":{\"problem\":\"A\"}}"
# 不存在任务
curl.exe http://127.0.0.1:18210/api/v1/tasks/T9999-0000000000
# 不支持的方法
curl.exe -X DELETE http://127.0.0.1:18210/api/v1/tasks/T0001-1787454312
```

**预期现象**（与接口契约一致）：
| 输入 | 响应 |
|---|---|
| 非法 type | `INVALID_ARGUMENT`「type must be ticket or code」 |
| ticket 缺 team | `INVALID_ARGUMENT`「data.team required for ticket」 |
| 不存在任务 | `NOT_FOUND`「task not found: ...」 |
| DELETE 方法 | `METHOD_NOT_ALLOWED`「method not allowed」 |

### S10 停止服务

前台运行窗口 `Ctrl+C`；后台运行：`Stop-Process -Name printsvc`。

**预期现象**：进程退出，页面探活状态条变红「服务离线」。

### S11 启动 / 停止 / 回退演练（D8）

| 步骤 | 操作 | 预期现象 |
|---|---|---|
| 11.1 端口回退 | 先用 `[System.Net.Sockets.TcpListener]` 占住 18210，再启动 `printsvc.exe` | 日志/`port.txt` 显示 18211（18210~18220 内递增回退） |
| 11.2 全占用优雅退出 | 占满 18210~18220 后启动 | 打印「端口 18210~18220 全部被占用」并以退出码 1 结束，不 panic |
| 11.3 停止后重启 | `Stop-Process -Name printsvc` 后再启动 | 进程退出干净；重启后正常监听、`port.txt` 重新生成 |
| 11.4 超大请求体（G7） | `POST /api/v1/tasks` 发 >1MB body | 400 `INVALID_ARGUMENT`，消息含 `too large` |
| 11.5 CORS 白名单（G7） | 带 `Origin: http://evil.example` 请求 | 响应无 `Access-Control-Allow-Origin`；本机 `http://127.0.0.1:18210` 来源则有 |

## 复现记录

| 字段 | 值 |
|---|---|
| 复现人 | （第二人姓名/环境名） |
| 环境 | Win10/11 + Go x.x + Chrome xx |
| 是否一次通过 | 是 / 否 |
| 卡点描述 | （卡在第几步、现象、解决方式） |
| 对说明的修改 | （复现后对本文档的修订内容） |

## 已知边界与临时假实现汇总

| 项 | 状态 | 说明 |
|---|---|---|
| 实体打印机出纸 | 未验证（D8 未借到实机，如实标注） | `CCPC_PRINTER` 指定打印机已实现并实测真实调用链；出纸行为待演示前借实机 |
| 安全边界（D8 G7） | 已实现 | CORS 仅放行本机来源、请求体上限 1MB、HTTP Server 显式超时；审计与残余风险见 `审查与安全清单_20260826.md` |
| 指定打印机 | 已实现（D7 G4） | 环境变量 `CCPC_PRINTER=<打印机名>`；Windows printui 切换默认→打印→恢复（try/finally+Go 兜底），Linux `lp -d`；未设置行为不变 |
| 前端最近任务列表 | 已实现（D7 G5） | `index.html` 任务表格+状态徽章+1.5s 轮询，localStorage 记录，不改接口契约 |
| 端口 18210~18220 全占用 | 已解决（D6 G3） | 优雅报错退出，port 包测试覆盖 |
| 语法高亮 | 临时假实现 | CSS 模拟着色，chroma 换真列入差距清单（D7 标"不做"，离线依赖受限） |
| Linux 真机验证 | 部分完成（D6 G1） | 交叉编译通过（ELF64），运行验证待 D8/演示前借真机 |
