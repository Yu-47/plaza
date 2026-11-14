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

        if palette_size > 256 or palette_size < 1:
            raise ValueError("调色板尺寸应不大于256，且大于0")
        
        self.width = width
        self.height = height
        self.palette_size = palette_size
        self._pixels = bytearray(width * height)


    def get(self, x: int, y: int) -> int:
        """取出某一格的颜色"""
        pass 

    def paint(self, x: int, y: int, color: int) -> None:
        """设置某一个的颜色"""
        pass

    def stamp(self, x: int, y: int, pattern: list[list[int]]) -> None:
        pass

    def snapshot(self) -> bytes:
        pass

