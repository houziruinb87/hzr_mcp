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

# 脚本路径（与 hzr_mcp.py 同目录）
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AIRPROCE_SCRIPT = os.path.join(_SCRIPT_DIR, "airproce", "ensure_connect_and_select.py")
XIAOMI_WUGUIDENG_SCRIPT = os.path.join(_SCRIPT_DIR, "xiaomi", "wuguideng", "control.py")
XIAOMI_ZOULANGDENG_SCRIPT = os.path.join(_SCRIPT_DIR, "xiaomi", "zoulangdeng", "control.py")

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


# 新风机脚本后台执行时的日志文件（便于排查，不阻塞 MCP 响应）
AIRPROCE_LOG = os.path.join(_SCRIPT_DIR, "airproce_last_run.log")


@mcp.tool()
def airproce_control(device_ip: str | None = None, port: str | None = None) -> dict:
    """当用户说「开启新风机」「关闭新风机」「启动新风机」「停止新风机」时调用此工具。
    通过 adb 在后台执行 airproce 脚本（连接设备、启动 Airproce、点击开关）；为避免小智 MCP 接入点超时，本工具立即返回，脚本在服务器后台继续执行。
    device_ip: 可选，手机 IP，不传则使用环境变量 ADB_DEVICE_IP 或脚本默认；port: 可选，默认 5555。"""
    if not os.path.isfile(AIRPROCE_SCRIPT):
        return {"success": False, "message": f"未找到脚本: {AIRPROCE_SCRIPT}"}
    cmd = [sys.executable, AIRPROCE_SCRIPT]
    if (device_ip or "").strip():
        cmd.append((device_ip or "").strip())
        if (port or "").strip():
            cmd.append((port or "").strip())
    try:
        # 后台执行，不等待，避免小智云端等 MCP 响应时超时（脚本需几十秒）
        log_file = open(AIRPROCE_LOG, "w", encoding="utf-8")
        log_file.write("=== airproce_control 后台执行 %s\n\n" % " ".join(cmd))
        log_file.flush()
        proc = subprocess.Popen(
            cmd,
            cwd=_SCRIPT_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )
        log_file.close()
        logger.info("airproce_control: started background pid=%s, log=%s", proc.pid, AIRPROCE_LOG)
        return {
            "success": True,
            "message": "已提交新风机控制，正在后台执行，请稍候在手机上确认（连接、启动 Airproce、点击开关）。若需查看执行详情可到服务器查看日志：%s" % AIRPROCE_LOG,
            "returncode": None,
        }
    except Exception as e:
        logger.exception("airproce_control failed")
        return {"success": False, "message": "[新风机控制失败] 启动后台任务异常: " + str(e), "returncode": -1}


def _run_xiaomi_script(script_path: str, arg: str) -> dict:
    """执行 xiaomi 某设备控制脚本（如 xiaomi/wuguideng/control.py on）。"""
    if not os.path.isfile(script_path):
        return {"success": False, "message": f"未找到脚本: {script_path}"}
    try:
        out = subprocess.run(
            [sys.executable, script_path, arg],
            cwd=_SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=15,
        )
        stdout = (out.stdout or "").strip()
        stderr = (out.stderr or "").strip()
        ok = out.returncode == 0
        return {
            "success": ok,
            "message": stdout if ok else (stderr or f"退出码 {out.returncode}"),
            "returncode": out.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "执行超时", "returncode": -1}
    except Exception as e:
        logger.exception("xiaomi script failed")
        return {"success": False, "message": str(e), "returncode": -1}


@mcp.tool()
def wuguideng_on() -> dict:
    """当用户说「打开乌龟灯」「开启乌龟灯」时调用此工具，打开乌龟灯（米家插座/灯）。"""
    return _run_xiaomi_script(XIAOMI_WUGUIDENG_SCRIPT, "on")


@mcp.tool()
def wuguideng_off() -> dict:
    """当用户说「关闭乌龟灯」「停止乌龟灯」「取消乌龟灯」时调用此工具，关闭乌龟灯（米家插座/灯）。"""
    return _run_xiaomi_script(XIAOMI_WUGUIDENG_SCRIPT, "off")


@mcp.tool()
def zoulangdeng_on() -> dict:
    """当用户说「打开走廊灯」「开启走廊灯」时调用此工具，打开走廊灯（米家插座/灯）。"""
    return _run_xiaomi_script(XIAOMI_ZOULANGDENG_SCRIPT, "on")


@mcp.tool()
def zoulangdeng_off() -> dict:
    """当用户说「关闭走廊灯」「停止走廊灯」「取消走廊灯」时调用此工具，关闭走廊灯（米家插座/灯）。"""
    return _run_xiaomi_script(XIAOMI_ZOULANGDENG_SCRIPT, "off")


if __name__ == "__main__":
    mcp.run(transport="stdio")
