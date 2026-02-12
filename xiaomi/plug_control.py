#!/usr/bin/env python3
"""用 Python API 控制插座/灯（绕过 miiocli 的 Click 兼容性 bug）。

用法（在项目根或 xiaomi 目录执行）:
  python xiaomi/plug_control.py 乌龟灯 on
  python xiaomi/plug_control.py 乌龟灯 off
  python xiaomi/plug_control.py 走廊灯 on

从 xiaomi/devices.json 按名称查 ip/token；支持 plug 类设备（cuco.plug、chuangmi.plug 等）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def load_devices(json_path: str) -> list[dict]:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("devices", data) if isinstance(data, dict) else data


def find_device(devices: list[dict], name: str) -> dict | None:
    for d in devices:
        if d.get("name") == name or d.get("name", "").strip() == name:
            return d
    return None


def plug_on_off(ip: str, token: str, model: str, on: bool) -> None:
    action = "on" if on else "off"
    # 优先用 ChuangmiPlug（支持 chuangmi.plug.v3 等），cuco.plug.v3 协议兼容可尝试
    try:
        from miio.integrations.chuangmi.plug.chuangmi_plug import ChuangmiPlug
        plug = ChuangmiPlug(ip=ip, token=token, model=model or None)
        if on:
            plug.on()
        else:
            plug.off()
        print(f"已{action}")
        return
    except Exception as e:
        pass
    # 回退：通用 Device 发 set_power
    try:
        from miio import Device
        dev = Device(ip, token)
        dev.send("set_power", [action])
        print(f"已{action}")
        return
    except Exception as e:
        print(f"失败: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="按设备名控制插座/灯 on/off")
    parser.add_argument("name", help="设备名，如 乌龟灯、走廊灯")
    parser.add_argument("action", choices=("on", "off"), help="on 或 off")
    parser.add_argument(
        "--devices-json",
        default=None,
        help="devices.json 路径，默认 xiaomi/devices.json",
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_json = os.path.join(script_dir, "devices.json")
    json_path = args.devices_json or default_json
    if not os.path.isfile(json_path):
        print(f"未找到 {json_path}", file=sys.stderr)
        sys.exit(1)

    devices = load_devices(json_path)
    dev = find_device(devices, args.name)
    if not dev:
        names = [d.get("name", "?") for d in devices]
        print(f"未找到设备「{args.name}」。当前有: {', '.join(names)}", file=sys.stderr)
        sys.exit(1)

    ip = dev.get("ip")
    token = dev.get("token")
    model = dev.get("model", "")
    if not ip or not token:
        print(f"设备 {args.name} 缺少 ip 或 token", file=sys.stderr)
        sys.exit(1)

    plug_on_off(ip, token, model, args.action == "on")


if __name__ == "__main__":
    main()
