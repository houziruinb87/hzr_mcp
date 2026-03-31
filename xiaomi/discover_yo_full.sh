#!/bin/bash
# YO 加湿器完整属性发现

IP="192.168.1.103"
TOKEN="f7f296300d02ac9b5bf0b13d1a3c7995"

echo "=== 扩展查询 siid=2 的更多属性 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[
  {"siid":2,"piid":1},
  {"siid":2,"piid":2},
  {"siid":2,"piid":3},
  {"siid":2,"piid":4},
  {"siid":2,"piid":5},
  {"siid":2,"piid":6},
  {"siid":2,"piid":7},
  {"siid":2,"piid":8},
  {"siid":2,"piid":9},
  {"siid":2,"piid":10}
]'

echo ""
echo "=== 查询 siid=3（通常是传感器/监控数据）==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[
  {"siid":3,"piid":1},
  {"siid":3,"piid":2},
  {"siid":3,"piid":3},
  {"siid":3,"piid":4},
  {"siid":3,"piid":5}
]'

echo ""
echo "=== 查询 siid=4（通常是辅助功能）==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[
  {"siid":4,"piid":1},
  {"siid":4,"piid":2},
  {"siid":4,"piid":3},
  {"siid":4,"piid":4},
  {"siid":4,"piid":5}
]'

echo ""
echo "=== 查询 siid=5（可能有额外功能）==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[
  {"siid":5,"piid":1},
  {"siid":5,"piid":2},
  {"siid":5,"piid":3}
]'

echo ""
echo "=== 测试开关控制 ==="
echo "1. 打开加湿器"
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":1,"value":true}]'

echo ""
echo "等待 3 秒..."
sleep 3

echo ""
echo "2. 查询状态（应该是开启）"
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":1}]'

echo ""
echo "3. 关闭加湿器"
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":1,"value":false}]'
