#!/bin/bash
# 生成「伊朗最新情况」的 opus 文件，供 verify_xiaozhi_full_chat.py 使用。
# 需要：pip install edge-tts，系统已安装 ffmpeg
set -e
TEXT="${1:-伊朗最新情况}"
WAV="/tmp/q.wav"
OPUS="/tmp/q_伊朗.opus"
edge-tts --text "$TEXT" --voice zh-CN-YunxiNeural --write-media "$WAV"
ffmpeg -y -i "$WAV" -acodec libopus -ar 16000 -ac 1 -frame_duration 60 -f opus "$OPUS" 2>/dev/null
rm -f "$WAV"
echo "已生成: $OPUS"
echo "运行: python3 verify_xiaozhi_full_chat.py --url ws://NAS_IP:8000/xiaozhi/v1/ --opus-file $OPUS"
