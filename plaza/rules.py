from plaza.canvas import check_pattern_shape

class Cooldowns:
    def __init__(self, ms_per_pixel: int) -> None: 
        if ms_per_pixel < 0:
            raise ValueError("每个像素的冷却时间应该是非负数")

        self.ms_per_pixel = ms_per_pixel
        self._available_at: dict[str, float] = {}


    def remaining(self, name: str, now: float) -> float:
        """这个人还要等多久才能画（0 表示现在就可以画）。now的单位是秒"""
        available = self._available_at.get(name, 0.0)
        return max(0.0, available - now)
        

    def charge(self, name: str, now: float, pixels: int) -> None:
        """修改一个人最早可以画的时间。画成功后调用：冷却 = 每格冷却时间 × 画的格数"""
        cooldown = pixels * self.ms_per_pixel / 1000
            
        if self.remaining(name, now) > 0:
            raise RuntimeError("在该连接还有cooldown的时候，不应该成功发出请求且调用cooldown.charge()")

        self._available_at[name] = now + cooldown


def stamp_too_large(pattern: list[list[int]], max_size: int) -> bool:
    """图案的宽或高超过了 max_size 时返回 True """
    check_pattern_shape(pattern)
        
    width = max((len(row) for row in pattern), default=0)
    return len(pattern) > max_size or width > max_size