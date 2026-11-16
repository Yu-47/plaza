# tests/test_protocol.py
import pytest

from plaza.protocol import (HelloRequest, 
                            ReadRequest, 
                            PaintRequest, 
                            StampRequest, 
                            SnapshotRequest, 
                            ProtocolError, 
                            parse_request)


def test_hello_success() -> None:
    text = '{"type":"hello","name":"xiaoming"}'
    assert parse_request(text) == HelloRequest(name="xiaoming")


def test_read_success() -> None:
    text = '{"type":"read","x":3,"y":5}'
    assert parse_request(text) == ReadRequest(x=3, y=5)


def test_paint_success() -> None:
    text = '{"type":"paint","x":3,"y":5,"color":7}'
    assert parse_request(text) == PaintRequest(x=3, y=5, color=7)


def test_stamp_success() -> None:
    text = '{"type":"stamp","x":0,"y":0,"pattern":[[1,2],[3,4]]}'
    assert parse_request(text) == StampRequest(x=0, y=0, pattern=[[1,2],[3,4]])


def test_snapshot_success() -> None:
    text = '{"type":"snapshot"}'
    assert parse_request(text) == SnapshotRequest()
 

def test_paint_negative_input_success() -> None:
    text = '{"type":"paint","x":-1,"y":0,"color":7}'
    assert parse_request(text) == PaintRequest(x=-1, y=0, color=7)


def test_paint_over_palette_size_success() -> None:
    text = '{"type":"paint","x":0,"y":0,"color":99}'
    assert parse_request(text) == PaintRequest(x=0, y=0, color=99)


def test_stamp_different_row_length_success() -> None:
    text = '{"type":"stamp","x":0,"y":0,"pattern":[[1,2],[3]]}'
    assert parse_request(text) == StampRequest(x=0, y=0, pattern=[[1,2],[3]])
    
    
@pytest.mark.parametrize("text",
                         [
                            "hello, world",
                            "",
                            '[1, 2]',
                            '5',
                            'null',
                            '"hello"',
                            '{"x": 3}',
                            '{"type": 5}',
                            '{"type":"paint","x":3,"y":5}',
                            '{"type":"paint","x":3,"y":5,"color":7,"z":1}',
                            '{"type":"snapshot","x":3}',
                            '{"type":"read","x":"3","y":5}',
                            '{"type":"read","x":3.0,"y":5}',
                            '{"type":"read","x":true,"y":5}',
                            '{"type":"read","x":null,"y":5}',
                            '{"type":"hello","name":5}',
                            '{"type":"stamp","x":0,"y":0,"pattern":5}',
                            '{"type":"stamp","x":0,"y":0,"pattern":[[1,2],[3, "a"]]}',
                            '{"type":"stamp","x":0,"y":0,"pattern":[1,2]}',
                            '{"type":"stamp","x":0,"y":0,"pattern":[[true]]}',
                         ])
def test_invalid_message(text) -> None:
    with pytest.raises(ProtocolError) as exc_info:
        parse_request(text)
    assert exc_info.value.code == "invalid_message"

@pytest.mark.parametrize("text",
                         [
                            '{"type":"jump","x":0,"y":0,"pattern":[[1,2],[3]]}',
                            '{"type":"STAMP","x":0,"y":0,"pattern":[[1,2],[3,4]]}'
                         ])
def test_unknown_type(text) -> None:
    with pytest.raises(ProtocolError) as exc_info:
        parse_request(text)
    assert exc_info.value.code == "unknown_type"