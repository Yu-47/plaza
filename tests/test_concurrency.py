import asyncio
import json
from functools import partial

import pytest
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

from plaza.canvas import Canvas
from plaza.server import handler

WIDTH = 8


@pytest.fixture
async def server_url():
    """每个测试启动一个全新的服务器，测试结束后自动关闭。"""
    canvas = Canvas(width=WIDTH, height=WIDTH)
    async with serve(partial(handler, canvas=canvas), "localhost", 0) as server:
        port = server.sockets[0].getsockname()[1]
        yield f"ws://localhost:{port}"


async def say_hello(ws, name: str) -> None:
    await ws.send(json.dumps({"type": "hello", "name": name}))
    await ws.recv()


async def read_region(ws) -> list[int]:
    """请求一次快照，返回左上角 4×4 区域的 16 个颜色值。"""
    message = json.dumps({"type": "snapshot"})
    await ws.send(message)
    snap = await ws.recv()
    region = []
    for y in range(4):
        region.extend(snap[WIDTH*y : WIDTH*y+4])

    return region


async def test_stamps_never_interleave(server_url: str) -> None:
    async with connect(server_url, proxy=None) as a, \
               connect(server_url, proxy=None) as b, \
               connect(server_url, proxy=None) as watcher:
        # 1. 三个客户端各自 hello（名字不同）
        await say_hello(a, "Aclient")
        await say_hello(b, "Bclient")
        await say_hello(watcher, "Watching")


        async def stamper(ws, color: int) -> None:
            pattern = [[color] * 4 for _ in range(4)]
            message = json.dumps({"type": "stamp", "x": 0, "y": 0, "pattern": pattern})
            for _ in range(200):
                await ws.send(message)
                reply_text = await ws.recv()
                reply = json.loads(reply_text)

                assert reply["type"] == "stamped", f"未成功盖章: {reply}"

        async def watch(ws) -> None:
            for _ in range(200):
                region = await read_region(ws)
                assert len(set(region)) == 1, f"发现交错：{region}"

        await asyncio.gather(stamper(a, 1), stamper(b, 4), watch(watcher))
        final = await read_region(watcher)
        assert set(final) in ({1}, {4}), f"最终结果不对：{final}"



# ------------- 坏服务器 -------------

from plaza.server import Session, handle_message


async def bad_handler(websocket, canvas: Canvas) -> None:
    """故意写坏的服务器：印章逐格绘制，每格之间让出控制权。"""
    session = Session()
    async for message in websocket:
        data = json.loads(message)
        if data.get("type") == "stamp" and session.name is not None:
            for dy, row in enumerate(data["pattern"]):
                for dx, color in enumerate(row):
                    canvas.paint(data["x"] + dx, data["y"] + dy, color)
                    await asyncio.sleep(0)          # ← 这一行就是 bug
            await websocket.send(json.dumps({"type": "stamped"}))
        else:
            await websocket.send(handle_message(message, canvas, session))