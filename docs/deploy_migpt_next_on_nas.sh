#!/usr/bin/env bash
# 在能 ssh jkj 连上极空间 NAS 时，于本机执行此脚本，完成 MiGPT-Next 目录创建、配置与 compose 上传、拉镜像、起容器。
# 用法：cd 到 hzr_mcp 仓库根目录后执行：bash docs/deploy_migpt_next_on_nas.sh

set -e
NAS_USER_HOST="jkj"
REMOTE_BASE="/data_n003/data/udata/real/18510411307/docker/MiGPT-Next"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_SRC="$SCRIPT_DIR/migpt-next-config.example.js"
COMPOSE_SRC="$SCRIPT_DIR/migpt-next-docker-compose.yml"

echo "==> 1. 在 NAS 上创建 MiGPT-Next 目录"
ssh "$NAS_USER_HOST" "mkdir -p $REMOTE_BASE"

echo "==> 2. 上传 config.js 与 docker-compose.yml"
scp "$CONFIG_SRC" "$NAS_USER_HOST:$REMOTE_BASE/config.js"
scp "$COMPOSE_SRC" "$NAS_USER_HOST:$REMOTE_BASE/docker-compose.yml"

echo "==> 3. 停止旧容器（若存在）并用 Docker Compose 启动"
ssh "$NAS_USER_HOST" "sg docker -c 'docker stop migpt-next 2>/dev/null || true; docker rm migpt-next 2>/dev/null || true'"
ssh "$NAS_USER_HOST" "cd $REMOTE_BASE && sg docker -c 'docker compose up -d'"

echo "==> 4. 查看容器状态"
ssh "$NAS_USER_HOST" "sg docker -c 'docker ps --filter name=migpt-next'"

echo ""
echo "完成。修改配置后重启： ssh $NAS_USER_HOST \"cd $REMOTE_BASE && sg docker -c 'docker compose restart'\""
