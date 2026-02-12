#!/bin/bash
# 测试 YO 加湿器的模式和档位

IP="192.168.50.203"
TOKEN="f7f296300d02ac9b5bf0b13d1a3c7995"

echo "=========================================="
echo "YO 加湿器模式和档位测试"
echo "=========================================="
echo ""

echo "=== 1. 先打开加湿器 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":1,"value":True}]'
sleep 2

echo ""
echo "=== 2. 查看当前所有参数 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":1},{"siid":2,"piid":2},{"siid":2,"piid":9},{"siid":2,"piid":10},{"siid":4,"piid":1},{"siid":5,"piid":1}]'

echo ""
echo "=========================================="
echo "测试 siid=2, piid=2 (档位/场景模式)"
echo "=========================================="
echo ""

echo "=== 测试值 0 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":2,"value":0}]'
sleep 2
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":2}]'
echo ">>> 观察加湿器变化，记录这是什么模式"
echo ">>> 按回车继续..."
read

echo ""
echo "=== 测试值 1 (可能是：弱/睡眠) ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":2,"value":1}]'
sleep 2
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":2}]'
echo ">>> 观察加湿器变化（档位、雾量、噪音、灯光等），记录这是什么模式"
echo ">>> 按回车继续..."
read

echo ""
echo "=== 测试值 2 (可能是：中/自动) ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":2,"value":2}]'
sleep 2
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":2}]'
echo ">>> 观察加湿器变化，记录这是什么模式"
echo ">>> 按回车继续..."
read

echo ""
echo "=== 测试值 3 (可能是：强/强劲) ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":2,"value":3}]'
sleep 2
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":2}]'
echo ">>> 观察加湿器变化，记录这是什么模式"
echo ">>> 按回车继续..."
read

echo ""
echo "=== 测试值 4 (可能有第4个模式?) ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":2,"value":4}]'
sleep 2
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":2}]'
echo ">>> 观察加湿器变化，记录这是什么模式（如果失败说明只有0-3）"
echo ">>> 按回车继续..."
read

echo ""
echo "=========================================="
echo "测试 siid=5, piid=1 (目标湿度)"
echo "=========================================="
echo ""

echo "=== 当前值 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":5,"piid":1}]'

echo ""
echo "=== 测试设置为 40% ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":5,"piid":1,"value":40}]'
sleep 2
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":5,"piid":1}]'
echo ">>> 观察加湿器（如果支持目标湿度，App 里应该显示 40%）"
echo ">>> 按回车继续..."
read

echo ""
echo "=== 测试设置为 60% ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":5,"piid":1,"value":60}]'
sleep 2
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":5,"piid":1}]'
echo ">>> 观察加湿器（如果支持目标湿度，App 里应该显示 60%）"
echo ">>> 按回车继续..."
read

echo ""
echo "=== 恢复为默认值 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":5,"piid":1,"value":25}]'

echo ""
echo "=========================================="
echo "测试 siid=4, piid=1 (辅助开关 - 可能是LED/蜂鸣器)"
echo "=========================================="
echo ""

echo "=== 当前值 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":4,"piid":1}]'

echo ""
echo "=== 打开 (True) ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":4,"piid":1,"value":True}]'
sleep 2
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":4,"piid":1}]'
echo ">>> 观察加湿器（LED灯是否亮了？有蜂鸣声？显示屏变化？）"
echo ">>> 按回车继续..."
read

echo ""
echo "=== 关闭 (False) ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":4,"piid":1,"value":False}]'
sleep 2
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":4,"piid":1}]'
echo ">>> 观察加湿器变化"

echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "=== 最终状态查询 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command get_properties '[{"siid":2,"piid":1},{"siid":2,"piid":2},{"siid":4,"piid":1},{"siid":5,"piid":1}]'

echo ""
echo "=== 关闭加湿器 ==="
miiocli miotdevice --ip $IP --token $TOKEN raw_command set_properties '[{"siid":2,"piid":1,"value":False}]'

echo ""
echo "请将观察到的模式对应关系告诉我，我会更新控制脚本！"
