import json
from dataclasses import dataclass

@dataclass(frozen=True)
class HelloRequest:
    name: str

@dataclass(frozen=True)
class ReadRequest:
    x: int
    y: int

@dataclass(frozen=True)
class PaintRequest:
    x: int
    y: int
    color: int

@dataclass(frozen=True)
class StampRequest:
    x: int
    y: int
    pattern: list[list[int]]

@dataclass(frozen=True)
class SnapshotRequest:
    pass

class ProtocolError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code

Request = HelloRequest | ReadRequest | PaintRequest | StampRequest | SnapshotRequest

def _require_int(data: dict, key: str) -> int:
    """取出 data[key]，确认它是整数，否则抛 ProtocolError。"""
    if type(data[key]) is int:
        return data[key]
    else:
        raise ProtocolError("invalid_message", f"{data[key]} 应该是整数类型的数据")

def _check_fields(data: dict, expected: set[str]) -> None:
    """data 的字段（不算 "type"）必须恰好等于 expected，缺少或多余都抛 ProtocolError。"""
    keys = set(data) - {"type"}
    missing = expected - keys
    extra = keys - expected

    if extra:
        raise ProtocolError("invalid_message", "多余字段")
    elif missing:
        raise ProtocolError("invalid_message", "字段过少")

def _require_str(data: dict, key: str) -> str:
    """取出 data[key]，确认它是字符串，否则抛 ProtocolError。"""
    if type(data[key]) is str:
        return data[key]
    else:
        raise ProtocolError("invalid_message", f"{data[key]} 应该是字符串类型的数据")

def _require_pattern(data: dict, key: str) -> list[list[int]]:
    """取出 data[key]，确认它是二维int列表，否则抛 ProtocolError。"""
    if type(data[key]) is list:
        for row in data[key]:
            if type(row) is list:
                for color in row:
                    if type(color) is int:
                        continue
                    else:
                        raise ProtocolError("invalid_message", f"{data[key]} 应该是二维int列表类型的数据")
            else:
                raise ProtocolError("invalid_message", f"{data[key]} 应该是二维int列表类型的数据")
        return data[key]
    else:
        raise ProtocolError("invalid_message", f"{data[key]} 应该是二维int列表类型的数据")

def _parse_hello(data: dict) -> HelloRequest:
    _check_fields(data, {"name"})
    return HelloRequest(
        name=_require_str(data, "name")
    )

def _parse_read(data: dict) -> ReadRequest:
    _check_fields(data, {"x", "y"})
    return ReadRequest(
        x=_require_int(data, "x"),
        y=_require_int(data, "y"),
    )

def _parse_paint(data: dict) -> PaintRequest:
    _check_fields(data, {"x", "y", "color"})
    return PaintRequest(
        x=_require_int(data, "x"),
        y=_require_int(data, "y"),
        color=_require_int(data, "color"),
    )

def _parse_stamp(data: dict) -> StampRequest:
    _check_fields(data, {"x", "y", "pattern"})
    return StampRequest(
        x=_require_int(data, "x"),
        y=_require_int(data, "y"),
        pattern=_require_pattern(data, "pattern")
    )

def _parse_snapshot(data: dict) -> SnapshotRequest:
    _check_fields(data, set())
    return SnapshotRequest()

def parse_request(text: str) -> Request:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise(ProtocolError("invalid_message", "非法json格式，解析出错")) from e

    if not isinstance(data, dict):
        raise ProtocolError("invalid_message", "未按照字典形式输入，解析失败")

    if "type" not in data:
        raise ProtocolError("invalid_message", "输入中没包含“type”键")

    if type(data["type"]) is str:
        match data["type"]:
            case "hello":
                return _parse_hello(data)

            case "read":
                return _parse_read(data)

            case "paint":
                return _parse_paint(data)

            case "stamp":
                return _parse_stamp(data)

            case "snapshot":
                return _parse_snapshot(data)

            case _:
                raise ProtocolError("unknown_type", "无法从type键中解析出对应对象，解析失败")
    else: 
        raise ProtocolError("invalid_message", "type字段应该输入str类型的数据")
