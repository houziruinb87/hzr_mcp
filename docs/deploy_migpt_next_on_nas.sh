#!/usr/bin/env bash
# 在能 ssh jkj 连上极空间 NAS 时，于本机执行此脚本，完成 MiGPT-Next 目录创建、配置上传、拉镜像、起容器。
# 用法：cd 到 hzr_mcp 仓库根目录后执行：bash docs/deploy_migpt_next_on_nas.sh

set -e
NAS_USER_HOST="jkj"
REMOTE_BASE="/data_n003/data/udata/real/18510411307/docker/MiGPT-Next"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_SRC="$SCRIPT_DIR/migpt-next-config.example.js"

echo "==> 1. 在 NAS 上创建 MiGPT-Next 目录"
ssh "$NAS_USER_HOST" "mkdir -p $REMOTE_BASE"

echo "==> 2. 上传 config.js（请到 NAS 上编辑 $REMOTE_BASE/config.js 填写小米 userId / password / did）"
scp "$CONFIG_SRC" "$NAS_USER_HOST:$REMOTE_BASE/config.js"

echo "==> 3. 拉取 MiGPT-Next 镜像并启动容器"
ssh "$NAS_USER_HOST" "sg docker -c 'docker stop migpt-next 2>/dev/null || true; docker rm migpt-next 2>/dev/null || true'"
ssh "$NAS_USER_HOST" "sg docker -c 'docker pull idootop/migpt-next:latest'"
ssh "$NAS_USER_HOST" "sg docker -c 'docker run -d --name migpt-next --restart unless-stopped -v $REMOTE_BASE/config.js:/app/config.js idootop/migpt-next:latest'"

echo "==> 4. 查看容器状态"
ssh "$NAS_USER_HOST" "sg docker -c 'docker ps --filter name=migpt-next'"

echo ""
echo "完成。请到 NAS 上编辑 config.js 填写真实的小米账号与设备名："
echo "  ssh $NAS_USER_HOST"
echo "  vi $REMOTE_BASE/config.js   # 修改 userId、password、did"
echo "  修改后执行: sg docker -c 'docker restart migpt-next'"
