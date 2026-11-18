import json

import pytest

from plaza.rules import Cooldowns
from plaza.canvas import Canvas
from plaza.server import ServerState, Session, handle_message


def identified() -> tuple[ServerState, Session]:
    """准备一块 3×2 画布，和一个已经 hello 过的会话。"""
    canvas = Canvas(width=3, height=2)
    cooldowns = Cooldowns(ms_per_pixel=1000)
    state = ServerState(canvas, cooldowns)
    return state, Session(name="xiaoming")


# ---------- 套路 1：检查错误回复 ----------

def test_request_before_hello_is_rejected() -> None:
    canvas, session = Canvas(width=3, height=2), Session()   # 还没 hello
    cooldowns = Cooldowns(ms_per_pixel=1000)
    state = ServerState(canvas, cooldowns)
    reply = json.loads(handle_message('{"type": "read", "x": 0, "y": 0}', state, session, now=0.0))
    assert reply["type"] == "error"
    assert reply["code"] == "not_identified"


# ---------- 套路 2：同时检查"回复"和"状态变化" ----------

def test_hello_sets_name_and_returns_welcome() -> None:
    canvas, session = Canvas(width=3, height=2), Session()
    cooldowns = Cooldowns(ms_per_pixel=1000)
    state = ServerState(canvas, cooldowns)
    reply = json.loads(handle_message('{"type": "hello", "name": "xiaoming"}', state, session, now=0.0))
    assert session.name == "xiaoming"            # 会话状态变了
    assert reply["type"] == "welcome"            # 回复对了
    assert reply["width"] == 3
    assert reply["height"] == 2


# ---------- 套路 3：失败后状态不能变 ----------

def test_second_hello_is_rejected_and_name_unchanged() -> None:
    state, session = identified()
    reply = json.loads(handle_message('{"type": "hello", "name": "other"}', state, session, now=0.0))
    assert reply["type"] == "error"
    assert reply["code"] == "already_identified"
    assert session.name == "xiaoming"            # 名字没被改掉


# ---------- 套路 4：检查对画布的影响 + 二进制回复 ----------

def test_snapshot_returns_canvas_bytes() -> None:
    state, session = identified()
    handle_message('{"type": "paint", "x": 2, "y": 1, "color": 7}', state, session, now=0.0)
    reply = handle_message('{"type": "snapshot"}', state, session, now=0.0)
    assert isinstance(reply, bytes)              # 快照是二进制，不能 json.loads
    assert reply == bytes([0, 0, 0,
                           0, 0, 7])


# ---------- 套路 5：用 parametrize 检查"错误翻译词典" ----------

@pytest.mark.parametrize(
    ("text", "code"),
    [
        ('{"type": "paint", "x": 3, "y": 0, "color": 1}', "out_of_bounds"),
        ('{"type": "paint", "x": 0, "y": 0, "color": 16}', "invalid_color"),
        ('{"type": "stamp", "x": 0, "y": 0, "pattern": [[1, 2], [3]]}', "invalid_pattern"),
    ],
)
def test_canvas_errors_are_translated(text: str, code: str) -> None:
    state, session = identified()
    reply = json.loads(handle_message(text, state, session, now=0.0))
    assert reply["type"] == "error"
    assert reply["code"] == code


def test_paint_success() -> None:
    state, session = identified()
    reply = json.loads(handle_message('{"type": "paint", "x": 1, "y": 0, "color": 1}', state, session, now=0.0))
    assert reply["type"] == "painted"
    assert state.canvas.get(1, 0) == 1


def test_read_success() -> None:
    state, session = identified()
    reply = json.loads(handle_message('{"type": "paint", "x": 1, "y": 0, "color": 1}', state, session, now=0.0))
    reply = json.loads(handle_message('{"type": "read", "x": 1, "y": 0}', state, session, now=0.0))
    assert reply["type"] == "pixel"
    assert reply["color"] == 1


def test_stamp_success() -> None:
    state, session = identified()
    reply = json.loads(handle_message('{"type": "stamp", "x": 0, "y": 0, "pattern": [[1,2],[3,4]]}', state, session, now=0.0))
    assert reply["type"] == "stamped"
    reply = handle_message('{"type": "snapshot"}', state, session, now=0.0)
    assert reply == bytes([1, 2, 0, 3, 4, 0])


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ('hello, world', "invalid_message"),
        ('{"type": "jump"}', "unknown_type"),
    ],
)
def test_wrong_protocol(text: str, code: str) -> None:
    state, session = identified()
    reply = json.loads(handle_message(text, state, session, now=0.0))
    assert reply["type"] == "error"
    assert reply["code"] == code


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ('{"type": "read", "x": 2, "y": 0}', "not_identified"),
        ('{"type": "paint", "x": 0, "y": 0, "color": 11}', "not_identified"),
        ('{"type": "snapshot"}', "not_identified"),
    ],
)
def test_no_hello(text: str, code: str) -> None:
    canvas, session = Canvas(width=3, height=2), Session()
    reply = json.loads(handle_message(text, canvas, session, now=0.0))
    assert reply["type"] == "error"
    assert reply["code"] == code