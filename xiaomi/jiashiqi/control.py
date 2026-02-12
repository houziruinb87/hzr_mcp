#!/usr/bin/env python3
"""YO 加湿器控制。供 hzr_mcp.py 通过 subprocess 调用。

用法:
  python control.py on           # 打开加湿器
  python control.py off          # 关闭加湿器
  python control.py status       # 查询状态
  python control.py level 1      # 设置为弱档（手动档位）
  python control.py level 2      # 设置为中档（手动档位）
  python control.py level 3      # 设置为强档（手动档位）
  python control.py mode 1       # 设置为睡眠模式（场景模式）
  python control.py mode 2       # 设置为自动模式（场景模式）
  python control.py mode 3       # 设置为强劲模式（场景模式）
  python control.py lock on      # 开启童锁
  python control.py lock off     # 关闭童锁

从 ../devices.json 读取 YO Humidifier 的 ip/token。
已验证属性：
  - siid=2, piid=1: 电源开关（True/False）
  - siid=2, piid=9: 场景模式（1=睡眠, 2=自动, 3=强劲）
  - siid=2, piid=10: 手动档位（1=弱档, 2=中档, 3=强档）
  - siid=4, piid=1: 功能锁/童锁（True/False）
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


def set_level(ip: str, token: str, level: int) -> None:
    """设置手动档位 (1=弱档, 2=中档, 3=强档)"""
    import subprocess
    if level not in (1, 2, 3):
        raise ValueError("档位必须是 1（弱）、2（中）或 3（强）")
    bin_dir = os.path.dirname(os.path.abspath(sys.executable))
    miiocli_cmd = os.path.join(bin_dir, "miiocli")
    if not os.path.isfile(miiocli_cmd):
        miiocli_cmd = "miiocli"
    cmd = [
        miiocli_cmd, "miotdevice",
        "--ip", ip, "--token", token,
        "raw_command", "set_properties",
        f'[{{"siid":2,"piid":10,"value":{level}}}]',
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if out.returncode != 0:
        raise RuntimeError(out.stderr or out.stdout or f"退出码 {out.returncode}")


def set_mode(ip: str, token: str, mode: int) -> None:
    """设置场景模式 (1=睡眠, 2=自动, 3=强劲)"""
    import subprocess
    if mode not in (1, 2, 3):
        raise ValueError("模式必须是 1（睡眠）、2（自动）或 3（强劲）")
    bin_dir = os.path.dirname(os.path.abspath(sys.executable))
    miiocli_cmd = os.path.join(bin_dir, "miiocli")
    if not os.path.isfile(miiocli_cmd):
        miiocli_cmd = "miiocli"
    cmd = [
        miiocli_cmd, "miotdevice",
        "--ip", ip, "--token", token,
        "raw_command", "set_properties",
        f'[{{"siid":2,"piid":9,"value":{mode}}}]',
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if out.returncode != 0:
        raise RuntimeError(out.stderr or out.stdout or f"退出码 {out.returncode}")


def set_child_lock(ip: str, token: str, locked: bool) -> None:
    """设置童锁 (True=锁定, False=解锁)"""
    import subprocess
    value = "True" if locked else "False"
    bin_dir = os.path.dirname(os.path.abspath(sys.executable))
    miiocli_cmd = os.path.join(bin_dir, "miiocli")
    if not os.path.isfile(miiocli_cmd):
        miiocli_cmd = "miiocli"
    cmd = [
        miiocli_cmd, "miotdevice",
        "--ip", ip, "--token", token,
        "raw_command", "set_properties",
        f'[{{"siid":4,"piid":1,"value":{value}}}]',
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
        '[{"siid":2,"piid":1},{"siid":2,"piid":10},{"siid":4,"piid":1}]',
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if out.returncode != 0:
        raise RuntimeError(out.stderr or out.stdout or f"退出码 {out.returncode}")
    
    # 解析输出（简单处理）
    return {"raw_output": out.stdout}


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: control.py on|off|status|level <1-3>|mode <1-3>|lock <on|off>", file=sys.stderr)
        return 1
    
    action = (sys.argv[1] or "").strip().lower()
    
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
        
        elif action == "on":
            set_power(ip, token, True)
            print("已开启加湿器")
            return 0
        
        elif action == "off":
            set_power(ip, token, False)
            print("已关闭加湿器")
            return 0
        
        elif action == "level":
            if len(sys.argv) < 3:
                print("用法: control.py level <1-3>", file=sys.stderr)
                print("  1 = 弱档, 2 = 中档, 3 = 强档", file=sys.stderr)
                return 1
            try:
                level = int(sys.argv[2])
                if level not in (1, 2, 3):
                    raise ValueError()
                set_level(ip, token, level)
                level_names = {1: "弱档", 2: "中档", 3: "强档"}
                print(f"已设置为{level_names[level]}")
                return 0
            except ValueError:
                print("档位必须是 1（弱档）、2（中档）或 3（强档）", file=sys.stderr)
                return 1
        
        elif action == "mode":
            if len(sys.argv) < 3:
                print("用法: control.py mode <1-3>", file=sys.stderr)
                print("  1 = 睡眠模式, 2 = 自动模式, 3 = 强劲模式", file=sys.stderr)
                return 1
            try:
                mode = int(sys.argv[2])
                if mode not in (1, 2, 3):
                    raise ValueError()
                set_mode(ip, token, mode)
                mode_names = {1: "睡眠模式", 2: "自动模式", 3: "强劲模式"}
                print(f"已设置为{mode_names[mode]}")
                return 0
            except ValueError:
                print("模式必须是 1（睡眠模式）、2（自动模式）或 3（强劲模式）", file=sys.stderr)
                return 1
        
        elif action == "lock":
            if len(sys.argv) < 3:
                print("用法: control.py lock <on|off>", file=sys.stderr)
                return 1
            lock_action = (sys.argv[2] or "").strip().lower()
            if lock_action not in ("on", "off"):
                print("用法: control.py lock <on|off>", file=sys.stderr)
                return 1
            locked = lock_action == "on"
            set_child_lock(ip, token, locked)
            print("已开启童锁" if locked else "已关闭童锁")
            return 0
        
        else:
            print("用法: control.py on|off|status|level <1-3>|mode <1-3>|lock <on|off>", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
