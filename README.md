# api-proxy

基于 FastAPI 的 API 代理服务，支持通过 handler 机制扩展多种数据源的搜索、详情、章节、内容接口。

## 快速开始

```bash
uv add fastapi httpx pydantic uvicorn
uv run python app.py
```

服务默认运行在 `http://0.0.0.0:8081`。

访问根路径 `http://0.0.0.0:8081/` 查看所有注册的路由列表。访问 `http://0.0.0.0:8081/docs` 查看自动生成的 API 文档。

## 依赖

- Python >= 3.13
- fastapi >= 0.139.0
- httpx >= 0.28.1
- pydantic >= 2.13.4
- uvicorn >= 0.51.0

## 项目结构

```
.
├── app.py                    # 应用入口，自动注册路由
├── pyproject.toml            # 项目配置与依赖
├── handlers/
│   ├── __init__.py           # 自动发现 handler 模块
│   ├── base/                 # 基础处理器与注册表
│   │   ├── __init__.py
│   │   ├── base.py           # HandlerRegistry, BaseHandler
│   │   ├── searchBase.py     # 搜索接口基类 (SearchResponse, BookItem)
│   │   ├── detailBase.py     # 详情接口基类 (BookDetail)
│   │   ├── chapterBase.py    # 章节接口基类 (ChapterResponse, ChapterItem)
│   │   └── contentBase.py    # 内容接口基类 (ContentResponse)
│   └── tutu/                 # tutu 数据源实现
│       ├── __init__.py
│       ├── search.py         # 搜索处理
│       ├── detail.py         # 详情处理
│       ├── chapter.py        # 章节处理
│       └── content.py        # 内容处理（小说/听书/漫画/短剧）
├── tests/
│   ├── conftest.py
│   └── test_content.py
└── AGENTS.md
```

## 架构说明

### 开闭原则

- **对扩展开放**：在 `handlers/` 下新建子目录，编写 handler 模块，继承 `base/` 中的基础处理器并用 `@HandlerRegistry.register` 装饰，启动自动注册
- **对修改封闭**：`app.py` 核心启动逻辑无需改动

### 路由注册流程

`handlers/__init__.py` → `_auto_discover()` 遍历 `handlers/` 子包 → 触发 `@HandlerRegistry.register` → `app.py` 调用 `get_all_handlers()` 获取所有处理器，动态生成路由闭包 → FastAPI `add_api_route` 注册

### 关键组件

| 组件 | 路径 | 说明 |
|------|------|------|
| `HandlerRegistry` | `handlers/base/base.py:13` | 全局路由注册表，支持有参/无参装饰器，`__init_subclass__` 保证子类独立 `_items` |
| `BaseHandler` | `handlers/base/base.py:59` | 抽象基类，定义 `path`/`name`/`methods`/`query_params`/`description`/`handle` |

### 响应模型

| 模型 | 定义位置 | 用途 |
|------|---------|------|
| `SearchResponse` / `BookItem` | `handlers/base/searchBase.py` | 搜索接口返回 |
| `BookDetail` | `handlers/base/detailBase.py` | 详情接口返回 |
| `ChapterResponse` / `ChapterItem` | `handlers/base/chapterBase.py` | 章节接口返回 |
| `ContentResponse` | `handlers/base/contentBase.py` | 内容接口返回（统一分发） |

## 新增数据源步骤

1. 在 `handlers/` 下新建子目录（如 `tutu/`）
2. 编写 handler 文件，继承 `base/` 中的基础处理器
3. 用 `@HandlerRegistry.register` 装饰，设置 `path`/`name`/`methods`/`query_params`
4. 实现 `handle` 方法
5. 创建 `__init__.py`，`from . import <module>` 触发注册

## 数据源：tutu

| 接口 | 路径 | 参数 |
|------|------|------|
| 搜索 | `/tutu/search` | `base_url`, `query`, `offset`, `count`, `tab_type` |
| 详情 | `/tutu/detail` | `base_url`, `book_id` |
| 章节 | `/tutu/chapter` | `base_url`, `book_id` |
| 内容 | `/tutu/content` | `base_url`, `book_id`, `item_id`, `tone_id`, `quality` |

`/tutu/content` 自动根据 `book_id` 识别类型分发：小说→文、听书→音频、漫画→图片、短剧/漫剧→视频。](

### tutu 类型识别

详情接口自动识别书籍类型：

| 类型 | 判断条件 |
|------|---------|
| `tingshu` 听书 | `book_type == "1"` 或 `genre == "4"` |
| `manhua` 漫画 | `comic_book_type` 存在或 `genre == "1"` |
| `duanju` 短剧 | `playlet_book_id` 存在，或 `genre == "205"` 且有 `album_book_order`，或 `genre == "203"` |
| `manju` 漫剧 | `genre == "205"` 且有 `schedule_mode`（无 `album_book_order`） |
| `xiaoshuo` 小说 | `is_ebook == "1"` 或 `genre == "0"` |

## 编码规范

- **导入路径**：包内使用相对导入（`from ..base.searchBase import ...`），避免绝对导入
- **`**kwargs`**：使用 `kwargs.get("key", default)` 而非 `kwargs["key"]` 或 `.pop()`
- **时间处理**：时间戳统一 UTC+8，`_format_time` / `_format_create_time` 格式化
- **异步 HTTP**：使用 `httpx.AsyncClient`，设 `Timeout(10.0, connect=5.0)`
- **响应模型**：`handle` 返回 Pydantic `BaseModel` 实例，`app.py` 自动 `model_dump()`
- **路由对**：不含 `query_params` 中未声明的参数，运行时 `request.query_params` 透传所有参数
- **URL 拼接**：使用 `f"{base_url.rstrip('/')}/search?..."` 避免双斜杠
