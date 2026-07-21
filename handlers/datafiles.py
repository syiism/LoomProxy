from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from typing_extensions import TypedDict

from base.base import HandlerRegistry, BaseHandler
from confMagr import ConfMagr
from utils.cache import cached

_DATA_ROOT = Path(__file__).resolve().parent.parent / ConfMagr.DATA_DIR


class FileInfo(BaseModel):
    name: str
    filename: str
    size: int
    description: str


class SourceInfo(BaseModel):
    file_count: int
    files: list[FileInfo]


class SourcesResponse(BaseModel):
    count: int
    sources: dict[str, SourceInfo]


class FileListResponse(BaseModel):
    source: str
    count: int
    files: list[FileInfo]


class FileContentResponse(BaseModel):
    source: str
    name: str
    filename: str
    size: int
    description: str
    data: Any


class ErrorResponse(BaseModel):
    error: str
    available: list[str]


def _data_dir(source: str) -> Path:
    return _DATA_ROOT / source


def _list_sources() -> list[str]:
    sources: list[str] = []
    if not _DATA_ROOT.is_dir():
        return sources
    for p in _DATA_ROOT.iterdir():
        if p.is_dir():
            sources.append(p.name)
    return sorted(sources)


_FILE_DESCRIPTIONS: dict[str, str] = {
    "fq_moduleMap": "模式映射（tab_type → bd_id）",
    "fq_sytjs": "推荐首页 tab_type 列表",
    "fq_categorys": "分类/榜单配置（genre_tab → 子榜列表）",
}


def _file_info(path: Path) -> FileInfo:
    stat = path.stat()
    return FileInfo(
        name=path.stem,
        filename=path.name,
        size=stat.st_size,
        description=_FILE_DESCRIPTIONS.get(path.stem, ""),
    )


def _list_files(source: str) -> list[FileInfo]:
    d = _data_dir(source)
    if not d.is_dir():
        return []
    return [_file_info(p) for p in sorted(d.glob(ConfMagr.DATA_FILE_GLOB))]


def _load_json(source: str, name: str) -> Any:
    path = _data_dir(source) / f"{name}.json"
    if not path.is_file():
        return None
    with open(path) as f:
        return json.load(f)


@HandlerRegistry.register
class DataFilesHandler(BaseHandler):
    path = "/data"
    name = "data_files"
    methods = ["GET"]
    query_params = ["source", "name"]
    description = "静态数据文件。source 指定数据源（如 fq），name 指定文件名（不含后缀）；缺省时列出可用数据源或文件"
    auth_required = False
    response_model = SourcesResponse | FileListResponse | FileContentResponse | ErrorResponse

    @cached(ttl=300)
    async def handle(self, **kwargs: Any) -> SourcesResponse | FileListResponse | FileContentResponse | ErrorResponse:
        source = kwargs.get("source", "")
        name = kwargs.get("name", "")

        if source and name:
            data = _load_json(source, name)
            if data is None:
                available = [f.name for f in _list_files(source)]
                return ErrorResponse(error=f"file '{name}.json' not found in source '{source}'", available=available)
            info = _file_info(_data_dir(source) / f"{name}.json")
            return FileContentResponse(
                source=source, data=data,
                name=info.name, filename=info.filename,
                size=info.size, description=info.description,
            )

        if source:
            files = _list_files(source)
            result: list[FileInfo] = []
            for f in files:
                if _load_json(source, f.name) is not None:
                    result.append(f)
            return FileListResponse(source=source, count=len(result), files=result)

        sources = _list_sources()
        return SourcesResponse(
            count=len(sources),
            sources={s: SourceInfo(file_count=len(_list_files(s)), files=_list_files(s)) for s in sources},
        )
