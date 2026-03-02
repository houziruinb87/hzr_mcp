#!/usr/bin/env python3
"""HTTP 桥接服务：供 Home Assistant 的 rest_command 调用，内部通过 docker exec 执行 hzr_mcp 脚本。

部署在 NAS 宿主机或能执行 docker 的环境，Home Assistant 通过 http://NAS_IP:8765/... 调用。

用法:
  python bridge_server.py
  默认监听 0.0.0.0:8765

环境变量:
  HZR_MCP_CONTAINER  容器名，默认 hzr_mcp
  HZR_MCP_APP_PATH   容器内 /app 路径，默认 /app
  BRIDGE_PORT         端口，默认 8765
"""
from __future__ import annotations

import os
import subprocess
import sys

try:
    from flask import Flask, jsonify, request
except ImportError:
    print("请安装: pip install flask", file=sys.stderr)
    sys.exit(1)

app = Flask(__name__)

CONTAINER = os.environ.get("HZR_MCP_CONTAINER", "hzr_mcp")
APP_PATH = os.environ.get("HZR_MCP_APP_PATH", "/app")
SCRIPT = "python"


def run_script(rel_path: str, *args: str) -> tuple[bool, str]:
    """在容器内执行 python 脚本。rel_path 为相对 /app 的路径，如 xiaomi/jiashiqi/control.py"""
    cmd = ["docker", "exec", CONTAINER, SCRIPT, f"{APP_PATH}/{rel_path}"] + list(args)
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return out.returncode == 0, (out.stdout or out.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return False, "执行超时"
    except Exception as e:
        return False, str(e)


def run_script_background(rel_path: str, *args: str) -> tuple[bool, str]:
    """在容器内后台执行 python 脚本，不等待完成，立即返回。用于耗时的 airproce 等脚本。"""
    cmd = ["docker", "exec", "-d", CONTAINER, SCRIPT, f"{APP_PATH}/{rel_path}"] + list(args)
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # 不 wait，立即返回；docker exec -d 会在容器内后台跑
        return True, "已提交，正在后台执行"
    except Exception as e:
        return False, str(e)


# ---------- 加湿器 ----------
@app.route("/jiashiqi/on", methods=["POST", "GET"])
def jiashiqi_on():
    ok, msg = run_script("xiaomi/jiashiqi/control.py", "on")
    return jsonify({"success": ok, "message": msg}), 200 if ok else 500


@app.route("/jiashiqi/off", methods=["POST", "GET"])
def jiashiqi_off():
    ok, msg = run_script("xiaomi/jiashiqi/control.py", "off")
    return jsonify({"success": ok, "message": msg}), 200 if ok else 500


# ---------- 乌龟灯 ----------
@app.route("/wuguideng/on", methods=["POST", "GET"])
def wuguideng_on():
    ok, msg = run_script("xiaomi/wuguideng/control.py", "on")
    return jsonify({"success": ok, "message": msg}), 200 if ok else 500


@app.route("/wuguideng/off", methods=["POST", "GET"])
def wuguideng_off():
    ok, msg = run_script("xiaomi/wuguideng/control.py", "off")
    return jsonify({"success": ok, "message": msg}), 200 if ok else 500


# ---------- 走廊灯 ----------
@app.route("/zoulangdeng/on", methods=["POST", "GET"])
def zoulangdeng_on():
    ok, msg = run_script("xiaomi/zoulangdeng/control.py", "on")
    return jsonify({"success": ok, "message": msg}), 200 if ok else 500


@app.route("/zoulangdeng/off", methods=["POST", "GET"])
def zoulangdeng_off():
    ok, msg = run_script("xiaomi/zoulangdeng/control.py", "off")
    return jsonify({"success": ok, "message": msg}), 200 if ok else 500


# ---------- 新风机（airproce：通过 adb 操作手机 App 点击开关，脚本较耗时，后台执行）----------
# 注意：ensure_connect_and_select.py 为「点击一次开关」即切换状态，on/off 都触发同一脚本
@app.route("/xinfengji/on", methods=["POST", "GET"])
def xinfengji_on():
    ok, msg = run_script_background("airproce/ensure_connect_and_select.py")
    return jsonify({"success": ok, "message": msg}), 200 if ok else 500


@app.route("/xinfengji/off", methods=["POST", "GET"])
def xinfengji_off():
    ok, msg = run_script_background("airproce/ensure_connect_and_select.py")
    return jsonify({"success": ok, "message": msg}), 200 if ok else 500


@app.route("/xinfengji/toggle", methods=["POST", "GET"])
def xinfengji_toggle():
    ok, msg = run_script_background("airproce/ensure_connect_and_select.py")
    return jsonify({"success": ok, "message": msg}), 200 if ok else 500


# ---------- 全屋灯 ----------
@app.route("/quanwudeng/on", methods=["POST", "GET"])
def quanwudeng_on():
    ok, msg = run_script("xiaomi/quanwudeng/control.py", "on")
    return jsonify({"success": ok, "message": msg}), 200 if ok else 500


@app.route("/quanwudeng/off", methods=["POST", "GET"])
def quanwudeng_off():
    ok, msg = run_script("xiaomi/quanwudeng/control.py", "off")
    return jsonify({"success": ok, "message": msg}), 200 if ok else 500


# ---------- 健康检查 ----------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


def main():
    port = int(os.environ.get("BRIDGE_PORT", "8765"))
    host = os.environ.get("BRIDGE_HOST", "0.0.0.0")
    print(f"桥接服务: http://{host}:{port}", file=sys.stderr)
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
