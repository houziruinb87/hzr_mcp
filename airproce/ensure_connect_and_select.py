#!/usr/bin/env python3
"""
通过 adb 连接 Android 设备并执行：connect → 校验状态 → 启动 Airproce → 五次 tap（选设备+开关）→ 启动飞鼠 App。
每步执行完后等待 ADB_WAIT_SEC 秒再执行下一步（避免设备未就绪）。不主动 disconnect，保留已有连接。
每步结果会记录并输出，便于小智/MCP 回传排查；关键步骤失败会立即退出并返回非 0。
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
# 启动 Airproce 后等待界面出现的时长（秒），可设环境变量 AIRPROCE_LAUNCH_WAIT_SEC 调大
AIRPROCE_LAUNCH_WAIT_SEC = int(os.environ.get("AIRPROCE_LAUNCH_WAIT_SEC", "5"))
# adb connect 单独超时（秒），避免手机不可达时长时间卡住
CONNECT_TIMEOUT_SEC = 15

# 步骤执行记录 [(步骤名, 是否成功, 详情)]，用于最后输出摘要并回传给调用方
STEP_LOG: list[tuple[str, bool, str]] = []

ADB_CMD = os.environ.get("ADB_PATH", "adb")
DEFAULT_IP = os.environ.get("ADB_DEVICE_IP", "192.168.1.100")
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
    """执行一步并打印结果，记录到 STEP_LOG；失败或超时时打印详情。返回是否成功。"""
    global STEP_LOG
    print(f"  → {desc} ... ", end="", flush=True)
    detail = ""
    try:
        r = run(cmd, timeout=timeout if timeout is not None else 30)
    except subprocess.TimeoutExpired as e:
        print("TIMEOUT")
        detail = "执行超时"
        if "connect" in desc.lower():
            detail = "connect 超时，请检查：手机与电脑同网、无线调试/网络 ADB 已开，或先用 USB 执行 adb tcpip 5555"
            print(f"      {detail}")
        STEP_LOG.append((desc, False, detail))
        return False
    ok = r.returncode == 0
    if not ok:
        out = (r.stderr or "").strip() or (r.stdout or "").strip()
        detail = (out[:300] if out else f"returncode={r.returncode}")
        print("FAIL")
        if out:
            print(f"      {out[:200]}")
    else:
        print("OK")
    STEP_LOG.append((desc, ok, detail))
    return ok


def _print_step_summary() -> None:
    """输出步骤摘要到 stdout，便于 MCP 回传给小智。"""
    print("\n--- 步骤摘要 ---")
    for name, ok, detail in STEP_LOG:
        status = "OK" if ok else "FAIL"
        print(f"  {name}: {status}" + (f" | {detail[:150]}" if detail else ""))


def main() -> int:
    global STEP_LOG
    STEP_LOG = []

    ip = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IP
    port = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PORT
    device = f"{ip}:{port}"
    print(f"设备: {device}\n")

    # 1. connect（不先 disconnect，单独超时避免手机不可达时卡住）
    if not step("connect", [ADB_CMD, "connect", device], timeout=CONNECT_TIMEOUT_SEC):
        _print_step_summary()
        print("\n[失败] connect 未成功，已中止。")
        return 1
    time.sleep(ADB_WAIT_SEC)

    # 2. get-state、getprop
    step("get-state", [ADB_CMD, "-s", device, "get-state"])
    time.sleep(ADB_WAIT_SEC)
    step("getprop", [ADB_CMD, "-s", device, "shell", "getprop", "sys.boot_completed"])
    time.sleep(ADB_WAIT_SEC)

    # 3. 启动 Airproce App（用 -n 指定 MainActivity）
    if not step("启动 Airproce", [
        ADB_CMD, "-s", device, "shell", "am", "start", "-n",
        f"{MYAIRPROCE_PACKAGE}/{MYAIRPROCE_ACTIVITY}",
    ]):
        _print_step_summary()
        print("\n[失败] 启动 Airproce 未成功（可能未安装或包名/Activity 不符），已中止。")
        return 2
    time.sleep(AIRPROCE_LAUNCH_WAIT_SEC)  # 给 Airproce 界面时间显示（可设环境变量 AIRPROCE_LAUNCH_WAIT_SEC 调大）

    # 4. 五次 tap：前四次每次间隔 1.5s；第 4 次与第 5 次之间单独等 2s
    for i, (x, y, desc) in enumerate(TAP_STEPS, 1):
        step(f"tap {i}/5 ({x},{y}) {desc}", [ADB_CMD, "-s", device, "shell", "input", "tap", str(x), str(y)])
        if i == 4:
            time.sleep(TAP_BEFORE_LAST_WAIT_SEC)
        elif i < 4:
            time.sleep(TAP_INTERVAL_SEC)

    time.sleep(2)

    # 5. 启动飞鼠 App
    step("启动飞鼠", [
        ADB_CMD, "-s", device, "shell", "am", "start", "-n",
        f"{FEISHU_PACKAGE}/{FEISHU_ACTIVITY}",
    ])
    time.sleep(ADB_WAIT_SEC)

    _print_step_summary()
    print("\n完成.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
