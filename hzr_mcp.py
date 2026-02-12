# hzr_mcp - MCP 服务，运行于极空间 office 容器，提供 adb 能力
from fastmcp import FastMCP
import sys
import logging
import os
import subprocess
import threading

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
XIAOMI_JIASHIQI_SCRIPT = os.path.join(_SCRIPT_DIR, "xiaomi", "jiashiqi", "control.py")

mcp = FastMCP("hzr")

# ---------- 延时任务管理 ----------
# 全局延时任务跟踪：{设备名: Timer对象}
_delayed_tasks = {}
_delayed_tasks_lock = threading.Lock()


def _cancel_device_delay(device_name: str) -> bool:
    """取消指定设备的延时任务。返回 True 如果有任务被取消，False 如果没有任务在运行。"""
    with _delayed_tasks_lock:
        if device_name in _delayed_tasks:
            timer = _delayed_tasks[device_name]
            timer.cancel()
            del _delayed_tasks[device_name]
            logger.info(f"已取消 {device_name} 的延时任务")
            return True
        return False


def _schedule_delayed_action(
    device_name: str, script_path: str, action: str, delay_seconds: float
) -> dict:
    """安排延时任务。如果该设备已有延时任务，会先取消旧任务。
    
    Args:
        device_name: 设备名称（如 "乌龟灯"）
        script_path: 控制脚本路径
        action: 动作（"on" 或 "off"）
        delay_seconds: 延时秒数
    
    Returns:
        {"success": True, "message": "...", "delay_seconds": ...}
    """
    # 先取消旧任务
    had_old_task = _cancel_device_delay(device_name)
    
    # 创建新任务
    def execute():
        try:
            logger.info(f"{device_name} 延时到期，执行 {action}")
            result = _run_xiaomi_script(script_path, action)
            if result.get("success"):
                logger.info(f"{device_name} {action} 成功")
            else:
                logger.error(f"{device_name} {action} 失败: {result.get('message')}")
        except Exception as e:
            logger.exception(f"{device_name} 延时任务执行异常")
        finally:
            # 任务完成后清理
            with _delayed_tasks_lock:
                if device_name in _delayed_tasks:
                    del _delayed_tasks[device_name]
    
    timer = threading.Timer(delay_seconds, execute)
    
    with _delayed_tasks_lock:
        _delayed_tasks[device_name] = timer
    
    timer.start()
    
    action_cn = "开启" if action == "on" else "关闭"
    msg = f"已设置 {device_name} 延时 {delay_seconds:.0f} 秒后{action_cn}"
    if had_old_task:
        msg += "（已覆盖之前的延时任务）"
    
    logger.info(msg)
    return {
        "success": True,
        "message": msg,
        "delay_seconds": delay_seconds,
        "action": action_cn,
    }


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
    """当用户说「打开乌龟灯」「开启乌龟灯」时调用此工具，立即打开乌龟灯（米家插座/灯）。"""
    return _run_xiaomi_script(XIAOMI_WUGUIDENG_SCRIPT, "on")


@mcp.tool()
def wuguideng_off() -> dict:
    """当用户说「关闭乌龟灯」「停止乌龟灯」时调用此工具，立即关闭乌龟灯（米家插座/灯）。
    注意：如果用户说「取消乌龟灯」且上下文是取消延时任务，应调用 wuguideng_cancel_delay。"""
    return _run_xiaomi_script(XIAOMI_WUGUIDENG_SCRIPT, "off")


@mcp.tool()
def wuguideng_delayed_on(delay: float, unit: str = "minutes") -> dict:
    """延时开启乌龟灯。当用户说「延时XX分钟后开启乌龟灯」「XX秒后打开乌龟灯」「XX小时后开乌龟灯」「等XX分钟后开启乌龟灯」时调用。
    如果已有延时任务在运行，新任务会自动覆盖旧任务。
    
    Args:
        delay: 延时时长（数字，如 5、30、1.5）
        unit: 时间单位，可选 "seconds"（秒）、"minutes"（分钟）、"hours"（小时），默认分钟
    
    Examples:
        - 用户说「30秒后开启乌龟灯」→ delay=30, unit="seconds"
        - 用户说「5分钟后打开乌龟灯」→ delay=5, unit="minutes"
        - 用户说「1小时后开乌龟灯」→ delay=1, unit="hours"
    """
    # 转换为秒
    unit_map = {"seconds": 1, "minutes": 60, "hours": 3600}
    multiplier = unit_map.get(unit.lower(), 60)  # 默认分钟
    delay_seconds = delay * multiplier
    
    if delay_seconds <= 0:
        return {"success": False, "message": "延时时长必须大于 0"}
    
    return _schedule_delayed_action("乌龟灯", XIAOMI_WUGUIDENG_SCRIPT, "on", delay_seconds)


@mcp.tool()
def wuguideng_delayed_off(delay: float, unit: str = "minutes") -> dict:
    """延时关闭乌龟灯。当用户说「延时XX分钟后关闭乌龟灯」「XX秒后关乌龟灯」「XX小时后关闭乌龟灯」「等XX分钟后关闭乌龟灯」时调用。
    如果已有延时任务在运行，新任务会自动覆盖旧任务。
    
    Args:
        delay: 延时时长（数字，如 5、30、1.5）
        unit: 时间单位，可选 "seconds"（秒）、"minutes"（分钟）、"hours"（小时），默认分钟
    
    Examples:
        - 用户说「30秒后关闭乌龟灯」→ delay=30, unit="seconds"
        - 用户说「5分钟后关乌龟灯」→ delay=5, unit="minutes"
        - 用户说「1小时后关闭乌龟灯」→ delay=1, unit="hours"
    """
    # 转换为秒
    unit_map = {"seconds": 1, "minutes": 60, "hours": 3600}
    multiplier = unit_map.get(unit.lower(), 60)  # 默认分钟
    delay_seconds = delay * multiplier
    
    if delay_seconds <= 0:
        return {"success": False, "message": "延时时长必须大于 0"}
    
    return _schedule_delayed_action("乌龟灯", XIAOMI_WUGUIDENG_SCRIPT, "off", delay_seconds)


@mcp.tool()
def wuguideng_cancel_delay() -> dict:
    """取消乌龟灯的所有延时任务。当用户说「取消乌龟灯计时」「取消乌龟灯延时」「取消倒计时乌龟灯」时调用。"""
    if _cancel_device_delay("乌龟灯"):
        return {"success": True, "message": "已取消乌龟灯的延时任务"}
    else:
        return {"success": True, "message": "乌龟灯当前没有延时任务"}


@mcp.tool()
def zoulangdeng_on() -> dict:
    """当用户说「打开走廊灯」「开启走廊灯」时调用此工具，立即打开走廊灯（米家插座/灯）。"""
    return _run_xiaomi_script(XIAOMI_ZOULANGDENG_SCRIPT, "on")


@mcp.tool()
def zoulangdeng_off() -> dict:
    """当用户说「关闭走廊灯」「停止走廊灯」时调用此工具，立即关闭走廊灯（米家插座/灯）。
    注意：如果用户说「取消走廊灯」且上下文是取消延时任务，应调用 zoulangdeng_cancel_delay。"""
    return _run_xiaomi_script(XIAOMI_ZOULANGDENG_SCRIPT, "off")


@mcp.tool()
def zoulangdeng_delayed_on(delay: float, unit: str = "minutes") -> dict:
    """延时开启走廊灯。当用户说「延时XX分钟后开启走廊灯」「XX秒后打开走廊灯」「XX小时后开走廊灯」「等XX分钟后开启走廊灯」时调用。
    如果已有延时任务在运行，新任务会自动覆盖旧任务。
    
    Args:
        delay: 延时时长（数字，如 5、30、1.5）
        unit: 时间单位，可选 "seconds"（秒）、"minutes"（分钟）、"hours"（小时），默认分钟
    """
    unit_map = {"seconds": 1, "minutes": 60, "hours": 3600}
    multiplier = unit_map.get(unit.lower(), 60)
    delay_seconds = delay * multiplier
    
    if delay_seconds <= 0:
        return {"success": False, "message": "延时时长必须大于 0"}
    
    return _schedule_delayed_action("走廊灯", XIAOMI_ZOULANGDENG_SCRIPT, "on", delay_seconds)


@mcp.tool()
def zoulangdeng_delayed_off(delay: float, unit: str = "minutes") -> dict:
    """延时关闭走廊灯。当用户说「延时XX分钟后关闭走廊灯」「XX秒后关走廊灯」「XX小时后关闭走廊灯」「等XX分钟后关闭走廊灯」时调用。
    如果已有延时任务在运行，新任务会自动覆盖旧任务。
    
    Args:
        delay: 延时时长（数字，如 5、30、1.5）
        unit: 时间单位，可选 "seconds"（秒）、"minutes"（分钟）、"hours"（小时），默认分钟
    """
    unit_map = {"seconds": 1, "minutes": 60, "hours": 3600}
    multiplier = unit_map.get(unit.lower(), 60)
    delay_seconds = delay * multiplier
    
    if delay_seconds <= 0:
        return {"success": False, "message": "延时时长必须大于 0"}
    
    return _schedule_delayed_action("走廊灯", XIAOMI_ZOULANGDENG_SCRIPT, "off", delay_seconds)


@mcp.tool()
def zoulangdeng_cancel_delay() -> dict:
    """取消走廊灯的所有延时任务。当用户说「取消走廊灯计时」「取消走廊灯延时」「取消倒计时走廊灯」时调用。"""
    if _cancel_device_delay("走廊灯"):
        return {"success": True, "message": "已取消走廊灯的延时任务"}
    else:
        return {"success": True, "message": "走廊灯当前没有延时任务"}


@mcp.tool()
def jiashiqi_on() -> dict:
    """当用户说「打开加湿器」「开启加湿器」时调用此工具，立即打开 YO 加湿器。"""
    return _run_xiaomi_script(XIAOMI_JIASHIQI_SCRIPT, "on")


@mcp.tool()
def jiashiqi_off() -> dict:
    """当用户说「关闭加湿器」「停止加湿器」时调用此工具，立即关闭 YO 加湿器。
    注意：如果用户说「取消加湿器」且上下文是取消延时任务，应调用 jiashiqi_cancel_delay。"""
    return _run_xiaomi_script(XIAOMI_JIASHIQI_SCRIPT, "off")


@mcp.tool()
def jiashiqi_delayed_on(delay: float, unit: str = "minutes") -> dict:
    """延时开启加湿器。当用户说「延时XX分钟后开启加湿器」「XX秒后打开加湿器」「XX小时后开加湿器」「等XX分钟后开启加湿器」时调用。
    如果已有延时任务在运行，新任务会自动覆盖旧任务。
    
    Args:
        delay: 延时时长（数字，如 5、30、1.5）
        unit: 时间单位，可选 "seconds"（秒）、"minutes"（分钟）、"hours"（小时），默认分钟
    """
    unit_map = {"seconds": 1, "minutes": 60, "hours": 3600}
    multiplier = unit_map.get(unit.lower(), 60)
    delay_seconds = delay * multiplier
    
    if delay_seconds <= 0:
        return {"success": False, "message": "延时时长必须大于 0"}
    
    return _schedule_delayed_action("加湿器", XIAOMI_JIASHIQI_SCRIPT, "on", delay_seconds)


@mcp.tool()
def jiashiqi_delayed_off(delay: float, unit: str = "minutes") -> dict:
    """延时关闭加湿器。当用户说「延时XX分钟后关闭加湿器」「XX秒后关加湿器」「XX小时后关闭加湿器」「等XX分钟后关闭加湿器」时调用。
    如果已有延时任务在运行，新任务会自动覆盖旧任务。
    
    Args:
        delay: 延时时长（数字，如 5、30、1.5）
        unit: 时间单位，可选 "seconds"（秒）、"minutes"（分钟）、"hours"（小时），默认分钟
    """
    unit_map = {"seconds": 1, "minutes": 60, "hours": 3600}
    multiplier = unit_map.get(unit.lower(), 60)
    delay_seconds = delay * multiplier
    
    if delay_seconds <= 0:
        return {"success": False, "message": "延时时长必须大于 0"}
    
    return _schedule_delayed_action("加湿器", XIAOMI_JIASHIQI_SCRIPT, "off", delay_seconds)


@mcp.tool()
def jiashiqi_cancel_delay() -> dict:
    """取消加湿器的所有延时任务。当用户说「取消加湿器计时」「取消加湿器延时」「取消倒计时加湿器」时调用。"""
    if _cancel_device_delay("加湿器"):
        return {"success": True, "message": "已取消加湿器的延时任务"}
    else:
        return {"success": True, "message": "加湿器当前没有延时任务"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
