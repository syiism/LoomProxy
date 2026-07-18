from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from base.base import BaseHandler, HandlerRegistry


class DatasourcesResponse(BaseModel):
    names: list[str]
    sources: dict[str, list]
    fileNames: dict[str, list]


@HandlerRegistry.register
class DatasourceHandler(BaseHandler):
    path = "/datasources"
    name = "datasources"
    methods = ["GET"]
    query_params: list[str] = []
    description = "列出所有可用数据源名称"

    response_model = DatasourcesResponse

    async def handle(self, **kwargs: Any) -> DatasourcesResponse:
        sources =  {
            "番茄（兔兔）": ["tutu", "fq"],
            "番茄（沐凡）": ["mufan", "fq"],
            "番茄（洛牧）": ["luomu", "fq"]
        }
        names = ["番茄（兔兔）", "番茄（沐凡）", "番茄（洛牧）"]
        fileNames = {'fq': ['fq_moduleMap.json', 'fq_sytjs.json', 'fq_categorys.json']}
        
        return DatasourcesResponse(names=names, sources=sources, fileNames=fileNames)
