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

# airproce 脚本路径（与 hzr_mcp.py 同目录下的 airproce/ensure_connect_and_select.py）
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AIRPROCE_SCRIPT = os.path.join(_SCRIPT_DIR, "airproce", "ensure_connect_and_select.py")

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


@mcp.tool()
def airproce_control(device_ip: str | None = None, port: str | None = None) -> dict:
    """当用户说「开启新风机」「关闭新风机」「启动新风机」「停止新风机」时调用此工具。
    通过 adb 执行 airproce 脚本：连接 Android 设备、启动 Airproce App、依次点击进入并触发新风机开关（开启/关闭为同一套点击流程）。
    device_ip: 可选，手机 IP，不传则使用环境变量 ADB_DEVICE_IP 或脚本默认；port: 可选，默认 5555。"""
    if not os.path.isfile(AIRPROCE_SCRIPT):
        return {"success": False, "message": f"未找到脚本: {AIRPROCE_SCRIPT}"}
    cmd = [sys.executable, AIRPROCE_SCRIPT]
    if (device_ip or "").strip():
        cmd.append((device_ip or "").strip())
        if (port or "").strip():
            cmd.append((port or "").strip())
    try:
        logger.info("airproce_control: running %s", cmd)
        out = subprocess.run(
            cmd,
            cwd=_SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        out_text = (out.stdout or "").strip()
        if (out.stderr or "").strip():
            out_text = out_text + "\n" + (out.stderr or "").strip()
        if not out_text:
            out_text = "脚本无输出，returncode=%s" % out.returncode

        logger.info("airproce_control: returncode=%s, output length=%s", out.returncode, len(out_text))
        if out.returncode != 0:
            logger.warning("airproce_control failed returncode=%s, first 500 chars: %s", out.returncode, out_text[:500])

        # 失败时在开头加一句简要说明，方便小智直接读出原因
        if out.returncode != 0:
            hint = {
                1: "adb connect 未成功（请检查手机同网、无线调试/授权）。",
                2: "启动 Airproce App 未成功（可能未安装或包名/Activity 不符）。",
            }.get(out.returncode, "脚本某步执行失败。")
            out_text = "[新风机控制失败] returncode=%s，可能原因：%s\n\n--- 脚本输出（步骤摘要）---\n%s" % (
                out.returncode, hint, out_text
            )

        return {
            "success": out.returncode == 0,
            "message": out_text,
            "returncode": out.returncode,
        }
    except subprocess.TimeoutExpired:
        logger.warning("airproce_control: timeout 120s")
        return {"success": False, "message": "[新风机控制失败] 执行超时（120s），请检查设备与网络。", "returncode": -1}
    except Exception as e:
        logger.exception("airproce_control failed")
        return {"success": False, "message": "[新风机控制失败] 异常: " + str(e), "returncode": -1}


if __name__ == "__main__":
    mcp.run(transport="stdio")
