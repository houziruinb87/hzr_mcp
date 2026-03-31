#!/bin/bash
# 测试 YO 加湿器开关控制

IP="192.168.1.103"
TOKEN="f7f296300d02ac9b5bf0b13d1a3c7995"

echo "=== 当前状态 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":1},{"siid":2,"piid":2},{"siid":2,"piid":9},{"siid":2,"piid":10},{"siid":4,"piid":1},{"siid":5,"piid":1}]'

echo ""
echo "=== 1. 打开加湿器（修正 JSON 格式）==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":1,"value":True}]'

echo ""
echo "等待 3 秒观察..."
sleep 3

echo ""
echo "=== 2. 查询开启后的状态 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":1},{"siid":2,"piid":2},{"siid":2,"piid":9},{"siid":2,"piid":10},{"siid":5,"piid":1}]'

echo ""
echo "=== 3. 关闭加湿器 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":1,"value":False}]'

echo ""
echo "=== 4. 查询关闭后的状态 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":1}]'

echo ""
echo "=== 测试完成 ==="
