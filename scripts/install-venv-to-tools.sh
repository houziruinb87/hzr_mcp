#!/bin/bash
# 在 tools 目录下创建 venv 并安装 requirements.txt，使 NAS / office / hzr_mcp 共用同一 Python 环境（含 python-miio）
# 用法（在 NAS 上，或任意能写 tools 的机器）：
#   export TOOLS_DIR=/data_n003/data/udata/real/18510411307/docker/office/tools
#   ./scripts/install-venv-to-tools.sh
# 或：TOOLS_DIR=/path/to/office/tools ./scripts/install-venv-to-tools.sh
#
# 要求：TOOLS_DIR 可写，且本机有 python3、pip；完成后 tools/venv 与 jdk-17、android-sdk 同级。

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HZR_MCP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -z "$TOOLS_DIR" ]; then
  echo "请设置 TOOLS_DIR，例如：export TOOLS_DIR=/data_n003/data/udata/real/18510411307/docker/office/tools" >&2
  exit 1
fi

VENV_DIR="$TOOLS_DIR/venv"
REQUIREMENTS="$HZR_MCP_DIR/requirements.txt"

if [ ! -f "$REQUIREMENTS" ]; then
  echo "未找到 $REQUIREMENTS" >&2
  exit 1
fi

echo "[install-venv-to-tools] TOOLS_DIR=$TOOLS_DIR"
echo "[install-venv-to-tools] 创建 venv: $VENV_DIR"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
echo "[install-venv-to-tools] 安装依赖: pip install -r requirements.txt（国内镜像）"
"$VENV_DIR/bin/pip" install -r "$REQUIREMENTS" \
  -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 300

echo "[install-venv-to-tools] 完成。NAS 本机 source tools/env-host.sh，office 容器 source tools/env-common.sh，hzr_mcp 由 entrypoint 自动使用。"
echo "  验证: $VENV_DIR/bin/python --version && $VENV_DIR/bin/miiocli --version"
