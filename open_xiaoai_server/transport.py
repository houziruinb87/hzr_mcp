# WebSocket 服务端：监听 4399，与 Open-XiaoAI 客户端同协议
# 收：Event、Stream(tag=record)；发：Request(start_play/start_recording)、Stream(tag=play)

import asyncio
import json
import logging
from typing import Callable, Optional

import websockets
from websockets.server import WebSocketServerProtocol

from .protocol import (
    Event,
    Request,
    Response,
    Stream,
    build_request,
    build_response,
    build_stream,
    parse_app_message,
)

logger = logging.getLogger(__name__)


class Transport:
    """与单个客户端的 WebSocket 连接，负责收发 AppMessage。"""

    def __init__(self, ws: WebSocketServerProtocol):
        self.ws = ws
        self.on_event: Optional[Callable] = None
        self.on_stream: Optional[Callable] = None
        self.on_request: Optional[Callable] = None  # 客户端发来的 Request 的 handler（若有）

    async def send_json(self, obj: dict) -> None:
        await self.ws.send(json.dumps(obj, ensure_ascii=False))

    async def send_binary(self, data: bytes) -> None:
        await self.ws.send(data)

    async def send_request(self, req: Request) -> None:
        await self.send_json(build_request(req))

    async def send_response(self, resp: Response) -> None:
        await self.send_json(build_response(resp))

    async def send_play_stream(self, audio_bytes: bytes, stream_id: str = "") -> None:
        """向客户端下发播放用音频流（tag=play）。"""
        from uuid import uuid4
        s = Stream(id=stream_id or uuid4().hex, tag="play", bytes=audio_bytes)
        await self.send_json(build_stream(s))

    async def run(self) -> None:
        try:
            async for message in self.ws:
                if isinstance(message, str):
                    try:
                        raw = json.loads(message)
                        kind, payload = parse_app_message(raw)
                        if kind == "Event" and self.on_event:
                            await self.on_event(payload)
                        elif kind == "Stream" and self.on_stream:
                            await self.on_stream(payload)
                        elif kind == "Request" and self.on_request:
                            resp = await self.on_request(payload)
                            if resp:
                                await self.send_response(resp)
                    except json.JSONDecodeError as e:
                        logger.warning("invalid json: %s", e)
                else:
                    # 二进制按 Stream 处理（若协议里 Stream 走 binary）
                    if self.on_stream:
                        await self.on_stream(Stream(id="", tag="record", bytes=message))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            logger.info("client disconnected")


async def serve(host: str = "0.0.0.0", port: int = 4399, on_connect=None) -> None:
    """启动 WebSocket 服务；on_connect(transport: Transport) 用于挂载 pipeline。"""

    async def handler(ws: WebSocketServerProtocol, path: str) -> None:
        transport = Transport(ws)
        if on_connect:
            on_connect(transport)
        await transport.run()

    async with websockets.serve(handler, host, port, ping_interval=20, ping_timeout=10):
        logger.info("open_xiaoai_server listening on %s:%s", host, port)
        await asyncio.Future()
