from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .base.base import BaseHandler, HandlerRegistry


class DatasourcesResponse(BaseModel):
    names: list[str]
    sources: dict[str, str]


@HandlerRegistry.register
class DatasourceHandler(BaseHandler):
    path = "/datasources"
    name = "datasources"
    methods = ["GET"]
    query_params: list[str] = []
    description = "列出所有可用数据源名称"

    response_model = DatasourcesResponse

    async def handle(self, **kwargs: Any) -> DatasourcesResponse:
        resp =  {
            "兔兔（番茄）": "tutu",
            "沐凡（番茄）": "mufan"
        }
        names = ["兔兔（番茄）", "沐凡（番茄）"]
        return DatasourcesResponse(names=names, sources=resp)
