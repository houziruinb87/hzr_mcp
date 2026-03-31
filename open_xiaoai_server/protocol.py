# 与 Open-XiaoAI client-rust 对齐的 AppMessage 结构
# 参考: packages/client-rust/src/services/connect/data.rs

import json
from dataclasses import dataclass, field
from typing import Any, Literal, Optional


@dataclass
class Stream:
    id: str
    tag: str  # "record"=客户端麦克风, "play"=服务端下发播放
    bytes: bytes
    data: Optional[dict] = None

    def to_dict(self) -> dict:
        d = {"id": self.id, "tag": self.tag, "bytes": list(self.bytes)}
        if self.data is not None:
            d["data"] = self.data
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Stream":
        return cls(
            id=d["id"],
            tag=d["tag"],
            bytes=bytes(d.get("bytes", [])),
            data=d.get("data"),
        )


@dataclass
class Event:
    id: str
    event: str
    data: Optional[dict] = None

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        return cls(id=d["id"], event=d["event"], data=d.get("data"))


@dataclass
class Request:
    id: str
    command: str  # 如 start_play, start_recording
    payload: Optional[dict] = None

    def to_dict(self) -> dict:
        d = {"id": self.id, "command": self.command}
        if self.payload is not None:
            d["payload"] = self.payload
        return d


@dataclass
class Response:
    id: str
    code: Optional[int] = None
    msg: Optional[str] = None
    data: Optional[dict] = None

    def to_dict(self) -> dict:
        d = {"id": self.id}
        if self.code is not None:
            d["code"] = self.code
        if self.msg is not None:
            d["msg"] = self.msg
        if self.data is not None:
            d["data"] = self.data
        return d

    @classmethod
    def success(cls, id: str) -> "Response":
        return cls(id=id, code=0, msg="success")


def parse_app_message(raw: dict) -> tuple[str, Any]:
    """解析一条 AppMessage（与 client-rust 枚举格式一致），返回 (variant, payload)。"""
    # client-rust 发来的是 {"Request": {...}} / {"Stream": {...}} 等
    for key in ("Request", "Response", "Event", "Stream"):
        if key in raw:
            body = raw[key]
            if key == "Request":
                return "Request", Request(
                    id=body["id"],
                    command=body["command"],
                    payload=body.get("payload"),
                )
            if key == "Event":
                return "Event", Event.from_dict(body)
            if key == "Stream":
                return "Stream", Stream.from_dict(body)
            if key == "Response":
                return "Response", Response(
                    id=body["id"],
                    code=body.get("code"),
                    msg=body.get("msg"),
                    data=body.get("data"),
                )
    return "Unknown", raw


def build_request(req: Request) -> dict:
    """发往客户端的 RPC 请求，序列化为 JSON 后发送。"""
    return {"Request": req.to_dict()}


def build_stream(stream: Stream) -> dict:
    """发往客户端的音频流，注意 bytes 需为 list 以可 JSON 序列化。"""
    return {"Stream": stream.to_dict()}


def build_response(resp: Response) -> dict:
    """回复客户端的 RPC。"""
    return {"Response": resp.to_dict()}
