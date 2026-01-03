from starlette.requests import Request


async def simple_middleware(request: Request, call_next):
    """示例中间件：展示中间件的基本结构与用途。

    中间件（Middleware）是位于请求/响应管道中的代码，常用于：
    - 全局日志/审计；
    - 请求限流、鉴权预处理；
    - 修改请求或响应（例如添加 header）。

    参数说明：
    - `request`: Starlette/FastAPI 的 `Request` 对象，包含请求头、路径等；
    - `call_next`: 下一个处理器的可调用对象，调用它以继续执行后续路由处理并获得响应对象。

    这个 `simple_middleware` 当前只是一个“空操作（noop）”示例：它直接把请求传递下去并返回响应。
    初学者可以在 `call_next(request)` 前后加入日志或测量耗时来理解中间件的作用。
    """
    # 在这里可以添加前置逻辑，比如：记录请求路径、检查 header 等
    response = await call_next(request)
    # 在这里可以添加后置逻辑，比如：在响应中注入调试 header
    return response
