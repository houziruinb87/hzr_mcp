#!/usr/bin/env bash
# 在 NAS 的 office/tools 目录下下载并解压 Eclipse Temurin OpenJDK 17，得到 tools/jdk-17/
# 用法（在 NAS 上）：
#   cd /data_n003/data/udata/real/18510411307/docker/office/tools
#   bash install-openjdk17-to-tools.sh
# 或指定目标目录：
#   bash install-openjdk17-to-tools.sh /path/to/office/tools

set -e
TARGET_DIR="${1:-$(dirname "$0")}"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"
INSTALL_DIR="$TARGET_DIR/jdk-17"
ARCH=$(uname -m)
case "$ARCH" in
  x86_64)  API_ARCH=x64 ;;
  aarch64|arm64) API_ARCH=aarch64 ;;
  *) echo "不支持的架构: $ARCH" >&2; exit 1 ;;
esac

echo "目标目录: $TARGET_DIR"
echo "架构: $ARCH -> $API_ARCH"
echo "将安装到: $INSTALL_DIR"

if [ -d "$INSTALL_DIR" ]; then
  echo "已存在 $INSTALL_DIR，跳过下载。若要重装请先删除该目录。"
  echo "JAVA_HOME=$INSTALL_DIR"
  exit 0
fi

DOWNLOAD_URL="https://api.adoptium.net/v3/binary/latest/17/ga/linux/${API_ARCH}/jdk/hotspot/normal/eclipse?project=jdk"
TARBALL="/tmp/openjdk-17-${API_ARCH}.tar.gz"

echo "正在下载 OpenJDK 17 (Eclipse Temurin) ..."
curl -sSL -o "$TARBALL" "$DOWNLOAD_URL"

echo "正在解压到 $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
tar -xzf "$TARBALL" -C "$TARGET_DIR"
# 解压后通常是一个 jdk-17.x.x+xx 目录，改名为 jdk-17
EXTRACTED=$(find "$TARGET_DIR" -maxdepth 1 -type d -name 'jdk-17*' | head -1)
if [ -n "$EXTRACTED" ] && [ "$EXTRACTED" != "$INSTALL_DIR" ]; then
  rm -rf "$INSTALL_DIR"
  mv "$EXTRACTED" "$INSTALL_DIR"
fi
rm -f "$TARBALL"

echo "完成。OpenJDK 17 已安装到: $INSTALL_DIR"
echo "使用方式："
echo "  export JAVA_HOME=$INSTALL_DIR"
echo "  export PATH=\$JAVA_HOME/bin:\$PATH"
echo "可在 office/tools/env.sh 中 source 或追加上述两行（或单独建 jdk17.env 再 source）。"
