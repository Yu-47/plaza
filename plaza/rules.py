class Cooldowns:
    def __init__(self, ms_per_pixel: int) -> None: ...

    def remaining(self, name: str, now: float) -> float:
        """这个人还要等多久才能画（0 表示现在就可以画）。"""
        ...

    def charge(self, name: str, now: float, cells: int) -> None:
        """画成功后调用：冷却 = 每格冷却时间 × 画的格数"""
        