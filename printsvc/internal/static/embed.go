package static

import _ "embed"

// IndexHTML 前端页面：go:embed 打包进二进制，运行不依赖工作目录
//
//go:embed index.html
var IndexHTML string
