#!/bin/sh
# 在 hzr_mcp 容器内验证 tools 环境（Python venv、JAVA、ADB）
# 用法（在 NAS 上执行）：
#   docker exec -it hzr_mcp sh /app/scripts/verify-tools-in-container.sh
# 或先进入容器再执行：docker exec -it hzr_mcp sh，然后 sh /app/scripts/verify-tools-in-container.sh

set -e
TOOLS_DIR="${TOOLS_DIR:-/workspace/tools}"

echo "=== TOOLS_DIR=$TOOLS_DIR ==="
[ -d "$TOOLS_DIR" ] || { echo "  [失败] 目录不存在（未挂载 office/tools）"; exit 1; }
echo "  [OK] 目录存在"

echo ""
echo "=== Python (tools/venv) ==="
if [ -x "$TOOLS_DIR/venv/bin/python" ]; then
  "$TOOLS_DIR/venv/bin/python" --version
  echo "  [OK] venv 可用"
else
  echo "  [跳过] $TOOLS_DIR/venv/bin/python 不存在"
fi

echo ""
echo "=== miiocli ==="
if [ -x "$TOOLS_DIR/venv/bin/miiocli" ]; then
  "$TOOLS_DIR/venv/bin/miiocli" --help | head -5
  echo "  [OK] miiocli 可用（勿用 miiocli --version，会报 miio 未安装）"
else
  echo "  [跳过] $TOOLS_DIR/venv/bin/miiocli 不存在"
fi

echo ""
echo "=== JAVA (tools/jdk-17) ==="
if [ -x "$TOOLS_DIR/jdk-17/bin/java" ]; then
  "$TOOLS_DIR/jdk-17/bin/java" -version 2>&1
  echo "  [OK] $TOOLS_DIR/jdk-17"
else
  echo "  [跳过] $TOOLS_DIR/jdk-17 不存在"
fi

echo ""
echo "=== ADB (tools/android-sdk) ==="
if [ -x "$TOOLS_DIR/android-sdk/platform-tools/adb" ]; then
  "$TOOLS_DIR/android-sdk/platform-tools/adb" version | head -1
  echo "  [OK] $TOOLS_DIR/android-sdk/platform-tools/adb"
else
  echo "  [跳过] $TOOLS_DIR/android-sdk 或 adb 不存在"
fi

echo ""
echo "=== PATH 中 python/miiocli（entrypoint 启动 CMD 时已加 venv/bin）==="
if command -v python >/dev/null 2>&1; then
  echo "  python -> $(command -v python)"
else
  echo "  python 不在 PATH（当前 shell 未走 entrypoint，属正常）"
fi
if command -v miiocli >/dev/null 2>&1; then
  echo "  miiocli -> $(command -v miiocli)"
else
  echo "  miiocli 不在 PATH（当前 shell 未走 entrypoint，属正常）"
fi

echo ""
echo "=== 验证完成 ==="
