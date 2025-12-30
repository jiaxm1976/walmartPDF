# ============================================================
# 文件: backend/app/services/direct_keyword_extractor.py
# 功能: 直接基于关键词定位提取数据（不做板块切分）
# 作者: 开发团队
# 创建时间: 2025-12-18
# 说明: 新策略 - 在完整左侧图片上根据关键词Y坐标范围直接提取数据
# ============================================================

import logging
import re
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

try:
    from app.services.ocr_engine import OCREngine
except ImportError:
    from backend.app.services.ocr_engine import OCREngine

logger = logging.getLogger(__name__)


class DirectKeywordExtractor:
    """直接基于关键词定位的数据提取器.

    新策略：
    1. OCR识别整个左侧图片，获取所有文本块和坐标
    2. 识别7个板块关键词的Y坐标
    3. 根据Y坐标范围，将文本块归类到对应板块
    4. 提取各板块的键值对数据
    5. 无需切分图片，避免边界问题

    优势：
    - 消除板块切分的边界误差
    - 统一使用Vision OCR的原始坐标
    - 更直观的坐标映射关系
    """

    # 板块关键词（按Y坐标从上到下排序）
    SECTION_KEYWORDS = [
        ('header', '回款等待'),
        ('sales', '销售'),
        ('refund', '退款'),
        ('adjustment', '调整'),
        ('wfs', '沃尔玛商品服务'),
        ('other', '其他活动'),
        ('footer', '向您支付的金额')
    ]

    def __init__(self, ocr_engine: OCREngine = None):
        """初始化提取器.

        Args:
            ocr_engine: OCR引擎实例，如果为None则创建新实例（低置信度阈值）
        """
        if ocr_engine is None:
            # 创建低置信度阈值的OCR引擎，确保识别到所有文字（包括模糊的）
            self.ocr_engine = OCREngine(confidence_threshold=0.3)
        else:
            self.ocr_engine = ocr_engine
        logger.info("=" * 60)
        logger.info("初始化直接关键词定位提取器")
        logger.info("=" * 60)


    def recognize_full_image(
        self,
        image: np.ndarray
    ) -> List[Dict[str, Any]]:
        """OCR识别整个左侧图片，返回所有文本块.

        Args:
            image: 左侧图片（numpy数组）

        Returns:
            List[Dict]: 文本块列表
                [
                    {
                        'text': '销售',
                        'box': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
                        'confidence': 0.95,
                        'x_left': 50,
                        'x_right': 200,
                        'y_top': 300,
                        'y_bottom': 350,
                        'y_center': 325
                    },
                    ...
                ]
        """
        logger.info("开始OCR识别完整左侧图片")

        # 调用OCR引擎
        ocr_results = self.ocr_engine.recognize_image(image)

        # 解析OCR结果，提取详细坐标信息
        text_blocks = []
        for box, (text, confidence) in ocr_results:
            # 提取四角坐标
            x_left = int(box[0][0])
            x_right = int(box[1][0])
            y_top = int(box[0][1])
            y_bottom = int(box[2][1])

            # 计算中心坐标
            y_center = int((y_top + y_bottom) / 2)

            text_blocks.append({
                'text': text.strip(),
                'box': box,
                'confidence': confidence,
                'x_left': x_left,
                'x_right': x_right,
                'y_top': y_top,
                'y_bottom': y_bottom,
                'y_center': y_center
            })

        logger.info(f"识别完成，共检测到 {len(text_blocks)} 个文本块")
        return text_blocks


    def find_keyword_positions(
        self,
        text_blocks: List[Dict[str, Any]],
        image_height: int = None
    ) -> Dict[str, int]:
        """从文本块中查找关键词Y坐标.

        Args:
            text_blocks: 文本块列表
            image_height: 图片高度（用于过滤Footer误识别）

        Returns:
            Dict[str, int]: 板块名 -> Y坐标（使用y_top作为参考）
                {
                    'header': 514,
                    'sales': 675,
                    'refund': 1380,
                    ...
                }
        """
        logger.info("查找板块关键词Y坐标")

        # 如果没有传入image_height，从text_blocks推测
        if image_height is None:
            image_height = max(b['y_bottom'] for b in text_blocks) + 100

        keyword_positions = {}

        for section_name, keyword in self.SECTION_KEYWORDS:
            # 在文本块中查找关键词
            found = False
            for block in text_blocks:
                text = block['text']

                # 精确匹配或包含匹配
                is_match = False

                if section_name == 'header' and text == keyword:
                    is_match = True
                elif section_name == 'sales' and (text == keyword or text.startswith(keyword)):
                    is_match = True
                elif section_name == 'refund' and (text == keyword or text.startswith(keyword)):
                    is_match = True
                elif section_name == 'adjustment' and text.startswith(keyword):
                    is_match = True
                elif section_name == 'wfs' and (keyword in text or '沃尔玛配送服务' in text):
                    is_match = True
                elif section_name == 'other' and keyword in text:
                    is_match = True
                elif section_name == 'footer' and '向您支付' in text:
                    is_match = True

                if is_match:
                    # ⭐ 使用y_top（左上角Y坐标）作为参考
                    # 原因：板块范围应从关键词标题的顶部开始
                    y_coord = block['y_top']

                    # 对于footer，取Y坐标最大的（最靠下的那个）
                    if section_name == 'footer':
                        # ⭐ 过滤掉图片上半部分的误识别
                        # Footer关键词必须在图片下半部分（>50%高度）
                        if y_coord < image_height * 0.5:
                            logger.warning(f"  [{section_name}] 跳过误识别（在图片上半部分）: Y={y_coord} < {image_height*0.5:.0f}")
                            continue

                        if section_name not in keyword_positions:
                            keyword_positions[section_name] = y_coord
                            logger.info(f"  [{section_name}] '{keyword}' (或变体) 初始 -> Y_top={y_coord}")
                        else:
                            # 使用max()确保取最大值（最靠下的那个）
                            old_y = keyword_positions[section_name]
                            keyword_positions[section_name] = max(old_y, y_coord)
                            if y_coord > old_y:
                                logger.info(f"  [{section_name}] '{keyword}' (或变体) 更新 -> Y_top={y_coord} (旧值={old_y})")
                            else:
                                logger.debug(f"  [{section_name}] 跳过较小的Y坐标 {y_coord} (当前最大={old_y})")
                    else:
                        keyword_positions[section_name] = y_coord
                        logger.info(f"  [{section_name}] '{keyword}' -> Y_top={y_coord}")

                    found = True
                    if section_name != 'footer':
                        break  # 找到第一个匹配即可（footer需要找最下面的）

            if not found:
                logger.warning(f"  [{section_name}] 未找到关键词 '{keyword}'")

        logger.info(f"关键词定位完成，共找到 {len(keyword_positions)} 个板块")
        return keyword_positions


    def calculate_section_ranges(
        self,
        keyword_positions: Dict[str, int],
        image_height: int
    ) -> Dict[str, Tuple[int, int]]:
        """计算每个板块的Y坐标范围（基于关键词Y坐标）.

        策略：
        - 每个板块从上一个关键词的Y坐标开始，到本板块关键词的Y坐标+扩展范围结束
        - 扩展范围：用于包含关键词下方的内容（如"总计"行）

        Args:
            keyword_positions: 关键词Y坐标字典
            image_height: 图片总高度

        Returns:
            Dict[str, Tuple[int, int]]: 板块名 -> (起始Y, 结束Y)
        """
        logger.info("计算板块Y坐标范围（新策略）")

        # 获取所有关键词Y坐标并排序
        sorted_sections = []
        for section_name, keyword in self.SECTION_KEYWORDS:
            if section_name in keyword_positions:
                sorted_sections.append((section_name, keyword_positions[section_name]))

        sorted_sections.sort(key=lambda x: x[1])  # 按Y坐标排序

        # 计算每个板块的范围
        section_ranges = {}

        for i, (section_name, keyword_y) in enumerate(sorted_sections):
            # 确定起始Y
            if i == 0:
                # 第一个板块：从图片顶部开始
                start_y = 0
            else:
                # 其他板块：从上一个板块的结束Y开始（无缝拼接）
                prev_section_name = sorted_sections[i - 1][0]
                start_y = section_ranges[prev_section_name][1]

            # 确定结束Y
            if i == len(sorted_sections) - 1:
                # 最后一个板块（footer）：
                # 扩展1000px（包含"向您支付的金额"和"期末余额"两个大字段）
                # 注意："期末余额"通常在"向您支付的金额"下方200-400px处
                # 为了确保不遗漏，使用较大的扩展范围
                FOOTER_EXTENSION = 1000
                end_y = min(image_height, keyword_y + FOOTER_EXTENSION)
            else:
                # 其他板块：扩展到下一个关键词Y坐标
                # 这样可以包含本板块的所有明细项和"总计"行
                next_keyword_y = sorted_sections[i + 1][1]
                end_y = next_keyword_y

            # 边界检查
            start_y = max(0, start_y)
            end_y = min(image_height, end_y)

            section_ranges[section_name] = (start_y, end_y)
            height = end_y - start_y
            logger.info(f"  [{section_name}] 范围: [{start_y}, {end_y}) = {height}px")

        logger.info(f"范围计算完成，共{len(section_ranges)}个板块")
        return section_ranges


    def classify_text_blocks_by_range(
        self,
        text_blocks: List[Dict[str, Any]],
        section_ranges: Dict[str, Tuple[int, int]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """将文本块归类到对应的板块范围.

        Args:
            text_blocks: 所有文本块列表
            section_ranges: 板块Y坐标范围字典

        Returns:
            Dict[str, List]: 板块名 -> 该板块的文本块列表
        """
        logger.info("将文本块归类到板块")

        classified_blocks = {section: [] for section in section_ranges.keys()}

        for block in text_blocks:
            # 使用y_bottom判断文本块属于哪个板块
            y_coord = block['y_bottom']

            # 遍历板块范围，找到包含该文本块的板块
            for section_name, (start_y, end_y) in section_ranges.items():
                if start_y <= y_coord < end_y:
                    classified_blocks[section_name].append(block)
                    break

        # 记录每个板块的文本块数量
        for section_name, blocks in classified_blocks.items():
            logger.info(f"  [{section_name}] 文本块数量: {len(blocks)}")

        return classified_blocks


    def extract_key_value_pairs(
        self,
        blocks: List[Dict[str, Any]],
        section_name: str
    ) -> Dict[str, str]:
        """从文本块中提取键值对.

        策略：
        1. 将Y坐标相近的文本块合并为一行（阈值30px）
        2. 解析每行的键值对（"标签 金额"）
        3. 支持多种金额格式：$ 或 美元
        4. header板块特殊处理：提取日期范围

        Args:
            blocks: 文本块列表
            section_name: 板块名称（用于日志）

        Returns:
            Dict[str, str]: 键值对字典
        """
        logger.info(f"  [{section_name}] 提取键值对")

        # Step 1: 按Y坐标排序
        sorted_blocks = sorted(blocks, key=lambda x: x['y_bottom'])

        # Step 2: 合并Y坐标相近的文本块（阈值30px）
        Y_THRESHOLD = 30
        merged_lines = []
        i = 0

        while i < len(sorted_blocks):
            current_block = sorted_blocks[i]
            line_blocks = [current_block]

            # 查找Y坐标相近的其他块
            j = i + 1
            while j < len(sorted_blocks):
                next_block = sorted_blocks[j]
                if abs(next_block['y_bottom'] - current_block['y_bottom']) <= Y_THRESHOLD:
                    line_blocks.append(next_block)
                    j += 1
                else:
                    break

            # 按X坐标排序
            line_blocks.sort(key=lambda x: x['x_left'])

            # 合并文本
            merged_text = ' '.join([b['text'] for b in line_blocks])
            merged_lines.append(merged_text)

            i = j

        # Step 3: 解析键值对
        data = {}

        # Header板块特殊处理：提取日期范围
        if section_name == 'header':
            for line in merged_lines:
                # 匹配格式: "2024年12月6日 - 2025年1月11日"
                date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)\s*[-−]\s*(\d{4}年\d{1,2}月\d{1,2}日)', line)
                if date_match:
                    data['开始日期'] = date_match.group(1)
                    data['结束日期'] = date_match.group(2)
                    logger.info(f"    识别到日期范围: {data['开始日期']} - {data['结束日期']}")
                    break

        # 通用键值对提取
        for line in merged_lines:
            # 提取金额
            amount_value = self._extract_amount_from_text(line)

            if amount_value:
                # 移除金额部分，剩下的就是标签
                key_part = line
                # 删除$格式金额
                key_part = re.sub(r'[-−]?\s*[$＄]\s*\d+[,\d]*\.?\d*', '', key_part)
                # 删除"美元"格式金额
                key_part = re.sub(r'[-−]?\s*\d+[,\d]*\.?\d*\s*美元', '', key_part)
                key_part = key_part.strip()

                if key_part:
                    # 规范化键名（去除冒号）
                    key_part = key_part.replace(':', '').replace('：', '').strip()
                    data[key_part] = amount_value

        logger.info(f"  [{section_name}] 提取到 {len(data)} 个字段")
        return data


    def _extract_amount_from_text(self, text: str) -> Optional[str]:
        """从文本中提取金额.

        支持格式：
        - "$ 1,654.40" 或 "-$ 1,654.40"
        - "1,654.40 美元" 或 "-1,654.40 美元"

        Args:
            text: 包含金额的文本

        Returns:
            Optional[str]: 提取的金额字符串（无逗号），如果未找到返回None
        """
        # 格式1: 美元符号格式
        dollar_pattern = r'([-−]?)\s*[$＄]\s*(\d+[,\d]*\.?\d*)'
        match = re.search(dollar_pattern, text)

        if match:
            sign = match.group(1).replace('−', '-')
            number = match.group(2).replace(',', '')
            return sign + number

        # 格式2: 中文美元格式
        yuan_pattern = r'([-−]?)\s*(\d+[,\d]*\.?\d*)\s*美元'
        match = re.search(yuan_pattern, text)

        if match:
            sign = match.group(1).replace('−', '-')
            number = match.group(2).replace(',', '')
            return sign + number

        return None


    def process_all_sections(
        self,
        image: np.ndarray
    ) -> Tuple[Dict[str, Any], Dict[str, int], Dict[str, Tuple[int, int]], List[Dict[str, Any]]]:
        """处理完整左侧图片，提取所有板块数据.

        Args:
            image: 左侧图片（numpy数组）

        Returns:
            Tuple:
                - 结构化数据字典
                - 关键词Y坐标字典（用于可视化）
                - 板块范围字典（用于可视化）
                - 所有文本块列表（用于可视化）
        """
        logger.info("=" * 60)
        logger.info("开始处理完整左侧图片（新策略）")
        logger.info("=" * 60)

        # Step 1: OCR识别整个图片
        text_blocks = self.recognize_full_image(image)

        # Step 2: 查找关键词Y坐标（传递image_height用于过滤Footer）
        image_height = image.shape[0]
        keyword_positions = self.find_keyword_positions(text_blocks, image_height)

        # Step 3: 计算板块范围
        section_ranges = self.calculate_section_ranges(keyword_positions, image_height)

        # Step 4: 将文本块归类到板块
        classified_blocks = self.classify_text_blocks_by_range(text_blocks, section_ranges)

        # Step 5: 提取各板块的键值对数据
        result = {}

        for section_name, blocks in classified_blocks.items():
            if blocks:
                section_data = self.extract_key_value_pairs(blocks, section_name)
                result[section_name] = section_data

        logger.info("=" * 60)
        logger.info(f"处理完成，共提取 {len(result)} 个板块数据")
        logger.info("=" * 60)

        return result, keyword_positions, section_ranges, text_blocks


# ============================================================
# END OF direct_keyword_extractor.py
# ============================================================
