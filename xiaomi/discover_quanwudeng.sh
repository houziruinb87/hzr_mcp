#!/bin/bash
# 发现全屋灯（lxzn.switch.cbcsmj）的 MIOT 属性

IP="192.168.50.218"
TOKEN="33ca310ad290afd1ac98453c44c3faa2"

echo "=== 1. 获取设备基本信息 ==="
miiocli device --ip $IP --token $TOKEN info

echo ""
echo "=== 2. 查询 siid=2（主要功能，通常是开关控制）==="
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
echo "=== 3. 查询 siid=3（可能的第二路开关或传感器）==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[
  {"siid":3,"piid":1},
  {"siid":3,"piid":2},
  {"siid":3,"piid":3},
  {"siid":3,"piid":4},
  {"siid":3,"piid":5}
]'

echo ""
echo "=== 4. 查询 siid=4（辅助功能）==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[
  {"siid":4,"piid":1},
  {"siid":4,"piid":2},
  {"siid":4,"piid":3},
  {"siid":4,"piid":4},
  {"siid":4,"piid":5}
]'

echo ""
echo "=== 5. 查询 siid=5（可能有扩展功能）==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[
  {"siid":5,"piid":1},
  {"siid":5,"piid":2},
  {"siid":5,"piid":3}
]'
