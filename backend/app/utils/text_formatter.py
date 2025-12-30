# ============================================================
# 文件: backend/app/utils/text_formatter.py
# 功能: 文本格式化和OCR结果合并处理
# 作者: Walmart PDF解析团队
# 创建时间: 2025-12-16
# 最后修改: 2025-12-26
# 依赖: logging, typing, dataclasses
# 说明: 提供统一的文本处理规则，用于格式化OCR识别结果和合并文本块
# ============================================================

# 导入标准库日志模块
import logging
# 导入类型提示相关模块
#   - Optional: 表示可选类型 (T | None)
#   - List: 列表类型注解
#   - Tuple: 元组类型注解
#   - Dict: 字典类型注解
#   - Any: 任意类型
from typing import Optional, List, Tuple, Dict, Any
# 导入dataclass装饰器，用于生成数据类
from dataclasses import dataclass

# 获取当前模块的logger对象，用于记录日志
logger = logging.getLogger(__name__)

# ============================================================
# 配置常量 - 所有魔法数字都集中在这里便于维护和调整
# ============================================================

# 【文本处理规则 - Y坐标和容差相关】
# 默认的Y坐标容差范围（像素单位），用于判断两个文本块是否在同一行
# 含义：Y坐标差值在±15像素以内，则认为在同一行
Y_TOLERANCE_DEFAULT = 10

# 特殊关键词，标记"支付金额"字段
# 用于触发特殊的支付金额块关联逻辑
PAYMENT_KEYWORD = "向您支付的金额"

# Y坐标阈值，用于过滤高于此值的"向您支付的金额"文本块
# 含义：只处理Y坐标小于100的支付金额文本（即页面上方的支付字段）
PAYMENT_AMOUNT_Y_THRESHOLD = 1000

# 支付金额块的Y轴偏移量（像素单位）
# 从"向您支付的金额"文本块的左下角Y坐标向下偏移50像素来查找对应的金额值
PAYMENT_OFFSET_Y = 200

# 支付金额块的X轴容差范围（像素单位）
# 金额块的X坐标可以在目标X坐标±10像素范围内
PAYMENT_OFFSET_X_TOLERANCE = 10

# 支付金额块的Y轴容差范围（像素单位）
# 金额块的Y坐标可以在目标Y坐标±10像素范围内
PAYMENT_OFFSET_Y_TOLERANCE = 10

# 【金额相关符号 - 用于识别和过滤金额文本】
# 包含多种金额符号的集合，用于is_amount()方法中判断文本是否是金额
#   - '$': 美元符号
#   - '美元': 中文描述
#   - '.': 小数点
#   - '¥', '￥': 人民币符号（两种写法）
AMOUNT_SYMBOLS = {'$', '美元', '.', '¥', '￥'}

# 【全角字符范围 - Unicode编码范围】
# 全角字符的Unicode起始码（65281对应全角'！'）
FULL_WIDTH_CHAR_START = 65281

# 全角字符的Unicode结束码（65374对应全角'～'）
FULL_WIDTH_CHAR_END = 65374

# 全角空格的Unicode码（12288）
# 需要特殊处理，转换为半角空格（32）
FULL_WIDTH_SPACE = 12288


# ============================================================
# 数据类定义 - 结构化文本块信息
# ============================================================

@dataclass
class TextInfo:
    """文本块信息数据类

    用于结构化存储从OCR结果中提取的文本块信息。
    相比使用字典，使用dataclass提供：
    - 类型安全：IDE可以提供自动补全
    - 结构清晰：属性定义明确
    - 代码复用：内置方法逻辑内聚

    属性说明：
        text (str): OCR识别的文本内容
        box (List[Tuple[int, int]]): 文本块的边界框坐标，格式为 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                                     代表矩形的四个顶点（左上、右上、右下、左下）
        confidence (float): OCR识别的置信度，取值范围 [0, 1]，值越大识别越准确
        center_x (float): 文本块的中心X坐标，计算方式：(left_x + right_x) / 2
        center_y (float): 文本块的中心Y坐标，计算方式：(top_y + bottom_y) / 2
        left_bottom_x (int): 文本块左下角的X坐标，用于支付金额特殊处理
        left_bottom_y (int): 文本块左下角的Y坐标，用于计算支付金额块的偏移位置
    """

    # OCR识别的原始文本内容
    text: str

    # 文本块的边界框（4个顶点的坐标）
    box: List[Tuple[int, int]]

    # 识别置信度 (0.0-1.0)
    confidence: float

    # 文本块中心X坐标
    center_x: float

    # 文本块中心Y坐标
    center_y: float

    # 文本块左下角X坐标
    left_bottom_x: int

    # 文本块左下角Y坐标
    left_bottom_y: int

    def is_amount(self) -> bool:
        """判断文本是否可能是金额

        检查文本内容是否包含数字和金额相关符号。
        用于识别"向您支付的金额"后面对应的金额值。

        判断规则：
        1. 文本必须非空
        2. 必须包含至少一个数字字符
        3. 必须包含至少一个金额相关符号

        返回值：
            bool: 如果是金额则返回True，否则返回False
        """
        # 如果文本为空或None，直接返回False
        if not self.text:
            return False

        # 检查是否包含数字（0-9任意一个）
        has_digit = any(char.isdigit() for char in self.text)

        # 检查是否包含金额符号（$、美元、.、¥等）
        has_currency = any(symbol in self.text for symbol in AMOUNT_SYMBOLS)

        # 同时满足两个条件才认为是金额
        return has_digit or has_currency

def _convert_full_to_half(text: str) -> str:
    """将全角字符转换为半角字符

    在PDF中，OCR识别到的中文和符号有时会被识别为全角形式。
    本函数将这些全角字符转换为半角字符，便于后续处理。

    处理规则：
    - 全角字符（65281-65374）：减去65248得到半角字符
      例：全角'A'(65313) -> 半角'A'(65)
    - 全角空格（12288）：转换为半角空格（32）
    - 其他字符：保持不变

    参数说明：
        text (str): 输入的原始文本，可能包含全角字符

    返回值：
        str: 转换后的文本，所有全角字符已转为半角

    异常处理：
        - 字符转换失败时记录warning日志，但不中断处理，继续处理下一个字符
    """
    # 如果输入文本为None或空字符串，直接返回空字符串
    if not text:
        return ""

    # 创建一个列表用于存储转换后的字符
    # （列表拼接比字符串拼接性能更好）
    result = []

    # 逐个字符处理
    for char in text:
        try:
            # 获取字符的Unicode码点值
            code = ord(char)

            # 检查是否在全角字符范围内（65281-65374）
            if FULL_WIDTH_CHAR_START <= code <= FULL_WIDTH_CHAR_END:
                # 全角字符转半角：减去偏移量65248
                # 例：全角'！'(65281) - 65248 = 33(半角'!')
                result.append(chr(code - 65248))

            # 检查是否是全角空格（12288）
            elif code == FULL_WIDTH_SPACE:
                # 转换为半角空格
                result.append(' ')

            # 其他字符保持不变
            else:
                result.append(char)

        # 异常处理：如果字符转换失败，记录日志但继续处理
        except (TypeError, ValueError) as e:
            # 记录转换失败的字符和原因（用于调试）
            logger.warning(f"字符转换失败: {char} ({ord(char) if isinstance(char, str) else 'N/A'}), 原因: {e}")
            # 原字符保持不变，加入结果
            result.append(char)

    # 将列表中的所有字符拼接为字符串并返回
    return ''.join(result)


def format_text(text: Optional[str]) -> str:
    """应用文本处理规则，将文本格式化

    将OCR识别到的文本进行标准化处理，确保数据格式一致。
    处理顺序经过精心设计，确保每一步的输出是下一步的有效输入。

    处理步骤说明：
    1. 替换所有空格：移除文本中的所有空格（包括多个连续空格）
    2. 全角字符转半角字符：统一字符格式
    3. 所有字母转大写：标准化字母格式（便于后续匹配）
    4. 替换所有$符号为空：移除金额符号
    5. 检查"总计"后是否有冒号：如果缺少冒号则自动补充

    处理顺序的意义：
    - 先空格再转大小写：避免大小写转换影响空格判断
    - 先全角转半角再大写：确保所有字符转换都已完成
    - 最后处理冒号：确保"总计"文本已完全处理

    参数说明：
        text (Optional[str]): 需要格式化的文本字符串
                             - None: 返回空字符串
                             - 空字符串: 返回空字符串
                             - 正常文本: 进行处理并返回

    返回值：
        str: 格式化后的文本字符串
             - 若输入为None/空，返回空字符串
             - 若处理过程异常，返回原文本或空字符串

    异常处理：
        本函数不抛出异常。任何处理过程中的异常都会被捕获，
        并返回原文本（或空字符串如果原文本也为None）。
    """
    # 空值检查：如果输入为None或空字符串，直接返回空字符串
    if not text:
        return ""

    try:
        # ===== 第1步：替换所有空格 =====
        # 作用：移除文本中的所有空格，包括：
        #   - 普通空格（ASCII 32）
        #   - 多个连续空格
        # 示例："Hello  World" -> "HelloWorld"
        text = text.replace(' ', '')
        logger.debug(f"[1/5] 替换空格后: {text}")

        # ===== 第2步：全角字符转半角字符 =====
        # 作用：将PDF中识别到的全角字符转换为半角
        # 这是重要的规范化步骤，确保同一字符的统一表示
        # 示例：全角"A" -> 半角"A"
        text = _convert_full_to_half(text)
        logger.debug(f"[2/5] 全角转半角后: {text}")

        # ===== 第3步：所有字母转大写 =====
        # 作用：将所有英文字母转为大写，便于后续的模式匹配
        # 中文字符无大小写概念，会保持不变
        # 示例："Hello" -> "HELLO"
        text = text.upper()
        logger.debug(f"[3/5] 转大写后: {text}")

        # ===== 第4步：替换所有$符号为空 =====
        # 作用：移除美元符号，因为数据库中只存储数字
        # 示例："$100.50" -> "100.50"
        #text = text.replace('$', '')
        #logger.debug(f"[4/5] 替换$后: {text}")

        # ===== 第5步：检查"总计"后是否有冒号 =====
        # 作用：确保"总计"字段格式统一为"总计:"
        # 检查条件：
        #   1. text.startswith('总计')：以"总计"开头
        #   2. not text.startswith('总计:')：但后面没有冒号
        # 处理：使用replace(..., 1)只替换第一个匹配的"总计"
        if text.startswith('总计') and not text.startswith('总计:'):
            # 只替换第一个"总计"（replace的第三个参数为1）
            # 避免误替换其他地方可能出现的"总计"
            text = text.replace('总计', '总计:', 1)
            logger.debug(f"[5/5] 添加冒号后: {text}")

        # 格式化成功，记录debug日志
        logger.debug(f"文本格式化成功: {text}")
        return text

    # ===== 异常处理 =====
    # 捕获所有异常，记录详细的错误信息（包括traceback），
    # 然后返回原文本或空字符串，确保函数不会中断程序流程
    except Exception as e:
        logger.error(f"文本格式化失败，返回原文本: {e}", exc_info=True)
        # 如果原文本为None，返回空字符串；否则返回原文本
        return text or ""

def _parse_ocr_result(result: Tuple) -> TextInfo:
    """解析OCR识别结果，构建TextInfo对象

    将PaddleOCR或其他OCR引擎返回的原始结果转换为结构化的TextInfo对象。
    这一步非常重要，因为它进行数据验证和坐标计算。

    OCR原始结果格式说明：
    result = (box_coordinates, (text, confidence))
    其中：
    - box_coordinates: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
      代表矩形的4个顶点（按顺序：左上、右上、右下、左下）
    - text: 识别的文本内容字符串
    - confidence: 识别置信度，范围[0, 1]

    坐标转换：
    - center_x = (left_x + right_x) / 2 = (box[0][0] + box[2][0]) / 2
    - center_y = (top_y + bottom_y) / 2 = (box[0][1] + box[2][1]) / 2
    - left_bottom_x = 左上角X = box[0][0]
    - left_bottom_y = 右下角Y = box[2][1]

    参数说明：
        result (Tuple): OCR结果元组
                       格式必须严格为 (box_coordinates, (text, confidence))
                       - box_coordinates: List[List[int]] 4个坐标点
                       - text: str 识别的文本
                       - confidence: float 置信度

    返回值：
        TextInfo: 结构化的文本块信息对象

    异常处理：
        捕获以下异常并抛出ValueError：
        - ValueError: 解包失败或数据格式错误
        - IndexError: 坐标列表越界（box长度不足）
        - TypeError: 数据类型错误（如box不是列表）

    异常示例：
        >>> _parse_ocr_result(("invalid",))  # ValueError
        >>> _parse_ocr_result(([], (None, None)))  # IndexError
        >>> _parse_ocr_result(None)  # TypeError
    """
    try:
        # ===== 解包OCR结果 =====
        # 将result元组解包为两部分：box和(text, confidence)
        box, (text, confidence) = result

        # ===== 计算中心坐标 =====
        # 中心X = (左上角X + 右下角X) / 2
        # 右下角X位于box[2][0]，左上角X位于box[0][0]
        center_x = (box[0][0] + box[2][0]) / 2

        # 中心Y = (左上角Y + 右下角Y) / 2
        # 左上角Y位于box[0][1]，右下角Y位于box[2][1]
        center_y = (box[0][1] + box[2][1]) / 2

        # ===== 获取左下角坐标 =====
        # 左下角X = box的第一个顶点的X坐标 = box[0][0]
        left_bottom_x = box[0][0]

        # 左下角Y = box的第三个顶点的Y坐标 = box[2][1]
        # （右下角的Y坐标就是矩形底部的Y坐标）
        left_bottom_y = box[2][1]

        # ===== 构建并返回TextInfo对象 =====
        return TextInfo(
            text=text,
            box=box,
            confidence=confidence,
            center_x=center_x,
            center_y=center_y,
            left_bottom_x=left_bottom_x,
            left_bottom_y=left_bottom_y
        )

    # ===== 异常处理 =====
    # 捕获可能出现的异常，记录错误信息，然后重新抛出为ValueError
    except (ValueError, IndexError, TypeError) as e:
        # 记录原始异常信息，包括输入数据（便于调试）
        logger.error(f"OCR结果解析失败: {e}, 输入: {result}")
        # 抛出新的ValueError，链接原始异常信息（from e）
        # 这样可以保留完整的traceback信息
        raise ValueError(f"无效的OCR结果格式: {e}") from e


def _find_payment_amount_block(
    text_info: TextInfo,
    amount_infos: List[TextInfo],
    processed: set,
    is_first: bool
) -> Tuple[Optional[TextInfo], int]:
    """查找并返回"向您支付的金额"对应的金额块

    Walmart对账单中，"向您支付的金额"文本后面通常跟着一个金额值。
    本函数通过空间位置推断来自动关联这两个文本块。

    特殊处理逻辑：
    - 第一个"向您支付的金额"：使用左下角坐标 + Y偏移量
      原因：第一个支付字段的坐标系统相对固定，左下角更准确
    - 后续"向您支付的金额"：使用中心坐标 + Y偏移量
      原因：后续字段可能在页面中部，中心坐标更通用

    坐标搜索范围说明：
    - X轴搜索范围：target_x ± 10像素
      允许金额块在支付文本的左右±10像素范围内
    - Y轴搜索范围：target_y ± 10像素
      允许金额块在目标Y坐标的上下±10像素范围内

    参数说明：
        text_infos (TextInfo): 包含"向您支付的金额"的文本块
                                     会在这个列表中搜索金额块
        amount_infos (List[TextInfo]) 所有文本块的信息列表
                                 用于计算目标金额块的搜索范围
        processed (set): 已处理过的文本块索引集合
                        用于避免重复处理同一个文本块
        is_first (bool): 是否为第一个"向您支付的金额"文本块
                        - True: 使用左下角坐标
                        - False: 使用中心坐标

    返回值：
        Tuple[Optional[TextInfo], int]:
        - 第一元素：找到的金额TextInfo对象，未找到时为None
        - 第二元素：找到的金额块在text_infos中的索引，未找到时为-1
        返回索引的作用：便于调用者标记该索引为已处理

    算法流程：
        1. 根据is_first判断使用哪个坐标系统
        2. 计算搜索范围（X和Y的容差范围）
        3. 遍历所有未处理的文本块
        4. 检查三个条件：Y坐标、X坐标、是否是金额
        5. 返回第一个匹配的文本块及其索引

    示例：
        payment_block: TextInfo(text="向您支付的金额", center_y=400, left_bottom_y=420)
        target_y = 420 + 50 = 470
        搜索范围：[460, 480]（Y坐标）
        如果找到center_y=470且是金额的文本块，就是要找的
    """
    # ===== 根据是否为第一个支付块选择坐标系统 =====
    payment_block=text_info
    if is_first:
        # 第一个"向您支付的金额"：使用左下角坐标
        # 原因：第一个支付字段位置固定，左下角精准度更高
        target_x = payment_block.left_bottom_x
        target_y = payment_block.left_bottom_y + PAYMENT_OFFSET_Y

    else:
        # 后续"向您支付的金额"：使用中心坐标
        # 原因：考虑到页面排版的多样性，中心坐标更通用
        target_x = payment_block.center_x
        target_y = payment_block.center_y

    # ===== 计算X轴搜索范围 =====
    # X轴容差：±10像素（从常量PAYMENT_OFFSET_X_TOLERANCE获取）
    target_x_range = (target_x - PAYMENT_OFFSET_X_TOLERANCE, target_x + PAYMENT_OFFSET_X_TOLERANCE)

    # ===== 计算Y轴搜索范围 =====
    # Y轴容差：±10像素（从常量PAYMENT_OFFSET_Y_TOLERANCE获取）
    target_y_range = (target_y - PAYMENT_OFFSET_Y_TOLERANCE, target_y + PAYMENT_OFFSET_Y_TOLERANCE)

    # ===== 遍历所有未处理的文本块 =====
    # for i, info in enumerate(text_infos):
    #     # 跳过已处理过的文本块
    #     if i not in processed:
    #         # ===== 三条件匹配检查 =====
    #         # 条件1：Y坐标在范围内
    #         y_match = target_y_range[0] <= info.center_y <= target_y_range[1]
    #         # 条件2：X坐标在范围内
    #         x_match = target_x_range[0] <= info.center_x <= target_x_range[1]
    #         # 条件3：文本确实是金额
    #         is_amount = info.is_amount()

    #         # 如果两个条件都满足，返回该文本块和索引
    #         if y_match and is_amount:
    #             return info, i

    # ===== 未找到匹配的文本块 =====
    # 返回None和-1标记为未找到
    return None, -1


def _detect_block_boundary(line_text: str) -> str:
    """检测当前行属于哪个板块

    通过关键词识别PDF中的板块结构。
    按照优先级从下到上检测，确保后面的板块不会误匹配。

    板块类型说明：
    - FOOTER: "向您支付的金额" - 最后的支付金额板块
    - OTHER: "其他活动" - 其他活动板块
    - WFS: "沃尔玛商品服务" 或 "WFS" - 物流服务板块
    - ADJUSTMENT: "调整" - 调整板块
    - REFUND: "退款" - 退款板块
    - SALES: "销售" - 销售板块
    - HEADER: 上述都不包含 - 页面头部板块

    参数说明：
        line_text (str): 当前行的合并文本内容

    返回值：
        str: 板块类型字符串，可选值为上述7种

    示例：
        >>> _detect_block_boundary("向您支付的金额")
        'FOOTER'
        >>> _detect_block_boundary("销售商品A")
        'SALES'
    """
    # 按优先级从后向前检测（确保特定词优先于通用词）
    if "向您支付的金额" in line_text:
        return "FOOTER"
    elif "其他活动" in line_text:
        return "OTHER"
    elif "沃尔玛商品服务" in line_text or "WFS" in line_text:
        return "WFS"
    elif "调整" in line_text:
        return "ADJUSTMENT"
    elif "退款" in line_text:
        return "REFUND"
    elif "销售" in line_text:
        return "SALES"
    else:
        return "HEADER"


def _get_matching_amount(
    text_info: TextInfo,
    amount_infos: List[TextInfo],
    processed_amounts: set,
    y_tolerance: int = Y_TOLERANCE_DEFAULT
) -> Optional[TextInfo]:
    """获取与指定文本块匹配的金额块

    根据中心Y坐标查找与文本块匹配的金额块，优先选择Y坐标最接近的金额。

    参数说明：
        text_info (TextInfo): 文本块信息
        amount_infos (List[TextInfo]): 金额块列表
        processed_amounts (set): 已处理的金额块索引集合
        y_tolerance (int): Y坐标容差范围

    返回值：
        Optional[TextInfo]: 匹配的金额块，如果没有匹配的则返回None
    """
    matched_amounts = []
    
    for i, amount_info in enumerate(amount_infos):
        if i not in processed_amounts and abs(text_info.center_y - amount_info.center_y) <= y_tolerance:
            matched_amounts.append((i, amount_info))
    
    if matched_amounts:
        # 按Y中心坐标最接近排序
        matched_amounts.sort(key=lambda x: abs(text_info.center_y - x[1].center_y))
        # 标记为已处理
        processed_amounts.add(matched_amounts[0][0])
        return matched_amounts[0][1]
    
    return None


def _format_line(line_data: List[TextInfo]) -> str:
    """格式化单行数据为输出字符串

    将一个或多个TextInfo对象转换为标准的输出格式。
    每个文本块用单引号包裹，多个文本块用逗号分隔。

    格式规则：
    - 单个文本块：'文本内容'
    - 多个文本块：'文本1','文本2','文本3'

    参数说明：
        line_data (List[TextInfo]): 该行的所有TextInfo对象列表
                                   已按X坐标排序

    返回值：
        str: 格式化的行字符串

    示例：
        >>> line = [TextInfo(text="销售"), TextInfo(text="$100.50")]
        >>> _format_line(line)
        "'销售','$100.50'"
    """
    # 提取所有文本块的text内容，用逗号和单引号组装
    formatted_texts = [f"'{info.text}'" for info in line_data]
    return ','.join(formatted_texts)


def _process_payment_amount(
    text_info: TextInfo,
    amount_infos: List[TextInfo],
    processed_amounts: set
) -> Tuple[Optional[TextInfo], Optional[TextInfo]]:
    """处理"向您支付的金额"特殊逻辑

    功能：
    1. 查找包含"向您支付的金额"的文本块
    2. 在特定的X和Y坐标范围内查找对应的金额块
    3. 标记找到的金额块为已处理

    参数：
        text_info: 普通文本字段集合
        amount_infos: 金额字段集合
        processed_amounts: 已处理的金额块索引集合

    返回：
        Tuple[Optional[TextInfo], Optional[TextInfo]]: 
        - payment_text_info: 找到的"向您支付的金额"文本块，未找到则为None
        - payment_amount_info: 对应的金额块，未找到则为None
    """
    payment_text_info = None
    payment_amount_info = None

    # 查找"向您支付的金额"文本
    #for text_info in text_infos:
    if "向您支付的金额" in text_info.text and text_info.center_y < PAYMENT_AMOUNT_Y_THRESHOLD:
        payment_text_info = text_info
        logger.debug(f"找到'向您支付的金额'文本: Y={text_info.center_y}")
        # break

    # 如果找到，则查找对应的金额
    if payment_text_info:
        target_x = payment_text_info.left_bottom_x
        target_y = payment_text_info.center_y + PAYMENT_OFFSET_Y
        target_x_range = (target_x - PAYMENT_OFFSET_X_TOLERANCE, target_x + PAYMENT_OFFSET_X_TOLERANCE)
        target_y_range = (target_y - Y_TOLERANCE_DEFAULT, target_y + Y_TOLERANCE_DEFAULT)

        # 在amount_infos中查找匹配的金额块
        for i, amount_info in enumerate(amount_infos):
            x_match = target_x_range[0] <= amount_info.left_bottom_x <= target_x_range[1]
            y_match = payment_text_info.center_y <= amount_info.center_y <= target_y_range[1]

            if x_match and y_match:
                # 记录找到的金额块
                payment_amount_info = amount_info
                # 标记为已处理
                processed_amounts.add(i)
                logger.info(f"找到'向您支付的金额'对应的金额: {amount_info.text}")
                break

    return payment_text_info, payment_amount_info


def merge_text_blocks(
    ocr_results: List[Tuple],
    y_tolerance: int = Y_TOLERANCE_DEFAULT
) -> Tuple[str, List[List[str]]]:
    """智能合并文本块，实现分层结构化的板块合并

    核心功能：
    1. 将原始OCR识别结果转换为结构化的TextInfo对象集合
    2. 识别并分离金额字段和普通文本字段
    3. 根据Y坐标容差将文本与金额进行配对
    4. 特殊处理"向您支付的金额"及其对应金额值
    5. 检测PDF的板块结构（销售、退款、调整等）
    6. 生成格式化输出，保持原始顺序

    算法流程：
    1. 解析OCR结果为TextInfo集合
    2. 分离金额字段和非金额字段
    3. 处理"向您支付的金额"特殊逻辑
    4. 按Y坐标从小到大遍历text_infos
    5. 对每个text_info查找Y坐标匹配的amount_infos
    6. 多个金额匹配时按Y中心坐标最接近排序
    7. 处理剩余未匹配的金额
    8. 检测板块边界，格式化输出

    参数说明：
        ocr_results (List[Tuple]): OCR识别结果列表，格式：[(box, (text, confidence)), ...]
        y_tolerance (int): Y坐标容差范围，默认15像素

    返回值：
        Tuple[str, List[TextInfo]]:
        - 第一元素：合并后的文本字符串，多行用\n分隔，每行格式为'文本1','金额1'或'文本1'
        - 第二元素：所有处理过的TextInfo对象列表

    异常处理：
        - 空OCR结果：返回("", [])
        - 无效OCR项：记录warning，跳过，继续处理
        - 处理异常：返回("", [])
    """
    # ===== 步骤1：输入验证 =====
    if not ocr_results:
        logger.warning("OCR结果为空")
        return "", []

    try:
        # ===== 步骤2：解析所有OCR结果为TextInfo集合 =====
        all_text_infos = []
        for result in ocr_results:
            try:
                text_info = _parse_ocr_result(result)
                all_text_infos.append(text_info)
            except ValueError as e:
                logger.warning(f"跳过无效的OCR结果: {e}")
                continue

        # 验证是否有有效结果
        if not all_text_infos:
            logger.error("没有有效的OCR结果")
            return "", []

        logger.debug(f"成功解析 {len(all_text_infos)} 个OCR结果")

        # ===== 步骤3：分离金额字段和普通文本字段 =====
        amount_infos = []  # 金额字段集合
        text_infos = []    # 普通文本字段集合
        
        # 第1行强制放在text_infos中，不考虑是否为金额
        if all_text_infos:
            text_infos.append(all_text_infos[0])
            # 处理剩余行
            for info in all_text_infos[1:]:
                if info.is_amount():
                    amount_infos.append(info)
                else:
                    text_infos.append(info)
        
        #logger.info(f"普通文本块:\n{chr(10).join([str(x) for x in text_infos])}")
        #logger.info(f"金额块:\n{chr(10).join([str(x) for x in amount_infos])}")

        logger.debug(f"分离完成 - 普通文本块: {len(text_infos)}, 金额块: {len(amount_infos)}")

        # ===== 步骤4：特殊处理"向您支付的金额" =====
        processed_amounts = set()  # 记录已处理的金额块索引

        text_infos_sorted = text_infos

        # ===== 步骤6：遍历text_infos进行Y坐标匹配（核心行合并） =====
        merged_lines = []  # 存储合并后的行数据
        class_id='header'
        for text_info in text_infos_sorted:
            # 创建行数据
            line_data = [text_info]
            line_data.append(class_id)
            if "," not in line and i>2:
            if text_info.text.strip() == "向您支付的金额" and text_info.center_y < PAYMENT_AMOUNT_Y_THRESHOLD:
                # 特殊处理："向您支付的金额"及其对应金额
                payment_text_info, payment_amount_info = _process_payment_amount(text_info, amount_infos, processed_amounts)
                if payment_amount_info:
                    line_data.append(payment_amount_info)
            else:
                # 普通文本块：查找匹配金额
                matched_amount = _get_matching_amount(text_info, amount_infos, processed_amounts, y_tolerance)
                if matched_amount:
                    line_data.append(matched_amount)

            merged_lines.append(line_data)


        logger.debug(f"合并完成 - 生成 {len(merged_lines)} 行数据")

        # ===== 步骤8：检测板块边界 + 格式化输出 =====
        output_lines = []
        current_block = None

        for line_data in merged_lines:
            # 检测板块边界
            line_text = ''.join([info.text for info in line_data])
            detected_block = _detect_block_boundary(line_text)

            # 如果板块发生变化，需要输出板块标题
            if detected_block != current_block and detected_block != "HEADER":
                current_block = detected_block
                # 输出板块标题（只输出第一次出现的板块标题行）
                # 这里的line_data本身就是板块标题
            elif detected_block != "HEADER":
                current_block = detected_block

            # 格式化当前行
            line_str = _format_line(line_data)
            output_lines.append(line_str)

        # ===== 生成最终结果 =====
        result_text = '\n'.join(output_lines)
        logger.info(f"文本块合并处理完成，共 {len(output_lines)} 行")
        text_infos=jg_structured_data(output_lines)
        logger.info(f"结构化数据提取完成，共 {text_infos} 行")
        
        return result_text, text_infos

    # ===== 全局异常处理 =====
    except Exception as e:
        logger.error(f"文本块合并失败: {e}", exc_info=True)
        return "", []


def parse_category_data(data: List[Any], default_category: str = 'header') -> List[List[str]]:
    """将分类数据转换为 [分类, 字段, 数值] 格式

    数据结构说明：
    - 单个字符串：表示新的分类头
    - 两个元素的元组/列表：表示当前分类下的明细（字段, 数值）

    参数说明：
        data (List[Any]): 输入数据列表
            - str: 分类名称
            - Tuple[str, str] 或 List[str]: [字段, 数值]
        default_category (str): 初始分类名称，默认为 'hd'

    返回值：
        List[List[str]]: 格式为 [分类, 字段, 数值] 的二维列表

    示例：
        输入: [('xxx', '2233'), ('www', '34'), 'aaa', ('a111', '23'), ('a13', '32'), 'bbb', ('err', '12')]
        输出: [['hd', 'xxx', '2233'], ['hd', 'www', '34'], ['aaa', 'a111', '23'],
               ['aaa', 'a13', '32'], ['bbb', 'err', '12']]

    异常处理：
        ValueError: 当明细数据前没有分类且没有默认分类时抛出
    """
    
    # 初始化结果列表，用于存储转换后的数据
    # 每个元素格式为: [分类名称, 字段名, 数值]
    result = []
    
    # 设置当前分类为默认分类
    # 在遇到第一个分类字符串之前，所有明细都属于这个默认分类
    current_category = default_category
    
    # 遍历输入数据列表中的每个元素
    for item in data:
        # 情况1: 元素是字符串类型
        # 判断逻辑: 使用 isinstance() 检查 item 是否为 str 类型
        # 处理: 将该字符串作为新的分类名称
        if isinstance(item, str):
            # 更新当前分类为新的分类名称
            # 之后的所有明细数据都将归属于这个新分类，直到再次遇到分类字符串
            current_category = item
            # 记录调试日志，便于追踪分类切换过程
            logger.debug(f"设置当前分类: {current_category}")
        
        # 情况2: 元素是列表或元组，且长度为2
        # 判断逻辑: 
        #   - isinstance(item, (list, tuple)): 检查是否为列表或元组类型
        #   - len(item) == 2: 检查长度是否为2（确保是 [字段, 数值] 格式）
        # 处理: 将该明细数据添加到当前分类下
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            # 安全检查: 确保当前分类已设置
            # 如果 current_category 为 None，说明在第一个分类字符串之前就遇到了明细数据
            # 这是不合法的数据格式，需要抛出异常
            if current_category is None:
                raise ValueError(f"明细数据 {item} 前必须有分类")
            
            # 将明细数据转换为 [分类, 字段, 数值] 格式并添加到结果列表
            # item[0]: 字段名称（明细的第一个元素）
            # item[1]: 数值（明细的第二个元素）
            result.append([current_category, item[0], item[1]])
            # 记录调试日志，便于追踪明细添加过程
            logger.debug(f"添加明细: [{current_category}, {item[0]}, {item[1]}]")
        
        # 情况3: 元素不符合上述任何格式
        # 可能的情况: 
        #   - None 值
        #   - 长度不为2的列表/元组
        #   - 其他数据类型（如数字、字典等）
        # 处理: 记录警告日志并跳过该元素，不中断处理流程
        else:
            logger.warning(f"跳过无效数据: {item}")
    
    # 返回转换后的结果列表
    # 列表中每个元素都是 [分类, 字段, 数值] 格式的子列表
    return result


def jg_structured_data(text_lines: List[str]) -> List[str，Dict[str, Any]]:
        """从文本行中提取结构化数据.
        
        基于文本内容和格式，提取关键字和对应的值，形成结构化数据.
        
        Args:
            text_lines: 文本行列表，每个元素包含text、confidence、bbox、y等字段
            
        Returns:
            Dict[str, Any]: 结构化数据字典
        """
        import time
        logger.info("开始提取结构化数据")
        
        try:
        #     # 初始化结构化数据
        #     structured_data = {
        #         "classdata": {
        #             "text_lines": text_lines,
        #             "key_value_pairs": {},
        #             "category_details": []  # 存储最终的类别+明细
        #         },
        #         "metadata": {
        #             "line_count": len(text_lines),
        #             "category_count": 0,
        #             "detail_count": 0,
        #             "processing_time": time.strftime("%Y-%m-%d %H:%M:%S")
        #         }
        #     }

            # 核心解析逻辑
            structured_data=[]  #返回合并的数据
            current_category = "header"  # 临时存储当前类别名
            current_details = []   # 临时存储当前类别的明细

            for i, line_dict in enumerate(text_lines, start=1):
                line = line_dict    #["text"]  # 从字典中获取文本内容
                
                # ---- 判断1：是【类别行】（纯字符串，无逗号） ----
                if "," not in line and i>2:
                    # 如果不是第一个类别，先把上一个类别的数据存入结构体
                    if current_category and current_details:
                        structured_data["classdata"]["category_details"].append({
                            "类别名称": current_category,
                            "明细列表": current_details
                        })
                    # 切换为新的类别
                    current_category = line
                    current_details = []  # 清空明细，准备存新类别的数据
                # ---- 判断2：是【明细行】（有逗号，字段名+金额） ----
                else:
                    if "向您支付的金额" in line.strip() and i>15:
                        # 如果不是第一个类别，先把上一个类别的数据存入结构体
                        if current_category and current_details:
                            structured_data["classdata"]["category_details"].append({
                                "类别名称": current_category,
                                "明细列表": current_details
                            })
                        # 切换为新的类别
                        current_category = "footer"
                        current_details = []  # 清空明细，准备存新类别的数
                    else:
                        # 解析明细行：剔除单引号 + 分割字段名和金额
                        field_name, amount_str = line.replace("'", "").split(",")
                        # 金额转数值类型(float)，并去除首尾空格（防止格式不规范）
                        amount = float(amount_str.strip())
                        # 把解析后的明细存入临时列表
                        current_details.append({
                            "字段名": field_name.strip(),
                            "金额": amount
                        })

            # ---- 处理最后一个类别的数据（循环结束后，最后一个类别还没存入） ----
            if current_category and current_details:
                structured_data["classdata"]["category_details"].append({
                    "类别名称": current_category,
                    "明细列表": current_details
                })

            # ========== 4. 自动更新元数据统计信息 ==========
            structured_data["metadata"]["category_count"] = len(structured_data["classdata"]["category_details"])
            # 统计所有明细的总行数
            total_detail = sum(len(item["明细列表"]) for item in structured_data["classdata"]["category_details"])
            structured_data["metadata"]["detail_count"] = total_detail
                    
            #logger.info(f"成功提取 {len(structured_data['key_value_pairs'])} 个键值对")
            return structured_data
        except Exception as e:
            logger.error(f"提取结构化数据失败: {e}")
            # 返回部分数据，而不是空字典
            return structured_data

