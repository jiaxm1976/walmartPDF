# ============================================================
# 文件: backend/app/services/pdf_parser.py
# 功能: 沃尔玛对账单PDF解析器核心类
# 作者: 开发团队
# 创建时间: 2025-12-13
# 最后修改: 2025-12-13
# 说明: 解析Walmart Marketplace的财务对账单PDF文件，
#       提取销售、退款、费用等财务数据
# ============================================================

import re  # 用于正则表达式匹配日期和金额
import json  # 用于处理extra_fields JSON数据
from typing import Dict, Any, Optional, Tuple  # 类型提示
from datetime import datetime  # 日期处理
import logging  # 日志记录
from pathlib import Path  # 路径处理

try:
    import pdfplumber  # PDF解析库
except ImportError:
    raise ImportError("请先安装pdfplumber: pip install pdfplumber")

# 创建logger实例，用于记录解析过程
logger = logging.getLogger(__name__)


# ========== 自定义异常类 ==========

class PDFReadError(Exception):
    """PDF文件读取错误异常.

    当PDF文件损坏、格式不正确或无法访问时抛出。
    """
    pass


class PDFParseError(Exception):
    """PDF解析错误异常.

    当PDF格式无法识别或关键数据缺失时抛出。
    """
    pass


# ========== PDF解析器主类 ==========

class PDFParser:
    """沃尔玛对账单PDF解析器.

    用于解析沃尔玛市场（Walmart Marketplace）的财务对账单PDF文件，
    提取销售、退款、费用等财务数据。

    Attributes:
        file_path (str): PDF文件路径
        pdf_version (str): PDF格式版本（v1/v2/unknown）
        raw_content (str): PDF原始文本内容
        parsed_data (dict): 解析后的结构化数据

    Example:
        >>> parser = PDFParser('MP_12032024_statement_summary.pdf')
        >>> data = parser.parse()
        >>> print(data['period_start'])  # 2024-10-08
    """

    def __init__(self, file_path: str):
        """初始化PDF解析器.

        Args:
            file_path: PDF文件的绝对路径或相对路径

        Raises:
            FileNotFoundError: 当PDF文件不存在时
        """
        # 转换为Path对象，方便路径操作
        self.file_path = Path(file_path)

        # 检查文件是否存在
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {file_path}")

        # 初始化版本为未知
        self.pdf_version = "unknown"

        # 初始化原始内容为空
        self.raw_content = ""

        # 初始化解析结果为空字典
        self.parsed_data: Dict[str, Any] = {}

        # 记录初始化日志
        logger.info(f"初始化PDF解析器: {self.file_path.name}")


    def extract_text(self) -> str:
        """从PDF中提取文本内容.

        使用pdfplumber库读取PDF的所有页面，将文本内容合并为一个字符串。

        Returns:
            str: PDF的完整文本内容

        Raises:
            PDFReadError: 当PDF文件损坏或无法读取时
        """
        # 初始化文本内容列表
        text_parts = []

        try:
            # 打开PDF文件
            with pdfplumber.open(self.file_path) as pdf:
                # 记录PDF总页数
                total_pages = len(pdf.pages)
                logger.info(f"PDF共有 {total_pages} 页")

                # 遍历每一页
                for page_num, page in enumerate(pdf.pages, start=1):
                    # 记录当前处理的页码
                    logger.debug(f"正在提取第 {page_num}/{total_pages} 页")

                    # 尝试多种方式提取文本
                    page_text = None

                    # 方法1: 默认提取
                    page_text = page.extract_text()

                    # 方法2: 如果方法1失败，尝试使用layout参数
                    if not page_text or len(page_text.strip()) < 10:
                        logger.debug(f"尝试使用layout模式提取第{page_num}页")
                        page_text = page.extract_text(layout=True)

                    # 方法3: 如果还是失败，尝试提取表格
                    if not page_text or len(page_text.strip()) < 10:
                        logger.debug(f"尝试提取第{page_num}页的表格")
                        tables = page.extract_tables()
                        if tables:
                            # 将表格转换为文本
                            table_texts = []
                            for table in tables:
                                for row in table:
                                    if row:
                                        row_text = ' '.join([str(cell) if cell else '' for cell in row])
                                        table_texts.append(row_text)
                            page_text = '\n'.join(table_texts)

                    # 将文本添加到列表（确保文本非空）
                    if page_text and len(page_text.strip()) > 0:
                        text_parts.append(page_text)
                        logger.debug(f"第{page_num}页提取了{len(page_text)}个字符")
                    else:
                        logger.warning(f"第 {page_num} 页没有提取到文本")

            # 将所有页面文本用换行符连接
            full_text = "\n".join(text_parts)

            # 保存原始内容到实例属性
            self.raw_content = full_text

            # 记录提取成功日志
            logger.info(f"成功提取PDF文本，共 {len(full_text)} 个字符")

            # 返回完整文本
            return full_text

        except Exception as e:
            # 记录错误日志
            logger.error(f"PDF文本提取失败: {str(e)}")
            # 抛出自定义异常
            raise PDFReadError(f"无法读取PDF文件: {str(e)}")


    def detect_version(self, content: str) -> str:
        """检测PDF格式版本.

        根据特定关键词判断PDF的格式版本：
        - v1: 旧版，包含"WFS配送费"
        - v2: 新版，包含"WFS商品费"
        - unknown: 无法识别

        Args:
            content: PDF文本内容

        Returns:
            str: 版本标识（v1/v2/unknown）
        """
        # 检查是否包含v1版本的特征关键词
        if 'WFS配送费' in content:
            # 设置版本为v1
            self.pdf_version = 'v1'
            logger.info("检测到PDF版本: v1 (包含'WFS配送费')")
            return 'v1'

        # 检查是否包含v2版本的特征关键词
        elif 'WFS商品费' in content:
            # 设置版本为v2
            self.pdf_version = 'v2'
            logger.info("检测到PDF版本: v2 (包含'WFS商品费')")
            return 'v2'

        # 无法识别版本
        else:
            # 设置版本为unknown
            self.pdf_version = 'unknown'
            logger.warning("无法识别PDF版本，将使用通用解析策略")
            return 'unknown'


    def parse_filename(self) -> Optional[datetime]:
        """从文件名解析日期.

        标准格式: MP_MMDDYYYY_statement_summary.pdf
        示例: MP_12032024_statement_summary.pdf -> 2024-12-03

        Returns:
            datetime: 解析出的日期，如果失败返回None
        """
        # 获取文件名（不含路径）
        filename = self.file_path.name

        # 定义文件名解析正则表达式
        # 格式: MP_MMDDYYYY_statement_summary.pdf
        # 示例: MP_12032024_statement_summary.pdf
        # 分组:
        #   (\d{2}): 月份（两位数字）
        #   (\d{2}): 日期（两位数字）
        #   (\d{4}): 年份（四位数字）
        pattern = r'MP_(\d{2})(\d{2})(\d{4})_statement_summary\.pdf'

        # 尝试匹配
        match = re.match(pattern, filename)

        if match:
            # 提取月、日、年
            month, day, year = match.groups()

            try:
                # 转换为datetime对象
                date = datetime(int(year), int(month), int(day))
                logger.info(f"从文件名解析日期: {date.date()}")
                return date
            except ValueError as e:
                # 日期无效（如13月、32日等）
                logger.error(f"文件名中的日期无效: {month}/{day}/{year} - {e}")
                return None
        else:
            # 文件名格式不匹配
            logger.warning(f"文件名格式不符合标准: {filename}")
            return None


    def parse_period(self, content: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """解析对账周期.

        从PDF文本中提取对账周期的起止日期。
        支持格式：
        1. YYYY年MM月DD日 - YYYY年MM月DD日
        2. YYYY/MM/DD - YYYY/MM/DD (备用)

        Args:
            content: PDF文本内容

        Returns:
            tuple: (起始日期, 结束日期)，解析失败返回(None, None)
        """
        # 优先匹配中文格式: 2024年10月8日 - 2024年11月10日
        zh_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*-\s*(\d{4})年(\d{1,2})月(\d{1,2})日'
        m = re.search(zh_pattern, content)
        if m:
            try:
                start_date = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                end_date = datetime(int(m.group(4)), int(m.group(5)), int(m.group(6)))
                if start_date > end_date:
                    logger.error(f"对账周期起始日期({start_date})晚于结束日期({end_date})")
                    return None, None
                logger.info(f"解析对账周期(中文格式): {start_date.date()} 至 {end_date.date()}")
                return start_date, end_date
            except ValueError as e:
                logger.error(f"日期转换失败(中文格式): {e}")
                return None, None

        # 兼容 YYYY/MM/DD - YYYY/MM/DD
        slash_pattern = r'(\d{4})/(\d{1,2})/(\d{1,2})\s*-\s*(\d{4})/(\d{1,2})/(\d{1,2})'
        m = re.search(slash_pattern, content)
        if m:
            try:
                start_date = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                end_date = datetime(int(m.group(4)), int(m.group(5)), int(m.group(6)))
                if start_date > end_date:
                    logger.error(f"对账周期起始日期({start_date})晚于结束日期({end_date})")
                    return None, None
                logger.info(f"解析对账周期(斜杠格式): {start_date.date()} 至 {end_date.date()}")
                return start_date, end_date
            except ValueError as e:
                logger.error(f"日期转换失败(斜杠格式): {e}")
                return None, None

        # 兼容英文月名，比如: Sep 6, 2025 - Sep 20, 2025 或 September 6, 2025 - September 20, 2025
        # 捕获两个英文日期片段
        en_pattern = r'([A-Za-z]{3,9}\s+\d{1,2},\s*\d{4})\s*-\s*([A-Za-z]{3,9}\s+\d{1,2},\s*\d{4})'
        m = re.search(en_pattern, content)
        if m:
            left = m.group(1).strip()
            right = m.group(2).strip()
            # 尝试多种英文月份解析格式
            for fmt in ("%b %d, %Y", "%B %d, %Y"):
                try:
                    start_date = datetime.strptime(left, fmt)
                    end_date = datetime.strptime(right, fmt)
                    if start_date > end_date:
                        logger.error(f"对账周期起始日期({start_date})晚于结束日期({end_date})")
                        return None, None
                    logger.info(f"解析对账周期(英文格式): {start_date.date()} 至 {end_date.date()}")
                    return start_date, end_date
                except ValueError:
                    continue
            # 若上述两种格式均失败，尝试去掉可能的时区信息（如 'PDT' 等）并再次解析
            left_clean = re.sub(r'\s+\w{2,4}$', '', left)
            right_clean = re.sub(r'\s+\w{2,4}$', '', right)
            for fmt in ("%b %d, %Y", "%B %d, %Y"):
                try:
                    start_date = datetime.strptime(left_clean, fmt)
                    end_date = datetime.strptime(right_clean, fmt)
                    if start_date > end_date:
                        logger.error(f"对账周期起始日期({start_date})晚于结束日期({end_date})")
                        return None, None
                    logger.info(f"解析对账周期(英文清理后): {start_date.date()} 至 {end_date.date()}")
                    return start_date, end_date
                except ValueError:
                    continue

        logger.error("无法从PDF中提取对账周期")
        return None, None


    def parse_amount(self, text: str, keyword: str) -> float:
        """解析金额.

        从文本中提取特定关键词后的金额数值。
        支持格式：
        1. "关键词  123.45 美元"
        2. "关键词  -123.45美元" (负数)
        3. "关键词  1,234.56 美元" (带千分位)
        4. "关键词  $ 123.45" (美元符号)

        Args:
            text: 包含金额的文本
            keyword: 金额标签关键词（如"产品价格"）

        Returns:
            float: 解析出的金额（可能为负数），未找到返回0.00
        """
        # 构建正则表达式：关键词 + 可选空格 + 金额 + "美元"
        # 金额格式:
        #   [-]?: 可选的负号
        #   \d+: 至少一个数字
        #   [,.]?: 可选的逗号或点（千分位分隔符）
        #   \d*: 任意个数字
        #   \.?: 可选的小数点
        #   \d+: 小数部分数字
        #   \s*美元: "美元"标识，前面可有空格
        pattern = rf'{re.escape(keyword)}\s+([-]?\d+[,]?\d*\.?\d+)\s*美元'

        # 在文本中搜索匹配
        match = re.search(pattern, text)

        # 如果找到匹配
        if match:
            # 提取金额字符串
            amount_str = match.group(1)

            # 移除可能的逗号分隔符（如 1,234.56 → 1234.56）
            amount_str = amount_str.replace(',', '')

            try:
                # 转换为浮点数
                amount = float(amount_str)

                # 记录解析结果
                logger.debug(f"解析金额 '{keyword}': {amount}")

                # 返回金额
                return amount

            except ValueError:
                # 转换失败
                logger.warning(f"金额转换失败 '{keyword}': {amount_str}")
                return 0.00

        # 如果没有找到，返回0.00
        else:
            logger.debug(f"未找到关键词 '{keyword}' 的金额，返回0.00")
            return 0.00


    def parse_payment_info(self, content: str) -> Dict[str, Any]:
        """解析付款信息.

        提取付款相关的元数据：
        - 应支付金额
        - 付款日期
        - 付款方式
        - 付款频率
        - 付款状态

        Args:
            content: PDF文本内容

        Returns:
            dict: 包含付款信息的字典
        """
        # 初始化付款信息字典
        payment_info = {}

        # 1. 解析应支付金额（可能是"向您支付的金额"或"应您支付的金额"）
        # 尝试多个关键词
        for keyword in ['向您支付的金额', '应您支付的金额']:
            amount = self.parse_amount(content, keyword)
            if amount != 0.00 or keyword in content:
                payment_info['total_amount_due'] = amount
                # 判断付款状态
                if amount > 0:
                    payment_info['payment_status'] = 'paid'  # 有付款
                else:
                    payment_info['payment_status'] = 'unpaid'  # 无付款
                break

        # 2. 解析付款日期
        # 格式: YYYY年MM月DD日 (太平洋夏令时) 或 MMM DD, YYYY PDT
        date_pattern = r'付款日期\s+(\d{4})年(\d{1,2})月(\d{1,2})日'
        match = re.search(date_pattern, content)
        if match:
            year, month, day = match.groups()
            try:
                payment_date = datetime(int(year), int(month), int(day))
                payment_info['payment_date'] = payment_date.strftime('%Y-%m-%d')
                logger.info(f"解析付款日期: {payment_info['payment_date']}")
            except ValueError:
                payment_info['payment_date'] = None
        else:
            payment_info['payment_date'] = None

        # 3. 解析付款方式（如pingpong）
        method_pattern = r'付款方式\s+(\S+)'
        match = re.search(method_pattern, content)
        if match:
            payment_info['payment_method'] = match.group(1)
        else:
            payment_info['payment_method'] = None

        # 4. 解析付款频率
        if '每周' in content or 'weekly' in content.lower():
            payment_info['payment_frequency'] = 'weekly'
        elif '每两周' in content or 'biweekly' in content.lower():
            payment_info['payment_frequency'] = 'biweekly'
        elif '每月' in content or 'monthly' in content.lower():
            payment_info['payment_frequency'] = 'monthly'
        else:
            payment_info['payment_frequency'] = None

        # 5. 解析设备方式
        device_pattern = r'设备方式\s+(.+?)(?:\n|$)'
        match = re.search(device_pattern, content)
        if match:
            payment_info['payment_device'] = match.group(1).strip()
        else:
            payment_info['payment_device'] = None

        # 6. 解析期末余额
        ending_balance = self.parse_amount(content, '期末余额')
        payment_info['ending_balance'] = ending_balance

        return payment_info


    def parse_sales_section(self, content: str) -> Dict[str, Any]:
        """解析销售板块数据.

        从PDF中提取销售相关的所有字段：
        - 产品价格（收入）
        - 运输费用
        - WFS运输退款
        - 已收税净额
        - 其他税款
        - 净佣金（支出，负值）
        - 扣缴税款额
        - WFS运输税退款
        - 沃尔玛补贴
        - 小计

        Args:
            content: PDF文本内容

        Returns:
            dict: 包含所有销售字段的字典
        """
        # 记录开始解析销售板块
        logger.info("开始解析销售板块")

        # 初始化结果字典
        sales_data = {}

        # 定义需要提取的字段列表
        # 格式: (中文名称, 数据库字段名)
        fields = [
            ('产品价格', 'product_price'),
            ('运输', 'shipping'),
            ('WFS运输退款', 'wfs_shipping_refund'),
            ('已收税净额', 'tax_collected'),
            ('其他税款', 'other_tax'),
            ('净佣金', 'commission'),
            ('扣缴税款额', 'withholding_tax'),
            ('WFS运输税退款', 'wfs_shipping_tax_refund'),
            ('下沃尔玛出资的币余额', 'walmart_subsidy'),
        ]

        # 尝试提取销售板块内容（在"销售"关键词之后，"退款"关键词之前）
        sales_pattern = r'销售\s+(.*?)(?:退款|调整|$)'
        sales_match = re.search(sales_pattern, content, re.DOTALL)

        if sales_match:
            # 提取销售板块文本
            sales_text = sales_match.group(1)
            logger.debug(f"提取到销售板块文本，长度: {len(sales_text)}")

            # 遍历每个字段进行解析
            for chinese_name, db_field in fields:
                # 调用parse_amount方法解析金额
                amount = self.parse_amount(sales_text, chinese_name)
                # 将结果存入字典
                sales_data[db_field] = amount

            # 解析小计金额（销售板块的总计）
            subtotal = self.parse_amount(sales_text, '小计')
            sales_data['subtotal'] = subtotal

            # 记录解析完成
            logger.info(f"销售板块解析完成，小计: {subtotal}")

        else:
            # 没有找到销售板块
            logger.warning("未找到销售板块，使用全文解析")

            # 从全文中尝试解析
            for chinese_name, db_field in fields:
                amount = self.parse_amount(content, chinese_name)
                sales_data[db_field] = amount

            sales_data['subtotal'] = 0.00

        return sales_data


    def parse_refund_section(self, content: str) -> Dict[str, Any]:
        """解析退款板块数据.

        提取退款相关字段：
        - 产品价格（退款，通常为负值）
        - 运输
        - 已收税净额
        - 佣金退还（正值）
        - 扣缴税款退还
        - 小计

        Args:
            content: PDF文本内容

        Returns:
            dict: 包含退款字段的字典
        """
        logger.info("开始解析退款板块")

        refund_data = {}

        # 定义退款板块字段
        fields = [
            ('产品价格', 'product_price'),  # 注意：退款板块的产品价格通常为负值
            ('运输', 'shipping'),
            ('已收税净额', 'tax_collected'),
            ('佣金', 'commission_refund'),  # 退款时佣金退回为正值
            ('扣缴税款额', 'withholding_tax_refund'),
            ('下沃尔玛出资的币余额', 'walmart_subsidy'),
        ]

        # 尝试提取退款板块内容（在"退款"关键词之后，"调整"或"WFS"关键词之前）
        refund_pattern = r'退款\s+(.*?)(?:调整|沃尔玛商品服务|WFS|其他活动|$)'
        refund_match = re.search(refund_pattern, content, re.DOTALL)

        if refund_match:
            # 提取退款板块文本
            refund_text = refund_match.group(1)
            logger.debug(f"提取到退款板块文本，长度: {len(refund_text)}")

            # 遍历字段解析
            for chinese_name, db_field in fields:
                amount = self.parse_amount(refund_text, chinese_name)
                refund_data[db_field] = amount

            # 解析小计
            subtotal = self.parse_amount(refund_text, '小计')
            refund_data['subtotal'] = subtotal

            logger.info(f"退款板块解析完成，小计: {subtotal}")

        else:
            logger.warning("未找到退款板块")
            # 初始化为0
            for _, db_field in fields:
                refund_data[db_field] = 0.00
            refund_data['subtotal'] = 0.00

        return refund_data


    def parse_wfs_fees(self, content: str) -> Dict[str, Any]:
        """解析WFS服务费板块.

        提取沃尔玛商品服务相关费用：
        - WFS商品费/配送费
        - WFS退货费
        - WFS以大份费
        - WFS仓储费
        - WFS总折扣
        - WFS库存支出
        - 世界FS调整
        - 小计

        Args:
            content: PDF文本内容

        Returns:
            dict: 包含WFS费用的字典
        """
        logger.info("开始解析WFS服务费板块")

        wfs_data = {}

        # 定义WFS字段（兼容v1和v2版本）
        fields = [
            ('WFS商品费', 'product_fee'),  # v2版本
            ('WFS配送费', 'product_fee'),  # v1版本，映射到同一字段
            ('WFS退货费', 'return_fee'),
            ('WFS以大份费', 'large_item_fee'),
            ('WFS仓储费', 'storage_fee'),
            ('WFS总折扣', 'discount'),
            ('WFS RC库存支出', 'inventory_expense'),
            ('世界FS调整', 'adjustment'),
        ]

        # 提取WFS板块（在"沃尔玛商品服务"或"WFS"关键词之后）
        wfs_pattern = r'(?:沃尔玛商品服务|沃尔玛配送服务)\(WFS\)\s+(.*?)(?:其他活动|向您支付的金额|$)'
        wfs_match = re.search(wfs_pattern, content, re.DOTALL)

        if wfs_match:
            wfs_text = wfs_match.group(1)
            logger.debug(f"提取到WFS板块文本，长度: {len(wfs_text)}")

            # 遍历字段解析
            for chinese_name, db_field in fields:
                amount = self.parse_amount(wfs_text, chinese_name)
                # 如果字段已存在且不为0，则不覆盖（处理v1/v2兼容）
                if db_field not in wfs_data or wfs_data[db_field] == 0.00:
                    wfs_data[db_field] = amount

            # 解析小计
            subtotal = self.parse_amount(wfs_text, '小计')
            wfs_data['subtotal'] = subtotal

            logger.info(f"WFS服务费板块解析完成，小计: {subtotal}")

        else:
            logger.warning("未找到WFS服务费板块")
            # 初始化为0
            unique_fields = set([field[1] for field in fields])
            for db_field in unique_fields:
                wfs_data[db_field] = 0.00
            wfs_data['subtotal'] = 0.00

        return wfs_data


    def parse_other_activities(self, content: str) -> list:
        """解析其他活动板块.

        提取其他活动相关费用（如广告费）：
        - 沃尔玛产品广告
        - 其他未知活动

        Args:
            content: PDF文本内容

        Returns:
            list: 活动列表，每项包含{type, amount, description}
        """
        logger.info("开始解析其他活动板块")

        activities = []

        # 提取其他活动板块
        other_pattern = r'其他活动\s+(.*?)(?:向您支付的金额|期末余额|$)'
        other_match = re.search(other_pattern, content, re.DOTALL)

        if other_match:
            other_text = other_match.group(1)
            logger.debug(f"提取到其他活动板块文本，长度: {len(other_text)}")

            # 解析沃尔玛产品广告
            ad_amount = self.parse_amount(other_text, '沃尔玛产品广告')
            if ad_amount != 0.00:
                activities.append({
                    'type': '沃尔玛产品广告',
                    'amount': ad_amount,
                    'description': '广告费用'
                })

            logger.info(f"其他活动板块解析完成，共 {len(activities)} 项")

        else:
            logger.warning("未找到其他活动板块")

        return activities


    def parse(self) -> Dict[str, Any]:
        """执行完整的PDF解析流程.

        主入口方法，按顺序执行：
        1. 提取文本
        2. 检测版本
        3. 解析文件名日期
        4. 解析对账周期
        5. 解析付款信息
        6. 解析销售板块
        7. 解析退款板块
        8. 解析WFS费用
        9. 解析其他活动
        10. 组装最终结果

        Returns:
            dict: 完整的解析结果，包含所有板块数据

        Raises:
            PDFParseError: 当关键数据解析失败时
        """
        logger.info("=" * 60)
        logger.info(f"开始解析PDF: {self.file_path.name}")
        logger.info("=" * 60)

        try:
            # 1. 提取文本
            content = self.extract_text()

            # 2. 检测版本
            version = self.detect_version(content)

            # 3. 解析文件名日期
            filename_date = self.parse_filename()

            # 4. 解析对账周期
            period_start, period_end = self.parse_period(content)

            # 5. 解析付款信息
            payment_info = self.parse_payment_info(content)

            # 6. 解析销售板块
            sales_data = self.parse_sales_section(content)

            # 7. 解析退款板块
            refund_data = self.parse_refund_section(content)

            # 8. 解析WFS费用
            wfs_data = self.parse_wfs_fees(content)

            # 9. 解析其他活动
            activities = self.parse_other_activities(content)

            # 10. 组装最终结果
            result = {
                # 元数据
                'file_name': self.file_path.name,
                'pdf_version': version,
                'filename_date': filename_date.strftime('%Y-%m-%d') if filename_date else None,

                # 对账周期
                'period_start': period_start.strftime('%Y-%m-%d') if period_start else None,
                'period_end': period_end.strftime('%Y-%m-%d') if period_end else None,

                # 付款信息
                **payment_info,

                # 销售数据
                'sales': sales_data,

                # 退款数据
                'refund': refund_data,

                # WFS费用
                'wfs_fees': wfs_data,

                # 其他活动
                'other_activities': activities,
            }

            # 保存到实例属性
            self.parsed_data = result

            logger.info("=" * 60)
            logger.info(f"PDF解析完成: {self.file_path.name}")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"PDF解析失败: {str(e)}", exc_info=True)
            raise PDFParseError(f"解析失败: {str(e)}")


    def to_json(self, indent: int = 2) -> str:
        """将解析结果导出为JSON格式.

        Args:
            indent: JSON缩进空格数

        Returns:
            str: JSON字符串
        """
        # 确保已经解析过
        if not self.parsed_data:
            raise ValueError("尚未执行解析，请先调用parse()方法")

        # 转换为JSON字符串（ensure_ascii=False保留中文）
        return json.dumps(self.parsed_data, indent=indent, ensure_ascii=False)


# ========== 工具函数 ==========

def parse_pdf_file(file_path: str) -> Dict[str, Any]:
    """便捷函数：解析单个PDF文件.

    Args:
        file_path: PDF文件路径

    Returns:
        dict: 解析结果

    Example:
        >>> result = parse_pdf_file('MP_12032024_statement_summary.pdf')
        >>> print(result['period_start'])
    """
    parser = PDFParser(file_path)
    return parser.parse()


if __name__ == "__main__":
    # 测试代码（如果直接运行此文件）
    import sys

    # 配置日志输出到控制台
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) > 1:
        # 从命令行参数获取PDF路径
        pdf_path = sys.argv[1]

        try:
            # 解析PDF
            result = parse_pdf_file(pdf_path)

            # 打印结果
            print("\n" + "=" * 60)
            print("解析结果:")
            print("=" * 60)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        except Exception as e:
            print(f"错误: {e}")
            sys.exit(1)

    else:
        print("用法: python pdf_parser.py <PDF文件路径>")
        sys.exit(1)
