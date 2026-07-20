"""
应用入口（遵循开闭原则）：
  1. 启动 FastAPI
  2. 自动扫描 handlers/ 目录下所有 BaseHandler 子类，注册为路由
扩展 API 端点：在 handlers/ 下新建子目录，在其中编写 handler 模块，
               继承 base/ 中的基础处理器并用 @HandlerRegistry.register 装饰，
               启动时将自动注册为路由，无需修改本文件。
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, create_model, field_validator

from confMagr import ConfMagr
from handlers import BaseHandler, get_all_handlers
from utils.network import is_safe_url

logger = logging.getLogger("LoomProxy")

# ------ 已知数据源的预期路由（按数据源+动作）------
EXPECTED_ROUTES: dict[str, list[str]] = {
    "tutu": ["search", "detail", "chapter", "content", "recommend", "rank", "related", "author"],
    "mufan": ["search", "detail", "chapter", "content", "front", "landing", "recommend", "rank"],
    "fq_xinghai": ["search", "detail", "chapter", "content", "recommend", "rank"],
    "luomu": ["search", "detail", "chapter", "content"],
    "jingluo": ["search", "detail", "chapter", "content"],
    "qq_luomu": ["search", "detail", "chapter", "content"],
    "qm_luomu": ["search", "detail", "chapter", "content"],
    "sq_luomu": ["search", "detail", "chapter", "content"],
}


# ------ Pydantic 查询模型工厂 ------
_PARAM_FIELD_DEFS: dict[str, tuple[type, Any]] = {
    "base_url": (str | None, None),
    "query": (str | None, None),
    "offset": (str | None, None),
    "count": (str | None, None),
    "book_id": (str | None, None),
    "item_id": (str | None, None),
    "tone_id": (str | None, None),
    "quality": (str | None, None),
    "tab_type": (str | None, None),
    "search_type": (str | None, None),
    "tab": (str | None, None),
    "category_id": (str | None, None),
    "genre_type": (str | None, None),
    "gender": (str | None, None),
    "word_number": (str | None, None),
    "book_status": (str | None, None),
    "sort_by": (str | None, None),
    "genre_tab": (str | None, None),
    "algo_type": (str | None, None),
    "limit": (str | None, None),
    "author_id": (str | None, None),
    "rank_sub_info_id": (str | None, None),
    "page": (str | None, None),
    "name": (str | None, None),
    "source": (str | None, None),
}


def _make_query_model(params: list[str]) -> type[BaseModel]:
    fields: dict[str, tuple[type, Any]] = {}
    for p in params:
        if p in _PARAM_FIELD_DEFS:
            fields[p] = _PARAM_FIELD_DEFS[p]
        else:
            fields[p] = (str | None, None)
    return create_model("DynamicQuery", **fields)


# ------ 路由注册验证 ------
def _validate_routes(registered: list[dict[str, Any]]) -> None:
    registered_paths = {r["path"] for r in registered}
    for source, actions in EXPECTED_ROUTES.items():
        for action in actions:
            expected = f"/{source}/{action}"
            if expected not in registered_paths:
                logger.critical(
                    "预期路由 %s 未注册（数据源 %s 的 %s 接口缺失）",
                    expected, source, action,
                )
                raise RuntimeError(f"数据源 {source} 的 {action} 接口缺失，请检查 handler 注册")


# ------- 对修改关闭/对扩展开放 -------
def _make_endpoint(handler_cls: type[BaseHandler]) -> dict[str, Any]:
    """为每个 handler 动态生成一个独立的路由闭包。"""
    instance: BaseHandler = handler_cls()
    methods: list[str] = list(instance.methods or ["GET"])
    params: list[str] = list(instance.query_params or [])

    query_model = _make_query_model(params) if params else None

    if query_model:
        async def endpoint(query: BaseModel = Depends(query_model)) -> JSONResponse:
            all_kwargs = {k: v for k, v in query.model_dump().items() if v is not None}
            _validate_base_url(all_kwargs)
            body = await instance.handle(**all_kwargs)
            if isinstance(body, BaseModel):
                body = body.model_dump()
            return JSONResponse(body)
    else:
        async def endpoint() -> JSONResponse:
            body = await instance.handle()
            if isinstance(body, BaseModel):
                body = body.model_dump()
            return JSONResponse(body)

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


def _validate_base_url(kwargs: dict[str, Any]) -> None:
    base_url = kwargs.get("base_url")
    if base_url and not is_safe_url(base_url):
        raise ValueError(f"不安全的 base_url: {base_url}")


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


# ------ 统一异常处理 ------
def _register_exception_handlers(fastapi_app: FastAPI) -> None:
    @fastapi_app.exception_handler(httpx.HTTPStatusError)
    async def httpx_status_error_handler(request: Request, exc: httpx.HTTPStatusError) -> JSONResponse:
        logger.warning("上游 HTTP %s: %s", exc.response.status_code, exc.request.url)
        return JSONResponse(
            status_code=502,
            content={"code": ConfMagr.ERROR_CODE, "msg": f"上游返回异常状态码 {exc.response.status_code}"},
        )

    @fastapi_app.exception_handler(httpx.TimeoutException)
    async def httpx_timeout_handler(request: Request, exc: httpx.TimeoutException) -> JSONResponse:
        logger.warning("上游请求超时: %s", exc.request.url if exc.request else "")
        return JSONResponse(
            status_code=504,
            content={"code": ConfMagr.ERROR_CODE, "msg": "上游请求超时"},
        )

    @fastapi_app.exception_handler(httpx.HTTPError)
    async def httpx_error_handler(request: Request, exc: httpx.HTTPError) -> JSONResponse:
        logger.warning("上游请求异常: %s", exc)
        return JSONResponse(
            status_code=502,
            content={"code": ConfMagr.ERROR_CODE, "msg": "上游数据异常"},
        )

    @fastapi_app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        logger.warning("参数校验失败: %s", exc)
        return JSONResponse(
            status_code=400,
            content={"code": ConfMagr.ERROR_CODE, "msg": str(exc)},
        )

    @fastapi_app.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
        logger.warning("数据解析缺少字段: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"code": ConfMagr.ERROR_CODE, "msg": f"数据解析异常：缺少字段 {exc}"},
        )

    @fastapi_app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("未捕获异常", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"code": ConfMagr.ERROR_CODE, "msg": "内部服务异常"},
        )


# ------ 组装 ------
def create_app() -> FastAPI:
    fastapi_app = FastAPI(title="LoomProxy")
    _register_exception_handlers(fastapi_app)
    registered_routes = register_handlers(fastapi_app)
    _validate_routes(registered_routes)

    @fastapi_app.get("/", include_in_schema=True, tags=["health"])
    async def root_health() -> dict[str, Any]:
        return {
            "app": "LoomProxy",
            "status": "ok",
            "endpoints": registered_routes,
        }

    return fastapi_app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=ConfMagr.SERVER_HOST, port=ConfMagr.SERVER_PORT, log_level=ConfMagr.SERVER_LOG_LEVEL)
