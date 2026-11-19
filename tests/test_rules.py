import pytest
from plaza.canvas import InvalidPatternError
from plaza.rules import Cooldowns, stamp_too_large


# ------------ cooldowns_tests ------------

def test_new_user_can_draw_immediately() -> None:
    cooldowns = Cooldowns(ms_per_pixel=1000)
    assert cooldowns.remaining("xiaoming", now=100.0) == 0


def test_remaining_right_after_charge() -> None:
    cooldowns = Cooldowns(ms_per_pixel=1000)
    cooldowns.charge("xiaoming", now=100.0, pixels=1)
    assert cooldowns.remaining("xiaoming", now=100.0) == pytest.approx(1.0)


def test_remaining_decreases_as_time_passes() -> None:
    cooldowns = Cooldowns(ms_per_pixel=1000)
    cooldowns.charge("xiaoming", now=100.0, pixels=10)       # 冷却 10 秒，到 110 秒为止
    assert cooldowns.remaining("xiaoming", now=104.0) == pytest.approx(6.0)


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (109.5, 0.5),    # 还差半秒
        (110.0, 0.0),    # 刚好到点
        (115.0, 0.0),    # 早就过了：不能是负数
    ],
)
def test_remaining_around_expiry(now: float, expected: float) -> None:
    cooldowns = Cooldowns(ms_per_pixel=1000)
    cooldowns.charge("xiaoming", now=100.0, pixels=10)
    assert cooldowns.remaining("xiaoming", now=now) == pytest.approx(expected)


def test_cooldown_scales_with_pixels() -> None:
    cooldowns = Cooldowns(ms_per_pixel=1000)
    cooldowns.charge("one_pixel", now=0.0, pixels=1)
    cooldowns.charge("sixteen_pixels", now=0.0, pixels=16)
    assert cooldowns.remaining("sixteen_pixels", now=0.0) == pytest.approx(
        16 * cooldowns.remaining("one_pixel", now=0.0)
    )


def test_ms_per_pixel_is_converted_to_seconds() -> None:
    cooldowns = Cooldowns(ms_per_pixel=500)                   # 每格 0.5 秒
    cooldowns.charge("xiaoming", now=100.0, pixels=4)
    assert cooldowns.remaining("xiaoming", now=100.0) == pytest.approx(2.0)


def test_users_are_independent() -> None:
    cooldowns = Cooldowns(ms_per_pixel=1000)
    cooldowns.charge("xiaoming", now=100.0, pixels=1)
    assert cooldowns.remaining("xiaoming", now=100) == pytest.approx(1.0)
    assert cooldowns.remaining("xiaohong", now=100) == pytest.approx(0.0)


def test_charge_after_expiry_restarts_cooldown() -> None:
    cooldowns = Cooldowns(ms_per_pixel=1000)
    cooldowns.charge("xiaoming", now=100.0, pixels=1)
    cooldowns.charge("xiaoming", now=200.0, pixels=1)
    assert cooldowns.remaining("xiaoming", now=200) == pytest.approx(1.0)


def test_charge_during_cooldown_raises() -> None:
    cooldowns = Cooldowns(ms_per_pixel=1000)
    cooldowns.charge("xiaoming", now=100.0, pixels=10)
    with pytest.raises(RuntimeError):
        cooldowns.charge("xiaoming", now=105.0, pixels=1)


def test_charge_exactly_at_expiry_is_allowed() -> None:
    cooldowns = Cooldowns(ms_per_pixel=1000)
    cooldowns.charge("xiaoming", now=100.0, pixels=10)
    cooldowns.charge("xiaoming", now=110.0, pixels=1)
    assert cooldowns.remaining("xiaoming", now=110.0) == pytest.approx(1.0)


def test_negative_ms_per_pixel_is_rejected() -> None:
    with pytest.raises(ValueError):
        Cooldowns(ms_per_pixel=-1)

    
def test_ms_per_pixel_is_zero() -> None:
    cooldowns = Cooldowns(ms_per_pixel=0)
    cooldowns.charge("xiaoming", now=100.0, pixels=10)
    assert cooldowns.remaining("xiaoming", now=110.0) == 0


# ------------ stamp_size_tests ------------

MAX_STAMP_SIZE = 8

def test_pattern_size() -> None:
    pattern = [[1 for _ in range(8)] for _ in range(8)]
    assert not stamp_too_large(pattern, MAX_STAMP_SIZE)


def test_too_large_pattern1() -> None:
    pattern = [[1] for _ in range(9)]
    assert stamp_too_large(pattern, MAX_STAMP_SIZE)


def test_too_large_pattern2() -> None:
    pattern = [[1 for _ in range(9)]]
    assert stamp_too_large(pattern, MAX_STAMP_SIZE)


def test_empty_pattern_is_rejected_as_invalid() -> None:
    pattern: list[list[int]] = []
    with pytest.raises(InvalidPatternError):
        stamp_too_large(pattern, MAX_STAMP_SIZE)


def test_invalid_pattern() -> None:
    pattern = [[1,4,5],[0,2],[5,1,2,3,4],[1,1,1,1,1,1,1,1,1,1,1],[0]]
    with pytest.raises(InvalidPatternError):
        stamp_too_large(pattern, MAX_STAMP_SIZE)
    