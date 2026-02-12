#!/bin/bash
# 测试 YO 加湿器各个参数的作用

IP="192.168.50.203"
TOKEN="f7f296300d02ac9b5bf0b13d1a3c7995"

echo "=== 当前所有可用属性的值 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":1},{"siid":2,"piid":2},{"siid":2,"piid":9},{"siid":2,"piid":10},{"siid":4,"piid":1},{"siid":5,"piid":1}]'

echo ""
echo "=== 测试 siid=2, piid=2（模式/档位）==="
echo "当前值：0，尝试设置为 1"
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":2,"value":1}]'
sleep 1
echo "查询结果："
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":2}]'

echo ""
echo "尝试设置为 2"
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":2,"value":2}]'
sleep 1
echo "查询结果："
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":2}]'

echo ""
echo "恢复为 0"
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":2,"value":0}]'

echo ""
echo "=== 测试 siid=4, piid=1（辅助开关）==="
echo "当前值：False，尝试设置为 True"
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":4,"piid":1,"value":True}]'
sleep 1
echo "查询结果："
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":4,"piid":1}]'
echo "（观察加湿器是否有 LED/声音/显示变化）"

echo ""
echo "恢复为 False"
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":4,"piid":1,"value":False}]'

echo ""
echo "=== 测试 siid=5, piid=1（数值参数）==="
echo "当前值：25，尝试设置为 60"
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":5,"piid":1,"value":60}]'
sleep 1
echo "查询结果："
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":5,"piid":1}]'
echo "（如果是目标湿度，加湿器可能开始调整）"

echo ""
echo "恢复为 25"
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":5,"piid":1,"value":25}]'

echo ""
echo "=== 最终状态 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":1},{"siid":2,"piid":2},{"siid":2,"piid":9},{"siid":2,"piid":10},{"siid":4,"piid":1},{"siid":5,"piid":1}]'
