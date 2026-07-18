# API 接口文档

> **基础地址**：`http://<host>:1968`
> **统一前缀**：`/api`
> **响应格式**：

```json
{
  "code": 0,        // 0 = 成功，负数 = 失败
  "msg": "ok",      // 状态描述
  "data": { }       // 业务数据
}
```

> **重要**：为对齐 Python 版，`/api/*` 即使出错也返回 **HTTP 200**，成败一律看 body 里的 `code`（见 [架构 · 中间件](./architecture.md#中间件执行顺序)）。逐字段细节也可对照 [`../../pyfq/docs/api.md`](../../pyfq/docs/api.md)。

## 通用约定

| 项 | 说明 |
|----|------|
| `tab_type` | 内容类型：`1`综合 / `2`听书 / `3`小说 / `5`(=8)漫画 / `6`(=11)短剧 / `19`漫剧 |
| 设备密钥 | 需密钥的端点由服务用设备池**自动签名**，调用方无需传密钥 |
| 多 ID | 多数端点同时接受 `item_id`（单个）和 `item_ids`（可逗号分隔批量） |
| 别名 | `key`/`query`、`book_id`/`bookId`/`fq_id` 等多写法并存，取第一个非空 |
| 容错 | **解密类**端点（`content`/`raw_full`/`manga`）遇某设备密钥被番茄判 `Invalid` 会**自动换设备轮询**直到成功；全部失败才返回 `-5`（msg 含「已轮询 N 台设备」）。单台坏密钥调用方无感。 |

> 每个端点用的**上游 `version_code` / 是否需要内容密钥 / 解密方式 / 是否轮询**，见 [架构 · 端点速查表](./architecture.md#端点--设备--版本号--解密-速查表)。

## 端点总览（速查）

> 设备=是否需要设备密钥签名；解密=是否用内容密钥解密（这类才会遇 `Invalid` 并自动轮询）；缓存=命中的内存缓存及 TTL。

| 端点 | 方法 | 用途 | 设备 | 解密 | 缓存 |
|------|:----:|------|:----:|------|------|
| `/api/search` | GET | 搜索书/听书/漫画/短剧 | ✅ | — | search 10m |
| `/api/detail` | GET | 书籍详情（移动端） | ✅ | — | — |
| `/api/book` | GET | 详情+目录（Web+ABogus） | ✅ | — | — |
| `/api/directory`、`/api/catalog` | GET | 章节目录 | ✅ | — | — |
| `/api/content` | GET | **正文/听书/详情/书评**统一入口 | ✅ | 正文AES-128 | content/directory 30m |
| `/api/audio` | GET | 独立听书音频 URL | ✅ | — | — |
| `/api/full` | GET/POST | DH 握手取正文（不依赖正文设备密钥） | ✅(仅签名) | AES-256/DH | — |
| `/api/download/txt`、`/api/txt` | GET | 拉目录后批量拼接 TXT 下载，支持同步文本与异步任务 | ✅(目录+full签名) | AES-256/DH | — |
| `/api/chapter` | GET | 网页正文（charset 还原） | — | — | general 10m |
| `/api/raw_full` | GET | 原始正文（保留 HTML，含图片章节） | ✅ | 正文AES-128 | — |
| `/api/item_info` | GET | 章节元信息 | ✅ | — | general 10m |
| `/api/manga`、`/api/comic` | GET | 漫画图片（解密→临时静态文件） | ✅ | 章节AES-128 + 图片AES-GCM | general 30m |
| `/api/video` | GET | 短剧视频（直链优先，失败回退官方 CENC） | ✅ | 直链 AES-CBC / spade_a→CEK | general |
| `/api/video_proxy` | GET | 视频/音频流代理（绕防盗链，Range） | — | — | — |
| `/api/video_decrypt` 🎬 | GET | CENC 解密代理（ffmpeg，文件缓存） | — | CENC AES-CTR | 文件 500MB/30m |
| `/api/video_transcode` 🎬 | GET | H.265→H.264 实时转码（ffmpeg） | — | — | — |
| `/api/player`、`/api/manga_reader`、`/api/novel_reader`、`/api/audio_player` | GET | HTML 播放器/阅读器页面 | — | — | — |
| `/api/wkcontent` | GET | 听书 TTS 时间轴 | ✅ | — | — |
| `/api/book_share` | GET | 分享信息（书名/封面…） | ✅ | — | — |
| `/api/novel_content`、`/api/novel_directory` | GET | Novel 直返正文/目录（无需密钥） | — | — | — |
| `/api/toutiao`、`/api/toutiao_article` | GET | 头条小说/文章 | 部分 | — | — |
| `/api/front`、`/api/landing`、`/api/explore` | GET | 发现页分类/落地页 | ✅ | — | — |
| `/api/bookmall/cell/change`、`/api/recommend/homepage` | GET | 新版发现页榜单/推荐 | 部分 | — | general 10m |
| `/api/related`、`/api/author`、`/api/author_bookshelf` | GET | 关联作品/作者作品/作者书架 | ✅ | — | general 10/30m |
| `/api/comment_count` … `/api/author_say`（11 个） | GET | 评论系统（段评/书评/章末/作家说） | ✅ | — | — |
| `/api/device_register`、`/api/ios_register`、`/api/device_pool` | GET | 设备注册/池管理 | — | — | — |
| `/api/ios_content` | GET | iOS 正文（单 iOS 密钥） | ✅(iOS) | 正文AES-128 | — |
| `/api/booksource` | GET | Legado 书源 JSON | — | — | — |
| `/api/opds`（+`/search`/`/recommend`/`/categories`/`/category/:c`） | GET | OPDS 订阅 | ✅ | — | — |
| `/api/health`、`/api/ping`、`/ping` | GET | 健康/存活/服务信息 | — | — | — |
| `/` | GET | 首页：**当日各接口调用次数 + 调用者 IP**（东八区自然日，每日 0 点归零）。浏览器返回移动端友好 HTML，非 HTML 客户端返回 JSON | — | — | — |
| `/stats/daily` | GET | 当日 + 昨日调用统计 JSON（首页数据源，可直接调用） | — | — | — |
| `/api/devices/stats` | GET | 设备池实时健康：`total`/`active`/`bad` + `by_status` 分组明细 | — | — | — |
| `/sy/{1..6}.json`、`/static/...` | GET | 发现页分类数据 / 漫画临时图片 | — | — | — |

## 缓存机制与内存/磁盘上限

服务里所有缓存都**有界**，正常和高负载下都不会无限增大：

| 缓存 | 介质 | TTL | 上限 | 回收 |
|------|------|-----|------|------|
| contentCache（正文） | 内存 | 30 min | **`cache.max_size`=10000 条** | 每 5 min 清过期；满则先清过期、再淘汰最近将过期项 |
| directoryCache（详情/目录） | 内存 | 30 min | 10000 条 | 同上 |
| searchCache（搜索） | 内存 | 10 min | 10000 条 | 同上 |
| generalCache（漫画/章节/元信息…） | 内存 | 10/30 min | 10000 条 | 同上 |
| 视频解密结果 | **磁盘**（temp/video_cache） | 30 min | **500 MB** | 每次解密请求触发清理：删 >30min 文件、超 500MB 削到 70% |
| 漫画解密图片 | **磁盘**（`web/static/img`） | — | 每请求生成、**120 秒后自动删** | 后台 `manga-cleanup` |
| 设备池 | 磁盘 `device_pool.json` | — | **20 台**（`maxSize`） | 失效淘汰 + 上限淘汰最差设备 |
| 调用统计 `api_stats.json` | 磁盘 | — | 累计按**端点名**聚合（~50 key）+ 当日「端点→IP」明细（IP 数有界，每日 0 点归零） | 不随请求量无限增长 |
| 日志（若 `output=file`） | 磁盘 | — | `logger.max_size`×`max_backups`（默认 100MB×3） | lumberjack 轮转 |

**结论：不会无限增大。** 4 个内存缓存各自硬上限 10000 条（约几十 MB 量级），写满后按「先清过期、再淘汰最接近过期项」淘汰；磁盘类缓存各有大小或时间上限。要调整内存缓存容量改 `config.yaml` 的 `cache.max_size`。详见 [架构 · 缓存](./architecture.md)。

## 鉴权（可选，默认关闭）

公网部署建议开启，防止被刷触发上游风控。`config.yaml` 设 `api_keys.enabled: true` 并在 `data/devices/api_keys.json` 放密钥数组后，所有 `/api/*` 需带密钥（`/api/health`、`/sy`、`/static`、`/` 不拦）：

```bash
curl -H "X-API-Key: your-key" "http://<host>:1968/api/search?key=都市&tab_type=3"
```

详见 [配置 · API Key 访问控制](./config.md#api-key-访问控制)。

---

## 一、搜索

### `GET /api/search`

搜索综合 / 听书 / 小说 / 漫画 / 短剧 / 漫剧。

| 参数 | 必填 | 默认 | 说明 |
|------|:----:|------|------|
| `key` 或 `query` | ✅ | — | 搜索关键词 |
| `tab_type` | 否 | `3` | 内容类型（见通用约定）；`19` 漫剧会优先走短剧视频搜索并尽量用详情筛出 `genre_type=2150`，筛不到时返回视频结果，避免混入小说 |
| `offset` | 否 | `0` | 分页偏移 |
| `search_type` | 否 | `default` | 搜索源：`default` 主源 / `fanqie` 备用源（`api.fanqiesdk.com`） |

- **上游**：`api5-normal-sinfonlinea.fqnovel.com/reading/bookapi/search/tab/v/`（aid=1967）
- **缓存**：10 分钟
- **tab 映射**：搜索时 `6→11`、`5→8` 自动转换（上游 2025 后调整）
- **书源快捷搜索**：`booksource/yangshizi_pyfq.json` 支持关键词前加 `+1/+2/+3/+8/+11/+19` 临时切换搜索类型，例如 `+19 修仙`；10 位以上纯数字 ID 仍走 `/api/search?query=<id>`，后端内部按详情精确查询并返回数组，避免阅读端把单对象当列表时报错。
- **书源搜索解析**：下发书源的 `ruleSearch.bookList` 使用稳定 JSONPath：`$..book_data[*]||$..video_data[*]||$..books[*]||$.data[*]||$.data`，覆盖综合/视频/ID 数组结果；此前 JS 递归聚合在部分阅读端会返回字符串或空列表，已回退。

```
GET /api/search?key=斗破苍穹&tab_type=3
GET /api/search?key=甜宠&tab_type=11&offset=10
GET /api/search?key=悬疑&tab_type=3&search_type=fanqie
```

**真实返回**（`key=都市&tab_type=3`，`data` 为上游搜索结构原样透传，已大幅截断）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "code": 0,
    "message": "SUCCESS",
    "log_id": "202606142132544A8AA539DA00950B7A65",
    "search_tabs": [
      {
        "data": [ /* 书目项数组，每项含下列字段 */ ],
        "has_more": false,
        "next_offset": 0
      }
    ]
  }
}
```

书目项（`search_tabs[].data[]` 内）的关键字段：

| 字段 | 示例 | 说明 |
|------|------|------|
| `book_id` | `"6678976107129080839"` | 书籍 ID，用于后续 detail/directory |
| `book_name` | `"都市神豪（别名：尘微入青云）"` | 书名 |
| `author` | `"北辰本尊"` | 作者 |
| `abstract` | `"女朋友嫌林云穷……"` | 简介 |
| `category` / `score` / `thumb_url` | … | 分类 / 评分 / 封面 |

---

## 二、书籍详情

### `GET /api/detail`

单本书籍详情（移动端 API）。

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `book_id` / `bookId` / `fq_id` | ✅ | 书籍 ID |

- **上游**：`.../reading/bookapi/detail/v/`（aid=1967）

### `GET /api/book`

书籍目录 + 详情（fanqienovel.com Web API + ABogus 签名）。

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `book_id` / `bookId` | ✅ | 书籍 ID |

- **上游**：`fanqienovel.com/api/reader/directory/detail`

**`/api/detail` 真实返回**（`book_id=6678976107129080839`，`data` 为上游书籍对象，已截断）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "book_id": "6678976107129080839",
    "book_name": "都市神豪（别名：尘微入青云）",
    "author": "北辰本尊",
    "abstract": "女朋友嫌林云穷，跟着富二代跑了……",
    "category": "都市",
    "creation_status": "0",
    "word_number": "...",
    "read_count": "...",
    "score": "...",
    "thumb_url": "https://p6-novel.byteimg.com/...",
    "tags": "都市,赘婿,扮猪吃虎"
  }
}
```

**内容类型判定字段**（`data` 内，用于「粘贴 book_id 直接打开」自动识别书籍类型）：

| 字段 | 小说 | 听书 | 漫画 | 短剧 | 说明 |
|------|:----:|:----:|:----:|:----:|------|
| `comic_book_type` | — | — | `1` | — | 存在即漫画（最高优先级） |
| `genre_type` | `0` | `1` | `110` | `2130`(漫剧 `2150`) | `2130/2150` → 短剧 |
| `book_type` | `0` | `1` | `0` | `0` | `1` → 听书 |

> 判定优先级：`comic_book_type` 存在或 `genre_type==110`→漫画 ＞ `genre_type∈{2130,2150}`（或 `genre∈{203,205}`）→短剧/漫剧 ＞ `book_type==1`→听书 ＞ 否则小说。
> 书源据此把 `book.type` 设为 `64`(IMAGE)/`8`(VIDEO)/`32`(AUDIO)/`0`(TEXT)，无需用户指定类型。

---

## 三、章节目录

### `GET /api/directory`（别名 `GET /api/catalog`）

完整章节目录。

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `fq_id` / `book_id` / `bookId` | ✅ | 书籍 ID |

- **上游**：`.../reading/bookapi/directory/all_items/v/`（aid=1967）
- **返回**：`data.item_data_list` 数组，每项含 `item_id`、`title` 等

```
GET /api/directory?book_id=7087519624329169951
GET /api/catalog?book_id=7087519624329169951
```

**真实返回**（`data` 为上游目录结构，`item_data_list` 是章节数组，已截断）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "item_data_list": [
      {
        "item_id": "6679027782799852039",
        "title": "第1章 一夜暴富",
        "volume_name": "正文",
        "version": "..."
      }
    ]
  }
}
```

> 拿到 `item_id` 后即可调 `/api/content`、`/api/item_info` 等。

---

## 四、正文内容（统一入口）

### `GET /api/content`

**最核心的端点**，按参数自动路由：

| 参数 | 必填 | 默认 | 说明 |
|------|:----:|------|------|
| `item_ids` / `item_id` | 条件 | — | 章节 ID（取正文/听书时必填） |
| `book_id` | 条件 | — | 书籍 ID（取详情/评论时必填，详情支持逗号分隔批量） |
| `ts` | 否 | — | `听书` = 音频模式 |
| `comment` | 否 | — | `评论` = 书评模式 |
| `tone_id` | 否 | `0` | 听书音色 ID |
| `count` / `offset` | 否 | `10`/`0` | 评论分页 |
| `api_type` | 否 | `full` | `full`（单章）或 `batch`（多章批量） |

**路由规则**（按优先级，见 [架构 · content 路由](./architecture.md#content-端点的路由逻辑)）：

| 条件 | 行为 | 上游 |
|------|------|------|
| `ts=听书` | 返回音频代理 URL | `reading.snssdk.com/.../audio/playinfo/` |
| `book_id` 且无 `comment` | 书籍详情（单 `detail`/多 `multi-detail`） | `reading.snssdk.com/reading/bookapi/...` |
| `book_id` + `comment=评论` | 书评（POST JSON） | `.../novel/commentapi/comment/list/{id}/v1` |
| 其他 | **正文**：AES-128-CBC 解密 + gzip | `.../reading/reader/full/v/`（或 `batch_full`） |

```
GET /api/content?item_ids=7089685628191048227
GET /api/content?item_ids=7074990077704768542&ts=听书&tone_id=1
GET /api/content?book_id=70875196...,75165365...        # 批量详情
GET /api/content?book_id=7087519624329169951&comment=评论&count=10
```

听书返回示例：

**正文真实返回**（`item_ids=6679027782799852039`，已解密；`content` 是清理后的 HTML，已截断）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "title": "第1章 一夜暴富",
    "item_id": "6679027782799852039",
    "content": "<p idx=\"0\">青阳市。</p><p idx=\"1\">华鼎大厦门口。</p><p idx=\"2\">林云面带笑容的站在门口……</p>",
    "content_md5": "…",
    "compress_status": 0,
    "novel_data": { "...": "章节元信息" }
  }
}
```

**听书真实返回**（`item_ids=...&ts=听书&tone_id=1`）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "content": "http://<host>/api/video_proxy?url=https%3A%2F%2Fv11-novelapp.fqnovelvod.com%2F...",
    "raw_url": "https://v11-novelapp.fqnovelvod.com/...",
    "backup_url": "https://v9-novelapp.fqnovelvod.com/...",
    "item_id": "7321553806754319422",
    "quality": 128,
    "vid": "v039b6g10000cmdm4orc...",
    "video_model_datas": []
  }
}
```

> 音频 URL 通过 `/api/video_proxy` 代理返回，绕过 CDN 防盗链。`quality` 是上游的比特率数字（如 `128`）。

### `GET /api/audio`

独立听书端点（等价于 `content?ts=听书`）。

| 参数 | 必填 | 默认 | 说明 |
|------|:----:|------|------|
| `item_id` / `item_ids` | ✅ | — | 章节 ID |
| `tone_id` | 否 | `0` | 音色 ID：`0`=默认，`1`~`8` 为不同 AI 嗓音（实测不同 `tone_id` 返回不同音频源） |

---

## 五、DH 握手正文

### `GET/POST /api/full`

通过 Diffie-Hellman 密钥交换 + AES-256-CBC 解密。它**不依赖正文解密用的设备密钥**，但不是匿名接口：现役上游仍要求 aid=3040 的 App 签名头，并会带设备池中任意可用设备的 `device_id` / `iid`。

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `book_id` | ✅ | 书籍 ID |
| `item_ids` / `item_id` | ✅ | 章节 ID，逗号分隔或 JSON 数组；单次最多 3000 个 |

- **上游**：`api5-sinfonlineb.novelfm.com/novelfm/playerapi/full/mget/v1/`（**aid=3040**，番茄畅听）
- **签名**：必须有 `x-gorgon` / `x-argus` / `x-ladon` 等 App 签名头；不签名会被上游返回 `code=6000`。
- **原理**：固定 DH 参数 + base 2，参数来自抓包/Python 实现，不是标准 RFC 3526 Group-14，详见 [加密 · DH 握手](./crypto.md#aes-256-cbc--dh-握手api-full)

```
GET /api/full?book_id=7087519624329169951&item_ids=7089685628191048227
POST /api/full   {"book_id":"...","item_ids":["..."]}
```

**真实返回**（2026-07-01 本地 `:1973` 实测，第一章，已截断）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "item_id": "7089685628191048227",
      "title": "小说：为了让小伙安心修道，老人把他关在山里十年，直到自己去世",
      "content": "十万大山，\n悬崖峭壁，古树参天。\n一座道观孤零零的立在山巅云层之中..."
    }
  ]
}
```

### `GET /api/download/txt`（别名：`GET /api/txt`）

小说 TXT 下载专用接口。服务端先取 `/api/catalog` 同源目录，再按批调用内部 `/api/full` 逻辑解密正文并拼接纯文本；默认单批最多 3000 章，不通过 HTTP 自调用。

联网调研结论：Legado 书源职责里 `chapterList(tocUrl)` 返回 `ChapterInfo[]` 目录，`chapterContent(chapterUrl)` 返回正文字符串；因此 TXT 下载不能再伪装成目录里的唯一章节，否则阅读端会把正常目录缓存成“全本 TXT 下载”单章。当前实现保持 `/api/catalog` 正常目录不变，TXT 下载只作为详情页 `ruleBookInfo.downloadUrls` 或手动 URL 使用。

| 参数 | 必填 | 默认 | 说明 |
|------|:----:|------|------|
| `book_id` / `bookId` / `fq_id` | ✅ | — | 书籍 ID |
| `limit` | 否 | `0` | 调试用，限制下载前 N 章；`0` 表示全本 |
| `batch_size` | 否 | `3000` | 每批正文数，超过 3000 会自动压到 3000 |
| `format` | 否 | — | `json` 返回 JSON；`limit=0&format=json` 默认转异步任务，避免旧缓存章节同步阻塞服务 |
| `async` / `mode=async` | 否 | `0` | 为真时立即返回后台任务 `job_id`，由服务端串行生成 TXT |
| `sync` | 否 | `0` | `format=json&sync=1` 强制同步返回完整 `content`，仅建议调试小 `limit` 使用 |

默认返回 `text/plain; charset=utf-8`，并带 `Content-Disposition: attachment`。书源的「TXT下载」开关只控制详情页下载地址是否下发，不改变 `tocUrl` 和 `chapterList`；点击阅读端“缓存章节”仍然只会按正常章节 `/api/content` 缓存，不等于 TXT 全本下载。

**阅读端使用步骤**：

1. 重新导入最新书源或刷新书源，确认 `/api/booksource` 是新版本。
2. 在书源登录/配置页把 `搜索类型` 设为小说/出版/综合，并开启 `TXT下载=✅`。
3. 重新打开书籍详情，正常目录应继续显示真实章节，章节 URL 仍为 `/api/content?...`。
4. 在详情页使用阅读端提供的下载入口，或手动访问 `/api/download/txt?book_id=<id>` 下载 TXT。

如果关闭 `TXT下载` 后日志仍出现 `/api/download/txt?book_id=...&format=json`，说明阅读端仍在使用旧版“全本 TXT 下载”伪章节缓存。服务端会把这种旧 `format=json` 全本请求自动转为异步任务并返回提示正文，避免整合服务被同步拼接卡住；客户端侧仍建议清除该书目录缓存后刷新目录。

```
GET /api/download/txt?book_id=7087519624329169951
GET /api/download/txt?book_id=7087519624329169951&async=1
GET /api/download/txt/status?job_id=<job_id>
GET /api/download/txt/result?job_id=<job_id>
GET /api/download/txt?book_id=7087519624329169951&limit=100&format=json&sync=1
```

**同步调试 JSON 返回**（`limit=1&batch_size=1&format=json`，已截断）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "book_id": "7087519624329169951",
    "book_name": "都市：修仙十年，下山即无敌",
    "count": 1,
    "missing_count": 0,
    "batch_size": 1,
    "full_batch_limit": 3000,
    "content_length": 6323,
    "content": "都市：修仙十年，下山即无敌\n\n第1章 十年后\n\n十万大山..."
  }
}
```

**异步任务返回**：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "job_id": "7087519624329169951-1782924000000000000",
    "book_id": "7087519624329169951",
    "status": "queued",
    "message": "TXT 下载任务已进入后台队列",
    "status_url": "/api/download/txt/status?job_id=...",
    "result_url": "/api/download/txt/result?job_id=...",
    "content": "TXT 下载已改为独立后台任务..."
  }
}
```

---

## 六、网页正文

### `GET /api/chapter`

抓 `fanqienovel.com` 网页正文，**不依赖签名**，自动按 `charset.json` 还原被替换的字符。

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `item_id` / `item_ids` | ✅ | 章节 ID |

- **上游**：`fanqienovel.com/reader/{item_id}`

### `GET /api/raw_full`

同上但保留 HTML 标签的原始内容。

---

## 七、章节元信息

### `GET /api/item_info`

章节元数据（标题、字数等），**不需签名**。

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `item_ids` / `item_id` | ✅ | 章节 ID，支持批量 |

- **上游**：`novel.snssdk.com/api/novel/book/directory/detail/v/`

**真实返回**（`item_ids=...`，上游结构嵌套在 `data.data.data[]`，已截断）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "data": {
      "code": 0,
      "data": [
        {
          "abstract": "女朋友嫌林云穷……",
          "author": "北辰本尊",
          "ad_free_show": "3",
          "add_bookshelf_count": "88406"
        }
      ]
    }
  }
}
```

---

## 八、漫画

### `GET /api/manga`（别名 `GET /api/comic`）

获取漫画章节图片，**AES-GCM 解密**后通过 `/static` 临时文件提供。

| 参数 | 必填 | 默认 | 说明 |
|------|:----:|------|------|
| `item_id` / `item_ids` | ✅ | — | 章节 ID |
| `show_html` | 否 | `0` | `1` 时额外返回拼好的 `<img>` HTML |

- **上游**：`.../reading/comics-api/episode/v/`（aid=1967）
- 解密见 [加密 · 漫画图片](./crypto.md#漫画图片解密aes-gcm)

---

## 九、短剧视频

### `GET /api/video`

获取短剧视频，按请求方式返回不同格式。`type=json` 默认优先走参考源验证过的红果短剧直链接口，成功时直接返回 MP4 直链；直链失败时自动回退番茄官方 `multi_video_model`，再派生 CEK 并拼成 `/api/video_decrypt`。

| 参数 | 必填 | 默认 | 说明 |
|------|:----:|------|------|
| `item_id` / `item_ids` / `video_id` | ✅ | — | 视频 ID |
| `book_id` | 否 | — | 书籍 ID（`type=json` 时取书名/作者/集数标题） |
| `type` | 否 | — | `json` = 简化输出（含可直接播放 URL） |
| `quality` | 否 | 最高画质 | `low` = 优先低画质（仅 `type=json` 生效） |
| `direct` | 否 | `1` | `0/false/off` 禁用直链，强制官方回退 |
| `no_direct` | 否 | `0` | `1/true/on` 禁用直链，等价于 `direct=0` |
| `direct_only` | 否 | `0` | `1/true/on` 时直链失败直接返回错误，不回退官方 |

- **直链上游**：参考源同款 `play_info.php?video_id=<item_id>&timestamp=<unix>&signature=md5(video_id+timestamp)`，返回 `data.Link` 后用 AES-256-CBC 解密得到 MP4。
- **官方回退上游**：`.../novel/player/multi_video_model/v1`（POST，aid=1967）。取流后**自动 spade_a→CEK 派生**，把 CEK 拼进 `video_decrypt` URL。

**返回模式**：

| 条件 | 返回 |
|------|------|
| `type=json` + 直链成功 | 简化 JSON：`source=hongguo_direct`、`encrypted=false`、`url/raw_url` 为 MP4 直链 |
| `type=json` + 直链失败或 `direct=0` | 简化 JSON：`source=official_multi_video_model`、`encrypted=true`、`url` 为 `/api/video_decrypt?...&key=<CEK>` |
| 浏览器（`Accept: text/html`） | 302 跳转到 `/api/player` 播放器 |
| 其他 | 完整 video_model（各清晰度 URL + 已派生的 `cek`） |

`type=json` 直链真实返回（2026-07-01 本地 `:1973` 实测，`item_id=7635674228238322712`，URL 已截断）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "title": "系统求着我花钱，我花成了富豪 - 第1集",
    "url": "https://v3-dreamina-de.jianying.com/...mime_type=video_mp4...",
    "raw_url": "https://v3-dreamina-de.jianying.com/...mime_type=video_mp4...",
    "pic": "https://p3-reading-sign.fqnovelpic.com/...",
    "quality": "direct",
    "source": "hongguo_direct",
    "encrypted": false,
    "fallback": "official_multi_video_model",
    "info": {
      "author": "阅益短剧",
      "chapter_title": "第1集",
      "create_time": "2026-05-03T22:28:25+08:00"
    }
  }
}
```

官方回退真实返回（同一集加 `direct=0`，中段已截断）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "title": "系统求着我花钱，我花成了富豪 - 第1集",
    "url": "http://127.0.0.1:1973/api/video_decrypt?url=https%3A%2F%2F...&key=...",
    "quality": "video_1",
    "definition": "360p",
    "source": "official_multi_video_model",
    "encrypted": true,
    "width": 360,
    "height": 640
  }
}
```

> 直链 URL 已用 Range 请求验证返回 `206 video/mp4`。官方回退里的 `key=...` 是从 `spade_a` 本地派生的 CEK（见 [视频解密](./video-decrypt.md)）；客户端直接请求该 `url`，服务端下载密文 → ffmpeg 解密 → 返回可播放 MP4。

### `GET /api/video_proxy`

代理视频/音频流，绕过 CDN 防盗链，支持 Range（拖进度条）。

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `url` | ✅ | 原始视频/音频 URL（需 URL 编码） |

### `GET /api/video_decrypt` 🎬需 ffmpeg

下载 CENC 加密视频 → ffmpeg 解密 → 标准 MP4，支持缓存（MD5(key) 命名，500MB 上限）和 Range。

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `url` | ✅ | 加密视频 URL |
| `key` | ✅ | CEK（16 字节 hex），通常由 `/api/video` 自动派生 |

### `GET /api/video_transcode` 🎬需 ffmpeg

实时转码 ByteVC1(H.265) → H.264，适合不支持 HEVC 的设备降级播放。

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `url` | ✅ | 源视频 URL |

> 缺 ffmpeg 时 `video_decrypt`/`video_transcode` 在启动时自动不注册。详见 [视频解密](./video-decrypt.md)。

---

## 十、设备管理

### `GET /api/device_register`

安卓设备注册与密钥管理。

| 参数 | 默认 | 说明 |
|------|------|------|
| `action` | `register` | `register` 注册新设备 / `status` 查看状态 / `refresh` 刷新密钥 |

### `GET /api/ios_register`

iOS 设备注册（TTEncrypt 通道）。

### `GET /api/ios_content`

用 iOS 密钥通过安卓签名通道取正文。

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `item_id` / `item_ids` | ✅ | 章节 ID |

- **上游**：`reading.snssdk.com/reading/reader/full/v/`
- 需先 `/api/ios_register`。详见 [设备注册](./device.md)。

---

## 十一~十四、播放器 / 阅读器（HTML 页面）

直接渲染内嵌的 `web/templates/*.html`，浏览器可直接打开。

| 端点 | 页面 | 关键参数 |
|------|------|----------|
| `GET /api/player` | 短剧竖屏播放器 | `item_id`、`book_id`、`title` |
| `GET /api/manga_reader` | 漫画全屏滚动阅读 | `item_id`、`book_id`、`title` |
| `GET /api/novel_reader` | 小说阅读器（翻页/字号/夜间） | `item_id`、`book_id`、`title` |
| `GET /api/audio_player` | 听书/朗读播放器 | `item_id`、`book_id`、`mode`(`audio`/`tts`)、`tone_id` |

> `audio_player` 的 `mode=tts`（小说朗读）支持多种 TTS 音色切换；`mode=audio`（有声书）为真人预录音频。

---

## 十五、听书时间轴

### `GET /api/wkcontent`

TTS 时间轴数据（字幕同步用）。

| 参数 | 必填 | 默认 | 说明 |
|------|:----:|------|------|
| `item_ids` / `item_id` | ✅ | — | 章节 ID |
| `tone_id` | 否 | `1` | 音色 ID |

- **上游**：`reading.snssdk.com/reading/reader/wkcontent/v/`

---

## 十六、书籍分享

### `GET /api/book_share`

从 detail 提取书名/作者/简介/封面，拼出分享信息。

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `book_id` / `bookId` | ✅ | 书籍 ID |

- **上游**：`.../reading/bookapi/detail/v/` + `fanqienovel.com/page/{id}`

---

## 十七、Novel 直返通道

无需设备密钥解密，走 `novel.snssdk.com`。

| 端点 | 参数 | 上游 |
|------|------|------|
| `GET /api/novel_content` | `item_id`/`item_ids` | `.../api/novel/reader/full/v1/` |
| `GET /api/novel_directory` | `book_id`/`bookId` | `.../api/novel/book/directory/detail/v/` |

---

## 十八、头条内容

| 端点 | 参数 | 上游 |
|------|------|------|
| `GET /api/toutiao` | `item_id`/`item_ids` | `novel.snssdk.com/api/novel/reader/full/v1/` |
| `GET /api/toutiao_article` | `item_id`（group_id/thread_id） | `m.toutiao.com/i{id}/info/`（清理 HTML） |

---

## 十九、设备池管理

### `GET /api/device_pool`

| 参数 | 默认 | 说明 |
|------|------|------|
| `action` | `list` | `list` 列出 / `register` 注册入池 / `delete` 移除 / `refill` 批量补充 |
| `device_id` | — | `delete` 时必填 |
| `count` | `3` | `refill` 批量数量 |

**`action=list` 真实返回**（`secret_key`/`device_id` 已脱敏）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "active": 12,
    "failed": 0,
    "total": 12,
    "devices": [
      {
        "device_id": "39641638********",
        "install_id": "39641638********",
        "secret_key": "****（敏感，已隐藏）****",
        "status": "active",
        "is_active": true,
        "fail_count": 0,
        "last_used": 1781443930,
        "update_time": "2026-06-13 22:46:57"
      }
    ]
  }
}
```

> 另有 RESTful 风格：`GET /api/devices`（列表）、`GET /api/devices/stats`（统计）、`POST /api/devices/register/android`、`POST /api/devices/register/ios`。

---

## 二十、健康检查与失败可观测

| 端点 | 说明 |
|------|------|
| `GET /api/health` | 运行时间、设备状态、**失败概况**（`stats` 字段） |
| `GET /api/stats` | 每端点完整统计（次数/失败/平均耗时）+ 失败概况，供监控/告警 |
| `GET /api/ping`、`GET /ping` | 存活探针 |

`GET /api/health` 真实返回（`stats` 为失败概况，仅在统计开启时出现）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "device": {
      "android": {"device_id": "2116984394822857", "registered": true, "update_time": "2026-06-13 22:46:18"},
      "ios":     {"device_id": "2275314051076666", "registered": true, "update_time": "2026-06-13 21:35:09"}
    },
    "status": "healthy",
    "uptime": "0d 0h 0m",
    "uptime_seconds": 19,
    "version": "2.1-go",
    "stats": {
      "total_calls": 1280,
      "total_fails": 12,
      "fail_rate": 0.009,
      "failing_apis": [
        {"path": "/api/directory", "count": 40, "fail": 40, "fail_rate": 1}
      ]
    }
  }
}
```

> **为什么需要这个**：本服务所有 `/api/*` 都返回 HTTP 200、靠 body 里的 `code`（负数=失败）判断成败——这对 Legado 书源友好，但监控只看 HTTP 状态会以为"永远健康"。`stats` 把"全 200 但某端点在大量业务失败"暴露出来。比如某机房在香港、`directory` 被番茄地域限制时（见 [故障排查](./troubleshooting.md#catalogdirectory-香港海外-ip-返回-101104该书不存在)），这里的 `failing_apis` 会直接显示 `/api/directory` 失败率 100%。

`GET /api/stats` 真实返回（每端点明细 + summary）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "summary": {
      "total_calls": 6, "total_fails": 4, "fail_rate": 0.667,
      "failing_apis": [
        {"path": "/api/book",   "count": 1, "fail": 1, "fail_rate": 1},
        {"path": "/api/detail", "count": 1, "fail": 1, "fail_rate": 1},
        {"path": "/api/search", "count": 3, "fail": 2, "fail_rate": 0.667}
      ]
    },
    "apis": {
      "/api/search": {"count": 3, "fail": 2, "total_time": 1141, "avg_time": 380, "last_call_time": "2026-06-17T14:35:09+08:00"}
    }
  }
}
```

> 建议接监控：轮询 `/api/stats`，对 `summary.fail_rate` 或某端点 `fail_rate` 超阈值（如 >0.5）告警。失败判定来自响应体 `code<0`，由统计中间件自动采集，不影响任何端点返回。`fail` 字段也会写进 `api_stats.json`。

### 首页 `GET /`（每日调用统计，需面板口令）

浏览器访问根路径（`Accept: text/html`）返回一张**当日调用统计页**：概览卡片（今日总调用 / 活跃接口 / 独立 IP / 当前时间）+ 每个接口的调用次数，点击接口行展开该接口的**调用者 IP 明细**（按次数降序）。

**⚠️ 隐私保护**：统计含**调用者 IP**（个人信息），故整页用独立**面板口令**保护，与 `/api/*` 的 API key 系统解耦：

| 口令状态 | 浏览器访问 `/` | 非 HTML 客户端访问 `/` |
|---|---|---|
| 未配置（默认） | 锁定页，无任何统计/IP | 仅 `code/msg/version`，无统计 |
| 已配置 + 口令正确 | 完整统计页（含 IP 明文） | 附带 `today` 快照 |
| 已配置 + 口令缺失/错误 | 锁定页（含口令输入框） | 仅 `code/msg/version` |

- **配置口令**：`config.yaml` 的 `stats.token`，或环境变量 `PYFQ_STATS_TOKEN`（优先，避免写死进配置）。留空则首页**默认锁定**，绝不暴露任何 IP。
- **携带口令**：查询参数 `?token=xxx`（浏览器直接用锁定页的输入框提交）、`?panel_token=xxx`，或请求头 `X-Stats-Token: xxx`。口令用定长比较，防计时侧信道。
- **统计口径**：按**东八区自然日**统计，每天 0 点自动归零（跨零点后旧数据转入"昨日"，页面顶部显示昨日总量）。
- **移动端适配**：响应式布局、深色主题，手机浏览器直接可读。
- 统计随请求实时累加，每 `stats.flush_interval` 落盘到 `api_stats.json`；重启不丢当天数据（跨零点重启会自动结算到昨日）。

### `GET /stats/daily`（当日统计 JSON，需面板口令）

首页数据的 JSON 形式，可直接调用或用于自建看板。**同样需要面板口令**（`?token=` / `?panel_token=` / `X-Stats-Token` 头），缺失或错误返回 `401 {"code":-401,"msg":"需要面板口令"}`：

```json
{
  "today": {
    "day": "2026-07-04",
    "total_calls": 128,
    "endpoints": [
      {"path": "/api/content", "count": 90, "fail": 2, "ips": {"120.229.221.77": 80, "180.101.245.251": 10}},
      {"path": "/api/search",  "count": 38, "fail": 0, "ips": {"223.68.80.160": 38}}
    ]
  },
  "prev_day": {"day": "2026-07-03", "total_calls": 512}
}
```

> `day` 为东八区日期；`ips` 是 `{IP: 次数}`。此接口只反映"今日"窗口，累计明细仍看 `/api/stats`。

---

## 二十一、书源下载

### `GET /api/booksource`

生成匹配当前服务地址的 Legado 书源（`{{host}}` 自动替换）。模板来自磁盘 `./booksource` 或内嵌副本。

| 参数 | 默认 | 说明 |
|------|------|------|
| `format` | `json` | `json` 纯数组 / `download` 触发下载 / `wrapped` 包装格式 |

**真实返回**（纯数组，首个书源对象，`bookSourceUrl` 已替换为当前服务地址，已截断）：

```json
[
  {
    "bookSourceName": "🍅洋柿子",
    "bookSourceGroup": "番茄",
    "bookSourceUrl": "http://127.0.0.1:1968",
    "bookSourceType": 0,
    "bookSourceComment": "接口:PyFQ\n书壳:archive\n适配PyFQ后端(root.data单层)",
    "enabled": true,
    "enabledExplore": true,
    "exploreUrl": "@js:\n...",
    "searchUrl": "..."
  }
]
```

> 直接把 `http://<host>:1968/api/booksource` 填进 Legado「网络导入」即可。

#### 🍅洋柿子书源设置（Legado 内「登录/书源配置」页）

| 设置 | 作用 |
|------|------|
| **后端地址** | 可填**多个**（换行/逗号分隔）与书源地址合并成服务器池；配 🔄切换服务器 / 📡检测服务器 按钮，请求失败自动故障转移 |
| **搜索类型** | 综合 / 小说 / 出版 / 听书 / 漫画 / 短剧 / 漫剧 / 短篇（决定 `tab_type` 与发现页模式） |
| **听书音色** | 选「听书」时出现，支持常用音色编号 `0/1/2/4/5/6/8/12/17/27/28/29/30/31/32/51/74/100/103/105/204`，对应 `/api/audio` 的 `tone_id` |
| **短剧画质 / 视频播放器** | 选「短剧」或「漫剧」时出现，省流/高清对应 `/api/video` 清晰度；播放器可选外部播放或 `/api/player` 内置播放器 |
| **TXT下载** | 选小说/出版/综合时出现，开启后详情页下发 `downloadUrls` 指向 `/api/download/txt?book_id=...`；正常章节目录和缓存仍走 `/api/catalog` → `/api/content` |
| **段评开关 / 章末评论 / 书籍评论 / 🫧气泡模版** | 选「小说/出版/综合」时出现，控制详情书评摘要、正文段评气泡和章末讨论 |
| **🍅登录番茄账号 / 番茄登录Token** | 登录番茄账号（WebView 抓 sessionid，或手填 Token）→ 发现页出现 👤个人中心（昵称、书架、书架分组、历史），见 [登录态](#二十三五登录态番茄账号) |

> 设置存于 Legado 端（`loginInfoMap`），不影响服务端。改设置后刷新发现页/重新搜索生效。

#### 🔢 粘贴 book_id 直接进书

搜索框输入 **10 位以上纯数字 book_id**（如 `6773701580693703688`）即精确打开该书，**无需先选搜索类型**：

- 书源 `searchUrl` 检测到 `/^[0-9]{10,}$/` → 请求 `/api/search?query=<id>&tab_type=<当前类型>&offset=0`（仅第 1 页，避免翻页重复）。
- 后端 `/api/search` 检测纯数字 ID 后内部调用详情接口，并返回 `[detail]` 数组，保证阅读端 `ruleSearch.bookList` 始终拿到列表。
- 打开书籍时 `ruleBookInfo.tocUrl` 读取 `/api/detail` 的 `comic_book_type` / `genre_type` / `book_type` 自动判定类型，设置 `book.type`（小说 TEXT / 听书 AUDIO / 漫画 IMAGE / 短剧 VIDEO），再走 `/api/catalog`。
- 四类已实测：路由判定全部正确，目录均正常返回章节。判定字段见 [书籍详情](#二书籍详情)。

---

## 二十二、OPDS 目录

供 Moon Reader / KOReader 等订阅。

| 端点 | 参数 | 说明 |
|------|------|------|
| `GET /api/opds` | — | OPDS 根目录 |
| `GET /api/opds/search` | `q` | 搜索 |
| `GET /api/opds/recommend` | — | 推荐 |
| `GET /api/opds/categories` | — | 分类列表 |
| `GET /api/opds/category/:category` | path 参数 | 分类书籍 |

---

## 二十三、发现页

| 端点 | 参数 | 上游 |
|------|------|------|
| `GET /api/front` | `tab`（默认 `0`） | `.../reading/bookapi/new_category/front/v` |
| `GET /api/landing` | `category_id`✅、`offset`、`genre_type`、`gender`、`word_number`、`book_status`、`sort_by` | `.../reading/bookapi/new_category/landing/v` |
| `GET /api/explore` | `category`（默认 `recommend`） | `.../new_category/front/v` |
| `GET /api/bookmall/cell/change` | `genre_tab`、`rank_sub_info_id`、`algo_type`、`offset`、`limit` | `.../reading/bookapi/bookmall/cell/change/v1/` |
| `GET /api/recommend/homepage` | `tab_type`、`offset`、`limit` | 兼容入口，内部复用 `cell/change` |
| `GET /api/related` | `book_id`✅ | 详情字段提取关联 ID 后 `multi-detail` 补详情 |
| `GET /api/author` | `author_id`、`author_name`、`book_id` | 作者名搜索并按作者过滤 |
| `GET /api/author_bookshelf` | `author_id`、`author_name`、`offset`、`count` | 作者书架兜底，当前复用同作者作品 |

> `genre_type` 如 `2130`=短剧、`2150`=漫剧；`gender` `1`男频/`2`女频。

### 新版发现页榜单 / 推荐

`/api/bookmall/cell/change` 默认补齐 `cell_id=7098235271900037133`、`genre_tab_list=2,3,4,5,6,7`、`rank_sub_info_id=2`、`algo_type=101`、`offset=0`、`limit=10`。返回会额外扁平化 `book_info`，兼容书源的 `$.data.book_info[*]||$.data.video_info[*]||$..book_data[*]||$..video_data[*]` 解析。

```bash
GET /api/bookmall/cell/change?genre_tab=2&algo_type=101&offset=0&limit=10
GET /api/recommend/homepage?tab_type=2&offset=0
```

常用 `genre_tab`：`2`小说、`3`出版、`4`短剧、`5`漫剧、`6`听书、`7`短篇。书源已把小说、出版、短剧、漫剧、听书、短篇的榜单按钮接到该接口。

当前书源只保留本地实测有数据且类型匹配的入口：

- 首页推荐：综合 `tab_type=2`、小说 `25`、听书 `5`、漫剧 `24`、短篇 `103`。
- 新版榜单：小说 `101/100/109/102/111`，出版 `101/196/197`，短剧 `101/502`，漫剧 `550`，听书 `201`，短篇 `601`。
- 标签筛选：综合模式下使用 `/api/category` + `/api/category/books`，支持频道、连载状态、字数过滤。
- 漫画：保留 `/sy/5.json` 分类入口和搜索 `+8`，不把当前为空的漫画首页推荐伪装成推荐页。

### 作者 / 关联作品

`/api/related` 从详情中的 `related`、`duplicate_content`、`bind_reputation` 等字段递归提取作品 ID，并用 `multi-detail` 回填详情。`/api/author` 和 `/api/author_bookshelf` 当前以作者名搜索并过滤作为兜底，返回统一 `data.book_info[]`。

```bash
GET /api/related?book_id=7237397843521047567
GET /api/author?author_id=2_7159445979974866176&author_name=月末影
GET /api/author_bookshelf?author_name=月末影&offset=0&count=20
```

### 分类浏览（小说 / 听书 / 漫画 / 短剧）

书源发现页按「搜索类型」从后端 `/sy/{n}.json` 读分类（小说→`2,1`、听书→`4`、漫画→`5`、短剧→`6`），
每个分类的 `category_id`+`genre_type` 拼成 `/api/landing` 请求。**已逐类实测可用**：

| 类型 | 示例 `category_id` / `genre_type` | landing 返回 | 实测 |
|------|------|------|:----:|
| 小说 | `7` / `0` | `data.book_info[]` | 10 本 ✅ |
| 听书 | `899` / `1` | `data.book_info[]` | 10 本 ✅ |
| 漫画 | `7` / `110` | `data.book_info[]` | 10 本（斗罗大陆）✅ |
| 短剧 | `1021` / `130` | `data.video_info[]` | 12 部 ✅ |

> 短剧返回 `video_info[]`（剧集），其余返回 `book_info[]`；书源 `ruleExplore.bookList` 用 `$.data.book_info[*]||$.data.video_info[*]` 统一解析，故四类发现页都能正常出内容。

---

### `GET /api/rank` 排行榜

聚合番茄**公开榜单**（无需设备/签名），归一化为标准书目结构，供发现页直接展示。

| 参数 | 默认 | 说明 |
|------|------|------|
| `type` | `巅峰` | `巅峰`/`出版`/`热搜`/`爆更`/`黑马`（也接受 `top`/`publication`） |
| `offset` | `0` | 分页偏移（每页 30） |

- **上游**（按 type 路由）：`巅峰`→`fanqienovel.com/.../top_book_list/v1`；`出版`→`fanqienovel.com/.../publication/list`；`热搜/爆更/黑马`→`api-lf.fanqiesdk.com/.../rank_list/v2`（`side_type` 12/15/13）。
- **返回**：归一化为 `data.book_info[]`，每项含 `book_id`、`book_name`、`author`、`thumb_url`、`abstract`、`category`、`score` —— 与 `/api/landing` 同构，书源发现页可用同一套解析规则。
- **缓存**：10 分钟。

```
GET /api/rank?type=巅峰&offset=0
GET /api/rank?type=爆更&offset=30
```

```json
{ "code": 0, "msg": "ok",
  "data": { "rank_type": "巅峰", "total": 30,
    "book_info": [
      {"book_id":"7276384138653862966","book_name":"我不是戏神","author":"三九音域","category":"都市高武","thumb_url":"https://...","abstract":"...","score":...}
    ] } }
```

> 🍅洋柿子书源「搜索类型=小说」时，发现页顶部已内置 **📈 排行榜**（巅峰/爆更/黑马/热搜/出版）。

---

## 二十三·五、登录态（番茄账号）

用户在 Legado 端用番茄账号登录（书源「🍅登录番茄账号」按钮，WebView 抓 `sessionid` Cookie；或手填「番茄登录Token」），随后这些端点用 `sessionid` 拉取**个人数据**。书架/历史的书目详情经设备签名的 `multi-detail` 补全为标准 `data.book_info[]`，发现页用与榜单同一套规则展示。

| 端点 | 参数 | 说明 |
|------|------|------|
| `GET /api/book_user` | `sessionid`✅ | 番茄用户信息（`data.name`/`isVip`/`avatar`/`id`）；未登录/过期 → `code:-2/-1` |
| `GET /api/book_shelf` | `sessionid`✅、`group`（可选分组名）、`meta`（可选） | 我的书架：`bookshelf/info/v`（Cookie）→ book_ids → `multi-detail` → `data.book_info[]`；`meta=1` 只返回 `groups[]/total`，供发现页快速显示分组 |
| `GET /api/read_history` | `sessionid`✅、`offset`（每页 20） | 阅读历史：签名 `read_history/list`（+Cookie）→ book_ids → `multi-detail` → `data.book_info[]` |
| `GET /api/book_add` ⚠️ | `sessionid`✅、`book_id`✅、`book_type`（默认 `0`） | 加入番茄书架（**写操作**，改真实账号）。**实验性/未验证**，见下 |
| `GET /api/book_remove` ⚠️ | `sessionid`✅、`book_id`✅、`book_type` | 移出番茄书架（**写操作**）。**实验性/未验证**，见下 |

- `sessionid` 也接受 `?session=` / `?token=` 三种参数名。
- `/api/book_shelf?meta=1` 返回 `data.groups[]`（`name/count`）和 `total`，不拉 `multi-detail`，适合发现页加载书架分组；传 `group=<分组名>` 时仍返回该分组书目。
- **真实验证**（用真实番茄账号 sessionid）：`book_user`→昵称正确；`book_shelf`→56 本；`read_history`→490 本。
- **read_history 分页**：番茄 `read_history/list` 一次返回全部历史（数百本），故服务端按 `offset` **本地分页**（每页 20，只对当页 `multi-detail` 补全），单页响应 ~1s；否则一次补全数百本会超时（实测旧版 24s → Legado 超时）。
- **隐私**：服务端只是带 `sessionid` 代理转发番茄官方接口，不存储、不记录该 Cookie。
- 番茄**个性推荐/猜你喜欢**无公开可解析书单 API，故未提供。
- ⚠️ **book_add / book_remove（书架写操作）实验性、当前不可用**：端点与登录态链路已就绪，但番茄书架写接口（`reading/bookapi/bookshelf/add/v`）经实测对各种参数/签名组合均返回 `PARAM_INVALID`（移动签名端 404；Web 端补 `msToken`+`a_bogus` 仍 `PARAM_INVALID`）。黑盒无法确定其必填签名，需抓真实 App 请求补全后才能启用。书源未接入这两个端点。

> 🍅洋柿子书源登录后，发现页顶部出现 **👤 个人中心**（昵称 / 📚我的书架 / 📁书架分组 / 🕘阅读历史）。

---

## 二十四、评论系统（11 个端点）

上游多为 **POST + JSON body** 并签名（先 `json` 序列化 → 算 MD5 作 `x-ss-stub` → 签名）。域名均为 `api5-normal-sinfonlinea.fqnovel.com`。

### 段评

| 端点 | 必填参数 | 上游 |
|------|----------|------|
| `GET /api/comment_count` | `item_id` | `POST .../commentapi/idea/list/{itemId}/v1` |
| `GET /api/chapter_comments` | `book_id`、`item_id`（`item_version`/`para_index`/`count`=10/`cursor`） | `POST .../commentapi/comment/list/{itemId}/v1` |
| `GET /api/comment_replies` | `comment_id`（`book_id`=0/`item_id`/`count`=10/`cursor`） | `POST .../commentapi/reply/list/{commentId}/v1` |

### 书评

| 端点 | 必填参数 | 上游 |
|------|----------|------|
| `GET /api/comments` | `book_id`（`count`=10/`offset`=0） | `POST .../commentapi/comment/list/{bookId}/v1` |
| `GET /api/comments_reply` | `book_id`、`comment_id`（`count`=10） | `POST .../commentapi/reply/list/{commentId}/v1` |
| `GET /api/comments_reply_reply` | `book_id`、`reply_id`（`count`=10） | `POST .../commentapi/reply/list/{replyId}/v1` |

### 章末评论

| 端点 | 必填参数 | 上游 |
|------|----------|------|
| `GET /api/forum_id` | `book_id`、`item_id`（`author_user_id`） | `POST .../reading/ugc/item/mix_data/get/v` |
| `GET /api/end_comments` | `book_id`、`forum_id`（`item_id`/`count`=10/`offset`=0） | `POST .../reading/ugc/item/mix_data/get/v` |
| `GET /api/end_comments_reply` | `book_id`、`post_id`（`count`=10/`offset`=0） | `GET .../reading/ugc/postdata/comment/v` |
| `GET /api/end_comments_reply_reply` | `book_id`、`group_id`、`comment_id`（`count`=10/`offset`=0） | `GET .../reading/ugc/reply/topic/v` |

### 作家说

| 端点 | 必填参数 | 上游 |
|------|----------|------|
| `GET /api/author_say` | `book_id`、`item_id` | `POST .../reading/ugc/author/topic/v` |

---

## 二十五、静态资源

| 端点 | 说明 |
|------|------|
| `GET /sy/{n}.json` | 发现页分类数据（`n`=1~6，来自磁盘或内嵌） |
| `GET /static/...` | 漫画解密后的临时图片等 |

---

## 二十六、服务状态

| 端点 | 说明 |
|------|------|
| `GET /` | 服务信息 + 全部端点清单（`endpoints` 字段）；带 `Accept: text/html` 时返回简单 HTML |
| `GET /openapi.json`、`GET /docs` | 兼容占位 |

**`GET /` 真实返回**（带 `Accept: application/json`，`endpoints` 已截断）：

```json
{
  "code": 0,
  "msg": "PyFQ-Go API 运行中",
  "version": "2.1-go",
  "endpoints": ["/api/search", "/api/book", "/api/directory", "/api/content",
                "/api/video", "/api/manga", "/api/full", "/api/health", "..."]
}
```

---

## 二十七、真实测试矩阵（2026-07-01）

测试环境：本地临时服务 `http://127.0.0.1:1973`，用户原有 `1968` 服务未参与；所有 JSON 端点均按 `/api/*` 兼容规则返回 HTTP 200，业务成败看 body `code`。响应过大的端点只记录核心字段、数组数量和数据形态。

| 模块 | 请求 | 结果 | 核心返回格式 |
|------|------|------|------|
| 存活 | `GET /api/ping` | HTTP 200 | 文本 `pong` |
| 健康 | `GET /api/health` | `code=0` | `data.status/config/device/cache` |
| 统计 | `GET /api/stats` | `code=0` | `data.summary/apis/failing_apis` |
| 搜索-小说 | `GET /api/search?query=系统&tab_type=3&offset=0` | `code=0` | 上游搜索对象，`search_tabs[].data[]` |
| 搜索-短剧 | `GET /api/search?query=系统&tab_type=11&offset=0` | `code=0` | 短剧搜索对象，含视频类书目 |
| 搜索-漫剧 | `GET /api/search?query=系统&tab_type=19&offset=0` | `code=0` | `data[]` 扁平数组，20 条 |
| 详情 | `GET /api/detail?book_id=7087519624329169951` | `code=0` | `data.book_id/book_name/author/genre_type/...` |
| Web 详情目录 | `GET /api/book?book_id=7087519624329169951` | `code=0` | `data.book_info/item_data_list/catalog_data` |
| 目录 | `GET /api/catalog?book_id=7087519624329169951` | `code=0` | `data.item_data_list[]`，1555 章 |
| 目录别名 | `GET /api/directory?book_id=7087519624329169951` | `code=0` | 同 `/api/catalog`，1555 章 |
| 章节元信息 | `GET /api/item_info?item_ids=7143038691945024547` | `code=0` | `data.http_code/data` |
| DH 正文 | `GET /api/full?book_id=7087519624329169951&item_ids=7089685628191048227` | `code=0` | `data[]`，每项 `item_id/title/content` |
| TXT 下载 JSON | `GET /api/download/txt?book_id=7087519624329169951&limit=1&batch_size=1&format=json` | `code=0` | `data.book_name/count/content_length/content` |
| TXT 下载文本 | `GET /api/download/txt?book_id=...` | HTTP 200 | `text/plain; charset=utf-8`，带 `Content-Disposition` |
| TXT 异步任务 | `GET /api/download/txt?book_id=...&async=1` | `code=0` | `data.job_id/status/status_url/result_url/content`，后台单并发生成 |
| TXT 异步结果 | `GET /api/download/txt/result?job_id=...` | HTTP 200 或 `code=0` | 完成后返回 TXT；未完成时返回任务状态 |
| 短剧直链 | `GET /api/video?item_id=7635674228238322712&book_id=7635672340797344792&type=json&quality=low` | `code=0` | `data.source=hongguo_direct`、`encrypted=false`、`url` 为 MP4 |
| 短剧官方回退 | `GET /api/video?...&type=json&quality=low&direct=0` | `code=0` | `data.source=official_multi_video_model`、`encrypted=true`、`url=/api/video_decrypt?...` |
| 短剧播放器 | `GET /api/player?item_id=7635674228238322712&book_id=7635672340797344792` | HTTP 200 | HTML，内置播放器模板 |
| 听书播放器 | `GET /api/audio_player?item_id=7143038691945024547&book_id=7087519624329169951` | HTTP 200 | HTML |
| 小说阅读器 | `GET /api/novel_reader?item_id=7143038691945024547&book_id=7087519624329169951` | HTTP 200 | HTML |
| 漫画阅读器 | `GET /api/manga_reader?item_id=7558345301194359320&book_id=7558345270663883838` | HTTP 200 | HTML |
| 分享 | `GET /api/book_share?book_id=7087519624329169951` | `code=0` | `data.share/book` |
| 发现首页 | `GET /api/front?tab=1` | `code=0` | `data.book_info[]` 等上游结构 |
| 探索别名 | `GET /api/explore?category=1` | `code=0` | 同 `/api/front` |
| 分类落地页 | `GET /api/landing?category_id=261&gender=1&offset=0` | `code=0` | `data.book_info[]`，10 本 |
| 排行榜 | `GET /api/rank?type=巅峰&offset=0` | `code=0` | `data.rank_type/total/book_info[]`，30 本 |
| 新版榜单 | `GET /api/bookmall/cell/change?genre_tab=2&algo_type=101&offset=0&limit=10` | `code=0` | `data.book_info[]`，16 本，另含 `cell_view` |
| 首页推荐兼容 | `GET /api/recommend/homepage?tab_type=25&offset=0&limit=10` | `code=0` | `data.book_info[]`，16 本 |
| 分类标签 | `GET /api/category` | `code=0` | `data.boy_category/girl_category/publish_category/...` |
| 分类筛选 | `GET /api/category/books?category_id=261&gender=1&creation_status=9&word_count=9&offset=0&limit=10` | `code=0` | `data.book_info[]`，10 本 |
| 关联作品 | `GET /api/related?book_id=7087519624329169951` | `code=0` | `data.book_info[]` 13 本、`related_ids[]` |
| 作者作品 | `GET /api/author?book_id=7087519624329169951` | `code=0` | `data.book_info[]`，5 本 |
| 作者书架 | `GET /api/author_bookshelf?book_id=7087519624329169951&offset=0&count=20` | `code=0` | `data.book_info[]`，5 本 |
| 书评 | `GET /api/comments?book_id=7087519624329169951&count=3&offset=0` | `code=0` | `data.data_list[]` 3 条、`common_list_info` |
| 段评计数 | `GET /api/comment_count?item_id=7143038691945024547` | `code=0` | `data.data` 段落计数字典 |
| 段评列表 | `GET /api/chapter_comments?book_id=7087519624329169951&item_id=7143038691945024547&count=3` | `code=0` | `data.data_list[]`，当前样例 0 条 |
| 书评回复 | `GET /api/comments_reply?book_id=7087519624329169951&comment_id=7138298534951977763&count=3` | `code=0` | `data.reply_list/common_list_info` |
| 书评二级回复 | `GET /api/comments_reply_reply?book_id=7087519624329169951&reply_id=7138298534951977763&count=3` | `code=0` | `data.reply_list/common_list_info` |
| 论坛 ID | `GET /api/forum_id?book_id=7087519624329169951&item_id=7143038691945024547` | `code=0` | `data.forum_id` 及章末混合数据 |
| 作家说 | `GET /api/author_say?book_id=7087519624329169951&item_id=7143038691945024547` | `code=0` | `data.topic` 或空对象 |
| 未登录用户 | `GET /api/book_user` | `code=-1` | 预期错误：缺少 `sessionid` |
| 未登录书架 | `GET /api/book_shelf?meta=1` | `code=-1` | 预期错误：缺少 `sessionid` |
| 未登录历史 | `GET /api/read_history` | `code=-1` | 预期错误：缺少 `sessionid` |
| 未登录加书架 | `GET /api/book_add?book_id=7087519624329169951` | `code=-1` | 预期错误：缺少 `sessionid` |
| 未登录移出书架 | `GET /api/book_remove?book_id=7087519624329169951` | `code=-1` | 预期错误：缺少 `sessionid` |
| 设备池 | `GET /api/device_pool?action=list` | `code=0` | `data.devices[]/total/active/failed` |
| Android 状态 | `GET /api/device_register?action=status` | `code=0` | `data.device_id/status/update_time` |
| iOS 状态 | `GET /api/ios_register?action=status` | `code=0` | `data.device_id/status/update_time` |
| 设备列表 | `GET /api/devices` | `code=0` | 同设备池列表 |
| 设备统计 | `GET /api/devices/stats` | `code=0` | `data.total/active/bad` + `data.by_status`（如 `{active,failed}`） |
| iOS 正文 | `GET /api/ios_content?item_ids=7143038691945024547` | `code=0` | `data.content`，该样例为空内容 |
| Novel 正文直返 | `GET /api/novel_content?item_id=7143038691945024547` | `code=0` | `data.content`，该样例为空内容 |
| Novel 目录直返 | `GET /api/novel_directory?book_id=7087519624329169951` | `code=0` | `data` 为上游直返结构，该样例为空对象 |
| 头条正文 | `GET /api/toutiao?item_id=7143038691945024547` | `code=0` | `data.content`，该样例为空内容 |
| 头条文章参数校验 | `GET /api/toutiao_article?url=https%3A%2F%2Fwww.toutiao.com%2Farticle%2F1` | `code=-1` | 预期错误：当前实现要求 `item_id` |
| 书源包装格式 | `GET /api/booksource?format=wrapped` | `code=0` | `data[]`，首项为 `🍅洋柿子` 书源 |
| OPDS 根 | `GET /api/opds` | HTTP 200 | `application/atom+xml` |
| OPDS 搜索 | `GET /api/opds/search?q=系统` | HTTP 200 | `application/atom+xml` |
| OPDS 推荐 | `GET /api/opds/recommend` | HTTP 200 | 文本/Atom，当前样例返回空推荐 |
| OPDS 分类 | `GET /api/opds/categories` | HTTP 200 | `application/atom+xml` |
| OPDS 分类书籍 | `GET /api/opds/category/玄幻` | HTTP 200 | 文本/Atom，当前样例分类名未命中 |

> `/api/content`、`/api/raw_full`、`/api/chapter`、`/api/audio`、`/api/wkcontent`、`/api/manga` 的旧样例 ID 在 2026-07-01 测试时被上游判定为“不存在或已停止合作”或网页 404，因此本文不把这些旧 ID 写成成功样例。下载链路已用当前目录第一章验证 `/api/full` 和 `/api/download/txt` 成功。

---

## 附录：错误码

`/api/*` 始终返回 HTTP 200，看 body 的 `code`（[`domain`](../internal/domain) `ErrorResponseWithCode`）：

| code | 含义 |
|------|------|
| `0` | 成功 |
| `-1` | 参数错误（缺必填参数） |
| `-2` | 设备密钥问题（未注册 / 加载失败） |
| `-3` | 上游请求失败 |
| `-4` | 解析失败 / 响应缺字段 |
| `-5` | 解密失败 / ffmpeg 错误 |
