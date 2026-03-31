#!/bin/bash
# 在 NAS 上执行，用于确认 Open-XiaoAI 是否已设置 PYTHONUNBUFFERED=1
# 用法：把本脚本拷到 NAS 后 chmod +x 再执行；或直接复制下面命令在 NAS SSH 里执行

set -e
CONTAINER="open-xiaoai-xiaozhi"

echo "=== 1. 检查容器 $CONTAINER 当前环境变量（CLI / PYTHONUNBUFFERED）==="
docker inspect "$CONTAINER" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep -E 'PYTHONUNBUFFERED|CLI' || true

if docker inspect "$CONTAINER" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep -q 'PYTHONUNBUFFERED=1'; then
  echo ""
  echo "已存在 PYTHONUNBUFFERED=1，无需修改。"
  exit 0
fi

echo ""
echo "=== 2. 未检测到 PYTHONUNBUFFERED=1 ==="
echo "请在你 NAS 上 Open-XiaoAI 的 docker-compose 所在目录（例如 Open-XiaoAI-Server）："
echo "  在 open-xiaoai-xiaozhi 的 environment 里增加一行：  - PYTHONUNBUFFERED=1"
echo "  然后执行：  docker compose up -d open-xiaoai-xiaozhi"
echo ""
echo "查看日志：  docker logs open-xiaoai-xiaozhi --tail 100"
