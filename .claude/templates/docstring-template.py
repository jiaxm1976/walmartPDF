"""
Docstring模板库 - 用于生成规范的函数/类文档字符串

本文件提供了多种docstring模板，适用于不同场景的函数和类。
所有模板遵循Google风格的docstring规范。

使用方法:
1. 复制对应场景的模板
2. 填写具体内容
3. 确保包含所有必需部分（Args/Returns/Example等）

最后更新: 2025-12-16
版本: v1.0
"""

# ============================================================
# 模板1: 标准函数模板（最常用）
# ============================================================

def standard_function_template(param1: str, param2: int, optional_param: float = 1.0) -> dict:
    """一句话描述函数功能（使用动词开头，如"计算"、"提取"、"转换"）.

    详细功能说明（可选，2-3句话）:
    - 第一个关键功能点
    - 第二个关键功能点
    - 第三个关键功能点

    核心流程（可选，适用于复杂函数）:
    1. 步骤1：做什么
    2. 步骤2：做什么
    3. 步骤3：做什么

    Args:
        param1: 参数1的含义和用途.
            - 格式说明：例如"必须是有效的文件路径"
            - 范围限制：例如"长度必须>0"
            - 示例：例如"'/path/to/file.pdf'"
        param2: 参数2的含义和用途.
            - 范围：例如"1-100之间的整数"
            - 默认值：如果有默认值，说明其含义
        optional_param: 可选参数的含义（默认值: 1.0）.
            - 说明：为什么选择这个默认值
            - 影响：改变此值会如何影响结果

    Returns:
        返回值的类型和含义，包含详细的结构说明：
        {
            "key1": value1,  # 说明key1的含义
            "key2": value2,  # 说明key2的含义
            "data": [...]    # 说明data的结构
        }

        OR（如果有多种返回情况）：
        - 情况1：返回dict，包含处理结果
        - 情况2：返回None，表示处理失败

    Raises:
        ValueError: 当param1为空字符串时抛出.
            原因：param1不能为空，因为需要用于...
        TypeError: 当param2不是整数时抛出.
            原因：param2用于索引，必须是整数
        FileNotFoundError: 当指定的文件不存在时抛出.

    Example:
        基本用法：
        >>> result = standard_function_template("test", 10)
        >>> print(result["key1"])
        'expected_value'

        高级用法（带可选参数）：
        >>> result = standard_function_template(
        ...     "test",
        ...     10,
        ...     optional_param=2.5
        ... )
        >>> print(result["key2"])
        100

    Note:
        - 注意事项1：例如"此函数不是线程安全的"
        - 注意事项2：例如"首次调用会加载模型，耗时约5秒"
        - 性能考虑：例如"处理大文件时建议增大optional_param"
        - 最佳实践：例如"建议先验证param1的有效性"

    See Also:
        related_function: 相关的函数
        AnotherClass.method: 相关的类方法
    """
    # 实现代码...
    result = {
        "key1": "value1",
        "key2": param2 * 10
    }
    return result


# ============================================================
# 模板2: 简单函数模板（适用于非常简单的函数）
# ============================================================

def simple_function_template(value: int) -> int:
    """一句话描述函数功能.

    Args:
        value: 参数含义

    Returns:
        返回值含义

    Example:
        >>> simple_function_template(5)
        10
    """
    return value * 2


# ============================================================
# 模板3: 复杂函数模板（带算法说明）
# ============================================================

def complex_algorithm_template(data: list, threshold: float = 0.8) -> list:
    """执行复杂算法处理数据.

    算法说明:
    本函数实现了[算法名称]算法，核心思想是...

    算法步骤:
    1. 预处理：对输入数据进行清洗和标准化
       - 去除异常值（超出3倍标准差）
       - 归一化到[0, 1]区间
    2. 主处理：应用[具体方法]
       - 公式：result = f(data, threshold)
       - 复杂度：O(n log n)
    3. 后处理：过滤和排序结果
       - 过滤低于threshold的结果
       - 按置信度降序排列

    时间复杂度: O(n log n)
    空间复杂度: O(n)

    Args:
        data: 输入数据列表.
            - 格式：[{"value": float, "label": str}, ...]
            - 要求：每个元素必须包含"value"和"label"字段
            - 长度：建议≤10000（超过会影响性能）
        threshold: 过滤阈值（默认: 0.8）.
            - 范围：0.0-1.0
            - 含义：低于此值的结果将被过滤
            - 调优：较高值会提高精度但降低召回率

    Returns:
        过滤和排序后的结果列表，格式同输入:
        [
            {"value": 0.95, "label": "A", "confidence": 0.98},
            {"value": 0.82, "label": "B", "confidence": 0.85},
            ...
        ]
        新增字段"confidence"表示结果的置信度

    Raises:
        ValueError: 当data为空或threshold不在[0, 1]范围内时.
        TypeError: 当data元素缺少必需字段时.

    Example:
        基本用法：
        >>> data = [
        ...     {"value": 0.9, "label": "A"},
        ...     {"value": 0.6, "label": "B"},
        ...     {"value": 0.95, "label": "C"}
        ... ]
        >>> result = complex_algorithm_template(data, threshold=0.8)
        >>> len(result)
        2
        >>> result[0]["label"]
        'C'

    Note:
        - 性能：处理10000条数据约需3秒
        - 精度权衡：threshold=0.9时精度95%召回60%，threshold=0.7时精度85%召回85%
        - 内存：大数据集建议逐批处理，每批≤1000条

    References:
        [1] 算法论文：Author et al., "Title", Conference 2020
        [2] 实现参考：https://github.com/example/algorithm
    """
    # 实现代码...
    pass


# ============================================================
# 模板4: 类的Docstring模板
# ============================================================

class ClassTemplate:
    """一句话描述类的核心功能（名词短语）.

    详细说明（2-3段）:
    第一段：描述类的主要用途和设计目标
    例如："本类封装了OCR引擎的所有功能，提供统一的文字识别接口。
    设计目标是简化OCR操作，隐藏底层复杂性。"

    第二段：描述类的核心特性和能力
    例如："支持CPU和GPU两种模式，自动处理图像预处理和坐标校准。
    内置缓存机制，避免重复识别相同图像。"

    第三段（可选）：使用场景和限制
    例如："适用于批量PDF文档识别，不适用于实时视频流OCR。"

    核心概念（可选）:
        术语1: 解释
        术语2: 解释

    类架构:
    ┌─────────────────┐
    │  ClassTemplate  │
    ├─────────────────┤
    │ + attribute1    │
    │ + attribute2    │
    ├─────────────────┤
    │ + method1()     │
    │ + method2()     │
    └─────────────────┘

    Attributes:
        attribute1 (str): 属性1的含义和用途.
            - 初始化：在__init__中设置
            - 范围：可能的值域
            - 示例："example_value"
        attribute2 (int): 属性2的含义（默认值: 10）.
            - 含义：详细说明
            - 影响：改变此值会影响...
        _private_attr (dict): 私有属性，存储内部状态.
            - 注意：不应直接访问，使用getter方法

    Class Variables:
        CLASS_CONSTANT (int): 类常量的含义.
            - 值：100
            - 用途：用于...

    Methods:
        public_method: 公开方法的简短描述
        _private_method: 私有方法的简短描述（内部使用）

    Example:
        基本用法：
        >>> obj = ClassTemplate("value1", 20)
        >>> result = obj.method1()
        >>> print(result)
        'expected_output'

        高级用法（配置选项）：
        >>> obj = ClassTemplate(
        ...     "value1",
        ...     attribute2=30,
        ...     enable_cache=True
        ... )
        >>> with obj:  # 使用上下文管理器
        ...     result = obj.method1()

    Note:
        - 线程安全性：此类不是线程安全的，多线程环境需要加锁
        - 资源管理：使用完毕后建议调用cleanup()释放资源
        - 性能考虑：首次初始化会加载模型，耗时约5秒

    See Also:
        RelatedClass: 相关的类
        alternative_function: 替代方案
    """

    CLASS_CONSTANT = 100  # 类常量

    def __init__(self, attribute1: str, attribute2: int = 10):
        """初始化ClassTemplate实例.

        Args:
            attribute1: 属性1的初始值
            attribute2: 属性2的初始值（默认: 10）

        Raises:
            ValueError: 当attribute1为空时
        """
        self.attribute1 = attribute1
        self.attribute2 = attribute2
        self._private_attr = {}

    def method1(self) -> str:
        """方法1的功能描述.

        Returns:
            处理结果字符串

        Example:
            >>> obj = ClassTemplate("test")
            >>> obj.method1()
            'processed_test'
        """
        return f"processed_{self.attribute1}"

    def _private_method(self) -> None:
        """私有方法，仅供内部使用.

        Note:
            此方法不应被外部调用
        """
        pass


# ============================================================
# 模板5: 生成器函数模板
# ============================================================

def generator_template(data: list, batch_size: int = 10):
    """逐批生成数据（生成器函数）.

    本函数是一个生成器，逐批yield数据而非一次性返回所有数据。
    优势：节省内存，适用于大数据集处理。

    Args:
        data: 输入数据列表
        batch_size: 每批数据的大小（默认: 10）

    Yields:
        list: 每次yield一个批次的数据，长度为batch_size
              （最后一批可能小于batch_size）

    Example:
        基本用法：
        >>> data = list(range(25))
        >>> for batch in generator_template(data, batch_size=10):
        ...     print(len(batch))
        10
        10
        5

        配合循环处理：
        >>> for batch in generator_template(large_dataset):
        ...     process_batch(batch)  # 逐批处理，节省内存

    Note:
        - 内存优势：处理1GB数据只需约100MB内存
        - 使用场景：数据流处理、大文件读取、批量API调用
    """
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]


# ============================================================
# 模板6: 装饰器函数模板
# ============================================================

def decorator_template(func):
    """装饰器功能描述（如性能计时、缓存、日志等）.

    本装饰器在函数执行前后添加额外功能：
    - 执行前：做什么
    - 执行后：做什么

    Args:
        func: 被装饰的函数

    Returns:
        装饰后的函数（保留原函数的签名和文档）

    Example:
        使用装饰器：
        >>> @decorator_template
        ... def my_function(x):
        ...     return x * 2
        >>> result = my_function(5)
        # 装饰器会自动执行额外功能
        >>> print(result)
        10

    Note:
        - 此装饰器保留原函数的__name__和__doc__
        - 支持带参数和不带参数的函数
    """
    import functools

    @functools.wraps(func)  # 保留原函数的元数据
    def wrapper(*args, **kwargs):
        # 执行前的操作
        print(f"调用函数: {func.__name__}")

        # 执行原函数
        result = func(*args, **kwargs)

        # 执行后的操作
        print(f"函数返回: {result}")

        return result

    return wrapper


# ============================================================
# 模板7: 异步函数模板
# ============================================================

async def async_function_template(url: str, timeout: int = 30) -> dict:
    """异步执行某个操作（如网络请求、I/O操作）.

    本函数是异步函数，使用await调用。
    适用于I/O密集型任务，可并发执行多个操作。

    Args:
        url: 请求的URL地址
        timeout: 超时时间（秒，默认: 30）

    Returns:
        请求结果字典：
        {
            "status": 200,
            "data": {...},
            "elapsed": 1.23  # 耗时（秒）
        }

    Raises:
        asyncio.TimeoutError: 当请求超时时
        aiohttp.ClientError: 当网络错误时

    Example:
        单个请求：
        >>> import asyncio
        >>> result = await async_function_template("https://api.example.com")
        >>> print(result["status"])
        200

        并发多个请求：
        >>> urls = ["url1", "url2", "url3"]
        >>> tasks = [async_function_template(url) for url in urls]
        >>> results = await asyncio.gather(*tasks)
        >>> print(len(results))
        3

    Note:
        - 并发优势：3个请求并发执行耗时约1秒，串行执行约3秒
        - 使用场景：批量API调用、并发下载、异步I/O
    """
    import asyncio
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=timeout) as response:
            data = await response.json()
            return {
                "status": response.status,
                "data": data,
                "elapsed": response.elapsed.total_seconds()
            }


# ============================================================
# 附录：Docstring风格指南
# ============================================================

"""
Docstring最佳实践：

1. 第一行（Summary）:
   - 必须是一句话，以句号结尾
   - 使用动词开头（函数）或名词短语（类）
   - 不超过80个字符
   - 例如："计算两个数的和."

2. 详细说明（Description）:
   - 第一行后空一行，然后写详细说明
   - 解释功能、原理、使用场景
   - 2-5句话为宜，不要过长

3. Args:
   - 每个参数占一行或多行
   - 格式：param_name: 类型和描述
   - 包含：含义、范围、默认值、示例
   - 可选参数注明"（可选）"或"（默认: xxx）"

4. Returns:
   - 明确说明返回值的类型和结构
   - 如果返回dict，列出所有字段
   - 如果有多种返回情况，逐一说明

5. Raises:
   - 列出所有可能抛出的异常
   - 说明什么情况下抛出
   - 格式：ExceptionType: 描述

6. Example:
   - 至少一个基本用法示例
   - 使用doctest格式（>>>）
   - 可以添加高级用法示例
   - 示例要可以直接运行

7. Note:
   - 重要的注意事项、限制、性能考虑
   - 使用bullet points
   - 每条简洁明了

8. See Also（可选）:
   - 相关函数、类、模块
   - 替代方案
   - 参考文档

格式规范：
- 缩进：4个空格
- 换行：每行不超过88个字符（遵循black格式化）
- 空行：各部分之间空一行
- 标点：中文文档使用中文标点，英文文档使用英文标点

常见错误：
❌ 第一行没有句号
❌ Args和Returns没有详细说明类型
❌ 没有Example
❌ 魔法数字没有解释
❌ 复杂算法没有说明原理
"""

# ============================================================
# END OF DOCSTRING TEMPLATES
# ============================================================
