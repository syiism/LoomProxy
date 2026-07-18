# api-proxy AGENTS.md

## 项目概述

基于 FastAPI 的 API 代理服务，支持通过 handler 机制扩展多种数据源的搜索、详情、章节接口。

## 架构说明

### 开闭原则

- **对扩展开放**：在 `handlers/` 下新建子目录，编写 handler 模块，继承 `base/` 中的基础处理器并用 `@HandlerRegistry.register` 装饰，启动自动注册
- **对修改封闭**：`app.py` 核心启动逻辑无需改动

### 路由注册流程

`handlers/__init__.py` → `_auto_discover()` 遍历 `handlers/` 子包 → 触发 `@HandlerRegistry.register` → `app.py` 调用 `get_all_handlers()` 获取所有处理器，动态生成路由闭包 → FastAPI `add_api_route` 注册

### 关键组件

| 组件 | 路径 | 说明 |
|------|------|------|
| `HandlerRegistry` | `handlers/base/base.py:13` | 全局路由注册表，支持有参/无参装饰器 |
| `BaseHandler` | `handlers/base/base.py:59` | 抽象基类，定义 `path`/`name`/`methods`/`query_params`/`description`/`handle` |
| `app.py` | `app.py:23` | `_make_endpoint` 动态生成路由闭包，`register_handlers` 批量注册 |

### 响应模型

| 模型 | 定义位置 | 用途 |
|------|---------|------|
| `SearchResponse` / `BookItem` | `handlers/base/searchBase.py` | 搜索接口返回 |
| `BookDetail` | `handlers/base/detailBase.py` | 详情接口返回 |
| `ChapterResponse` / `ChapterItem` | `handlers/base/chapterBase.py` | 章节接口返回 |
| `DatasourcesResponse` | `handlers/datasource.py` | 数据源列表返回 |

### 端点：数据源列表

`GET /datasources` 返回所有可用数据源及其端点信息（path / methods / params / description），按数据源名称分组排序。

### 新增数据源步骤

1. 在 `handlers/` 下新建子目录（如 `tutu/`）
2. 编写 handler 文件，继承 `base/` 中的基础处理器
3. 用 `@HandlerRegistry.register` 装饰，设置 `path`/`name`/`methods`/`query_params`
4. 实现 `handle` 方法
5. 创建 `__init__.py`，`from . import <module>` 触发注册

### URL 拼接规范

```python
url = f"{base_url.rstrip('/')}/search?query={query}&offset={offset}&count={count}&tab_type={tab_type}"
```

- `base_url` 末尾可能带 `/`，使用 `rstrip('/')` 去除
- `base_url` 应包含 API 前缀（如 `/api/v1`）

## 已实现的数据源

### tutu

| 接口 | 路径 | 参数 |
|------|------|------|
| 搜索 | `/tutu/search` | `base_url`, `query`, `offset`, `count`, `tab_type` |
| 详情 | `/tutu/detail` | `base_url`, `book_id` |
| 章节 | `/tutu/chapter` | `base_url`, `book_id` |
| 内容 | `/tutu/content` | `base_url`, `book_id`, `item_id`, `tone_id`, `quality` |

内容接口自动根据 `book_id` 识别类型分发。

#### tutu 搜索数据解析

- `parse_tab_item`：递归解析 `search_tabs`，收集 `book_data`（书籍）/ `video_data`（视频）/ `abstract` 节点
- `build_kind`：拼接 `性别,评分,类型,状态,最近更新` 用于书籍
- `build_video_kind`：拼接 `rec_text,sub_title(·→,)` 用于视频
- `build_book_item`：根据是否含 `book_name` 区分书籍项和视频项

### mufan

| 接口 | 路径 | 参数 |
|------|------|------|
| 搜索 | `/mufan/search` | `base_url`, `query`, `offset`, `tab_type`, `search_type` |
| 详情 | `/mufan/detail` | `base_url`, `book_id` |
| 章节 | `/mufan/chapter` | `base_url`, `book_id` |
| 内容 | `/mufan/content` | `base_url`, `book_id`, `item_id`, `tone_id`, `quality` |
| 发现分类 | `/mufan/front` | `base_url`, `tab` |
| 分类书籍 | `/mufan/landing` | `base_url`, `category_id`, `offset`, `genre_type`, `gender`, `word_number`, `book_status`, `sort_by` |

内容接口自动根据 `book_id` 识别类型分发。

#### tutu 类型识别

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
