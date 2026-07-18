"""
应用入口（遵循开闭原则）：
  1. 启动 FastAPI
  2. 自动扫描 handlers/ 目录下所有 BaseHandler 子类，注册为路由
扩展 API 端点：在 handlers/ 下新建子目录，在其中编写 handler 模块，
               继承 base/ 中的基础处理器并用 @HandlerRegistry.register 装饰，
               启动时将自动注册为路由，无需修改本文件。
"""

from __future__ import annotations

import inspect
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from handlers import BaseHandler, get_all_handlers


# ------- 对修改关闭/对扩展开放 -------
def _make_endpoint(handler_cls: type[BaseHandler]) -> dict[str, Any]:
    """为每个 handler 动态生成一个独立的路由闭包。"""
    instance: BaseHandler = handler_cls()
    methods: list[str] = list(instance.methods or ["GET"])
    params: list[str] = list(instance.query_params or [])

    async def endpoint(request: Request, **kwargs: Any) -> JSONResponse:
        all_kwargs = dict(request.query_params)
        body = await instance.handle(**all_kwargs)
        if isinstance(body, BaseModel):
            body = body.model_dump()
        return JSONResponse(body)

    sig_params = []
    for name in params:
        sig_params.append(
            inspect.Parameter(
                name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=Query(None, description=f"Query parameter: {name}"),
            )
        )
    sig_params.append(
        inspect.Parameter(
            "request",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=...,
            annotation=Request,
        )
    )
    endpoint.__signature__ = inspect.Signature(parameters=sig_params)

    return {
        "path": instance.path,
        "methods": methods,
        "name": instance.name or handler_cls.__name__,
        "description": instance.description or None,
        "summary": instance.description or None,
        "params": params,
        "endpoint": endpoint,
        "handler": handler_cls.__name__,
        "response_model": getattr(instance, "response_model", None),
    }


# ------- 注册 -------
def register_handlers(fastapi_app: FastAPI) -> list[dict[str, Any]]:
    """遍历注册表中的所有 handler 注册为路由。"""
    registered: list[dict[str, Any]] = []
    for item in (_make_endpoint(c) for c in get_all_handlers()):
        fastapi_app.add_api_route(
            item["path"],
            item["endpoint"],
            methods=item["methods"],
            name=item["name"],
            summary=item["summary"],
            description=item["description"],
            response_model=item.get("response_model"),
        )
        registered.append({
            "path": item["path"],
            "description": item["description"],
            "methods": item["methods"],
            "params": item["params"],
            "handler": item["handler"],
        })
    return registered


# ------ 组装 ------
def create_app() -> FastAPI:
    fastapi_app = FastAPI(title="api-proxy")
    registered_routes = register_handlers(fastapi_app)

    @fastapi_app.get("/", include_in_schema=True, tags=["health"])
    async def root_health() -> dict[str, Any]:
        return {
            "app": "api-proxy",
            "status": "ok",
            "endpoints": registered_routes,
        }

    return fastapi_app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")
