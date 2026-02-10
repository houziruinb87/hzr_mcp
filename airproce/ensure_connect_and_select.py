#!/usr/bin/env python3
"""
通过 adb 连接 Android 设备并执行：connect → 校验状态 → 启动 Airproce → 五次 tap（选设备+开关）→ 启动飞鼠 App。
每步执行完后等待 ADB_WAIT_SEC 秒再执行下一步（避免设备未就绪）。不主动 disconnect，保留已有连接。
"""
import os
import subprocess
import sys
import time

# 每步 adb 执行后的等待时间（秒）
ADB_WAIT_SEC = 1
# 前四次 tap 之间的间隔（秒）
TAP_INTERVAL_SEC = 1.5
# 第四次与第五次 tap 之间的额外等待（秒）
TAP_BEFORE_LAST_WAIT_SEC = 3
# adb connect 单独超时（秒），避免手机不可达时长时间卡住
CONNECT_TIMEOUT_SEC = 15

ADB_CMD = os.environ.get("ADB_PATH", "adb")
DEFAULT_IP = os.environ.get("ADB_DEVICE_IP", "10.5.234.21")
DEFAULT_PORT = os.environ.get("ADB_DEVICE_PORT", "5555")

# 以下包名/Activity 按实际设备修改
MYAIRPROCE_PACKAGE = "com.airproce.airapp"
MYAIRPROCE_ACTIVITY = ".MainActivity"
FEISHU_PACKAGE = "com.example.feishunet"
FEISHU_ACTIVITY = ".MainActivity"

# 五次点击：(x, y, 说明)
TAP_STEPS = [
    (104, 2158, "底部 home"),
    (70, 225, "开启左侧边栏"),
    (364, 514, "选中360新风机"),
    (323, 2132, "底部tab第二个调节按钮"),
    (549, 1860, "开启/关闭新风机"),
]


def run(cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """执行命令，返回 subprocess 结果。"""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def step(desc: str, cmd: list[str], timeout: int | None = None) -> bool:
    """执行一步并打印结果，失败或超时时打印信息。返回是否成功。"""
    print(f"  → {desc} ... ", end="", flush=True)
    try:
        r = run(cmd, timeout=timeout if timeout is not None else 30)
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        if "connect" in desc.lower():
            print("      connect 超时，请检查：手机与电脑同网、无线调试/网络 ADB 已开，或先用 USB 执行 adb tcpip 5555")
        return False
    ok = r.returncode == 0
    print("OK" if ok else "FAIL")
    if not ok and (r.stderr or r.stdout):
        out = (r.stderr or "").strip() or (r.stdout or "").strip()
        if out:
            print(f"      {out[:200]}")
    return ok


def main() -> int:
    ip = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IP
    port = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PORT
    device = f"{ip}:{port}"
    print(f"设备: {device}\n")

    # 1. connect（不先 disconnect，单独超时避免手机不可达时卡住）
    if not step("connect", [ADB_CMD, "connect", device], timeout=CONNECT_TIMEOUT_SEC):
        return 1
    time.sleep(ADB_WAIT_SEC)

    # 2. get-state、getprop
    step("get-state", [ADB_CMD, "-s", device, "get-state"])
    time.sleep(ADB_WAIT_SEC)
    step("getprop", [ADB_CMD, "-s", device, "shell", "getprop", "sys.boot_completed"])
    time.sleep(ADB_WAIT_SEC)

    # 3. 启动 Airproce App（用 -n 指定 MainActivity，LAUNCHER intent 在该机上无法 resolve）
    step("启动 Airproce", [
        ADB_CMD, "-s", device, "shell", "am", "start", "-n",
        f"{MYAIRPROCE_PACKAGE}/{MYAIRPROCE_ACTIVITY}",
    ])
    time.sleep(3)  # 给 Airproce 界面时间显示，再执行后面的 tap

    # 4. 五次 tap：前四次每次间隔 1.5s；第 4 次与第 5 次之间单独等 2s
    for i, (x, y, desc) in enumerate(TAP_STEPS, 1):
        step(f"tap {i}/5 ({x},{y}) {desc}", [ADB_CMD, "-s", device, "shell", "input", "tap", str(x), str(y)])
        if i == 4:
            time.sleep(TAP_BEFORE_LAST_WAIT_SEC)  # 第 4 次点完，等 2s 再点第 5 次
        elif i < 4:
            time.sleep(TAP_INTERVAL_SEC)

    time.sleep(2)  # 五次点击完成后等 2s 再启动飞鼠

    # 5. 启动飞鼠 App
    step("启动飞鼠", [
        ADB_CMD, "-s", device, "shell", "am", "start", "-n",
        f"{FEISHU_PACKAGE}/{FEISHU_ACTIVITY}",
    ])
    time.sleep(ADB_WAIT_SEC)

    print("\n完成.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
