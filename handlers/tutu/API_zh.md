# API 文档

## 快速开始

- **默认端口**: `8080`
- **基础 URL**: `http://localhost:8080`
- **API 前缀**: `/api/v1`

### 响应格式

所有接口直接返回上游 API 的原始响应（JSON 透传）。

错误（来自服务端中间件 —— 鉴权、校验）：
```json
{ "success": false, "error": "错误描述" }
```

### 设备重试

内容接口在以下情况会自动切换失败设备并重试：
- API 请求失败（网络/HTTP 错误）
- JSON 解析失败
- 解密后内容为空

---

## 章节接口

所有章节接口返回上游 API 原始响应，其中加密的 `content` 字段已在原位置解密。

### 获取单章

```bash
curl http://localhost:8080/api/v1/chapters/7276663560427471412
```

**响应**（原始 `full/v` API 结构）：
```json
{
  "code": 0,
  "data": {
    "content": "解密后的章节文本..."
  }
}
```

### 批量获取章节

```bash
curl "http://localhost:8080/api/v1/chapters/batch?item_ids=7276663560427471412,7341402209906606616"
```

| 参数       | 类型  | 必填 | 说明                    |
|-----------|-------|------|-------------------------|
| `item_ids`| query | 是   | 逗号分隔的章节 ID 列表   |

### 获取章节（小说 API，不解密）

```bash
curl http://localhost:8080/api/v1/chapters/7173216089122439711/novel
```

### 获取完整多章节（DH 密钥交换）

```bash
curl -X POST http://localhost:8080/api/v1/chapters/full \
  -H "Content-Type: application/json" \
  -d '{"book_id":"7237397843521047567","item_ids":["7237398596146954784","7237399221590820562"],"tone_id":0}'
```

最多 3000 章。

| 参数       | 类型   | 默认值 | 说明        |
|-----------|--------|--------|-------------|
| `book_id` | string | 必填   | 书籍 ID     |
| `item_ids`| array  | 必填   | 章节 ID 数组|
| `tone_id` | int    | `0`    | 音色 ID     |

也支持 GET：
```bash
curl "http://localhost:8080/api/v1/chapters/full?book_id=7237397843521047567&item_ids=7237398596146954784,7237399221590820562&tone_id=0"
```

### 获取头条章节（DH）

```bash
curl http://localhost:8080/api/v1/chapters/7276663560427471412/toutiao
```

### 获取音频时间线

```bash
curl "http://localhost:8080/api/v1/chapters/7319413832366443582/timeline?genre=4&tone_id=99"
```

| 参数       | 类型  | 默认值 | 说明   |
|-----------|-------|--------|--------|
| `genre`   | query | `4`    | 类型   |
| `tone_id` | query | `99`   | 音色   |

### 获取章节评论

```bash
curl -X POST "http://localhost:8080/api/v1/chapters/7491705434915488318/reviews?author_user_id=1988336383174046&book_id=7491705400958405694&forum_id=7492533906713973529"
```

| 参数              | 类型  | 必填 | 默认值 |
|------------------|-------|------|--------|
| `author_user_id` | query | 是   | -      |
| `book_id`        | query | 是   | -      |
| `forum_id`       | query | 是   | -      |
| `count`          | query | 否   | `20`   |

### 获取段落评论（段评）

```bash
curl -X POST "http://localhost:8080/api/v1/chapters/7491705434915488318/paragraphs/44/reviews?group_id=7491705434915488318&book_id=7491705400958405694&author_user_id=1988336383174046&item_version=b271c896b27dbe2e51c2ca26deabade2"
```

| 参数              | 类型  | 必填 | 默认值                          |
|------------------|-------|------|---------------------------------|
| `para_index`     | path  | 是   | -                               |
| `group_id`       | query | 是   | -                               |
| `book_id`        | query | 是   | -                               |
| `author_user_id` | query | 是   | -                               |
| `item_version`   | query | 是   | -                               |
| `group_type`     | query | 否   | `15`                            |
| `count`          | query | 否   | `20`                            |
| `client_ab_params`| query| 否   | `{"comment_dislike_filter":"2"}`|

### 获取短篇段落评论（短篇段评）

```bash
curl -X POST "http://localhost:8080/api/v1/chapters/7416956264086766104/paragraphs/3/short-reviews?group_id=7416952589742260760&book_id=7416956264086766104&item_version=49b64631576a4d0701d1a6494c7b40e5_1_9b5a405d222249c"
```

| 参数           | 类型  | 必填 | 默认值 |
|---------------|-------|------|--------|
| `para_index`  | path  | 是   | -      |
| `group_id`    | query | 是   | -      |
| `book_id`     | query | 是   | -      |
| `item_version`| query | 是   | -      |
| `count`       | query | 否   | `20`   |

### 获取条目信息

```bash
curl "http://localhost:8080/api/v1/items/7507512821328904729,7507960973773242905"
```

### 查询圈子 ID

```bash
curl "http://localhost:8080/api/v1/forum-id?author_user_id=3395746397165147&book_id=7592279900040465433&item_id=7601087627936154136"
```

```json
{
  "forum_id": "7492533906713973529",
  "author_user_id": "3395746397165147",
  "book_id": "7592279900040465433",
  "item_id": "7601087627936154136"
}
```

| 参数              | 类型  | 必填 |
|------------------|-------|------|
| `author_user_id` | query | 是   |
| `book_id`        | query | 是   |
| `item_id`        | query | 是   |

### 获取评论回复列表

```bash
curl -X POST "http://localhost:8080/api/v1/comments/7532767563971527448/replies?group_id=7412284152524849689&book_id=7412259933569158169&count=3"
```

| 参数         | 类型  | 必填 | 默认值 |
|-------------|-------|------|--------|
| `comment_id`| path  | 是   | -      |
| `group_id`  | query | 是   | -      |
| `book_id`   | query | 是   | -      |
| `count`     | query | 否   | `10`   |

---

## 书籍接口

所有书籍接口返回上游 API 原始响应。

### 获取书籍详情

```bash
curl http://localhost:8080/api/v1/books/7491705400958405694
```

通过 `detail/v` API 获取。

### 获取书籍目录（阅读版）

```bash
curl http://localhost:8080/api/v1/books/7237397843521047567/directory
```

### 获取书籍目录（小说版）

```bash
curl http://localhost:8080/api/v1/books/7237397843521047567/directory/novel
```

### 获取书籍目录（番茄版）

```bash
curl http://localhost:8080/api/v1/books/7237397843521047567/directory/fanqie
```

### 获取书籍详情（旧版多详情）

```bash
curl http://localhost:8080/api/v1/books/7237397843521047567/detail
```

### 获取书籍评论（旧版）

```bash
curl "http://localhost:8080/api/v1/books/7237397843521047567/comments?count=10&offset=0"
```

| 参数     | 类型  | 默认值 |
|---------|-------|--------|
| `count` | query | `10`   |
| `offset`| query | `0`    |

### 获取书籍分享信息 & 摘要

```bash
curl "http://localhost:8080/api/v1/books/6925013713007184903/share?mode=both"
```

| 参数   | 类型  | 默认值    | 可选值                     |
|-------|-------|-----------|----------------------------|
| `mode`| query | `share`   | `share`, `excerpt`         |

`mode=share`（默认）：原始分享 API 响应。
`mode=excerpt`：原始摘要 API 响应。

### 获取书籍书评

```bash
curl -X POST "http://localhost:8080/api/v1/books/7491705400958405694/reviews?count=20&item_count=0"
```

| 参数         | 类型  | 默认值 |
|-------------|-------|--------|
| `count`     | query | `20`   |
| `item_count`| query | `0`    |

### 获取书籍音色

```bash
curl http://localhost:8080/api/v1/books/7491705400958405694/tones
```

### 获取章节摘要

```bash
curl "http://localhost:8080/api/v1/books/7491705400958405694/chapters/summary?item_ids=7491705434915488318"
```

| 参数       | 类型  | 必填 |
|-----------|-------|------|
| `item_ids`| query | 是   |

### 获取相关作品

```bash
curl http://localhost:8080/api/v1/books/7491705400958405694/related
```

---

## 小说接口

### 获取小说详情

```bash
curl http://localhost:8080/api/v1/novels/7237397843521047567
```

---

## 搜索接口

### 搜索（阅读 API）

```bash
curl "http://localhost:8080/api/v1/search?query=fantasy&offset=0&count=10&tab_type=1"
```

| 参数       | 类型  | 必填 | 默认值     |
|-----------|-------|------|-----------|
| `query`   | query | 是   | -         |
| `offset`  | query | 否   | `0`       |
| `count`   | query | 否   | `0`       |
| `tab_type`| query | 否   | `1`       |
| `passback`| query | 否   | (空)      |

### 搜索（番茄）

```bash
curl "http://localhost:8080/api/v1/search/fanqie?q=修仙&offset=0"
```

| 参数     | 类型  | 必填 | 默认值 |
|---------|-------|------|--------|
| `q`     | query | 是   | -      |
| `offset`| query | 否   | `0`    |

### 搜索建议

```bash
curl "http://localhost:8080/api/v1/search/suggest?q=fantasy"
```

| 参数 | 类型  | 必填 |
|-----|-------|------|
| `q` | query | 是   |

### 热搜

```bash
curl "http://localhost:8080/api/v1/search/hot?offset=0&scene=10"
```

| 参数     | 类型  | 默认值 |
|---------|-------|--------|
| `offset`| query | `0`    |
| `scene` | query | `10`   |

---

## 音频接口

### 获取有声书详情

```bash
curl http://localhost:8080/api/v1/audio/books/7491705400958405694
```

### 获取音频章节播放信息

```bash
curl "http://localhost:8080/api/v1/audio/books/7491705400958405694/chapters/7491705434915488318?tone_id=1"
```

| 参数     | 类型  | 默认值 |
|---------|-------|--------|
| `tone_id`| query| `0`    |

### 音频播放

```bash
curl -X POST "http://localhost:8080/api/v1/audio/play?item_ids=7276663560427471412&book_id=7491705400958405694&tone_id=1"
```

| 参数       | 类型  | 必填 |
|-----------|-------|------|
| `item_ids`| query | 是   |
| `book_id` | query | 是   |
| `tone_id` | query | 否（`0`） |

---

## 作者接口

### 获取作者信息

```bash
curl http://localhost:8080/api/v1/authors/1988336383174046
```

### 获取作者书架

```bash
curl "http://localhost:8080/api/v1/authors/1988336383174046/bookshelf?count=30&offset=0"
```

| 参数     | 类型  | 默认值 |
|---------|-------|--------|
| `count` | query | `30`   |
| `offset`| query | `0`    |

---

## 漫画 / 视频接口

### 获取漫画图片

```bash
curl "http://localhost:8080/api/v1/manga/7097103732478837255?show_html=0"
```

解密图片到 `src/` 目录。设置 `show_html=1` 可查看 HTML 页面。

### 阅读器插件系统

```bash
curl "http://localhost:8080/api/v1/viewer?plugin=manga_reader&book_id=xxx&item_id=xxx"
```

所有阅读器插件都是 `plugins/` 目录下独立的 HTML 文件。服务端会注入 `window.PLUGIN_PARAMS` 包含所有查询参数，插件自行处理 API 调用和渲染。插件可编辑，无需重新编译 Go。

| 参数     | 类型  | 必填 | 说明                          |
|---------|-------|------|-------------------------------|
| `plugin`| query | 是   | 插件名称（不含 `.html`）       |
| `*`     | query | —    | 所有其他参数传递给插件         |

**内置插件：**

| 插件名          | 文件路径                       | 说明                     |
|----------------|-------------------------------|--------------------------|
| `manga_reader` | `plugins/manga_reader.html`   | 滚动阅读、章节导航、全屏   |
| `player`       | `plugins/player.html`         | 视频播放、滑动选集、倍速   |

### 获取漫画视频合集详情

```bash
curl http://localhost:8080/api/v1/manga/videos/7526874845758376985
```

### 获取视频模型 / 流（旧版单路）

```bash
curl http://localhost:8080/api/v1/videos/7553551995894762521
```

旧版单视频本地解密（最佳画质）。推荐使用 `/videos/multi` 选择画质（与 HG_py `multi_video.py` 对齐）。

### 多视频本地解密（`multi_video.py`）

下载 + CENC 解密选定画质，将 `main_url` 替换为本地 `/src/` URL。
响应格式与 Python 一致：`{status, video_ids, quality, response}`。

```bash
# 使用选定画质解密（省略或未找到则自动选最高）
curl "http://localhost:8080/api/v1/videos/multi?video_ids=7553551995894762521&quality=720p&book_id=7655547242555657241"

# 路径形式
curl "http://localhost:8080/api/v1/videos/multi/7553551995894762521?quality=1080p"

# 列出可用画质（动态，非硬编码）
curl "http://localhost:8080/api/v1/videos/multi?video_ids=7553551995894762521&list_qualities=1"
```

| 参数                  | 类型       | 默认值         | 说明                                      |
|----------------------|-----------|----------------|-------------------------------------------|
| `video_ids` / `item_ids` | query/path | 必填       | 视频 ID（逗号分隔）                        |
| `quality`            | query     | *(自动选最高)*   | 取自该视频的 `video_meta.definition`       |
| `book_id`            | query     | 空             | 传入上游请求体                              |
| `list_qualities`     | query     | `0`            | `1` = 仅列出可用画质                        |

### 解析视频 CDN 地址（不下载）

获取原始兜底响应，仅解密 `main_url` / `backup_url_1`。
**不**下载、不做 CENC 解密、不剥离字段、不包装 payload。

```bash
curl "http://localhost:8080/api/v1/videos/resolve?item_ids=7553551995894762521&book_id=7562089466370722878"

# 路径形式
curl "http://localhost:8080/api/v1/videos/resolve/7553551995894762521?book_id=7562089466370722878"
```

| 参数       | 类型       | 默认值 | 说明                          |
|-----------|-----------|--------|-------------------------------|
| `item_ids`| query/path | 必填   | 视频 ID（逗号分隔）            |
| `video_id`| query     | —      | `item_ids` 的别名              |
| `book_id` | query     | 必填   | 上游请求体中使用的书籍/合集 ID  |

---

## 发现接口

### 首页推荐

```bash
curl "http://localhost:8080/api/v1/recommend/homepage?tab_type=2&offset=0"
```

| 参数               | 类型  | 默认值 |
|-------------------|-------|--------|
| `client_template` | query | `0`    |
| `tab_type`        | query | `2`    |
| `offset`          | query | `0`    |

### 排行榜

```bash
curl "http://localhost:8080/api/v1/rank/7098235271900037133?offset=0&genre_tab=2&rank_sub_info_id=2&algo_type=101"
```

| 参数                | 类型  | 默认值 |
|--------------------|-------|--------|
| `offset`           | query | `0`    |
| `genre_tab`        | query | `2`    |
| `rank_sub_info_id` | query | `2`    |
| `algo_type`        | query | `101`  |

---

## 文章接口

### 获取头条文章

```bash
curl http://localhost:8080/api/v1/articles/7276663560427471412
```

---

## JS 响应过滤

所有 API 响应可在发送给客户端前通过 JavaScript 过滤器进行转换。完整文档见 [FILTER.md](FILTER.md)。

### 快速上手

1. 在 `filter.json` 中启用路由：
```json
{
  "routes": {
    "/api/v1/chapters": { "enabled": true, "js": "filters/chapter.js" }
  }
}
```

2. 在 JS 文件中编写 `filter(data)`：
```javascript
function filter(data) {
    // data 是解析后的上游 API 响应 JSON
    // 修改并返回
    return data;
}
```

3. 重启服务 —— JS 文件在启动时编译。

### 内置模板

| 过滤文件            | 路由前缀           | 涵盖范围                                                                 |
|--------------------|-------------------|-------------------------------------------------------------------------|
| `filters/chapter.js`| `/api/v1/chapters`| 单章、批量、完整、头条、小说、时间线、段落评论、短篇段落评论                |
| `filters/book.js`   | `/api/v1/books`   | 详情、目录、分享、书评、音色、摘要、相关、旧版                            |
| `filters/search.js` | `/api/v1/search`  | 阅读搜索、番茄、建议、热搜                                                |
| `filters/audio.js`  | `/api/v1/audio`   | 详情、播放、播放中                                                        |
| `filters/author.js` | `/api/v1/authors` | 信息、书架                                                                |
| `filters/manga.js`  | `/api/v1/manga`   | 图片、阅读器、视频详情                                                    |
| `filters/novel.js`  | `/api/v1/novels`  | 小说详情                                                                  |
| `filters/recommend.js` | `/api/v1/recommend` | 首页                                                              |
| `filters/rank.js`   | `/api/v1/rank`    | 排行榜                                                                    |
| `filters/article.js`| `/api/v1/articles`| 头条文章                                                                  |
| `filters/item.js`   | `/api/v1/items`   | 条目信息                                                                  |
| `filters/video.js`  | `/api/v1/videos`  | 旧版流、多路（本地解密）、解析（CDN 地址）、画质列表                        |
| `filters/viewer.js` | `/api/v1/viewer`  | 阅读器插件系统                                                            |
| `filters/forum_id.js`| `/api/v1/forum-id`| 圈子 ID 查询                                                            |
| `filters/comment.js`| `/api/v1/comments`| 评论回复列表                                                              |

---

## 配置（`config.json`）

```json
{
  "algorithm_type": "0404",
  "port": 8080,
  "anti_crawler": {
    "enabled": true,
    "redirect_url": "https://www.example.com"
  }
}
```

| 字段                        | 说明                                       |
|----------------------------|-------------------------------------------|
| `algorithm_type`           | 签名算法：`8404` 或 `0404`                 |
| `port`                     | 服务端口（默认 `8080`）                     |
| `anti_crawler.enabled`     | 是否重定向非 API 流量                       |
| `anti_crawler.redirect_url`| 重定向目标 URL                              |

---

## 授权

服务需要有效的 `auth/auth.json` 文件，使用 RSA-SHA256 签名并**绑定机器设备码**。

### 设备绑定

1. 首次授权失败时，程序会在工作目录写入 `设备码.txt` 并退出。
2. 将该设备码发送给授权方。
3. 授权方签名 `auth_data`，其中包含 `device_code` 字段（必须与本机匹配）。
4. 将文件放置在 `auth/auth.json` 并重启。

`auth_data` JSON 字段：

| 字段                  | 必填 | 说明                                       |
|----------------------|------|-------------------------------------------|
| `client_id`          | 是   | 授权客户端 ID                               |
| `timestamp`          | 是   | 签发时间（unix）                            |
| `expire_time`        | 是   | 过期时间（unix）                            |
| `expire_time_formatted` | 是 | UTC 格式 `YYYY-MM-DD HH:MM:SS`，即 expire_time |
| `device_code`        | 是   | 机器指纹，例如 `A1B2-C3D4-...`             |

如果授权过期、设备不匹配，或运行中重新验证失败，所有 API 请求将返回 HTTP 403。
