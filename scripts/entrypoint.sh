#!/bin/sh
# 容器每次启动：放弃本地改动、从 GitLab 拉取最新代码，再安装依赖并执行 CMD（mcp_pipe 长连接）
# 要求：/app 必须为宿主机挂载的 git 仓库（即 NAS 上 clone 的 hzr_mcp 工程）

set -e
cd /app

if [ ! -d .git ]; then
  echo "错误: /app 下未发现 .git，请将宿主机上 clone 的 hzr_mcp 目录挂载到 /app" >&2
  exit 1
fi

# 挂载的目录属主是宿主机用户，容器内 root 需标记为 safe
git config --global --add safe.directory /app

# 若挂载了宿主机 .ssh，复制到容器内并设权限，避免 "Bad owner or permissions on /root/.ssh/config"
if [ -d /root/.ssh ] && [ -f /root/.ssh/config ]; then
  mkdir -p /root/.ssh_local
  cp -r /root/.ssh/. /root/.ssh_local/
  chmod 700 /root/.ssh_local
  [ -f /root/.ssh_local/config ] && chmod 600 /root/.ssh_local/config
  [ -f /root/.ssh_local/known_hosts ] && chmod 600 /root/.ssh_local/known_hosts
  for f in /root/.ssh_local/id_* /root/.ssh_local/*.pub; do
    [ -f "$f" ] && chmod 600 "$f"
  done
  export GIT_SSH_COMMAND="ssh -F /root/.ssh_local/config -o IdentitiesOnly=yes -o UserKnownHostsFile=/root/.ssh_local/known_hosts -o StrictHostKeyChecking=accept-new"
  # 若 known_hosts 为空，用 git remote 的 host:port 预先拉取 host key，避免 Host key verification failed
  if [ ! -s /root/.ssh_local/known_hosts ]; then
    GIT_HOST=$(git remote get-url origin 2>/dev/null | sed -n 's|ssh://[^@]*@\([^:/]*\).*|\1|p')
    GIT_PORT=$(git remote get-url origin 2>/dev/null | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
    if [ -n "$GIT_HOST" ]; then
      [ -z "$GIT_PORT" ] && GIT_PORT=22
      ssh-keyscan -p "$GIT_PORT" "$GIT_HOST" >> /root/.ssh_local/known_hosts 2>/dev/null || true
      chmod 600 /root/.ssh_local/known_hosts
    fi
  fi
fi

BRANCH="${GIT_BRANCH:-main}"
echo "[entrypoint] 拉取最新代码: git fetch origin && git reset --hard origin/${BRANCH}"
git fetch origin
git reset --hard "origin/${BRANCH}"

echo "[entrypoint] 安装依赖: pip install -r requirements.txt（国内镜像 + 长超时）"
pip install --no-cache-dir -r requirements.txt \
  -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 300

echo "[entrypoint] 启动: $*"
exec "$@"
