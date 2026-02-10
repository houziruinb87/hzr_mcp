# hzr_mcp - MCP 服务，运行于极空间 office 容器，提供 adb 能力
from fastmcp import FastMCP
import sys
import logging
import os
import subprocess

logger = logging.getLogger("hzr_mcp")

if sys.platform == "win32":
    sys.stderr.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

# ---------- ADB 配置（极空间 office 容器内已配置 ANDROID_HOME / PATH）----------
ADB_CMD = os.environ.get("ADB_PATH", "adb")
ANDROID_ADB_PORT = os.environ.get("ANDROID_ADB_PORT", "5555")

mcp = FastMCP("hzr")


@mcp.tool()
def adb_devices() -> dict:
    """列出当前 adb 已连接设备。运行于极空间 office 容器时，可看到通过 adb connect 连上的手机。"""
    try:
        out = subprocess.run(
            [ADB_CMD, "devices"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        lines = (out.stdout or "").strip().splitlines()
        devices = []
        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith("*"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                devices.append({"serial": parts[0], "state": parts[1]})
        return {"success": True, "devices": devices, "raw": out.stdout}
    except FileNotFoundError:
        return {"success": False, "message": "未找到 adb，请设置 ADB_PATH 或确保 PATH 中有 adb"}
    except Exception as e:
        logger.exception("adb devices failed")
        return {"success": False, "message": str(e)}


@mcp.tool()
def adb_connect(device_ip: str, port: str = ANDROID_ADB_PORT) -> dict:
    """通过 WiFi 连接 Android 设备。device_ip: 手机 IP（如飞鼠虚拟网 IP）；port 默认 5555。"""
    device_ip = (device_ip or "").strip()
    if not device_ip:
        return {"success": False, "message": "请提供设备 IP"}
    device = f"{device_ip}:{port}"
    try:
        out = subprocess.run(
            [ADB_CMD, "connect", device],
            capture_output=True,
            text=True,
            timeout=15,
        )
        out_text = (out.stdout or "").strip() + "\n" + (out.stderr or "").strip()
        return {
            "success": out.returncode == 0,
            "message": out_text or ("已发起连接 " + device),
            "device": device,
        }
    except FileNotFoundError:
        return {"success": False, "message": "未找到 adb", "device": device}
    except Exception as e:
        logger.exception("adb connect failed")
        return {"success": False, "message": str(e), "device": device}


if __name__ == "__main__":
    mcp.run(transport="stdio")
