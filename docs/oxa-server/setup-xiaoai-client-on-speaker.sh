#!/bin/bash
# 在已刷机的小爱音箱上安装 Open-XiaoAI Rust Client，连到 NAS 的 Server
# 用法：把 SPEAKER_IP 改成你的音箱 IP，在 Mac 上运行：./setup-xiaoai-client-on-speaker.sh
# 会提示输入音箱的 root 密码（刷机时设的）

set -e
SPEAKER_IP="${1:-192.168.1.50}"
NAS_IP="192.168.1.100"
SERVER_URL="ws://${NAS_IP}:4399"

echo "小爱音箱 IP: $SPEAKER_IP"
echo "NAS Server:   $SERVER_URL"
echo ""

ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa root@${SPEAKER_IP} "
  set -e
  echo '>>> 创建 /data/open-xiaoai'
  mkdir -p /data/open-xiaoai
  echo '>>> 写入 Server 地址: $SERVER_URL'
  echo '$SERVER_URL' > /data/open-xiaoai/server.txt
  cat /data/open-xiaoai/server.txt
  echo ''
  echo '>>> 下载并执行 init.sh 安装 Rust Client'
  curl -sSfL https://gitee.com/idootop/artifacts/releases/download/open-xiaoai-client/init.sh | sh
  echo ''
  echo '>>> 完成。若需开机自启，请在小爱音箱上执行：'
  echo '    curl -L -o /data/init.sh https://gitee.com/idootop/artifacts/releases/download/open-xiaoai-client/boot.sh'
  echo '    reboot'
"

echo ""
echo "Rust Client 已安装并启动，音箱会连到 NAS:4399。可用「小智同学」等唤醒词测试。"
