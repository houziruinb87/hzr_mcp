# hzr_mcp - MCP 服务，运行于极空间 office 容器，提供计算与 adb 能力
from fastmcp import FastMCP
import sys
import logging
import os
import subprocess
import time
import glob
import json

logger = logging.getLogger("hzr_mcp")

if sys.platform == "win32":
    sys.stderr.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

import math
import random

# ---------- ADB 配置（极空间 office 容器内已配置 ANDROID_HOME / PATH）----------
ADB_CMD = os.environ.get("ADB_PATH", "adb")
ANDROID_ADB_PORT = os.environ.get("ANDROID_ADB_PORT", "5555")
ANDROID_APK_STORE_PATH = os.environ.get(
    "ANDROID_APK_STORE_PATH",
    "/workspace/tools/android-sdk/store",
)
ANDROID_CONNECT_WAIT_SEC = int(os.environ.get("ANDROID_CONNECT_WAIT_SEC", "8"))

_NAME_TO_IP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "name_to_ip.json")
NAME_TO_IP = {}
if os.path.isfile(_NAME_TO_IP_FILE):
    try:
        with open(_NAME_TO_IP_FILE, "r", encoding="utf-8") as f:
            NAME_TO_IP = json.load(f)
    except Exception as e:
        logger.warning("name_to_ip.json 加载失败: %s", e)
if not NAME_TO_IP:
    NAME_TO_IP = {}

_env_map = os.environ.get("ANDROID_NAME_TO_IP")
if _env_map:
    try:
        NAME_TO_IP.update(json.loads(_env_map))
    except Exception:
        pass

mcp = FastMCP("hzr")


@mcp.tool()
def calculator(python_expression: str) -> dict:
    """用 Python 表达式做数学计算，可直接使用 math、random，无需 import。"""
    result = eval(python_expression, {"math": math, "random": random})
    logger.info("calculator: %s => %s", python_expression, result)
    return {"success": True, "result": result}


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


def _find_largest_numeric_folder(store_path: str) -> str | None:
    if not os.path.isdir(store_path):
        return None
    nums = []
    for name in os.listdir(store_path):
        subdir = os.path.join(store_path, name)
        if os.path.isdir(subdir) and name.isdigit():
            nums.append(int(name))
    return str(max(nums)) if nums else None


def _find_apk_in_folder(folder: str) -> str | None:
    for f in glob.glob(os.path.join(folder, "*.apk")):
        return f
    return None


@mcp.tool()
def install_android_apk(person_name: str, build_number: str = "") -> dict:
    """按人名给对应手机安装 Android APK。person_name 从 name_to_ip.json 解析为 IP；build_number 为 store 下构建号文件夹，不传则用数字最大的。需先能 adb connect 到该手机。"""
    person_name = (person_name or "").strip()
    build_number = (build_number or "").strip()
    if not person_name:
        return {"success": False, "message": "未指定安装对象（人名）"}

    ip = NAME_TO_IP.get(person_name)
    if not ip:
        return {"success": False, "message": f"未找到「{person_name}」对应的 IP，请检查 name_to_ip.json"}

    store_path = ANDROID_APK_STORE_PATH
    if not os.path.isdir(store_path):
        return {"success": False, "message": f"store 目录不存在: {store_path}"}

    if build_number:
        folder = os.path.join(store_path, build_number)
        if not os.path.isdir(folder):
            return {"success": False, "message": f"未找到构建号文件夹: {build_number}"}
        folder_name = build_number
    else:
        folder_name = _find_largest_numeric_folder(store_path)
        if not folder_name:
            return {"success": False, "message": "store 下没有数字命名的构建文件夹"}
        folder = os.path.join(store_path, folder_name)

    apk_path = _find_apk_in_folder(folder)
    if not apk_path:
        return {"success": False, "message": f"文件夹 {folder_name} 下没有 APK", "build_folder": folder_name}

    device = f"{ip}:{ANDROID_ADB_PORT}"
    logger.info("install_android_apk: person=%s, folder=%s, device=%s", person_name, folder_name, device)

    try:
        subprocess.run([ADB_CMD, "connect", device], capture_output=True, text=True, timeout=5)
        time.sleep(ANDROID_CONNECT_WAIT_SEC)

        out = subprocess.run(
            [ADB_CMD, "-s", device, "install", "-r", apk_path],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if out.returncode == 0:
            return {
                "success": True,
                "message": f"已安装到 {person_name}（{device}）",
                "build_folder": folder_name,
                "person_name": person_name,
                "device": device,
            }
        return {
            "success": False,
            "message": (out.stderr or out.stdout or "install failed").strip(),
            "build_folder": folder_name,
            "device": device,
        }
    except FileNotFoundError:
        return {"success": False, "message": "未找到 adb，请设置 ADB_PATH", "build_folder": folder_name}
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "安装超时", "build_folder": folder_name, "device": device}
    except Exception as e:
        logger.exception("install_android_apk failed")
        return {"success": False, "message": str(e), "build_folder": folder_name}


if __name__ == "__main__":
    mcp.run(transport="stdio")
