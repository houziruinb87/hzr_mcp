# hzr_mcp：小智 MCP 接入（WebSocket 连小智云端，长连接）
# 代码不打包进镜像，由挂载的 git 仓库提供；每次启动时 entrypoint 会拉取最新代码再启动
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 仅复制入口脚本；应用代码由宿主机挂载到 /app（即 NAS 上 clone 的 hzr_mcp 目录）
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
# 需环境变量 MCP_ENDPOINT 或 MCP_BASE_URL + MCP_TOKEN；可选 GIT_BRANCH（默认 main）
CMD ["python", "mcp_pipe.py", "hzr_mcp.py"]
