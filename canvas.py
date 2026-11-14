class Canvas:
    def __init__(self, width: int, height: int) -> None: 
        self.width = width
        self.height = height

    def get(self, x: int, y: int) -> int:
        pass 
    
    def set(self) -> None:
        # 抛出异常，可以提醒user是什么地方错了
        # 但是我还是不太理解set方法是设定规则还是什么？怎么表示设定规则？
        pass

    def draw_block(self, x: int, y: int, color: int) -> None:
        pass

    def stamp(self, x_start: int, x_end: int, y_start: int, y_end: int, pattern) -> None:
        # 应该是在class外定义后循环调用
        pass

    def snapshot(self) -> int:
        pass
