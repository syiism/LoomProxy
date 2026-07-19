# api-proxy AGENTS.md

## 项目概述

基于 FastAPI 的 API 代理服务，支持通过 handler 机制扩展多种数据源的搜索、详情、章节、内容、探索接口。

## 架构说明

### 三层单向依赖

```
base/  ──→  (无依赖，纯抽象)
utils/ ──→  base/ (引用 BookItem 等模型)
handlers/ → base/ + utils/ (具体实现)
```

### 开闭原则

- **对扩展开放**：在 `handlers/` 下新建子目录，编写 handler 模块，继承 `base/` 中的基础处理器并用 `@HandlerRegistry.register` 装饰，启动自动注册
- **对修改封闭**：`app.py` 核心启动逻辑无需改动

### 路由注册流程

`handlers/__init__.py` → `_auto_discover()` 遍历 `handlers/` 子包 → 触发 `@HandlerRegistry.register` → `app.py` 调用 `get_all_handlers()` 获取所有处理器，动态生成路由闭包 → FastAPI `add_api_route` 注册

### 关键组件

| 组件 | 路径 | 说明 |
|------|------|------|
| `HandlerRegistry` | `base/base.py:13` | 全局路由注册表，支持有参/无参装饰器 |
| `BaseHandler` | `base/base.py:44` | 抽象基类，定义 `path`/`name`/`methods`/`query_params`/`description`/`handle` |
| `app.py` | `app.py:23` | `_make_endpoint` 动态生成路由闭包，`register_handlers` 批量注册 |

### 响应模型

| 模型 | 定义位置 | 用途 |
|------|---------|------|
| `SearchResponse` / `BookItem` | `base/searchBase.py` | 搜索接口返回 |
| `BookDetail` | `base/detailBase.py` | 详情接口返回 |
| `ChapterResponse` / `ChapterItem` | `base/chapterBase.py` | 章节接口返回 |
| `ContentResponse` | `base/contentBase.py` | 内容接口返回 |
| `ExploreResponse` | `base/exploreBase.py` | 探索接口返回（bookList） |
| `DatasourcesResponse` | `handlers/datasource.py` | 数据源列表返回 |

### 共享工具（utils/fq_utils.py）

| 函数/常量 | 说明 |
|-----------|------|
| `normalize_api_base(base_url, prefix)` | 统一拼接 API 基础路径 |
| `strip_search_prefix(query)` | 去除 Legado 书源前缀 `+1/+3/+11/+19` |
| `normalize_video_item(item)` | 从 `card_tips` / `secondary_info_list` 补齐视频项字段 |
| `extract_book_data(obj)` | 递归提取嵌套响应中的 `book_data` / `video_data` |
| `build_book_kind(item)` / `build_video_kind(item)` | 拼接 `kind` 字段 |
| `build_book_item(item)` | 构建 `BookItem`（自动区分书籍/视频） |
| `_detect_book_type(data)` / `book_type_code(type)` | 番茄系类型识别 |
| `DEFAULT_TIMEOUT` / `TZ_SHANGHAI` / `GENDER_MAP` / `CREATION_STATUS_MAP` | 共享常量 |

### 端点：数据源列表 / 静态数据

| 端点 | 路径 | 说明 |
|------|------|------|
| 数据源列表 | `GET /datasources` | 返回所有可用数据源名称 |
| 静态数据 | `GET /data` | 返回静态 JSON 数据文件（`?source=fq&name=fq_moduleMap`） |

## 项目结构

```
.
├── app.py                    # 应用入口，自动注册路由
├── base/                     # 抽象层（纯 Pydantic 模型 + 基类）
│   ├── __init__.py
│   ├── base.py               # HandlerRegistry, BaseHandler
│   ├── searchBase.py         # 搜索接口基类 (SearchResponse, BookItem)
│   ├── detailBase.py         # 详情接口基类 (BookDetail)
│   ├── chapterBase.py        # 章节接口基类 (ChapterResponse, ChapterItem)
│   ├── contentBase.py        # 内容接口基类 (ContentResponse)
│   └── exploreBase.py        # 探索接口基类 (ExploreResponse)
├── utils/                    # 共享工具
│   ├── __init__.py
│   ├── fq_utils.py           # 番茄系通用工具函数
│   └── fq_data/              # 番茄系静态 JSON 数据
│       ├── fq_categorys.json
│       ├── fq_moduleMap.json
│       └── fq_sytjs.json
├── handlers/                 # 具体实现层
│   ├── __init__.py           # 自动发现 handler 模块
│   ├── datafiles.py          # /data 端点
│   ├── datasource.py         # /datasources 端点
│   ├── tutu/                 # 番茄（兔兔）
│   ├── mufan/                # 番茄（沐凡）
│   ├── fq_xinghai/           # 番茄（星海）
│   ├── luomu/                # 番茄（落幕）
│   ├── jingluo/              # 番茄（鲸落）
│   ├── qq_luomu/             # QQ阅读（落幕）
│   ├── qm_luomu/             # 七猫（落幕）
│   └── sq_luomu/             # 书旗（落幕）
├── tests/
│   ├── conftest.py
│   └── test_content.py
└── AGENTS.md
```

### 新增数据源步骤

1. 在 `handlers/` 下新建子目录（如 `tutu/`）
2. 编写 handler 文件，继承 `base/` 中的基础处理器
3. 用 `@HandlerRegistry.register` 装饰，设置 `path`/`name`/`methods`/`query_params`
4. 实现 `handle` 方法，返回 Pydantic `BaseModel` 实例
5. 创建 `__init__.py`，`from . import <module>` 触发注册
6. 如需共享工具，从 `utils/fq_utils.py` 导入（番茄系）或创建 `utils/{source}_utils.py`

### 静态数据文件

在 `utils/` 下创建 `{source}_data/` 目录，放入 `{source}_*.json` 文件即可被 `/data` 端点自动发现。

## 已实现的数据源

### tutu（番茄（兔兔））

| 接口 | 路径 | 参数 |
|------|------|------|
| 搜索 | `/tutu/search` | `base_url`, `query`, `offset`, `count`, `tab_type` |
| 详情 | `/tutu/detail` | `base_url`, `book_id` |
| 章节 | `/tutu/chapter` | `base_url`, `book_id` |
| 内容 | `/tutu/content` | `base_url`, `book_id`, `item_id`, `tone_id`, `quality` |
| 首页推荐 | `/tutu/recommend` | `base_url`, `tab_type`, `offset` |
| 排行榜 | `/tutu/rank` | `base_url`, `book_id`, `offset`, `genre_tab`, `rank_sub_info_id`, `algo_type` |
| 相关作品 | `/tutu/related` | `base_url`, `book_id` |
| 作者作品 | `/tutu/author` | `base_url`, `author_id` |

内容接口自动根据 `book_id` 识别类型分发。API 前缀 `/api/v1`。

#### tutu 搜索数据解析

- `parse_tab_item`：递归解析 `search_tabs`，收集 `book_data`（书籍）/ `video_data`（视频）/ `abstract` 节点

### mufan（番茄（沐凡））

| 接口 | 路径 | 参数 |
|------|------|------|
| 搜索 | `/mufan/search` | `base_url`, `query`, `offset`, `count`, `tab_type`, `search_type` |
| 详情 | `/mufan/detail` | `base_url`, `book_id` |
| 章节 | `/mufan/chapter` | `base_url`, `book_id` |
| 内容 | `/mufan/content` | `base_url`, `book_id`, `item_id`, `tone_id`, `quality` |
| 发现分类 | `/mufan/front` | `base_url`, `tab` |
| 分类书籍 | `/mufan/landing` | `base_url`, `category_id`, `offset`, `genre_type`, `gender`, `word_number`, `book_status`, `sort_by` |
| 首页推荐 | `/mufan/recommend` | `base_url`, `tab_type`, `offset` |
| 排行榜 | `/mufan/rank` | `base_url`, `genre_tab`, `algo_type`, `offset`, `limit` |

内容接口自动根据 `book_id` 识别类型分发。API 前缀 `/api`。

### fq_xinghai（番茄（星海））

| 接口 | 路径 | 参数 |
|------|------|------|
| 搜索 | `/fq_xinghai/search` | `base_url`, `query`, `offset`, `tab_type` |
| 详情 | `/fq_xinghai/detail` | `base_url`, `book_id` |
| 章节 | `/fq_xinghai/chapter` | `base_url`, `book_id` |
| 内容 | `/fq_xinghai/content` | `base_url`, `book_id`, `item_id`, `tone_id`, `quality` |
| 首页推荐 | `/fq_xinghai/recommend` | `base_url`, `tab_type`, `offset` |
| 排行榜 | `/fq_xinghai/rank` | `base_url`, `book_id`, `offset`, `genre_tab`, `rank_sub_info_id`, `algo_type` |

- API 前缀 `/api/v1`，所有接口带 `filter=none` 参数
- 内容：音频响应格式为平铺 list `[{"main_url","backup_url",...}]`；视频响应格式为 `{"play":{"play_url","decrypt_url","cek",...}}`

### luomu（番茄（落幕））

| 接口 | 路径 | 参数 |
|------|------|------|
| 搜索 | `/luomu/search` | `base_url`, `query`, `offset`, `count`, `tab_type` |
| 详情 | `/luomu/detail` | `base_url`, `book_id` |
| 章节 | `/luomu/chapter` | `base_url`, `book_id` |
| 内容 | `/luomu/content` | `base_url`, `book_id`, `item_id`, `tone_id`, `quality` |

API 无统一前缀，`normalize_api_base(base_url, "")`。

### jingluo（番茄（鲸落））

| 接口 | 路径 | 参数 |
|------|------|------|
| 搜索 | `/jingluo/search` | `base_url`, `query`, `offset`, `count`, `tab_type` |
| 详情 | `/jingluo/detail` | `base_url`, `book_id` |
| 章节 | `/jingluo/chapter` | `base_url`, `book_id` |
| 内容 | `/jingluo/content` | `base_url`, `book_id`, `item_id`, `tone_id`, `quality` |

API 无统一前缀，`normalize_api_base(base_url, "")`。章节使用 `real_chapter_order` 字段。

### qq_luomu（QQ阅读（落幕））

| 接口 | 路径 | 参数 |
|------|------|------|
| 搜索 | `/qq_luomu/search` | `base_url`, `query`, `offset` |
| 详情 | `/qq_luomu/detail` | `base_url`, `book_id` |
| 章节 | `/qq_luomu/chapter` | `base_url`, `book_id` |
| 内容 | `/qq_luomu/content` | `base_url`, `book_id`, `item_id` |

### qm_luomu（七猫（落幕））

| 接口 | 路径 | 参数 |
|------|------|------|
| 搜索 | `/qm_luomu/search` | `base_url`, `query`, `offset` |
| 详情 | `/qm_luomu/detail` | `base_url`, `book_id` |
| 章节 | `/qm_luomu/chapter` | `base_url`, `book_id` |
| 内容 | `/qm_luomu/content` | `base_url`, `book_id`, `item_id` |

### sq_luomu（书旗（落幕））

| 接口 | 路径 | 参数 |
|------|------|------|
| 搜索 | `/sq_luomu/search` | `base_url`, `query`, `offset` |
| 详情 | `/sq_luomu/detail` | `base_url`, `book_id` |
| 章节 | `/sq_luomu/chapter` | `base_url`, `book_id` |
| 内容 | `/sq_luomu/content` | `base_url`, `book_id`, `item_id` |

#### 番茄系类型识别

| 类型 | 判断条件 |
|------|---------|
| `tingshu` 听书 | `book_type == "1"` 或 `genre == "4"` |
| `manhua` 漫画 | `comic_book_type` 存在或 `genre == "1"` |
| `duanju` 短剧 | `playlet_book_id` 存在，或 `genre == "205"` 且有 `album_book_order`，或 `genre == "203"` |
| `manju` 漫剧 | `genre == "205"` 且有 `schedule_mode`（无 `album_book_order`） |
| `xiaoshuo` 小说 | `is_ebook == "1"` 或 `genre == "0"` |

## 添加数据源方法论

以下步骤适用于添加任意新数据源，不依赖特定上游 API 风格。

### 第一步：创建目录与注册入口

```
handlers/{source}/
├── __init__.py          # from . import module1, module2, ...
└── search.py            # (示例) 搜索 handler
```

`__init__.py` 必须显式 import 各模块以触发 `@HandlerRegistry.register`。无需修改 `handlers/__init__.py` 或 `app.py`。

### 第二步：按接口类型选择基类

| 接口语义 | 基类 | 返回模型 | 典型路径 |
|----------|------|----------|----------|
| 搜索 | `SearchBaseHandler` | `SearchResponse` | `/{source}/search` |
| 详情 | `DetailBaseHandler` | `BookDetail` | `/{source}/detail` |
| 章节 | `ChapterBaseHandler` | `ChapterResponse` | `/{source}/chapter` |
| 内容 | `ContentBaseHandler` | `ContentResponse` | `/{source}/content` |
| 探索/推荐/榜单 | `ExploreBaseHandler` | `ExploreResponse` | `/{source}/recommend` 等 |
| 非标准接口 | `BaseHandler` | 自定 | 自定 |

**原则**：一个 handler 只做一个接口，不合并多个语义到同一个类。

### 第三步：实现 Handler

```python
@HandlerRegistry.register
class XxxSearchHandler(SearchBaseHandler):
    path = "/{source}/search"
    name = "{source}_search"
    methods = ["GET"]
    query_params = ["base_url", "query", ...]
    description = "..."
    # 可选：response_model 默认继承基类，也可覆盖

    async def handle(self, **kwargs: Any) -> SearchResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api/v1")
        query = kwargs.get("query", "")
        ...
        return SearchResponse(bookList=[...])
```

**要点**：
- `path` 以 `/{source}/` 开头，数据源间路径不冲突
- `query_params` 声明所有接收的参数名，未声明的参数会被忽略
- 内部使用 `kwargs.get(key, default)`，不抛 KeyError
- `normalize_api_base(base_url, prefix)` 统一处理 API 前缀，prefix 参数对每个数据源可不同

### 第四步：创建数据源工具模块

当数据源有特定字段映射或解析逻辑时：

```
utils/{source}_utils.py    # 数据源专用工具
utils/{source}_data/       # 可选：静态 JSON 数据
```

**判断标准**：
- 逻辑只被一个数据源引用 → 放在 `handlers/{source}/` 模块内部
- 逻辑可被同系列数据源复用 → 提取到 `utils/{source}_utils.py`
- 逻辑完全不依赖数据源（时间、HTTP、通用提取） → 复用 `utils/fq_utils.py`

### 第五步：注册到数据源列表

修改 `handlers/datasource.py`，在 `handle` 方法中添加数据源信息和名称：

```python
resp = {
    "...": "{source}",
    ...
}
names = [...]
return DatasourcesResponse(names=names, sources=resp)
```

### 第六步（可选）：添加静态数据

在 `utils/` 下创建 `{source}_data/` 目录，放入 `{source}_*.json` 文件，`GET /data?source={source}` 自动发现。

### 接口设计约定

- **路径格式**：`/{source}/{action}`（如 `/tutu/search`、`/mufan/rank`）
- **参数风格**：统一使用 query string 参数，不依赖 path 参数或 request body
- **`base_url`**：每个 handler 的第一个参数，用户指定上游服务地址
- **前缀处理**：不同数据源可能使用不同 API 前缀（如 `/api/v1` vs `/api`），通过 `normalize_api_base(base_url, prefix)` 的 `prefix` 参数区分

### 辅助函数复用策略

| 场景 | 推荐做法 |
|------|----------|
| 上游响应含嵌套 `book_data`/`video_data` | 复用 `extract_book_data` |
| 构建 `BookItem`（书籍/视频混合） | 复用 `build_book_item` |
| 拼接书籍 `kind` 字段 | 复用 `build_book_kind` |
| 拼接视频 `kind` 字段 | 复用 `build_video_kind` |
| 去除 Legado 搜索前缀 `+1/+3/+11/+19` | 复用 `strip_search_prefix` |
| 视频字段归一化（`card_tips` → `rec_text`） | 复用 `normalize_video_item` |
| 检测番茄系书籍类型 | 复用 `_detect_book_type` |
| 需要自定义字段映射 | 在 `{source}_utils.py` 中自行实现 |

## 编码规范

- **导入路径**：使用绝对导入（`from base.searchBase import ...` / `from utils.fq_utils import ...`）
- **`**kwargs`**：使用 `kwargs.get("key", default)` 而非 `kwargs["key"]` 或 `.pop()`
- **时间处理**：时间戳统一 UTC+8，使用 `TZ_SHANGHAI` 常量
- **异步 HTTP**：使用 `httpx.AsyncClient`，设 `DEFAULT_TIMEOUT`
- **响应模型**：`handle` 返回 Pydantic `BaseModel` 实例，`app.py` 自动 `model_dump()`
- **`normalize_api_base`**：统一使用 `normalize_api_base(base_url, prefix)` 拼接 API 基础路径，而非手动 `rstrip`/`endswith`
- **URL 拼接**：`url = f"{base_url.rstrip('/')}/path?param={value}"`
