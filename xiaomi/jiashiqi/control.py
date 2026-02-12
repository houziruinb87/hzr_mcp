#!/usr/bin/env python3
"""YO 加湿器控制。供 hzr_mcp.py 通过 subprocess 调用。

用法:
  python control.py on        # 打开加湿器
  python control.py off       # 关闭加湿器
  python control.py status    # 查询状态

从 ../devices.json 读取 YO Humidifier 的 ip/token。
已发现属性：
  - siid=2, piid=1: 电源开关（True/False）
  - siid=2, piid=2: 模式/档位（数值，待测试）
  - siid=4, piid=1: 未知开关（待测试）
"""
from __future__ import annotations

import json
import os
import sys


def load_device_by_name(name: str) -> dict:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    devices_path = os.path.join(script_dir, "..", "devices.json")
    if not os.path.isfile(devices_path):
        raise FileNotFoundError(f"未找到 {devices_path}")
    with open(devices_path, encoding="utf-8") as f:
        data = json.load(f)
    devices = data.get("devices", data) if isinstance(data, dict) else data
    for d in devices:
        if d.get("name") == name:
            return d
    raise KeyError(f"未找到设备「{name}」")


def set_power(ip: str, token: str, on: bool) -> None:
    import subprocess
    value = "True" if on else "False"  # Python 风格：大写 True/False
    bin_dir = os.path.dirname(os.path.abspath(sys.executable))
    miiocli_cmd = os.path.join(bin_dir, "miiocli")
    if not os.path.isfile(miiocli_cmd):
        miiocli_cmd = "miiocli"
    cmd = [
        miiocli_cmd, "miotdevice",
        "--ip", ip, "--token", token,
        "raw_command", "set_properties",
        f'[{{"siid":2,"piid":1,"value":{value}}}]',
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if out.returncode != 0:
        raise RuntimeError(out.stderr or out.stdout or f"退出码 {out.returncode}")


def get_status(ip: str, token: str) -> dict:
    """查询加湿器状态"""
    import subprocess
    bin_dir = os.path.dirname(os.path.abspath(sys.executable))
    miiocli_cmd = os.path.join(bin_dir, "miiocli")
    if not os.path.isfile(miiocli_cmd):
        miiocli_cmd = "miiocli"
    cmd = [
        miiocli_cmd, "miotdevice",
        "--ip", ip, "--token", token,
        "raw_command", "get_properties",
        '[{"siid":2,"piid":1},{"siid":2,"piid":2},{"siid":4,"piid":1}]',
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if out.returncode != 0:
        raise RuntimeError(out.stderr or out.stdout or f"退出码 {out.returncode}")
    
    # 解析输出（简单处理）
    return {"raw_output": out.stdout}


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: control.py on|off|status", file=sys.stderr)
        return 1
    action = (sys.argv[1] or "").strip().lower()
    if action not in ("on", "off", "status"):
        print("用法: control.py on|off|status", file=sys.stderr)
        return 1
    
    try:
        dev = load_device_by_name("YO Humidifier")
        ip = dev.get("ip")
        token = dev.get("token")
        if not ip or not token:
            print("YO Humidifier 缺少 ip 或 token", file=sys.stderr)
            return 1
        
        if action == "status":
            result = get_status(ip, token)
            print(result.get("raw_output", "无状态信息"))
            return 0
        else:
            on = action == "on"
            set_power(ip, token, on)
            print("已开" if on else "已关")
            return 0
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
