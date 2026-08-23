# printsvc 主路径演示说明（第 5 天）

> 目标：让一个**陌生环境/第二人**仅凭本说明即可复现「Web 提交 → 任务排队 → 渲染 PDF → 打印/PDF 兜底 → 状态查询」主路径。
> 适用于 Windows；Linux 差异在第 8 步注明。

## 环境前提

| 项 | 要求 | 检查命令（Windows） |
|---|---|---|
| Go | 1.22+ | `go version` |
| Chrome | 已安装 | 默认探测 `C:\Program Files\Google\Chrome\Application\chrome.exe` 与 `(x86)` |
| 实体打印机 | **可选** | 无打印机时自动走 PDF 兜底，PDF 即为产物 |

> 临时假实现说明：当前版本未接实体打印机验证出纸（D7 待办），无打印机时打印模块自动回退为 PDF 兜底并视作成功——这是**有意的临时行为**，非 bug。气球小票/代码渲染均为真实实现。

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

**失败检查**：18210~18220 全被占用 → 进程退出并打印端口协商失败日志（此场景当前为已知边界，D5 差距清单已记录）。

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
2. 自动轮询（1.5s/次），约 2~4 秒后状态变为 `"completed"`，响应含 `output_path`。

**失败检查**：状态长时间停在 `pending` → 查看服务端日志是否有 render 报错（Chrome 未找到、渲染超时 30s）。

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
| 实体打印机出纸 | 临时假实现 | 无打印机时 PDF 兜底，D7 借实机验证 |
| 端口 18210~18220 全占用 | 已知边界 | 进程报错退出，暂未优雅降级（D5 差距清单） |
| 语法高亮 | 临时假实现 | CSS 模拟着色，chroma 换真列入差距清单 |
| Linux 真机验证 | 待验证 | 本机无 WSL，D6 交叉编译 + 远程验证 |
