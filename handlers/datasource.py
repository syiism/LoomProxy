from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from base.base import BaseHandler, HandlerRegistry
from utils.cache import cached


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

    @cached(ttl=300)
    async def handle(self, **kwargs: Any) -> DatasourcesResponse:
        sources =  {
            "番茄（兔兔）": ["tutu", "fq"],
            "番茄（沐凡）": ["mufan", "fq"],
            "番茄（星海）": ["fq_xinghai", "fq"],
            "番茄（落幕）": ["luomu", ""],
            "番茄（鲸落）": ["jingluo", ""],
            "QQ阅读（落幕）": ["qq_luomu", ""],
            "七猫（落幕）": ["qm_luomu", ""],
            "书旗（落幕）": ["sq_luomu", ""]
        }
        names = ["番茄（兔兔）", "番茄（沐凡）", "番茄（星海）", "番茄（落幕）", "番茄（鲸落）", "QQ阅读（落幕）", "七猫（落幕）", "书旗（落幕）"]
        fileNames = {'fq': ['fq_moduleMap', 'fq_sytjs', 'fq_categorys']}
        
        return DatasourcesResponse(names=names, sources=sources, fileNames=fileNames)
