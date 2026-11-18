import asyncio
import json
import time
import math
from dataclasses import dataclass
from plaza.rules import Cooldowns
from plaza.protocol import parse_request, ProtocolError, HelloRequest, ReadRequest, PaintRequest, StampRequest, SnapshotRequest
from plaza.canvas import Canvas, InvalidColorError, OutOfBoundsError, InvalidPatternError, CanvasError
from websockets.asyncio.server import serve

from functools import partial

CANVAS_ERROR_CODES = {
    OutOfBoundsError: "out_of_bounds",
    InvalidColorError: "invalid_color",
    InvalidPatternError: "invalid_pattern",
}

@dataclass(frozen=True)
class ServerState:
    canvas: Canvas
    cooldowns: Cooldowns


@dataclass
class Session:
    name: str | None = None    # None 表示还没发过 hello


def _error(code: str, message: str, **kwargs: object) -> str:
    return json.dumps({"type": "error", "code": code, "message": message, **kwargs}, ensure_ascii=False)


def _cooldown_error(state: ServerState, session: Session, now: float) -> str | None:
    """判断是否在冷却时间内，如果在冷却时间内，则返回error。如没在冷却时间内，返回None"""
    wait = state.cooldowns.remaining(session.name, now)
    if wait > 0:
        return _error("cooldown", "还在冷却时间中。", retry_after_ms=math.ceil(round(wait*1000, 6)))
    return None

Reply = bytes | str


def handle_message(text: str, state: ServerState, session: Session, now: float) -> Reply:
    """处理一条客户端消息，返回要发回的回复；所有错误都转成错误回复，不向外抛出"""
    try:
        request = parse_request(text)
    except ProtocolError as e:
        return _error(e.code, str(e))

    is_hello = isinstance(request, HelloRequest)
    if session.name is None and not is_hello:
        return _error("not_identified", "请先发送 hello 命令表明身份")
    if session.name is not None and is_hello:
        return _error("already_identified", f"该连接已以{session.name}的身份登录，不能更改名字")
    if session.name is None and is_hello:
        session.name = request.name
        return json.dumps({
            "type": "welcome",
            "width": state.canvas.width,
            "height": state.canvas.height,
            "palette_size": state.canvas.palette_size,
        })

    try:
        match request:
            case ReadRequest():
                return json.dumps({
                    "type": "pixel",
                    "x": request.x, 
                    "y": request.y, 
                    "color": state.canvas.get(request.x, request.y),
                })
            
            case PaintRequest():
                error = _cooldown_error(state, session, now)
                if error is not None:
                    return error

                state.canvas.paint(request.x, request.y, request.color)
                state.cooldowns.charge(session.name, now, pixels=1)
                
                return json.dumps({
                    "type": "painted", 
                    "x": request.x, 
                    "y": request.y, 
                    "color": request.color, 
                    "cooldown_ms": state.cooldowns.ms_per_pixel,
                })

            
            case StampRequest():
                error = _cooldown_error(state, session, now)
                if error is not None:
                    return error
                
                state.canvas.stamp(request.x, request.y, request.pattern)
                cells = len(request.pattern[0])*len(request.pattern)
                state.cooldowns.charge(session.name, now, pixels=cells)

                return json.dumps({
                    "type": "stamped", 
                    "x": request.x, 
                    "y": request.y, 
                    "width": len(request.pattern[0]), 
                    "height": len(request.pattern), 
                    "cooldown_ms": cells*state.cooldowns.ms_per_pixel,
                })
                
            case SnapshotRequest():
                return state.canvas.snapshot()
            
            case _:
                return _error("invalid_message", "无法识别命令语句")
    except CanvasError as e:
        return _error(CANVAS_ERROR_CODES[type(e)], str(e))


async def handler(websocket, state: ServerState) -> None:
    session = Session()
    async for message in websocket:
        now = time.monotonic()
        reply = handle_message(message, state, session, now)    # 普通函数，不碰网络
        await websocket.send(reply)


async def main() -> None:
    canvas = Canvas(100, 100, 16)
    cooldowns = Cooldowns(ms_per_pixel=1000)
    state = ServerState(canvas, cooldowns)
    async with serve(partial(handler, state=state), "localhost", 8765) as server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())