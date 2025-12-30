# ============================================================
# 文件: backend/app/services/left_section_cutter.py
# 功能: 左侧图片按关键词Y坐标切分成板块
# 作者: 开发团队
# 创建时间: 2025-12-16
# 说明: Step 4 - 根据关键词坐标将左侧图片切分成7个板块
# ============================================================

import logging
from typing import Dict, List, Tuple
from pathlib import Path
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class LeftSectionCutter:
    """左侧图片板块切分器.

    根据关键词Y坐标将左侧图片切分成7个独立板块：
    - header: 回款等待
    - sales: 销售
    - refund: 退款
    - adjustment: 调整
    - wfs: 沃尔玛商品服务
    - other: 其他活动
    - footer: 向您支付的金额

    切分规则（方案A：无缝拼接）：
    - header: [0, 销售Y-100)
    - sales: [销售Y-100, 退款Y-100)
    - refund: [退款Y-100, 调整Y-100)
    - adjustment: [调整Y-100, WFSY-100)
    - wfs: [WFSY-100, 其他Y-100)
    - other: [其他Y-100, footerY-100)
    - footer: [footerY-100, 图片底部]
    """

    # 板块顺序和对应的关键词（按Y坐标从上到下排序）
    SECTION_ORDER = [
        ('header', '回款等待'),
        ('sales', '销售'),
        ('refund', '退款'),
        ('adjustment', '调整'),
        ('wfs', '沃尔玛商品服务'),
        ('other', '其他活动'),
        ('footer', '向您支付的金额')
    ]

    # Y坐标偏移量（像素）
    # 120px偏移确保包含"总计:"行（蓝色加粗文字），避免切掉关键数据
    # 根据测试，总计行通常在关键词标题下方100-120px范围内
    OFFSET = 120

    def __init__(self):
        """初始化切分器."""
        logger.info("=" * 60)
        logger.info("初始化左侧图片板块切分器")
        logger.info("=" * 60)
        logger.info(f"偏移量设置: {self.OFFSET}px")
        logger.info(f"切分板块数量: {len(self.SECTION_ORDER)}")

    def _ensure_footer_keyword(
        self,
        keyword_map: Dict[str, Dict[str, int]],
        image_height: int
    ) -> None:
        """确保footer关键词存在且位置合理，如果不存在则使用默认位置.

        Args:
            keyword_map: 关键词映射表（会被就地修改）
            image_height: 图片总高度

        说明:
        - Footer板块包含"向您支付的金额"和"期末余额"，每个PDF都有
        - Footer必须在所有其他板块之后（Y坐标最大）
        - 如果OCR未识别到或位置不合理，使用经验位置：图片高度的85%
        """
        footer_keyword = "向您支付的金额"
        has_footer = False
        footer_y = None

        # 检查两种格式
        # 格式1: {'footer': {'向您支付的金额': 3000}, ...}
        if 'footer' in keyword_map and isinstance(keyword_map['footer'], dict):
            if footer_keyword in keyword_map['footer']:
                has_footer = True
                footer_y = keyword_map['footer'][footer_keyword]

        # 格式2: {'向您支付的金额': 3000, ...}
        if footer_keyword in keyword_map and isinstance(keyword_map[footer_keyword], int):
            has_footer = True
            footer_y = keyword_map[footer_keyword]

        if has_footer:
            # 验证footer位置：必须大于所有其他板块的Y坐标
            # 获取所有非footer关键词的Y坐标
            other_y_coords = []
            for section_name, keyword_cn in self.SECTION_ORDER:
                if section_name == 'footer':
                    continue

                # 尝试获取Y坐标
                y_coord = None
                if section_name in keyword_map and isinstance(keyword_map[section_name], dict):
                    if keyword_cn in keyword_map[section_name]:
                        y_coord = keyword_map[section_name][keyword_cn]
                elif keyword_cn in keyword_map and isinstance(keyword_map[keyword_cn], int):
                    y_coord = keyword_map[keyword_cn]

                if y_coord is not None:
                    other_y_coords.append((section_name, keyword_cn, y_coord))

            # 检查footer是否在所有板块之后
            if other_y_coords:
                max_other_y = max(y for _, _, y in other_y_coords)
                if footer_y <= max_other_y:
                    logger.warning(
                        f"Footer位置不合理: Y={footer_y} <= max_other_Y={max_other_y}，"
                        f"将使用默认位置"
                    )
                    has_footer = False  # 标记为无效，使用默认位置

        if not has_footer:
            # 使用默认位置（图片高度的85%）
            # 原因：footer通常在底部15%范围内，85%是经验值
            # MAX_FOOTER_HEIGHT=800px的限制会确保不会延伸到图片底部
            default_footer_y = int(image_height * 0.85)
            keyword_map[footer_keyword] = default_footer_y
            logger.warning(
                f"Footer关键词{'位置不合理' if footer_y else '未找到'}，"
                f"使用默认位置: Y={default_footer_y} (图片高度={image_height})"
            )

    def calculate_section_ranges(
        self,
        keyword_map: Dict[str, Dict[str, int]],
        image_height: int
    ) -> Dict[str, Tuple[int, int]]:
        """计算每个板块的Y坐标范围（方案A：无缝拼接）.

        Args:
            keyword_map: 关键词映射表
                {
                    'header': {'回款等待': 514},
                    'sales': {'销售': 675},
                    ...
                }
            image_height: 图片总高度

        Returns:
            Dict[str, Tuple[int, int]]: 板块名 -> (起始Y, 结束Y)
                {
                    'header': (0, 575),
                    'sales': (575, 1380),
                    ...
                }
        """
        logger.info("开始计算板块Y坐标范围")

        # Footer默认位置处理：如果未找到footer关键词，使用默认位置
        # 原因：Footer板块包含"向您支付的金额"和"期末余额"，必定存在
        # 如果OCR未识别到，使用经验值（图片底部85%位置）
        self._ensure_footer_keyword(keyword_map, image_height)

        # 提取所有关键词的Y坐标（按板块顺序）
        y_coords = []
        section_names = []

        for section_name, keyword_cn in self.SECTION_ORDER:
            # 支持两种格式：
            # 格式1: {'header': {'回款等待': 514}, ...} (ImageSplitter返回)
            # 格式2: {'回款等待': 514, ...} (KeywordExtractor返回)
            y_coord = None

            # 尝试格式1（嵌套字典）
            if section_name in keyword_map and isinstance(keyword_map[section_name], dict):
                if keyword_cn in keyword_map[section_name]:
                    y_coord = keyword_map[section_name][keyword_cn]
            # 尝试格式2（简单字典）
            elif keyword_cn in keyword_map and isinstance(keyword_map[keyword_cn], int):
                y_coord = keyword_map[keyword_cn]

            if y_coord is not None:
                y_coords.append(y_coord)
                section_names.append(section_name)
                logger.info(f"  [{section_name}] {keyword_cn}: Y={y_coord}")
            else:
                logger.warning(f"  [{section_name}] {keyword_cn}: 未找到关键词")
                # 如果关键词未找到，使用None占位
                y_coords.append(None)
                section_names.append(section_name)

        # 板块顺序验证：确保Y坐标递增
        # 如果发现某个板块的Y坐标小于前面的板块，说明识别错误，将其标记为None
        logger.info("验证板块顺序...")
        last_valid_y = -1
        for i in range(len(y_coords)):
            if y_coords[i] is not None:
                if y_coords[i] <= last_valid_y:
                    logger.warning(
                        f"  [{section_names[i]}] Y坐标={y_coords[i]} 不符合顺序"
                        f"（前一个有效Y坐标={last_valid_y}），标记为无效"
                    )
                    # 同步更新keyword_map，将无效的关键词移除
                    keyword_cn = self.SECTION_ORDER[i][1]
                    if keyword_cn in keyword_map:
                        del keyword_map[keyword_cn]
                    y_coords[i] = None
                else:
                    last_valid_y = y_coords[i]

        # Footer位置二次检查：如果footer被标记为无效，使用智能默认位置
        footer_index = section_names.index('footer')
        if y_coords[footer_index] is None:
            logger.info("Footer关键词无效，计算智能默认位置")
            # 找到最后一个有效板块的Y坐标
            last_valid_y = -1
            for i in range(footer_index):
                if y_coords[i] is not None and y_coords[i] > last_valid_y:
                    last_valid_y = y_coords[i]

            if last_valid_y > 0:
                # 使用最后有效板块之后200px作为footer起始位置
                # 200px是经验值，确保footer有足够空间
                default_footer_y = last_valid_y + 200
                # 确保不超过图片高度的95%
                max_footer_y = int(image_height * 0.95)
                default_footer_y = min(default_footer_y, max_footer_y)
            else:
                # 如果没有有效板块，使用图片高度的85%
                default_footer_y = int(image_height * 0.85)

            keyword_map["向您支付的金额"] = default_footer_y
            y_coords[footer_index] = default_footer_y
            logger.info(f"  [footer] 使用智能默认位置: Y={default_footer_y} (最后有效Y={last_valid_y})")

        # 计算每个板块的范围（方案A：无缝拼接）
        section_ranges = {}

        for i, section_name in enumerate(section_names):
            # Header板块特殊处理：不依赖关键词，固定从Y=0开始到"销售"位置
            if section_name == 'header':
                # Header从顶部开始
                start_y = 0

                # Header结束于"销售"关键词位置
                # 找到sales的Y坐标
                sales_y = None
                for j, name in enumerate(section_names):
                    if name == 'sales' and y_coords[j] is not None:
                        sales_y = y_coords[j]
                        break

                if sales_y is None:
                    logger.warning(f"跳过板块 [header]（无法找到销售关键词）")
                    continue

                end_y = sales_y - self.OFFSET

                # 边界检查
                if start_y >= end_y:
                    logger.warning(f"板块 [header] 范围无效: [{start_y}, {end_y})")
                    continue

                section_ranges[section_name] = (start_y, end_y)
                height = end_y - start_y
                logger.info(f"  [header] 范围: [{start_y}, {end_y}) = {height}px (固定从顶部到销售)")
                continue

            # 其他板块：需要关键词
            if y_coords[i] is None:
                logger.warning(f"跳过板块 [{section_name}]（关键词未找到）")
                continue

            # 确定起始Y
            if i == 0:
                # 第一个板块：从图片顶部开始
                start_y = 0
            else:
                # 其他板块：从当前关键词Y-100开始
                start_y = y_coords[i] - self.OFFSET

            # 确定结束Y
            if i == len(section_names) - 1:
                # 最后一个板块（footer）：限制最大高度
                # 原因：footer只包含"向您支付的金额"和"期末余额"两个字段（可能还有储蓄信息）
                # 不应该延伸到图片底部，避免包含第2页的内容或其他无关数据
                # 根据测试，footer区域高度通常在400-700px之间
                MAX_FOOTER_HEIGHT = 800
                end_y = min(image_height, start_y + MAX_FOOTER_HEIGHT)
            else:
                # 其他板块：到下一个关键词Y-100
                # 找到下一个有效的关键词
                next_y = None
                for j in range(i + 1, len(y_coords)):
                    if y_coords[j] is not None:
                        next_y = y_coords[j]
                        break

                if next_y is None:
                    # 如果后面没有有效关键词，到图片底部
                    end_y = image_height
                else:
                    # 到下一个关键词Y-100
                    end_y = next_y - self.OFFSET

            # 边界检查
            start_y = max(0, start_y)
            end_y = min(image_height, end_y)

            # 确保start_y < end_y
            if start_y >= end_y:
                logger.warning(f"板块 [{section_name}] 范围无效: [{start_y}, {end_y})")
                continue

            section_ranges[section_name] = (start_y, end_y)
            height = end_y - start_y
            logger.info(f"  [{section_name}] 范围: [{start_y}, {end_y}) = {height}px")

        logger.info(f"板块范围计算完成，共{len(section_ranges)}个有效板块")
        return section_ranges


    def cut_sections(
        self,
        left_image: np.ndarray,
        section_ranges: Dict[str, Tuple[int, int]],
        output_dir: str,
        base_filename: str
    ) -> Dict[str, str]:
        """切分左侧图片并保存各板块.

        Args:
            left_image: 左侧图片（numpy数组）
            section_ranges: 板块Y坐标范围字典
            output_dir: 输出目录路径
            base_filename: 基础文件名（如"MP_01142025"）

        Returns:
            Dict[str, str]: 板块名 -> 输出文件路径
                {
                    'header': '/path/to/MP_01142025_header.png',
                    'sales': '/path/to/MP_01142025_sales.png',
                    ...
                }
        """
        logger.info("=" * 60)
        logger.info("开始切分左侧图片")
        logger.info("=" * 60)

        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"输出目录: {output_dir}")

        # 获取图片尺寸
        image_height, image_width = left_image.shape[:2]
        logger.info(f"左侧图片尺寸: {image_width}x{image_height}")

        # 切分每个板块
        saved_files = {}

        for section_name, (start_y, end_y) in section_ranges.items():
            # 切分图片
            section_image = left_image[start_y:end_y, :]
            section_height, section_width = section_image.shape[:2]

            # 生成文件名（方案3：简化版）
            filename = f"{base_filename}_{section_name}.png"
            file_path = output_path / filename

            # 保存图片
            cv2.imwrite(str(file_path), section_image)
            saved_files[section_name] = str(file_path)

            logger.info(f"  [{section_name}] {section_width}x{section_height}px -> {filename}")

        logger.info("=" * 60)
        logger.info(f"切分完成，共保存 {len(saved_files)} 个板块图片")
        logger.info("=" * 60)

        return saved_files


# ============================================================
# END OF left_section_cutter.py
# ============================================================
