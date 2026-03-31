# utils.py - from pu-007/oxa-server, with bridge_call added for NAS bridge_server
from oxa_ext.type_defines import SpeakerProtocol, Actions, ActionFunction
from typing import Any, Literal, Optional
import os
import subprocess
import asyncio


def map_all_to(keys: tuple[str, ...], value: Actions) -> dict[str, Actions]:
    return {key: value for key in keys}


def ensure_dependencies(requirements: list[str]):
    import importlib.util
    missing_packages = [pkg for pkg in requirements if not importlib.util.find_spec(pkg)]
    if not missing_packages:
        return
    print(f"检测到缺失的依赖: {missing_packages}，正在尝试安装...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    python_executable = os.path.join(script_dir, ".venv", "bin", "python")
    if not os.path.exists(python_executable):
        import sys
        python_executable = sys.executable
    subprocess.run([python_executable, "-m", "ensurepip"], check=False)
    subprocess.run([python_executable, "-m", "pip", "install", *missing_packages], check=True)
    print("依赖安装完成。")


def map_the_switches(*devices: str, type: Literal["on", "off", "all"] = "all") -> dict:
    command_dict = {}
    for device in devices:
        if type == "on" or type == "all":
            command_dict[f"请开{device}"] = [f"打开{device}"]
        if type == "off" or type == "all":
            command_dict[f"请关{device}"] = [f"关闭{device}"]
    return command_dict


def switch_cmds(*devices: str, type: Literal["on", "off", "all"] = "all") -> list:
    commands = []
    for device in devices:
        if type == "on" or type == "all":
            commands.append(f"打开{device}")
        if type == "off" or type == "all":
            commands.append(f"关闭{device}")
    return commands


def off(*devices: str) -> list:
    return switch_cmds(*devices, type="off")


def on(*devices: str) -> list:
    return switch_cmds(*devices, type="on")


async def interrupt_xiaoai(speaker: SpeakerProtocol):
    await speaker.abort_xiaoai()
    await asyncio.sleep(2)


def wol(computer_mac: str, broadcast_ip: str) -> ActionFunction:
    ensure_dependencies(["wakeonlan"])

    async def wake_up_computer(_: SpeakerProtocol):
        from wakeonlan import send_magic_packet
        await asyncio.to_thread(send_magic_packet, computer_mac, ip_address=broadcast_ip)
        print(f"已向 {computer_mac} 发送网络唤醒包。")

    return wake_up_computer


def xiaoai_play(
    text: Optional[str] = None,
    url: Optional[str] = None,
    buffer: Optional[bytes] = None,
    blocking: bool = True,
    timeout: int = 10 * 60 * 1000,
):
    async def _play(speaker: SpeakerProtocol):
        await speaker.play(text, url, buffer, blocking, timeout)

    return _play


def bridge_call(base_url: str, path: str) -> ActionFunction:
    """调用 NAS 上的 bridge_server HTTP 接口（如新风机、加湿器等）。"""
    ensure_dependencies(["aiohttp"])

    async def _call(_: SpeakerProtocol):
        import aiohttp
        url = f"{base_url.rstrip('/')}{path}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        print(f"bridge_call 成功: {url}")
                    else:
                        print(f"bridge_call 失败 ({response.status}): {url}")
        except Exception as e:
            print(f"bridge_call 异常: {e}")

    return _call


def hass_action(
    url: str, token: str, domain: str, service: str, entity_id: str
) -> ActionFunction:
    ensure_dependencies(["aiohttp"])

    async def _call_hass(_: SpeakerProtocol):
        import aiohttp
        api_url = f"{url.rstrip('/')}/api/services/{domain}/{service}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"entity_id": entity_id}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        print(f"HASS 指令成功: {domain}.{service} -> {entity_id}")
                    else:
                        text = await response.text()
                        print(f"HASS 指令失败 ({response.status}): {text}")
        except Exception as e:
            print(f"HASS 请求异常: {e}")

    return _call_hass


class AppConfigBuilder:
    def __init__(
        self,
        direct_vad_wakeup_keywords: list[str],
        direct_vad_command_map: dict[str, Actions],
        xiaoai_wakeup_keywords: list[str],
        xiaoai_extension_command_map: dict[str, Actions],
        vad_config: dict[str, Any],
        xiaozhi_config: dict[str, Any],
        wakeup_timeout: int = 5,
        on_wakeup_play_text: str = "小智来了",
        on_execute_play_text: str = "已执行",
        on_exit_play_text: str = "主人再见",
    ):
        self.direct_vad_wakeup_keywords = direct_vad_wakeup_keywords
        self.direct_vad_command_map = direct_vad_command_map
        self.xiaoai_wakeup_keywords = xiaoai_wakeup_keywords
        self.xiaoai_extension_command_map = xiaoai_extension_command_map
        self.vad_config = vad_config
        self.xiaozhi_config = xiaozhi_config
        self.wakeup_timeout = wakeup_timeout
        self.on_wakeup_play_text = on_wakeup_play_text
        self.on_execute_play_text = on_execute_play_text
        self.on_exit_play_text = on_exit_play_text

    async def _execute_actions(self, speaker: SpeakerProtocol, actions: Actions):
        for action in actions:
            if isinstance(action, str):
                print(f" -> 执行小爱原生指令: '{action}'")
                await speaker.ask_xiaoai(text=action, silent=True)
            elif callable(action):
                print(f" -> 执行自定义函数: {getattr(action, '__name__', 'unknown_function')}")
                await action(speaker)
            await asyncio.sleep(0.2)

    async def _internal_before_wakeup(self, speaker: SpeakerProtocol, text: str, source: str) -> bool:
        if source == "kws":
            if text in self.direct_vad_wakeup_keywords:
                if self.on_wakeup_play_text:
                    await speaker.play(text=self.on_wakeup_play_text)
                return True
            actions = self.direct_vad_command_map.get(text)
            if actions:
                print(f"接收到直接VAD指令: '{text}'")
                await self._execute_actions(speaker, actions)
                if self.on_execute_play_text:
                    await speaker.play(text=self.on_execute_play_text)
                return False
        elif source == "xiaoai":
            if text in self.xiaoai_wakeup_keywords:
                await interrupt_xiaoai(speaker)
                if self.on_wakeup_play_text:
                    await speaker.play(text=self.on_wakeup_play_text)
                return True
            actions = self.xiaoai_extension_command_map.get(text)
            if actions:
                print(f"接收到小爱扩展指令: '{text}'")
                await interrupt_xiaoai(speaker)
                await self._execute_actions(speaker, actions)
                return False
        return False

    async def _internal_after_wakeup(self, speaker: SpeakerProtocol):
        if self.on_exit_play_text:
            await speaker.play(text=self.on_exit_play_text)

    def build(self) -> dict[str, Any]:
        async def before_wakeup_wrapper(speaker: SpeakerProtocol, text: str, source: str) -> bool:
            return await self._internal_before_wakeup(speaker, text, source)

        async def after_wakeup_wrapper(speaker: SpeakerProtocol):
            return await self._internal_after_wakeup(speaker)

        all_vad_keywords = [
            *self.direct_vad_wakeup_keywords,
            *list(self.direct_vad_command_map.keys()),
        ]
        wakeup_config = {
            "keywords": all_vad_keywords,
            "timeout": self.wakeup_timeout,
            "before_wakeup": before_wakeup_wrapper,
            "after_wakeup": after_wakeup_wrapper,
        }
        return {
            "vad": self.vad_config,
            "xiaozhi": self.xiaozhi_config,
            "wakeup": wakeup_config,
        }
