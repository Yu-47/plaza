# tests/test_canvas.py
import pytest

from plaza.canvas import Canvas, InvalidColorError, OutOfBoundsError, InvalidPatternError

PALETTE_SIZE = 16

# ---------- __init__ ----------


def test_init_stores_size() -> None:
    canvas = Canvas(width=3, height=2)
    assert canvas.width == 3
    assert canvas.height == 2


@pytest.mark.parametrize(
    ("width", "height"),
    [(0, 2), (-1, 2), (3, 0), (3, -1)],
)
def test_init_rejects_non_positive_size(width: int, height: int) -> None:
    with pytest.raises(ValueError):
        Canvas(width=width, height=height)


@pytest.mark.parametrize("palette_size", [1, 16, 256])
def test_init_accepts_valid_palette_size(palette_size: int) -> None:
    canvas = Canvas(width=3, height=2, palette_size=palette_size)
    assert canvas.palette_size == palette_size


@pytest.mark.parametrize("palette_size", [0, -1, 257])
def test_init_rejects_invalid_palette_size(palette_size: int) -> None:
    with pytest.raises(ValueError):
        Canvas(width=3, height=2, palette_size=palette_size)


# ---------- get ----------


def test_new_canvas_corners_are_zero() -> None:
    canvas = Canvas(width=3, height=2)
    assert canvas.get(0, 0) == 0
    assert canvas.get(2, 1) == 0  # 右下角 (width-1, height-1)


@pytest.mark.parametrize(
    ("x", "y"),
    [(-1, 0), (0, -1), (3, 0), (0, 2)],  # 左、上、右、下，各刚好越界一格
)
def test_get_out_of_bounds_raises(x: int, y: int) -> None:
    canvas = Canvas(width=3, height=2)
    with pytest.raises(OutOfBoundsError):
        canvas.get(x, y)


# ---------- paint ----------


def test_paint_one_grid() -> None:
    canvas = Canvas(width=3, height=2)
    canvas.paint(1, 1, 5)
    assert canvas.get(1, 1) == 5


@pytest.mark.parametrize("color", [0, PALETTE_SIZE - 1])
def test_paint_accepts_boundary_colors(color: int) -> None:
    canvas = Canvas(width=3, height=2, palette_size=PALETTE_SIZE)
    canvas.paint(1, 1, color)
    assert canvas.get(1, 1) == color


@pytest.mark.parametrize("color", [-1, PALETTE_SIZE])
def test_invalid_color_keeps_previous_color(color: int) -> None:
    canvas = Canvas(width=3, height=2, palette_size=PALETTE_SIZE)
    canvas.paint(1, 1, 6)
    with pytest.raises(InvalidColorError):
        canvas.paint(1, 1, color)
    assert canvas.get(1, 1) == 6


@pytest.mark.parametrize(
    ("x", "y"),
    [(-1, 0), (0, -1), (3, 0), (0, 2)],  # 左、上、右、下，各刚好越界一格
)
def test_paint_out_of_bounds_raises(x: int, y: int) -> None:
    canvas = Canvas(width=3, height=2)
    with pytest.raises(OutOfBoundsError):
        canvas.paint(x, y, 1)


def test_other_grids_stay_unchanged() -> None:
    canvas = Canvas(width=3, height=2)
    canvas.paint(1, 1, 1)
    assert canvas.get(0, 0) == 0
    assert canvas.get(1, 0) == 0
    assert canvas.get(2, 1) == 0    


def test_paint_a_grid_twice() -> None:
    canvas = Canvas(width=3, height=2)
    canvas.paint(1, 1, 1)
    canvas.paint(1, 1, 6)
    assert canvas.get(1, 1) == 6


# ---------- snapshot ----------


def test_snapshot_return_type_is_bytes() -> None:
    canvas = Canvas(width=3, height=2)
    s = canvas.snapshot()
    assert isinstance(s, bytes)


def test_snapshot_length() -> None:
    canvas = Canvas(width=3, height=2)
    s = canvas.snapshot()
    assert len(s) == canvas.width * canvas.height


def test_new_canvas_snapshot_all_zero() -> None:
    canvas = Canvas(width=3, height=2)
    s = canvas.snapshot()
    assert s == bytes(6)


def test_colored_snapshot() -> None:
    canvas = Canvas(width=3, height=2)
    canvas.paint(2, 1, 7)
    s = canvas.snapshot()
    assert s == bytes([0, 0, 0, 0, 0, 7])


def test_paint_after_snapshot() -> None:
    canvas = Canvas(width=3, height=2)
    s = canvas.snapshot()
    canvas.paint(2, 1, 7)
    assert s == bytes([0, 0, 0, 0, 0, 0])


# ---------- other ----------


def test_two_independent_canvas() -> None:
    canvas1 = Canvas(width=3, height=2)
    canvas2 = Canvas(width=7, height=4)

    canvas1.paint(1, 1, 10)
    assert canvas1.get(1, 1) == 10
    assert canvas2.get(1, 1) == 0


# ---------- stamp ----------

def test_stamp_pattern() -> None:
    p = [[1, 2], [3, 4]]
    canvas = Canvas(width=4, height=3)
    canvas.stamp(1, 1, p)

    assert canvas.snapshot() == bytes([0, 0, 0, 0,
                                       0, 1, 2, 0,
                                       0, 3, 4, 0])


def test_stamp_corner() -> None:
    p = [[1, 2], [3, 4]]
    canvas = Canvas(width=4, height=3)
    canvas.stamp(2, 1, p)

    assert canvas.snapshot() == bytes([0, 0, 0, 0,
                                       0, 0, 1, 2,
                                       0, 0, 3, 4])


def test_one_grid_out_of_boundary() -> None:
    p = [[1, 1], [1, 1]]
    canvas = Canvas(width=4, height=3)
    with pytest.raises(OutOfBoundsError):
        canvas.stamp(3, 1, p)

    assert canvas.snapshot() == bytes([0, 0, 0, 0,
                                       0, 0, 0, 0,
                                       0, 0, 0, 0])


def test_one_invalid_color() -> None:
    p = [[1, 1], [1, 16]]
    canvas = Canvas(width=4, height=3)
    with pytest.raises(InvalidColorError):
        canvas.stamp(1, 1, p)

    assert canvas.snapshot() == bytes([0, 0, 0, 0,
                                       0, 0, 0, 0,
                                       0, 0, 0, 0])


@pytest.mark.parametrize(
    ("pattern"),
    [[], [[]], [[3, 0],[]], [[0],[0, 2]]],
)
def test_invalid_pattern(pattern) -> None:
    canvas = Canvas(width=4, height=3)
    with pytest.raises(InvalidPatternError):
        canvas.stamp(1, 1, pattern)

    assert canvas.snapshot() == bytes([0, 0, 0, 0,
                                       0, 0, 0, 0,
                                       0, 0, 0, 0])


def test_rectangle_stamp1() -> None:
    canvas = Canvas(width=4, height=4)
    p = [[3, 0, 1]]
    canvas.stamp(1, 1, p)

    assert canvas.snapshot() == bytes([0, 0, 0, 0,
                                       0, 3, 0, 1,
                                       0, 0, 0, 0,
                                       0, 0, 0, 0])    


def test_rectangle_stamp2() -> None:
    canvas = Canvas(width=4, height=4)
    p = [[0],[1],[2]]
    canvas.stamp(1, 1, p)

    assert canvas.snapshot() == bytes([0, 0, 0, 0,
                                       0, 0, 0, 0,
                                       0, 1, 0, 0,
                                       0, 2, 0, 0])    

