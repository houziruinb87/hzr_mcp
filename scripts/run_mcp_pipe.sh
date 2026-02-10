#!/bin/bash
# 供 launchd / 手动 / NAS 常驻调用的 MCP pipe 启动脚本
# 连接小智 MCP 接入点（wss://api.xiaozhi.me/mcp/?token=...），将本地 hzr_mcp.py（stdio）桥接上去，保持长连接。
# 使用前在项目根目录配置 .env：MCP_BASE_URL=wss://api.xiaozhi.me/mcp/ 与 MCP_TOKEN=你的JWT
# 接入文档：https://my.feishu.cn/wiki/HiPEwZ37XiitnwktX13cEM5KnSb

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HZR_MCP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$HZR_MCP_DIR"

if [ -d ".venv/bin" ]; then
    exec .venv/bin/python mcp_pipe.py hzr_mcp.py
else
    exec python3 mcp_pipe.py hzr_mcp.py
fi
