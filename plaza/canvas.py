class CanvasError(Exception):
    """所有画布操作错误的基类。"""

class OutOfBoundsError(CanvasError):
    """坐标超出画布范围。"""

class InvalidColorError(CanvasError):
    """颜色不存在或无效"""

class InvalidPatternError(CanvasError):
    """印章形状非法或者pattern为空"""

class Canvas:
    def __init__(self, width: int, height: int, palette_size: int = 16) -> None: 
        if width <= 0 or height <= 0:
            raise ValueError("画布的宽和高都应该是大于0的数字。")

        if not 1 <= palette_size <= 256:
            raise ValueError("调色板尺寸应不大于256，且大于0")
        
        self.width = width
        self.height = height
        self.palette_size = palette_size
        self._pixels = bytearray(width * height)

    def _check_bounds(self, x: int, y: int) -> None:
        """检查传入坐标是否超出画布边界"""
        if (not 0 <= x < self.width) or (not 0 <= y < self.height):
            raise OutOfBoundsError(f"坐标 ({x}, {y}) 超出画布范围 {self.width}×{self.height}")

    def _index(self, x: int, y: int) -> int:
        """调用前必须先检查越界，本函数自己不检查"""
        return y * self.width + x

    def _check_color(self, color: int) -> None:
        """检查该颜色是否为有效颜色"""
        if not 0 <= color < self.palette_size:
            raise InvalidColorError(f"颜色 {color} 超出调色盘范围 {self.palette_size}")

    def get(self, x: int, y: int) -> int:
        """取出某一格的颜色"""
        self._check_bounds(x, y)

        return self._pixels[self._index(x, y)]
         

    def paint(self, x: int, y: int, color: int) -> None:
        """设置某一格的颜色"""
        self._check_bounds(x, y)
        self._check_color(color)
        
        self._pixels[self._index(x, y)] = color

    def stamp(self, x: int, y: int, pattern: list[list[int]]) -> None:
        """盖印章"""

        if not pattern or not pattern[0]:
            raise InvalidPatternError("pattern不能为空")

        pattern_width = len(pattern[0])
        pattern_height = len(pattern)
        for row in pattern[1:]:
            if len(row) != pattern_width:
                raise InvalidPatternError("pattern每行长度应相等")

        self._check_bounds(x, y)
        self._check_bounds(x+pattern_width-1, y+pattern_height-1)

        for row in pattern:
            for color in row:
                self._check_color(color)

        for dy, row in enumerate(pattern):
            for dx, color in enumerate(row):
                self._pixels[self._index(dx+x, dy+y)] = color

    def snapshot(self) -> bytes:
        """返回当前画布快照"""
        return bytes(self._pixels)

