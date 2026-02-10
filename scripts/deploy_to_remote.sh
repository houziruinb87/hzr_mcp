#!/bin/bash
# 在 Mac 本地执行：SSH 到远端 NAS，重启 WSS 长连接容器（容器启动时 entrypoint 会 git fetch 并重连小智）
# 用法：./scripts/deploy_to_remote.sh              # 部署
#       ./scripts/deploy_to_remote.sh --logs       # 部署并跟踪日志
#       ./scripts/deploy_to_remote.sh --setup-ssh # 首次配置免密（执行一次即可）

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG="$REPO_DIR/deploy.config"

if [ ! -f "$CONFIG" ]; then
    echo "错误: 未找到 deploy.config"
    echo "请复制 deploy.config.example 为 deploy.config 并填写 REMOTE_HOST / REMOTE_USER / REMOTE_PATH"
    echo "  cp deploy.config.example deploy.config"
    exit 1
fi

. "$CONFIG"
REMOTE_HOST="${REMOTE_HOST:?请在 deploy.config 中设置 REMOTE_HOST}"
REMOTE_PATH="${REMOTE_PATH:?请在 deploy.config 中设置 REMOTE_PATH}"
REMOTE_PORT="${REMOTE_PORT:-}"
# 若 REMOTE_USER 为空则直接用 REMOTE_HOST（如 ssh config 里配了 Host jkj 含 User/Port）
[ -n "$REMOTE_USER" ] && SSH_TARGET="$REMOTE_USER@$REMOTE_HOST" || SSH_TARGET="$REMOTE_HOST"
[ -n "$REMOTE_PORT" ] && SSH_OPTS=(-p "$REMOTE_PORT") || SSH_OPTS=()

if [ "$1" = "--setup-ssh" ]; then
    echo "==> 配置 SSH 免密登录 $SSH_TARGET（只需执行一次，会提示输入 NAS 密码）"
    ssh-copy-id "${SSH_OPTS[@]}" "$SSH_TARGET"
    echo "==> 配置完成，之后执行 ./scripts/deploy_to_remote.sh 无需再输入密码"
    exit 0
fi

echo "==> 远端 NAS 拉取并重启 WSS 长连接: $SSH_TARGET:$REMOTE_PATH"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "cd $REMOTE_PATH && docker compose restart"
echo "==> 已执行 docker compose restart（容器启动时会 git fetch 并重连小智）"

if [ "$1" = "--logs" ]; then
    echo "==> 跟踪日志（Ctrl+C 退出）"
    ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "cd $REMOTE_PATH && docker compose logs -f"
fi
