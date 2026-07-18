# api-proxy

基于 FastAPI 的 API 代理服务，支持通过 handler 机制扩展多种数据源的搜索、详情、章节、内容、探索接口。

## 快速开始

```bash
uv sync
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
│   ├── tutu/                 # tutu 数据源
│   │   ├── __init__.py
│   │   ├── search.py
│   │   ├── detail.py
│   │   ├── chapter.py
│   │   ├── content.py
│   │   └── explore.py
│   └── mufan/                # mufan 数据源
│       ├── __init__.py
│       ├── search.py
│       ├── detail.py
│       ├── chapter.py
│       ├── content.py
│       └── explore.py
├── tests/
│   ├── conftest.py
│   └── test_content.py
└── AGENTS.md
```

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
| `HandlerRegistry` | `base/base.py` | 全局路由注册表，支持有参/无参装饰器 |
| `BaseHandler` | `base/base.py` | 抽象基类，定义 `path`/`name`/`methods`/`query_params`/`description`/`handle` |

## 新增数据源步骤

1. 在 `handlers/` 下新建子目录（如 `tutu/`）
2. 编写 handler 文件，继承 `base/` 中的基础处理器
3. 用 `@HandlerRegistry.register` 装饰，设置 `path`/`name`/`methods`/`query_params`
4. 实现 `handle` 方法，返回 Pydantic `BaseModel` 实例
5. 创建 `__init__.py`，`from . import <module>` 触发注册
6. 如需共享工具，从 `utils/fq_utils.py` 导入（番茄系）

## 已注册端点

| 端点 | 说明 |
|------|------|
| `/datasources` | 数据源列表 |
| `/data` | 静态数据文件（`?source=fq&name=fq_moduleMap`） |
| `/tutu/search` | tutu 搜索 |
| `/tutu/detail` | tutu 详情 |
| `/tutu/chapter` | tutu 章节 |
| `/tutu/content` | tutu 内容（自动识别类型分发） |
| `/tutu/recommend` | tutu 首页推荐 |
| `/tutu/rank` | tutu 排行榜 |
| `/tutu/related` | tutu 相关作品 |
| `/tutu/author` | tutu 作者作品 |
| `/mufan/search` | mufan 搜索 |
| `/mufan/detail` | mufan 详情 |
| `/mufan/chapter` | mufan 章节 |
| `/mufan/content` | mufan 内容（自动识别类型分发） |
| `/mufan/front` | mufan 发现页分类 |
| `/mufan/landing` | mufan 分类书籍列表 |
| `/mufan/recommend` | mufan 首页推荐 |
| `/mufan/rank` | mufan 排行榜 |

## 编码规范

- **导入路径**：使用绝对导入（`from base.searchBase import ...` / `from utils.fq_utils import ...`）
- **`**kwargs`**：使用 `kwargs.get("key", default)` 而非 `kwargs["key"]` 或 `.pop()`
- **时间处理**：时间戳统一 UTC+8，使用 `TZ_SHANGHAI` 常量
- **异步 HTTP**：使用 `httpx.AsyncClient`，设 `DEFAULT_TIMEOUT`
- **响应模型**：`handle` 返回 Pydantic `BaseModel` 实例，`app.py` 自动 `model_dump()`
- **`normalize_api_base`**：统一使用 `normalize_api_base(base_url, prefix)` 拼接 API 基础路径
