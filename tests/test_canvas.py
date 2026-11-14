# tests/test_canvas.py
import pytest
from plaza.canvas import Canvas, OutOfBoundsError


def test_new_canvas_is_all_zero() -> None:
    canvas = Canvas(width=3, height=2)
    assert canvas.get(0, 0) == 0
    assert canvas.get(2, 1) == 0


def test_get_out_of_bounds_raises() -> None:
    canvas = Canvas(width=3, height=2)
    with pytest.raises(OutOfBoundsError):
        canvas.get(3, 0)

def right_get() -> None:
    canvas = Canvas(width=4, height=3)
    canvas.paint(0, 0, 7)
    assert canvas.get(0, 0) == 7