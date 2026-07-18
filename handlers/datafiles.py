from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from base.base import HandlerRegistry, BaseHandler

_UTILS_DIR = Path(__file__).resolve().parent.parent / "utils"


def _data_dir(source: str) -> Path:
    return _UTILS_DIR / f"{source}_data"


def _list_sources() -> list[str]:
    sources: list[str] = []
    for p in _UTILS_DIR.iterdir():
        if p.is_dir() and p.name.endswith("_data"):
            sources.append(p.name.removesuffix("_data"))
    return sorted(sources)


def _list_files(source: str) -> dict[str, str]:
    files: dict[str, str] = {}
    d = _data_dir(source)
    if not d.is_dir():
        return files
    for p in sorted(d.glob(f"{source}_*.json")):
        files[p.stem] = p.name
    return files


def _load_json(source: str, name: str) -> dict[str, Any] | list[Any] | None:
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

    async def handle(self, **kwargs: Any) -> dict[str, Any]:
        source = kwargs.get("source", "")
        name = kwargs.get("name", "")

        if source and name:
            data = _load_json(source, name)
            if data is None:
                available = list(_list_files(source).keys())
                return {"error": f"file '{name}.json' not found in source '{source}'", "available": available}
            return {"source": source, "name": name, "data": data}

        if source:
            files = _list_files(source)
            result: dict[str, Any] = {}
            for stem in files:
                data = _load_json(source, stem)
                if data is not None:
                    result[stem] = data
            return {"source": source, "files": result}

        sources = _list_sources()
        return {
            "sources": {s: list(_list_files(s).keys()) for s in sources},
        }
