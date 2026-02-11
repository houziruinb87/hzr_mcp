#!/usr/bin/env python3
"""从小米云拉取账号下所有设备及 token（命令行）。

用法:
  # 交互输入账号密码
  python xiaomi/list_devices_from_cloud.py

  # 环境变量（密码建议交互输入，不要写进 shell 历史）
  export MI_USER=你的小米账号
  export MI_PASS=你的密码
  python xiaomi/list_devices_from_cloud.py

  # 仅输出 token 与 IP，便于脚本消费
  python xiaomi/list_devices_from_cloud.py --simple
"""
from __future__ import annotations

import argparse
import os
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="从小米云获取账号下所有设备及 token")
    parser.add_argument(
        "--simple",
        action="store_true",
        help="仅输出: name model ip token（制表符分隔）",
    )
    parser.add_argument(
        "--locale",
        default=None,
        help="云区域，如 cn、de、i2、ru、sg、us；不传则查所有区域",
    )
    args = parser.parse_args()

    try:
        from miio.cloud import CloudInterface
    except ImportError:
        print("请先安装: pip install python-miio", file=sys.stderr)
        sys.exit(1)

    username = os.environ.get("MI_USER") or input("小米账号（手机/邮箱）: ").strip()
    password = os.environ.get("MI_PASS")
    if not password:
        import getpass
        password = getpass.getpass("密码: ")

    if not username or not password:
        print("需要账号和密码", file=sys.stderr)
        sys.exit(1)

    try:
        ci = CloudInterface(username=username, password=password)
        devices = ci.get_devices(locale=args.locale)
    except Exception as e:
        print(f"拉取设备列表失败: {e}", file=sys.stderr)
        sys.exit(1)

    if not devices:
        print("未获取到设备")
        return

    if args.simple:
        for did, dev in devices.items():
            ip = getattr(dev, "localip", None) or getattr(dev, "ip", None) or ""
            print(f"{dev.name}\t{dev.model}\t{ip}\t{dev.token or ''}")
        return

    for did, dev in devices.items():
        ip = getattr(dev, "localip", None) or getattr(dev, "ip", None) or "(无)"
        print(f"--- {dev.name} (did={did}) ---")
        print(f"  model: {dev.model}")
        print(f"  ip:    {ip}")
        print(f"  token: {dev.token or '(无)'}")
        print(f"  online: {getattr(dev, 'is_online', '?')}")
        print()


if __name__ == "__main__":
    main()
