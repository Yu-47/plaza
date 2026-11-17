# 设计文档

## 阶段 1：需求与功能决定

### 需求（"什么算对"）

| 编号 | 内容 | 为什么 |
|---|---|---|
| 需求 1 | 同一格多人修改，以服务器收到的最后一次为准 | 谁先谁后本来就不确定，结果是红是蓝都可以接受；真正的错误是混色或半红半蓝。需要一条明确的规则来定"谁是最后"，所以用服务器收到的顺序 |
| 需求 2 | 快照 = 某一真实时刻的完整画面，不保证最新 | 边抄边改会拼出从没存在过的画面（抄白板问题 B）。"最新"本来就做不到，因为数据传输期间画布可能又变了，所以只要求"真实存在过" |
| 需求 3 | 印章整体生效，没有"盖了一半" | 两个印章逐格交错会出现绿紫混杂，任何先后顺序都解释不了；盖了一半被别人看到，也不符合用户意图 |

**总原则：** 所有人看到的结果，都必须等于"把操作按某种顺序一个一个做完"的结果（可串行化）。

### 功能决定

| 编号 | 决定 | 为什么 | 放弃的做法 / 代价 |
|---|---|---|---|
| 决定 1 | 画布固定大小，大小可配置 | 扩展会让"坐标是否合法""快照大小"随时间变化，还会引入扩展瞬间的并发问题，10–14 天内性价比低 | 放弃：可扩展画布（留作加分项）。代价：画布满了不能变大 |
| 决定 2 | 16 色调色板，可配置 | 每格 1 字节，RGB 需要 3 字节，快照数据量约为 1/3；输入检查只需判断 0–15；画风统一 | 放弃：任意 RGB。代价：用户可选颜色少 |
| 决定 3 | 印章 = 自定义图案，尺寸设上限 | 纯色方块是图案的特例，图案更通用；上限防止一次覆盖大片画布 | 代价：输入数据更大，要检查的内容更多 |
| 决定 4 | 印章任一格超出画布就整个拒绝；先检查，后动笔 | 超出边缘多半是用户放错位置，明确报错比悄悄画一部分更符合预期。先检查可以保证不出现"画了一半"的可见状态，也不需要撤回逻辑 | 放弃：只画画布内部分（也满足原子性，但不符合用户意图）；边画边检查再撤回 |
| 决定 5 | 连接时报一次用户名；冷却按用户名记录在服务器端 | 永远不信任客户端，所以冷却必须由服务器记。按用户名记，断线重连后冷却不变，规则对所有人一致 | 放弃：按连接记（重连就清零）。已知局限：换名字可以绕过冷却，真正解决需要账号认证，超出本项目范围 |
| 决定 6 | 冷却 = 每格冷却时间 × 画的格数 | 印章越大代价越大，印章就没法用来绕过冷却 | 放弃：每次操作固定冷却。代价：大印章要等很久，所以配合尺寸上限 |
| 决定 7 | 重名处理：同名的多个连接视为同一用户，共用冷却 | 重连没问题；开多条同名连接也绕不过冷却 | 两个真正不同的"小明"会互相抢冷却 |
| 决定 8 | 画布用一维 bytearray 按行优先存储 | 每格 1 字节，正好对应 16 色编号，内存约为普通列表的 1/8；快照只需整体复制一次，结果可直接发送；赋值超出 0–255 会直接报错 | 放弃：二维列表（复制容易踩坑）、字典（拿快照最慢）|
| 决定 9 | 通信用 WebSocket | 需要服务器主动推送更新（HTTP 请求-响应做不到）；浏览器不能直接用 TCP；WebSocket 自带消息边界，不用自己处理粘包 | 放弃：裸 TCP（要自己分帧，浏览器用不了）、HTTP 轮询（大量白问的请求）。代价：多一个第三方库依赖 |
| 决定 10 | 最简网页前端（显示画布 + 点击画一格），放在最后做 | 面试时可以直观演示；后端岗位的重点仍是服务器 | 代价：额外的 HTML/JS 工作量，所以排在最后 |
| 决定 11 | 分层：Canvas 类不知道网络的存在，网络层只负责"收消息 → 调用 Canvas → 回复" | 换通信方式时只改网络层；Canvas 可以脱离网络单独测试 | 代价：多一层代码 |
| 决定 12 | 命令用 JSON，快照用二进制 | JSON 字段有名字，加字段不会打乱旧格式，Python 和 JS 都自带解析；快照数据量约为 JSON 的 1/3，且画布本身就是 bytearray，可直接发送 | 代价：客户端要处理两种消息；二进制不可读，调试不方便 |
| 决定 13 | 连接后服务器先发 welcome，告知画布尺寸等配置 | 同一信息只存一处，由服务器告诉客户端，避免两边配置不一致 | 代价：多一轮握手 |
| 决定 14 | 印章图案用二维列表；各行长度不一致则整个拒绝 | 一眼能看出图案形状，宽高可以直接从列表算出；行长度不一致时，宽度有歧义，按某一行宽度去读其他行会越界，盖到一半出错 | 放弃：宽高 + 一维列表（宽高和列表长度可能对不上）。代价：需要逐行检查长度 |
| 决定 15 | 同一条连接上，第二次 hello 一律拒绝，回复 already_identified，名字保持不变 | 冷却是按名字记录的（决定 5）。如果允许改名，用户在冷却期间发一句 hello 换个名字，就能立刻继续画画，冷却形同虚设 | 决定 5 选择"连接时报一次名字"，好处正是"同一条连接上没法中途换名字"，允许改名就把这个好处丢掉了 |

## 通信协议

坐标约定：x = 列，y = 行，从 0 开始。
消息格式：命令和回复都是 JSON 文本消息；只有快照是二进制消息。
所有 JSON 消息都有 "type" 字段，表示消息种类。

### 0. 连接握手
连接后客户端必须先发 hello，否则其他请求一律返回 not_identified。

- 请求：{"type": "hello", "name": "xiaoming"}
- 成功：{"type": "welcome", "width": 1000, "height": 1000,
         "palette_size": 16, "cooldown_ms_per_pixel": 1000, "max_stamp_size": 8}
- 失败：invalid_name（名字为空或过长）

### 1. 画一格
- 请求：{"type": "paint", "x": 3, "y": 5, "color": 7}
- 成功：{"type": "painted", "x": 3, "y": 5, "color": 7, "cooldown_ms": 1000}
- 失败：out_of_bounds / invalid_color / cooldown

### 2. 读一格
- 请求：{"type": "read", "x": 3, "y": 5}
- 成功：{"type": "pixel", "x": 3, "y": 5, "color": 7}
- 失败：out_of_bounds

### 3. 快照
- 请求：{"type": "snapshot"}
- 成功：一条**二进制**消息，共 width × height 个字节，按行优先排列，
        每个字节是一格的颜色编号。宽高从 welcome 消息得知。
- 客户端规则：收到二进制消息 = 快照；收到文本消息 = 按 JSON 解析。

### 4. 盖印章
- 请求：{"type": "stamp", "x": 10, "y": 20,
         "pattern": [[7, 7, 7],
                     [7, 3, 7],
                     [7, 7, 7]]}
  x, y 是图案左上角；pattern 是二维列表，每个子列表是一行。
- 成功：{"type": "stamped", "x": 10, "y": 20, "width": 3, "height": 3, "cooldown_ms": 9000}
- 失败：out_of_bounds / invalid_color / invalid_pattern / stamp_too_large / cooldown

### 错误回复（统一格式）
{"type": "error", "code": "<代号>", "message": "<给人看的说明>", ...附带字段}

| 代号 | 含义 | 附带字段 |
|---|---|---|
| invalid_message | 不是合法 JSON、缺字段、字段类型不对 | — |
| unknown_type | type 不认识 | — |
| not_identified | 还没发 hello | — |
| invalid_name | 名字为空或太长 | — |
| out_of_bounds | 坐标超出画布（印章：任一格超出） | — |
| invalid_color | 颜色不在 0–15 | — |
| invalid_pattern | 图案为空，或各行长度不一致 | — |
| stamp_too_large | 图案宽或高超过上限 | max_stamp_size |
| cooldown | 冷却中 | retry_after_ms |
| already_indentified | 已经表明过身份了 | - |

（订阅相关的消息留到阶段 5 再设计。）

## 阶段 2：单用户版本

### 任务 1：项目结构

我们的程序大概要负责这几件事：
- 画布本身（存、取、快照、印章）
- 解析和检查消息（JSON 是否合法、字段对不对）
- 网络（WebSocket 收发）
- 配置（画布大小、冷却时间……）
- 测试

文件夹结构：
plaza/                  # 仓库根目录
  README.md             # 项目说明
  pyproject.toml        # 项目配置：依赖、pytest 设置
  .gitignore            # 不提交的文件（scratch/、缓存……）
  docs/
    design.md
  scratch/              # 实验文件，被 .gitignore 忽略
  plaza/                # 代码包
    __init__.py         # 有这个文件，Python 才把文件夹当成包
    canvas.py           # 画布本身
    protocol.py         # 解析、检查 JSON 消息
    server.py           # WebSocket 网络层
    config.py           # 配置参数
    __main__.py         # 启动入口（python -m plaza）
  tests/
    test_canvas.py      # 每个模块对应一个测试文件

  
## 测试框架
| 角度 | 例子 |
| --- | --- |
| 正常情况 | 画一格后读出来，颜色对不对 |
| 边界值 | 坐标 0 和 width−1 能不能画？颜色 0 和 15 呢？|
| 越界 | 坐标 −1、width；颜色 −1、16 |
| 构造参数 | width = 0 或 −5 |
| 快照 | 内容对不对；拿到快照后再画一格，快照会不会跟着变？|
| 刚才的陷阱 | 创建两块画布，画其中一块，另一块会不会变？|

### __init__
- 正常创建 3×2 画布 → 不报错，width=3，height=2
- width = 0 → ValueError
- width = 负数 → ValueError
- height = 0 → ValueError
- height = 负数 → ValueError
- palette_size = 0 → ValueError
- palette_size = 1 → 不报错
- palette_size = 256 → 不报错
- palette_size = 257 → ValueError

### get
- 新画布读 (0, 0) → 0
- 读右下角 (width-1, height-1) → 0（边界值，不应报错）
- 越界检查 x 太小：(-1, 0) → OutOfBoundsError
- 越界检查 y 太小：(0, -1) → OutOfBoundsError
- 越界检查 x 太大：(width, 0) → OutOfBoundsError
- 越界检查 y 太大：(0, height) → OutOfBoundsError

### paint
- 画 (1, 1) 颜色 5，再 get(1, 1) → 5
- 颜色边界：0 和 palette_size-1 能画上
- 颜色越界：-1 和 palette_size → InvalidColorError
- 颜色非法时，原来那一格保持不变
- 坐标越界四个方向 → OutOfBoundsError
- 画一格不影响其他格：画 (1, 1)，(0, 0) 和 (2, 1) 仍然是 0
- 同一格画两次 → 以后一次为准（需求 1）

### snapshot
- 返回类型是 bytes
- 长度 = width × height
- 新画布的快照全是 0
- 3×2 画布画 (x=2, y=1) 颜色 7 → 快照第 1×3+2 = 5 个字节是 7，其余是 0（验证行优先、行列没有搞反）
- 拿到快照后再 paint → 之前的快照内容不变（需求 2）

### 其他
- 两块画布互相独立：画其中一块，另一块不变

### stamp
- 正常盖一个 2×2 图案，每一格都对吗？
- 图案刚好贴着右下角边缘，能盖上吗？
- 图案只有一格超出边缘 → OutOfBoundsError
- 图案里只有一格颜色非法 → InvalidColorError
- 空图案 []、空行 [[]]、各行长度不一致 → InvalidPatternError
- 上面任何一种失败发生后，画布是否一格都没变？怎么写测试来证明这一点？


## 协议层设计

### 哪些消息应该由协议层拦下，哪些由Canvas判断

| # |  收到的消息 |  谁来拦截 | 
|---|---|---| 
| a | hello world（不是 JSON） | 协议层 | 
| b | {"type": "jump"} | 协议层 | 
| c | {"type": "paint", "x": 3, "y": 5}（缺 color）| 协议层 |
| d | {"type": "paint", "x": "3", "y": 5, "color": 7} | 协议层 |
| e | {"type": "paint", "x": 3.0, "y": 5, "color": 7} | 协议层 |
| f | {"type": "paint", "x": true, "y": 5, "color": 7} | 协议层 |
| g | {"type": "paint", "x": -1, "y": 5, "color": 7} | Canvas |
| h | {"type": "paint", "x": 3, "y": 5, "color": 99} | Canvas |
| i | {"type": "stamp", "x": 0, "y": 0, "pattern": [[1, 2], [3]]} | Canvas |
| j | {"type": "stamp", "x": 0, "y": 0, "pattern": [[1, 2], [3, 'k']]} | 协议层 |
| k | {"type": "paint", "x": 3, "y": 5, "color": 7, "z": 1}（多了一个字段） | 协议层 |

## 设计"标准表格"，根据阶段 1 的协议，每种请求定义一个 dataclass，只写字段和类型：

``` python
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
```


## 设计入口函数和异常

### parse_request 列测试清单

测试清单（tests/test_protocol.py）

合法请求，解析成正确的对象
- {"type":"hello","name":"xiaoming"} → HelloRequest(name="xiaoming")
- {"type":"read","x":3,"y":5} → ReadRequest(x=3, y=5)
- {"type":"paint","x":3,"y":5,"color":7} → PaintRequest(x=3, y=5, color=7)
- {"type":"stamp","x":0,"y":0,"pattern":[[1,2],[3,4]]} → 对应的 StampRequest
- {"type":"snapshot"} → SnapshotRequest()

协议层应该放行（交给 Canvas 判断）
- paint 的 x = -1 → 正常解析，不抛异常
- paint 的 color = 99 → 正常解析
- stamp 的 pattern = [[1,2],[3]]（各行不等长）→ 正常解析

invalid_message：JSON 层面
- hello world（不是 JSON）
- 空字符串 ""
- 合法 JSON 但不是对象：[1, 2]、"hello"、5、null

invalid_message：type 字段
- 没有 type：{"x": 3}
- type 不是字符串：{"type": 5}

invalid_message：字段缺少或多余
- paint 缺 color
- paint 多一个 "z": 1
- snapshot 多一个字段：{"type":"snapshot","x":1}

invalid_message：字段类型不对（都用 paint 的 x）
- "3"（字符串）、3.0（小数）、true（布尔）、null
- hello 的 name 是 5

invalid_message：pattern 的类型不对
- pattern 不是列表：5
- 某一行不是列表：[1, 2]
- 元素是字符串：[[1, "a"]]
- 元素是布尔：[[true]]

unknown_type
- {"type": "jump"}
- {"type": "PAINT"}（大小写不同，也算不认识）
