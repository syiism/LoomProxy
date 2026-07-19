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
- python-dotenv >= 1.0.0

## 项目结构

```
.
├── app.py                    # 应用入口，自动注册路由
├── confMagr.py               # 集中配置管理（支持 .env 覆盖）
├── .env.example              # 环境变量模板
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
│   ├── network.py            # SSRF 防御 (is_safe_url)
│   ├── cache.py              # 内存 LRU 缓存 (@cached)
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
| `is_safe_url` | `utils/network.py` | SSRF 防御，校验 base_url 安全 |
| `@cached` | `utils/cache.py` | 内存 LRU 缓存装饰器 |
| `ConfMagr` | `confMagr.py` | 集中配置管理，支持 `.env` 覆盖 |

### 安全：SSRF 防御

所有 `base_url` 参数自动通过 `is_safe_url` 校验，仅允许公网 `http://`/`https://`，禁止私有 IP 和回环地址。

### 统一异常处理

| 异常 | HTTP 状态码 | 响应体 |
|------|------------|--------|
| `httpx.HTTPStatusError` | 502 | `{"code": -1, "msg": "上游返回异常状态码 {code}"}` |
| `httpx.TimeoutException` | 504 | `{"code": -1, "msg": "上游请求超时"}` |
| `httpx.HTTPError` | 502 | `{"code": -1, "msg": "上游数据异常"}` |
| `ValueError`（含 SSRF） | 400 | `{"code": -1, "msg": "..."}` |
| `KeyError` | 500 | `{"code": -1, "msg": "数据解析异常：缺少字段 {key}"}` |
| `Exception`（兜底） | 500 | `{"code": -1, "msg": "内部服务异常"}` |

### 缓存

`utils/cache.py` 提供 `@cached(ttl=300, maxsize=128)` 装饰器，当前应用于 `/datasources` 和 `/data` 端点。

### 配置管理

`confMagr.py` 集中管理所有公共配置，通过 `python-dotenv` 加载 `.env` 文件覆盖默认值：

```bash
# .env 示例
TIMEOUT_CONNECT=5.0
TIMEOUT_POOL=10.0
SERVER_PORT=9090
```

`.env` 文件已被 `.gitignore` 忽略，参考格式见 `.env.example`。

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
| `/tutu/*` | 番茄（兔兔）搜索/详情/章节/内容/推荐/排行/相关/作者 |
| `/mufan/*` | 番茄（沐凡）搜索/详情/章节/内容/发现/分类/推荐/排行 |
| `/fq_xinghai/*` | 番茄（星海）搜索/详情/章节/内容/推荐/排行 |
| `/luomu/*` | 番茄（落幕）搜索/详情/章节/内容 |
| `/jingluo/*` | 番茄（鲸落）搜索/详情/章节/内容 |
| `/qq_luomu/*` | QQ阅读（落幕）搜索/详情/章节/内容 |
| `/qm_luomu/*` | 七猫（落幕）搜索/详情/章节/内容 |
| `/sq_luomu/*` | 书旗（落幕）搜索/详情/章节/内容 |

## 编码规范

- **导入路径**：使用绝对导入（`from base.searchBase import ...` / `from utils.fq_utils import ...`）
- **`**kwargs`**：使用 `kwargs.get("key", default)` 而非 `kwargs["key"]` 或 `.pop()`
- **时间处理**：时间戳统一 UTC+8，使用 `TZ_SHANGHAI` 常量
- **异步 HTTP**：使用 `httpx.AsyncClient`，设 `ConfMagr.default_timeout()`；调用 `self.fetch(url)` 替代裸 `client.get()`，便于测试 mock
- **响应模型**：`handle` 返回 Pydantic `BaseModel` 实例，`app.py` 自动 `model_dump()`
- **`normalize_api_base`**：统一使用 `normalize_api_base(base_url, prefix)` 拼接 API 基础路径
- **缓存**：静态数据（数据源列表、JSON 文件）使用 `@cached(ttl=300)` 装饰器减少重复计算
- **SSRF**：用户提供的 `base_url` 在入口处自动通过 `is_safe_url` 校验，禁止内网/回环地址
- **配置**：全局配置通过 `confMagr.py` 集中管理，`.env` 文件可覆盖默认值
