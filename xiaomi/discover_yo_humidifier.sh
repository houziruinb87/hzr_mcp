#!/bin/bash
# 发现 YO 加湿器的 MIOT 属性和能力

IP="192.168.1.103"
TOKEN="f7f296300d02ac9b5bf0b13d1a3c7995"

echo "=== 1. 获取设备基本信息 ==="
miiocli device --ip $IP --token $TOKEN info

echo ""
echo "=== 2. 获取设备状态（通用 MIoT 设备）==="
miiocli genericmiot --ip $IP --token $TOKEN status

echo ""
echo "=== 3. 尝试查询常见加湿器属性（siid=2,3,4）==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[
  {"siid":2,"piid":1},
  {"siid":2,"piid":2},
  {"siid":2,"piid":3},
  {"siid":2,"piid":4},
  {"siid":2,"piid":5},
  {"siid":2,"piid":6},
  {"siid":2,"piid":7},
  {"siid":3,"piid":1},
  {"siid":3,"piid":2},
  {"siid":4,"piid":1},
  {"siid":4,"piid":2},
  {"siid":4,"piid":3}
]'

echo ""
echo "=== 4. 尝试 MIoT 加湿器命令 ==="
miiocli airhumidifiermiot --ip $IP --token $TOKEN status
