# ============================================================
# 文件: backend/app/services/left_section_ocr.py
# 功能: 左侧板块OCR识别和数据提取
# 作者: 开发团队
# 创建时间: 2025-12-16
# 说明: Step 5 - OCR识别各左侧板块并提取结构化数据输出JSON
# ============================================================

import logging
import re
import json
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import cv2
import numpy as np

from backend.app.services.ocr_engine import OCREngine
from backend.app.utils.text_formatter import merge_text_blocks


logger = logging.getLogger(__name__)


class LeftSectionOCR:
    """左侧板块OCR识别和数据提取器.

    对Step 4切分的7个左侧板块图片进行OCR识别，
    提取结构化数据并输出JSON格式。

    板块类型：
    - header: 头部信息（期初余额、备用金、回款等待）
    - sales: 销售明细
    - refund: 退款明细
    - adjustment: 调整明细
    - wfs: 沃尔玛商品服务明细
    - other: 其他活动明细
    - footer: 尾部信息（向您支付的金额、期末余额）
    """

    def __init__(self, ocr_engine: OCREngine):
        """初始化OCR识别器.

        Args:
            ocr_engine: OCR引擎实例
        """
        self.ocr_engine = ocr_engine
        logger.info("=" * 60)
        logger.info("初始化左侧板块OCR识别器")
        logger.info("=" * 60)


    def extract_text_lines(self, image: np.ndarray) -> List[Tuple[str, float]]:
        """从图片中提取文本行.

        OCR可能将同一行文本分成多个块（如标签和金额分开）。
        本函数将Y坐标相近的文本块合并为一行。

        Args:
            image: 输入图片（numpy数组）

        Returns:
            List[Tuple[str, float]]: 文本行列表 [(文本, Y坐标), ...]
                按Y坐标从上到下排序
        """
        # OCR识别
        ocr_results = self.ocr_engine.recognize_image(image)
        
        # 使用text_formatter中的merge_text_blocks函数合并文本块
        merged_text, text_infos = merge_text_blocks(ocr_results, y_tolerance=15)
        
        # 将合并后的文本字符串转换为List[Tuple[str, float]]格式
        text_lines = []
        if merged_text:
            lines = merged_text.split('\n')
            for line in lines:
                if line.strip():
                    # 使用正则提取单引号内的文本块，避免把金额中的千位分隔符（逗号）错误拆分
                    # 之前的实现使用 line.split(',') 会将 "'$1,868.55'" 拆成 ["'$1", "868.55'"],
                    # 导致金额解析丢失高位数字。改为提取引号内内容保持金额完整性。
                    text_blocks = re.findall(r"'([^']*)'", line)
                    # 合并为一个字符串（用空格分隔原始块顺序）
                    merged_line_text = ' '.join(tb.strip() for tb in text_blocks)
                    # 计算该行的Y坐标（取所有文本块的中心Y坐标平均值）
                    line_y = sum(info.center_y for info in text_infos) / len(text_infos) if text_infos else 0.0
                    text_lines.append((merged_line_text, line_y))
        
        # 按Y坐标排序
        text_lines.sort(key=lambda x: x[1])
        
        return text_lines

    def extract_text_blocks(self, image: np.ndarray) -> List[str]:
        """从图片中提取文本块，只返回文本内容，不包含坐标信息.

        Args:
            image: 输入图片（numpy数组）

        Returns:
            List[str]: 文本块列表
        """
        # 使用新的recognize_image_text方法获取文本块
        text_blocks = self.ocr_engine.recognize_image_text(image)
        
        logger.info(f"\n===== extract_text_blocks返回值 =====")
        logger.info(f"文本块数量: {len(text_blocks)}")
        for i, text in enumerate(text_blocks):
            logger.info(f"文本块 {i+1}: {text}")
        logger.info("====================================\n")
        
        return text_blocks
        # OCR识别
        ocr_results = self.ocr_engine.recognize_image(image)
        
        # 输出recognize_image函数的返回值
        logger.info("\n===== recognize_image函数返回值 =====")
        logger.info(f"OCR结果数量: {len(ocr_results)}")
        for i, (box, (text, confidence)) in enumerate(ocr_results):
            logger.info(f"结果 {i+1}:")
            logger.info(f"  文本: {text}")
            logger.info(f"  置信度: {confidence:.2f}")
            logger.info(f"  坐标框: {box}")
        logger.info("====================================\n")

        # 提取文本、X坐标和Y坐标
        text_blocks = []
        for box, (text, confidence) in ocr_results:
            # 计算X坐标（左边界）和Y坐标（基线）
            x_coord = int(box[0][0])  # 左上角X
            # 实验方案A：使用底部Y坐标（基线）替代几何中心
            # 原代码：y_coord = int((box[0][1] + box[2][1]) / 2)  # Y中心
            # 新代码：使用底部Y坐标，因为同一行文本的底部对齐更稳定
            #        负号不会影响底部位置，只会影响顶部位置
            y_coord = int(box[2][1])  # Y底部（基线）
            text_blocks.append((text, x_coord, y_coord))

        # 按Y坐标排序
        text_blocks.sort(key=lambda x: x[2])

        # 合并Y坐标相近的文本块（阈值：30像素）
        Y_THRESHOLD = 30
        merged_lines = []
        i = 0

        while i < len(text_blocks):
            current_text, current_x, current_y = text_blocks[i]
            line_blocks = [(current_text, current_x)]

            # 查找Y坐标相近的其他块
            j = i + 1
            while j < len(text_blocks):
                next_text, next_x, next_y = text_blocks[j]
                if abs(next_y - current_y) <= Y_THRESHOLD:
                    line_blocks.append((next_text, next_x))
                    j += 1
                else:
                    break

            # 按X坐标排序（从左到右）
            line_blocks.sort(key=lambda x: x[1])

            # 合并文本（用空格连接）
            merged_text = ' '.join([text for text, _ in line_blocks])
            merged_lines.append((merged_text, current_y))

            i = j

        return merged_lines


    def post_process_total(
        self,
        data: Dict[str, str],
        text_lines: List[Tuple[str, float]],
        section_name: str = ""
    ) -> Dict[str, str]:
        """智能后处理：补充缺失的总计字段.

        OCR有时无法识别"总计:"标签，但能识别金额。
        本函数检测最后一行是否只有孤立的金额，如果是则自动补充"总计"字段。

        处理逻辑：
        1. 如果已有"总计"/"总计:"/"总计："字段，直接返回
        2. 检查文本行的最后一行是否只包含金额（格式：数字+美元）
        3. 如果是孤立金额，补充"总计"字段
        4. 通过求和验证（可选）确认是否为总计

        Args:
            data: 已提取的键值对数据
            text_lines: 原始文本行列表
            section_name: 板块名称（用于日志）

        Returns:
            Dict: 补充后的数据

        Example:
            输入text_lines最后一行: ("-60.67 美元", 596)
            输入data: {"产品价格": "-65.55", "运输": "0.00", ...}
            输出data: {"产品价格": "-65.55", "运输": "0.00", ..., "总计": "-60.67"}
        """
        # 1. 检查是否已有总计字段
        total_keys = ['总计', '总计:', '总计：']
        if any(key in data for key in total_keys):
            logger.debug(f"  [{section_name}] 已有总计字段，无需后处理")
            return data

        # 1.5. 检查最后一个字段是否为总计等价物
        # 某些板块使用"总折扣"、"WFS总折扣"等表示总计
        total_equivalent_keywords = ['总折扣', 'WFS总折扣', 'WFS 总折扣']
        if data:
            last_key = list(data.keys())[-1]
            for keyword in total_equivalent_keywords:
                if keyword in last_key:
                    # 将该字段重命名为"总计"
                    last_value = data.pop(last_key)
                    data['总计'] = last_value
                    logger.info(f"  ✓ [{section_name}] 智能后处理：检测到总计等价物'{last_key}'，规范化为'总计' = {last_value}")
                    return data

        # 2. 检查是否有文本行
        if not text_lines or len(text_lines) == 0:
            logger.debug(f"  [{section_name}] 无文本行，跳过后处理")
            return data

        # 3. 检查最后一行是否只有金额，或者最后一行是否是"总计："标签
        last_line_text = text_lines[-1][0].strip()

        # 情况A: 最后一行只有金额
        # 尝试两种格式：$格式和"美元"格式
        amount_value = self._extract_amount_from_text(last_line_text)
        # 检查是否是纯金额（不包含其他文字）
        is_pure_amount = False
        if amount_value:
            # 移除金额后检查是否还有其他文字
            temp = last_line_text
            temp = re.sub(r'[-−]?[$＄]\d+[,\d]*\.?\d*', '', temp)
            temp = re.sub(r'[-−]?\d+[,\d]*\.?\d*美元', '', temp)
            is_pure_amount = len(temp.strip()) == 0

        if amount_value and is_pure_amount:
            # 补充总计字段（amount_value已经在上面提取）
            data['总计'] = amount_value
            logger.info(f"  ✓ [{section_name}] 智能后处理：检测到孤立金额，补充总计字段 = {amount_value}")

            # 可选：验证是否为总计（通过求和）
            self._verify_total_if_possible(data, amount_value, section_name)

        # 情况B: 最后一行是"总计："标签，但没有金额（OCR未识别到金额）
        elif '总计' in last_line_text and not self._extract_amount_from_text(last_line_text):
            # 通过求和明细项计算总计
            total_value = self._calculate_total_from_details(data, section_name)
            if total_value is not None:
                data['总计'] = str(total_value)
                logger.info(f"  ✓ [{section_name}] 智能后处理：检测到总计标签但缺金额，通过求和计算 = {total_value}")
            else:
                logger.warning(f"  ⚠️  [{section_name}] 检测到总计标签但无法计算：明细项不足")
        else:
            logger.debug(f"  [{section_name}] 最后一行不符合后处理条件，跳过: {last_line_text}")

        return data


    def _extract_amount_from_text(self, text: str) -> Optional[str]:
        """从文本中提取金额（支持中英文两种格式）.

        支持的格式：
        1. 中文格式: "1,654.40 美元" 或 "-1,654.40 美元"
        2. 英文格式: "$ 1,654.40" 或 "-$ 1,654.40" 或 "$1,654.40"
        3. 混合格式: "-$1,654.40" 或 "- $ 1,654.40"

        Args:
            text: 包含金额的文本

        Returns:
            Optional[str]: 提取的金额字符串（如"-1654.40"），无逗号，有负号
                          如果未找到金额返回None

        Example:
            "$ 1,654.40" -> "1654.40"
            "-$ 1,654.40" -> "-1654.40"
            "1,654.40 美元" -> "1654.40"
            "-1,654.40 美元" -> "-1654.40"
        """
        # 统一的金额匹配正则（支持$和美元两种格式）
        # 策略：先尝试匹配$格式，再尝试匹配"美元"格式

        # 格式1: 美元符号格式（同时支持半角$和全角＄）
        # "$1,654.40" 或 "-$1,654.40" 或 "$1,654.40" 或 "-＄2.23"（预处理后无空格）
        dollar_pattern = r'([-−]?)[$＄](\d+[,\d]*\.?\d*)'
        match = re.search(dollar_pattern, text)

        if match:
            sign = match.group(1).replace('−', '-')
            number = match.group(2).replace(',', '')
            return sign + number

        # 格式2: 中文美元格式 "1,654.40美元" 或 "-1,654.40美元"（预处理后无空格）
        yuan_pattern = r'([-−]?)(\d+[,\d]*\.?\d*)美元'
        match = re.search(yuan_pattern, text)

        if match:
            sign = match.group(1).replace('−', '-')
            number = match.group(2).replace(',', '')
            return sign + number

        return None


    def _calculate_total_from_details(
        self,
        data: Dict[str, str],
        section_name: str
    ) -> Optional[float]:
        """通过求和明细项计算总计.

        Args:
            data: 包含明细项的数据
            section_name: 板块名称（用于日志）

        Returns:
            Optional[float]: 计算的总计值，如果无法计算则返回None
        """
        detail_values = []
        for key, value in data.items():
            if key not in ['总计', '总计:', '总计：']:
                try:
                    num_value = float(value.replace(',', ''))
                    detail_values.append(num_value)
                except (ValueError, AttributeError):
                    pass  # 跳过非数字字段

        if detail_values:
            total = sum(detail_values)
            # 保留2位小数
            return round(total, 2)
        return None


    def _verify_total_if_possible(
        self,
        data: Dict[str, str],
        detected_total: str,
        section_name: str
    ) -> None:
        """验证检测到的总计是否正确（通过求和明细项）.

        注意：这是一个辅助验证函数，仅用于日志输出，不影响最终结果。

        Args:
            data: 包含明细项的数据
            detected_total: 检测到的总计值
            section_name: 板块名称
        """
        try:
            # 提取所有明细项的金额（排除总计本身）
            detail_values = []
            for key, value in data.items():
                if key not in ['总计', '总计:', '总计：']:
                    # 尝试转换为数字
                    try:
                        num_value = float(value.replace(',', ''))
                        detail_values.append(num_value)
                    except (ValueError, AttributeError):
                        pass  # 跳过非数字字段

            # 计算总和
            if detail_values:
                calculated_sum = sum(detail_values)
                detected_value = float(detected_total.replace(',', ''))
                diff = abs(calculated_sum - detected_value)

                # 如果差异小于0.01（1分钱），认为验证通过
                if diff < 0.01:
                    logger.info(f"    ✓ 验证通过：求和={calculated_sum:.2f}, 检测={detected_value:.2f}")
                else:
                    logger.warning(f"    ⚠ 验证警告：求和={calculated_sum:.2f}, 检测={detected_value:.2f}, 差值={diff:.2f}")
        except Exception as e:
            logger.debug(f"    验证跳过（无法计算）: {e}")


    def extract_key_value_pairs(
        self,
        text_lines: List[Tuple[str, float]],
        extract_total_from_title: bool = False
    ) -> Dict[str, str]:
        """从文本行中提取键值对.

        解析模式：
        1. "标签 金额" -> {"标签": "金额"}（优先）
        2. "板块标题 金额" -> {"总计": "金额"}（如果extract_total_from_title=True）
        3. "总计:" + "金额" -> {"总计": "金额"}
        4. "标签" + "金额" (分两行) -> {"标签": "金额"}

        Args:
            text_lines: 文本行列表
            extract_total_from_title: 是否从板块标题行提取总计

        Returns:
            Dict[str, str]: 键值对字典
        """
        data = {}
        i = 0

        # 板块标题列表（包含各种变体，已预处理）
        section_titles = ['销售', '退款', '调整', '沃尔玛商品服务(WFS)', '沃尔玛商品服务', '沃尔玛配送服务(WFS)', '沃尔玛配送服务', '其他活动']

        while i < len(text_lines):
            # 对文本进行预处理：全角转半角、清除所有空格、小写转大写
            text = text_lines[i][0]

            # 处理板块标题行（如"销售 1,160.45美元" 或 "销售 $ 1,160.45"）
            if extract_total_from_title:
                # 检查是否是包含金额的板块标题行
                title_match = False
                for title in section_titles:
                    if text == title:  # 纯板块标题
                        i += 1
                        title_match = True
                        break
                    elif title in text and len(text) > len(title):  # 板块标题在文本中且后面有内容
                        # 检查是否有金额
                        value = self._extract_amount_from_text(text)
                        if value:
                            # 只有当总计字段尚未设置时才设置
                            if '总计' not in data:
                                logger.info(f"  ✓ 从板块标题行提取总计: {title} -> {value}")
                                data['总计'] = value
                            i += 1
                            title_match = True
                            break
                if title_match:
                    continue

            # 跳过纯板块标题（没有金额的）
            if text in section_titles:
                i += 1
                continue

            # 模式1（优先）: "标签 金额" 在同一行
            # 例如: "产品价格 1,355.89美元" 或 "产品价格 $ 1,355.89"
            # 所有明细项都在本行
            amount_value = self._extract_amount_from_text(text)
            if amount_value:
                # 移除金额部分，剩下的就是标签
                # 策略：依次尝试删除$格式和"美元"格式
                key_part = text
                # 删除$格式金额（包括负号）
                key_part = re.sub(r'[-−]?[$＄]\d+[,\d]*\.?\d*', '', key_part)
                # 删除"美元"格式金额（包括负号）
                key_part = re.sub(r'[-−]?\d+[,\d]*\.?\d*美元', '', key_part)
                key_part = key_part.strip()

                if key_part:  # 确保有标签
                    # 避免将其他字段错误识别为总计
                    if key_part not in ['总计', '总计:', '总计：']:
                        logger.info(f"  ✓ 提取键值对: {key_part} -> {amount_value}")
                        data[key_part] = amount_value
                    elif '总计' not in data:  # 只有当总计字段尚未设置时才设置
                        logger.info(f"  ✓ 从模式1提取总计: {key_part} -> {amount_value}")
                        data['总计'] = amount_value
                    i += 1
                    continue
                else:
                    # 孤立金额（没有标签），跳过该行
                    # 这种情况通常是OCR识别错误或重复识别
                    logger.warning(f"  ⚠️ 跳过孤立金额行（无标签）: {text}")
                    i += 1
                    continue

            # 模式2: "总计:" 或 "总计：" 或 "总计" + "金额"
            # 增强识别：支持"总计:"、"总计："、"总计"等多种格式
            # 统一规范化为"总计"（无冒号）
            if '总计' in text:
                # 只有当总计字段尚未设置时才处理
                if '总计' not in data:
                    logger.info(f"  ✓ 识别到总计标签行: {text}")
                    # 先尝试在同一行查找金额
                    value = self._extract_amount_from_text(text)
                    if value:
                        logger.info(f"  ✓ 从模式2提取总计: {text} -> {value}")
                        data['总计'] = value  # 统一使用"总计"（无冒号）
                        i += 1
                        continue
                    # 如果同一行没有金额，查找下一行
                    elif i + 1 < len(text_lines):
                        # 对下一行也应用预处理
                        next_text = text_lines[i + 1][0]
                        value = self._extract_amount_from_text(next_text)
                        if value:
                            logger.info(f"  ✓ 从模式2（跨行）提取总计: {text} + {next_text} -> {value}")
                            data['总计'] = value  # 统一使用"总计"（无冒号）
                            i += 2
                            continue
                # 如果总计已存在或无法提取金额，继续
                i += 1
                continue

            # 模式3: 标签和金额分两行（用于header/footer特殊字段）
            # 例如: "向您支付的金额" (第i行)
            #       "0.00美元" 或 "$ 0.00" (第i+1行，大字体)
            if i + 1 < len(text_lines):
                # 对下一行也应用预处理
                next_text = text_lines[i + 1][0]
                # 检查下一行是否是金额
                value = self._extract_amount_from_text(next_text)
                if value:
                    key = text
                    # 避免将其他字段错误识别为总计
                    if key not in ['总计', '总计:', '总计：']:
                        data[key] = value
                    elif '总计' not in data:  # 只有当总计字段尚未设置时才设置
                        data['总计'] = value
                    i += 2
                    continue

            i += 1

        return data


    def process_header_section(self, image: np.ndarray) -> Dict[str, Any]:
        """处理header板块.

        提取内容：
        - 开始日期
        - 结束日期
        - 期初余额
        - 备用金
        - 回款等待

        Args:
            image: header板块图片

        Returns:
            Dict: header数据
        """
        logger.info("处理header板块...")
        text_lines = self.extract_text_lines(image)

        data = {
            "开始日期": "",
            "结束日期": "",
            "期初余额": "0.00",
            "备用金": "0.00",
            "回款等待": "0.00"
        }

        # 提取对账单日期范围
        for text, _ in text_lines:
            # 匹配格式: "2024年12月6日-2025年1月11日"（预处理后无空格）
            date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)[-−](\d{4}年\d{1,2}月\d{1,2}日)', text)
            if date_match:
                data["开始日期"] = date_match.group(1)
                data["结束日期"] = date_match.group(2)
                break

        # 提取键值对（过滤掉日期相关的键，避免重复）
        kv_pairs = self.extract_key_value_pairs(text_lines)
        for key, value in kv_pairs.items():
            # 跳过日期键（避免重复）
            if '年' in key and '月' in key and '日' in key:
                continue
            data[key] = value

        # 如果备用金金额未识别到，尝试区域特定OCR
        if data.get("备用金") == "0.00" or not data.get("备用金"):
            logger.info("  备用金金额未识别到，尝试区域特定OCR")
            petty_cash_amount = self.detect_petty_cash_amount(image)
            if petty_cash_amount:
                data["备用金"] = petty_cash_amount
                logger.info(f"  ✓ 备用金金额识别成功: {petty_cash_amount}")

        logger.info(f"  提取到 {len(data)} 个字段")
        return data

    def detect_petty_cash_amount(self, image: np.ndarray) -> Optional[str]:
        """从头部图片的特定区域检测备用金金额.
        
        备用金金额通常位于图片左侧区域，X:2500-3000, Y:820-920左右（800DPI）.
        
        Args:
            image: 头部图片
            
        Returns:
            Optional[str]: 提取的备用金金额字符串，未识别到则返回None
        """
        try:
            # 根据图片大小动态调整区域坐标（适配不同DPI）
            img_height, img_width = image.shape[:2]
            
            # 设置备用金金额区域（基于800DPI的经验值，可根据实际情况调整）
            # 对于800DPI的图片，备用金金额通常位于以下区域：
            # X: 2500-3000, Y: 820-920
            # 动态计算区域，确保在不同尺寸的图片上都能定位到合适区域
            # 基于图片宽度和高度的比例来计算
            x1 = int(img_width * 0.7)  # 70%宽度位置
            x2 = int(img_width * 0.85)  # 85%宽度位置
            y1 = int(img_height * 0.5)  # 50%高度位置
            y2 = int(img_height * 0.6)  # 60%高度位置
            
            # 确保区域在合理范围内
            x1 = max(0, x1)
            x2 = min(img_width, x2)
            y1 = max(0, y1)
            y2 = min(img_height, y2)
            
            # 检查区域是否有效
            if x2 <= x1 or y2 <= y1:
                logger.warning("  备用金检测区域无效，跳过区域识别")
                return None
            
            # 裁剪备用金金额区域
            petty_cash_region = image[y1:y2, x1:x2]
            
            # 使用较低的置信度阈值进行OCR识别
            ocr_results = self.ocr_engine.recognize_image(petty_cash_region, confidence_threshold=0.2, preprocess=True)
            
            # 从识别结果中提取金额
            for box, (text, confidence) in ocr_results:
                # 清理文本
                cleaned_text = text.strip()
                if not cleaned_text:
                    continue
                
                # 提取金额
                amount = self._extract_amount_from_text(cleaned_text)
                if amount:
                    return amount
            
            logger.info("  区域特定OCR未识别到备用金金额")
            return None
            
        except Exception as e:
            logger.error(f"  备用金金额检测失败: {e}")
            return None


    def process_sales_section(self, image: np.ndarray) -> Dict[str, str]:
        """处理sales板块.

        Args:
            image: sales板块图片

        Returns:
            Dict: sales数据
        """
        logger.info("处理sales板块...")
        text_lines = self.extract_text_lines(image)
        
        # 调试：显示原始文本行
        logger.info("  原始文本行:")
        for i, (text, y_coord) in enumerate(text_lines):
            logger.info(f"    行{i}: {text} (Y={y_coord})")
            logger.info(f"    原始文本: {text}")
        
        data = self.extract_key_value_pairs(text_lines, extract_total_from_title=True)
        
        # 调试：显示提取的键值对
        logger.info("  提取的键值对:")
        for key, value in data.items():
            logger.info(f"    {key}: {value}")
            
        # 智能后处理：补充缺失的总计字段
        data = self.post_process_total(data, text_lines, section_name="sales")
        logger.info(f"  提取到 {len(data)} 个字段")
        return data


    def process_refund_section(self, image: np.ndarray) -> Dict[str, str]:
        """处理refund板块.

        Args:
            image: refund板块图片

        Returns:
            Dict: refund数据
        """
        logger.info("处理refund板块...")
        text_lines = self.extract_text_lines(image)
        data = self.extract_key_value_pairs(text_lines, extract_total_from_title=True)
        # 智能后处理：补充缺失的总计字段
        data = self.post_process_total(data, text_lines, section_name="refund")
        logger.info(f"  提取到 {len(data)} 个字段")
        return data


    def process_adjustment_section(self, image: np.ndarray) -> Dict[str, str]:
        """处理adjustment板块.

        Args:
            image: adjustment板块图片

        Returns:
            Dict: adjustment数据
        """
        logger.info("处理adjustment板块...")
        text_lines = self.extract_text_lines(image)
        data = self.extract_key_value_pairs(text_lines, extract_total_from_title=True)
        # 智能后处理：补充缺失的总计字段
        data = self.post_process_total(data, text_lines, section_name="adjustment")
        logger.info(f"  提取到 {len(data)} 个字段")
        return data


    def process_wfs_section(self, image: np.ndarray) -> Dict[str, str]:
        """处理wfs板块.

        Args:
            image: wfs板块图片

        Returns:
            Dict: wfs数据
        """
        logger.info("处理wfs板块...")
        text_lines = self.extract_text_lines(image)
        data = self.extract_key_value_pairs(text_lines, extract_total_from_title=True)
        # 智能后处理：补充缺失的总计字段
        data = self.post_process_total(data, text_lines, section_name="wfs")
        logger.info(f"  提取到 {len(data)} 个字段")
        return data


    def process_other_section(self, image: np.ndarray) -> Dict[str, str]:
        """处理other板块.

        Args:
            image: other板块图片

        Returns:
            Dict: other数据
        """
        logger.info("处理other板块...")
        text_lines = self.extract_text_lines(image)
        data = self.extract_key_value_pairs(text_lines, extract_total_from_title=True)
        # 智能后处理：补充缺失的总计字段
        data = self.post_process_total(data, text_lines, section_name="other")
        logger.info(f"  提取到 {len(data)} 个字段")
        return data


    def process_footer_section(self, image: np.ndarray) -> Dict[str, str]:
        """处理footer板块.

        提取内容：
        - 向您支付的金额
        - 期末余额

        处理策略：
        1. 按顺序扫描文本行
        2. 识别到"期末余额"字段后立即停止，抛弃后续内容
        3. 如果未识别到"期末余额"，发出警告

        Args:
            image: footer板块图片

        Returns:
            Dict: footer数据
        """
        logger.info("处理footer板块...")
        text_lines = self.extract_text_lines(image)

        data = {}

        # 逐行扫描，识别到"期末余额"后停止
        for i, (text, y_coord) in enumerate(text_lines):
            # 检查是否包含"期末余额"
            if '期末余额' in text:
                # 提取金额
                value = self._extract_amount_from_text(text)
                if value:
                    data['期末余额'] = value
                else:
                    # 如果同一行没有金额，查找下一行
                    if i + 1 < len(text_lines):
                        next_text = text_lines[i + 1][0]
                        value = self._extract_amount_from_text(next_text)
                        if value:
                            data['期末余额'] = value

                # 识别到"期末余额"后，停止处理后续文本
                logger.info("  ✓ 识别到'期末余额'字段，停止处理后续内容")
                break

            # 检查是否包含"向您支付的金额"
            if '向您支付的金额' in text:
                value = self._extract_amount_from_text(text)
                if value:
                    data['向您支付的金额'] = value
                else:
                    # 如果同一行没有金额，查找下一行
                    if i + 1 < len(text_lines):
                        next_text = text_lines[i + 1][0]
                        value = self._extract_amount_from_text(next_text)
                        if value:
                            data['向您支付的金额'] = value

            # 提取其他字段（在"期末余额"之前）
            amount_value = self._extract_amount_from_text(text)
            if amount_value:
                # 移除金额部分，剩下的就是标签
                key_part = text
                key_part = re.sub(r'[-−]?\s*[$＄]\s*\d+[,\d]*\.?\d*', '', key_part)
                key_part = re.sub(r'[-−]?\s*\d+[,\d]*\.?\d*\s*美元', '', key_part)
                key_part = key_part.strip()

                if key_part and key_part not in ['向您支付的金额', '期末余额']:
                    # 只保留footer相关的字段
                    # 避免包含其他板块的数据（如"期初余额"、"产品价格"等）
                    if any(keyword in key_part for keyword in ['期初', '产品', '运输', '佣金', '税', '退款', '调整', '沃尔玛', '广告']):
                        # 跳过其他板块的字段
                        logger.debug(f"  跳过其他板块字段: {key_part}")
                        continue
                    data[key_part] = amount_value

        # 验证是否识别到必需字段
        if '期末余额' not in data:
            # "期末余额"可能在第2页，这是正常情况，不发出警告
            logger.info("  ℹ️ 未识别到'期末余额'字段（可能在第2页）")
            data['期末余额'] = "0.00"  # 设置默认值

        if '向您支付的金额' not in data:
            logger.warning("  ⚠️ 未识别到'向您支付的金额'字段")
            data['向您支付的金额'] = "0.00"  # 设置默认值

        logger.info(f"  提取到 {len(data)} 个字段")
        return data


    def process_all_sections(
        self,
        section_images: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """处理所有板块并生成完整的JSON数据.

        Args:
            section_images: 板块图片字典
                {
                    'header': image_array,
                    'sales': image_array,
                    ...
                }

        Returns:
            Dict: 完整的结构化数据
        """
        logger.info("=" * 60)
        logger.info("开始处理所有板块")
        logger.info("=" * 60)

        result = {}

        # 处理各个板块
        if 'header' in section_images:
            result['header'] = self.process_header_section(section_images['header'])

        if 'sales' in section_images:
            result['sales'] = self.process_sales_section(section_images['sales'])

        if 'refund' in section_images:
            result['refund'] = self.process_refund_section(section_images['refund'])

        if 'adjustment' in section_images:
            result['adjustment'] = self.process_adjustment_section(section_images['adjustment'])

        if 'wfs' in section_images:
            result['wfs'] = self.process_wfs_section(section_images['wfs'])

        if 'other' in section_images:
            result['other'] = self.process_other_section(section_images['other'])

        if 'footer' in section_images:
            result['footer'] = self.process_footer_section(section_images['footer'])

        logger.info("=" * 60)
        logger.info(f"所有板块处理完成，共{len(result)}个板块")
        logger.info("=" * 60)

        return result

    def process_directly(self, left_image: np.ndarray) -> Dict[str, Any]:
        """直接处理整个左侧板块（跳过关键词提取和板块切分）.

        直接OCR识别整个左侧板块，通过文本行内容检测板块边界，
        然后应用相应的板块处理逻辑。

        Args:
            left_image: 整个左侧板块图片

        Returns:
            Dict[str, Any]: 完整的结构化数据
        """
        logger.info("=" * 60)
        logger.info("开始直接处理左侧板块")
        logger.info("=" * 60)

        # 提取整个左侧板块的所有文本行
        text_lines = self.extract_text_lines(left_image)

        # 调试：显示所有文本行
        logger.info("  所有文本行:")
        for i, (text, y_coord) in enumerate(text_lines):
            logger.info(f"    行{i}: {text} (Y={y_coord})")

        # 板块标题列表（按出现顺序）
        section_titles = {
            'sales': ['销售'],
            'refund': ['退款'],
            'adjustment': ['调整'],
            'wfs': ['沃尔玛商品服务(WFS)', '沃尔玛商品服务', '沃尔玛配送服务(WFS)', '沃尔玛配送服务'],
            'other': ['其他活动'],
            'footer': ['向您支付的金额']
        }

        # 检测各板块的开始行
        section_boundaries = {'header': {'start': 0}}
        for i, (text, y_coord) in enumerate(text_lines):
            for section, titles in section_titles.items():
                if any(title in text for title in titles) and section not in section_boundaries:
                    section_boundaries[section] = {'start': i}
                    logger.info(f"  检测到板块 {section} 的开始行: {i} ({text})")

        # 添加header结束行
        if len(section_boundaries) > 1:
            section_boundaries['header']['end'] = section_boundaries[list(section_boundaries.keys())[1]]['start']
        else:
            section_boundaries['header']['end'] = len(text_lines)

        # 添加其他板块的结束行
        section_order = ['header', 'sales', 'refund', 'adjustment', 'wfs', 'other', 'footer']
        for i in range(len(section_order) - 1):
            current_section = section_order[i]
            next_section = section_order[i + 1]
            if current_section in section_boundaries and next_section in section_boundaries:
                section_boundaries[current_section]['end'] = section_boundaries[next_section]['start']

        # 为最后一个板块设置结束行
        last_section = None
        for section in section_order[::-1]:
            if section in section_boundaries:
                last_section = section
                break
        if last_section:
            section_boundaries[last_section]['end'] = len(text_lines)

        logger.info("  板块边界:")
        for section, boundaries in section_boundaries.items():
            logger.info(f"    {section}: {boundaries['start']} -> {boundaries['end']}")

        # 处理各板块
        result = {}

        # 处理header
        if 'header' in section_boundaries:
            header_lines = text_lines[section_boundaries['header']['start']:section_boundaries['header']['end']]
            result['header'] = self._process_header_directly(header_lines)

        # 处理sales
        if 'sales' in section_boundaries:
            sales_lines = text_lines[section_boundaries['sales']['start']:section_boundaries['sales']['end']]
            result['sales'] = self._process_section_directly(sales_lines, 'sales')

        # 处理refund
        if 'refund' in section_boundaries:
            refund_lines = text_lines[section_boundaries['refund']['start']:section_boundaries['refund']['end']]
            result['refund'] = self._process_section_directly(refund_lines, 'refund')

        # 处理adjustment
        if 'adjustment' in section_boundaries:
            adjustment_lines = text_lines[section_boundaries['adjustment']['start']:section_boundaries['adjustment']['end']]
            result['adjustment'] = self._process_section_directly(adjustment_lines, 'adjustment')

        # 处理wfs
        if 'wfs' in section_boundaries:
            wfs_lines = text_lines[section_boundaries['wfs']['start']:section_boundaries['wfs']['end']]
            result['wfs'] = self._process_section_directly(wfs_lines, 'wfs')

        # 处理other
        if 'other' in section_boundaries:
            other_lines = text_lines[section_boundaries['other']['start']:section_boundaries['other']['end']]
            result['other'] = self._process_section_directly(other_lines, 'other')

        # 处理footer
        if 'footer' in section_boundaries:
            footer_lines = text_lines[section_boundaries['footer']['start']:section_boundaries['footer']['end']]
            result['footer'] = self._process_footer_directly(footer_lines)

        logger.info("=" * 60)
        logger.info(f"直接处理完成，共{len(result)}个板块")
        logger.info("=" * 60)

        return result

    def _process_header_directly(self, text_lines: List[Tuple[str, float]]) -> Dict[str, Any]:
        """直接处理header板块的文本行.

        Args:
            text_lines: header板块的文本行列表

        Returns:
            Dict: header数据
        """
        logger.info("直接处理header板块...")

        data = {
            "开始日期": "",
            "结束日期": "",
            "期初余额": "0.00",
            "备用金": "0.00",
            "回款等待": "0.00"
        }

        # 提取对账单日期范围
        for text, _ in text_lines:
            # 匹配格式: "2024年12月6日-2025年1月11日"
            date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)[-−](\d{4}年\d{1,2}月\d{1,2}日)', text)
            if date_match:
                data["开始日期"] = date_match.group(1)
                data["结束日期"] = date_match.group(2)
                break

        # 提取键值对
        kv_pairs = self.extract_key_value_pairs(text_lines)
        for key, value in kv_pairs.items():
            # 跳过日期键（避免重复）
            if '年' in key and '月' in key and '日' in key:
                continue
            data[key] = value

        logger.info(f"  提取到 {len(data)} 个字段")
        return data

    def _process_section_directly(self, text_lines: List[Tuple[str, float]], section_name: str) -> Dict[str, str]:
        """直接处理普通板块的文本行.

        Args:
            text_lines: 板块的文本行列表
            section_name: 板块名称

        Returns:
            Dict: 板块数据
        """
        logger.info(f"直接处理{section_name}板块...")

        data = self.extract_key_value_pairs(text_lines, extract_total_from_title=True)

        # 智能后处理：补充缺失的总计字段
        data = self.post_process_total(data, text_lines, section_name=section_name)

        logger.info(f"  提取到 {len(data)} 个字段")
        return data

    def _process_footer_directly(self, text_lines: List[Tuple[str, float]]) -> Dict[str, str]:
        """直接处理footer板块的文本行.

        Args:
            text_lines: footer板块的文本行列表

        Returns:
            Dict: footer数据
        """
        logger.info("直接处理footer板块...")

        data = {}

        # 逐行扫描，识别到"期末余额"后停止
        for i, (text, y_coord) in enumerate(text_lines):
            # 检查是否包含"期末余额"
            if '期末余额' in text:
                # 提取金额
                value = self._extract_amount_from_text(text)
                if value:
                    data['期末余额'] = value
                else:
                    # 如果同一行没有金额，查找下一行
                    if i + 1 < len(text_lines):
                        next_text = text_lines[i + 1][0]
                        value = self._extract_amount_from_text(next_text)
                        if value:
                            data['期末余额'] = value

                # 识别到"期末余额"后，停止处理后续文本
                logger.info("  ✓ 识别到'期末余额'字段，停止处理后续内容")
                break

            # 检查是否包含"向您支付的金额"
            if '向您支付的金额' in text:
                value = self._extract_amount_from_text(text)
                if value:
                    data['向您支付的金额'] = value
                else:
                    # 如果同一行没有金额，查找下一行
                    if i + 1 < len(text_lines):
                        next_text = text_lines[i + 1][0]
                        value = self._extract_amount_from_text(next_text)
                        if value:
                            data['向您支付的金额'] = value

            # 提取其他字段（在"期末余额"之前）
            amount_value = self._extract_amount_from_text(text)
            if amount_value:
                # 移除金额部分，剩下的就是标签
                key_part = text
                key_part = re.sub(r'[-−]?\s*[$＄]\s*\d+[,\d]*\.?\d*', '', key_part)
                key_part = re.sub(r'[-−]?\s*\d+[,\d]*\.?\d*\s*美元', '', key_part)
                key_part = key_part.strip()

                if key_part and key_part not in ['向您支付的金额', '期末余额']:
                    # 只保留footer相关的字段
                    if any(keyword in key_part for keyword in ['期初', '产品', '运输', '佣金', '税', '退款', '调整', '沃尔玛', '广告']):
                        # 跳过其他板块的字段
                        logger.debug(f"  跳过其他板块字段: {key_part}")
                        continue
                    data[key_part] = amount_value

        # 验证是否识别到必需字段
        if '期末余额' not in data:
            # "期末余额"可能在第2页，这是正常情况，不发出警告
            logger.info("  ℹ️ 未识别到'期末余额'字段（可能在第2页）")
            data['期末余额'] = "0.00"  # 设置默认值

        if '向您支付的金额' not in data:
            logger.warning("  ⚠️ 未识别到'向您支付的金额'字段")
            data['向您支付的金额'] = "0.00"  # 设置默认值

        logger.info(f"  提取到 {len(data)} 个字段")
        return data


    def save_json(self, data: Dict[str, Any], output_path: str):
        """保存JSON数据到文件.

        Args:
            data: 结构化数据
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON数据已保存: {output_path}")


# ============================================================
# END OF left_section_ocr.py
# ============================================================
