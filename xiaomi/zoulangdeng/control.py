#!/usr/bin/env python3
"""走廊灯开关控制。供 hzr_mcp.py 通过 subprocess 调用。

用法:
  python control.py on   # 打开走廊灯
  python control.py off  # 关闭走廊灯

从 ../devices.json 读取 走廊灯 的 ip/token；使用 MIOT set_property(siid=2, piid=1)。
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
    value = "True" if on else "False"
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


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: control.py on|off", file=sys.stderr)
        return 1
    action = (sys.argv[1] or "").strip().lower()
    if action not in ("on", "off"):
        print("用法: control.py on|off", file=sys.stderr)
        return 1
    on = action == "on"
    try:
        dev = load_device_by_name("走廊灯")
        ip = dev.get("ip")
        token = dev.get("token")
        if not ip or not token:
            print("走廊灯 缺少 ip 或 token", file=sys.stderr)
            return 1
        set_power(ip, token, on)
        print("已开" if on else "已关")
        return 0
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
