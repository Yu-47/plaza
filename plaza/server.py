import asyncio
import json
from dataclasses import dataclass
from plaza.protocol import parse_request, ProtocolError, HelloRequest, ReadRequest, PaintRequest, StampRequest, SnapshotRequest
from plaza.canvas import Canvas, InvalidColorError, OutOfBoundsError, InvalidPatternError, CanvasError
from websockets.asyncio.server import serve

from functools import partial

CANVAS_ERROR_CODES = {
    OutOfBoundsError: "out_of_bounds",
    InvalidColorError: "invalid_color",
    InvalidPatternError: "invalid_pattern",
}


@dataclass
class Session:
    name: str | None = None    # None 表示还没发过 hello


def _error(code: str, message: str) -> str:
    return json.dumps({"type": "error", "code": code, "message": message}, ensure_ascii=False)


Reply = bytes | str


def handle_message(text: str, canvas: Canvas, session: Session) -> Reply:
    """处理一条客户端消息，返回要发回的回复；所有错误都转成错误回复，不向外抛出"""
    try:
        request = parse_request(text)
    except ProtocolError as e:
        return _error(e.code, str(e))

    is_hello = isinstance(request, HelloRequest)
    if session.name is None and not is_hello:
        return _error("not_identified", "请先发送 hello 命令表明身份")
    if session.name is not None and is_hello:
        return _error("already_identified", "该连接已以{session.name}的身份登陆，不能更改名字")
    if session.name is None and is_hello:
        session.name = request.name
        return json.dumps({
            "type": "welcome",
            "width": canvas.width,
            "height": canvas.height,
            "palette_size": canvas.palette_size,
        })

    try:
        match request:
            case ReadRequest():
                return json.dumps({
                    "type": "pixel",
                    "x": request.x, 
                    "y": request.y, 
                    "color": canvas.get(request.x, request.y),
                })
            
            case PaintRequest():
                canvas.paint(request.x, request.y, request.color)
                return json.dumps({
                    "type": "painted", 
                    "x": request.x, 
                    "y": request.y, 
                    "color": request.color, 
                })
            
            case StampRequest():
                canvas.stamp(request.x, request.y, request.pattern)
                return json.dumps({
                    "type": "stamped", 
                    "x": request.x, 
                    "y": request.y, 
                    "width": len(request.pattern[0]), 
                    "height": len(request.pattern), 
                })
                
            case SnapshotRequest():
                return canvas.snapshot()
            
            case _:
                return _error("invalid_message", "无法识别命令语句")
    except CanvasError as e:
        return _error(CANVAS_ERROR_CODES[type(e)], str(e))


async def handler(websocket, canvas: Canvas) -> None:
    session = Session()
    async for message in websocket:
        reply = handle_message(message, canvas, session)    # 普通函数，不碰网络
        await websocket.send(reply)


async def main() -> None:
    canvas = Canvas(100, 100, 16)
    async with serve(partial(handler, canvas=canvas), "localhost", 8765) as server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())