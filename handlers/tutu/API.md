# API Documentation

## Quick Start

- **Default Port**: `8080`
- **Base URL**: `http://localhost:8080`
- **API Prefix**: `/api/v1`

### Response Format

All endpoints return the raw upstream API response directly (JSON passthrough). 

Error (from server middleware — auth, validation):
```json
{ "success": false, "error": "description" }
```

### Device Retry

Content endpoints automatically replace failed devices and retry when:
- API request fails (network/HTTP error)
- JSON parse fails
- Content is empty after decryption

---

## Chapter APIs

All chapter endpoints return the raw upstream API response with encrypted `content` fields decrypted in place. 

### Get Single Chapter

```bash
curl http://localhost:8080/api/v1/chapters/7276663560427471412
```

**Response** (raw `full/v` API structure):
```json
{
  "code": 0,
  "data": {
    "content": "decrypted chapter text..."
  }
}
```

### Get Batch Chapters

```bash
curl "http://localhost:8080/api/v1/chapters/batch?item_ids=7276663560427471412,7341402209906606616"
```


| Parameter  | Type  | Required | Description              |
|------------|-------|----------|--------------------------|
| `item_ids` | query | yes      | Comma-separated chapter IDs |

### Get Chapter (Novel API, No Decrypt)

```bash
curl http://localhost:8080/api/v1/chapters/7173216089122439711/novel
```

### Get Full Multi-Chapter (DH Key Exchange)

```bash
curl -X POST http://localhost:8080/api/v1/chapters/full \
  -H "Content-Type: application/json" \
  -d '{"book_id":"7237397843521047567","item_ids":["7237398596146954784","7237399221590820562"],"tone_id":0}'
```

Max 3000 chapters.

| Parameter  | Type    | Default  | Description              |
|------------|---------|----------|--------------------------|
| `book_id`  | string  | required | Book ID                  |
| `item_ids` | array   | required | Chapter ID array         |
| `tone_id`  | int     | `0`      | Voice tone ID            |

Supports GET as well:
```bash
curl "http://localhost:8080/api/v1/chapters/full?book_id=7237397843521047567&item_ids=7237398596146954784,7237399221590820562&tone_id=0"
```

### Get Toutiao Chapter (DH)

```bash
curl http://localhost:8080/api/v1/chapters/7276663560427471412/toutiao
```

### Get Audio Timeline

```bash
curl "http://localhost:8080/api/v1/chapters/7319413832366443582/timeline?genre=4&tone_id=99"
```

| Parameter | Type  | Default | Description  |
|-----------|-------|---------|--------------|
| `genre`   | query | `4`     | Genre type   |
| `tone_id` | query | `99`    | Voice tone   |

### Get Chapter Reviews

```bash
curl -X POST "http://localhost:8080/api/v1/chapters/7491705434915488318/reviews?author_user_id=1988336383174046&book_id=7491705400958405694&forum_id=7492533906713973529"
```

| Parameter        | Type  | Required | Default |
|------------------|-------|----------|---------|
| `author_user_id` | query | yes      | -       |
| `book_id`        | query | yes      | -       |
| `forum_id`       | query | yes      | -       |
| `count`          | query | no       | `20`    |

### Get Paragraph Reviews (段评)

```bash
curl -X POST "http://localhost:8080/api/v1/chapters/7491705434915488318/paragraphs/44/reviews?group_id=7491705434915488318&book_id=7491705400958405694&author_user_id=1988336383174046&item_version=b271c896b27dbe2e51c2ca26deabade2"
```


| Parameter         | Type  | Required | Default                        |
|-------------------|-------|----------|--------------------------------|
| `para_index`      | path  | yes      | -                              |
| `group_id`        | query | yes      | -                              |
| `book_id`         | query | yes      | -                              |
| `author_user_id`  | query | yes      | -                              |
| `item_version`    | query | yes      | -                              |
| `group_type`      | query | no       | `15`                           |
| `count`           | query | no       | `20`                           |
| `client_ab_params`| query | no       | `{"comment_dislike_filter":"2"}` |

### Get Short Paragraph Reviews (短篇段评)

```bash
curl -X POST "http://localhost:8080/api/v1/chapters/7416956264086766104/paragraphs/3/short-reviews?group_id=7416952589742260760&book_id=7416956264086766104&item_version=49b64631576a4d0701d1a6494c7b40e5_1_9b5a405d222249c"
```

| Parameter      | Type  | Required | Default |
|----------------|-------|----------|---------|
| `para_index`   | path  | yes      | -       |
| `group_id`     | query | yes      | -       |
| `book_id`      | query | yes      | -       |
| `item_version` | query | yes      | -       |
| `count`        | query | no       | `20`    |

### Get Item Info

```bash
curl "http://localhost:8080/api/v1/items/7507512821328904729,7507960973773242905"
```

### Query Forum ID

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

| Parameter        | Type  | Required |
|------------------|-------|----------|
| `author_user_id` | query | yes      |
| `book_id`        | query | yes      |
| `item_id`        | query | yes      |

### Get Comment Reply List

```bash
curl -X POST "http://localhost:8080/api/v1/comments/7532767563971527448/replies?group_id=7412284152524849689&book_id=7412259933569158169&count=3"
```

| Parameter    | Type  | Required | Default |
|--------------|-------|----------|---------|
| `comment_id` | path  | yes      | -       |
| `group_id`   | query | yes      | -       |
| `book_id`    | query | yes      | -       |
| `count`      | query | no       | `10`    |

---

## Book APIs

All book endpoints return raw upstream API responses.

### Get Book Detail

```bash
curl http://localhost:8080/api/v1/books/7491705400958405694
```

Via `detail/v` API.

### Get Book Directory (Reading)

```bash
curl http://localhost:8080/api/v1/books/7237397843521047567/directory
```

### Get Book Directory (Novel)

```bash
curl http://localhost:8080/api/v1/books/7237397843521047567/directory/novel
```

### Get Book Directory (Fanqie)

```bash
curl http://localhost:8080/api/v1/books/7237397843521047567/directory/fanqie
```

### Get Book Detail (Legacy Multi-Detail)

```bash
curl http://localhost:8080/api/v1/books/7237397843521047567/detail
```

### Get Book Comments (Legacy)

```bash
curl "http://localhost:8080/api/v1/books/7237397843521047567/comments?count=10&offset=0"
```

| Parameter | Type  | Default |
|-----------|-------|---------|
| `count`   | query | `10`    |
| `offset`  | query | `0`     |

### Get Book Share Info & Excerpts

```bash
curl "http://localhost:8080/api/v1/books/6925013713007184903/share?mode=both"
```

| Parameter | Type  | Default | Options                    |
|-----------|-------|---------|----------------------------|
| `mode`    | query | `share` | `share`, `excerpt`         |

`mode=share` (default): raw share API response.
`mode=excerpt`: raw excerpt API response.

### Get Book Reviews

```bash
curl -X POST "http://localhost:8080/api/v1/books/7491705400958405694/reviews?count=20&item_count=0"
```

| Parameter    | Type  | Default |
|--------------|-------|---------|
| `count`      | query | `20`    |
| `item_count` | query | `0`     |

### Get Book Tones

```bash
curl http://localhost:8080/api/v1/books/7491705400958405694/tones
```

### Get Chapter Summaries

```bash
curl "http://localhost:8080/api/v1/books/7491705400958405694/chapters/summary?item_ids=7491705434915488318"
```

| Parameter  | Type  | Required |
|------------|-------|----------|
| `item_ids` | query | yes      |

### Get Related Works

```bash
curl http://localhost:8080/api/v1/books/7491705400958405694/related
```

---

## Novel APIs

### Get Novel Detail

```bash
curl http://localhost:8080/api/v1/novels/7237397843521047567
```

---

## Search APIs

### Search (Reading API)

```bash
curl "http://localhost:8080/api/v1/search?query=fantasy&offset=0&count=10&tab_type=1"
```

| Parameter  | Type  | Required | Default     |
|------------|-------|----------|-------------|
| `query`    | query | yes      | -           |
| `offset`   | query | no       | `0`         |
| `count`    | query | no       | `0`         |
| `tab_type` | query | no       | `1`         |
| `passback` | query | no       | (empty)     |

### Search (Fanqie)

```bash
curl "http://localhost:8080/api/v1/search/fanqie?q=修仙&offset=0"
```

| Parameter | Type  | Required | Default |
|-----------|-------|----------|---------|
| `q`       | query | yes      | -       |
| `offset`  | query | no       | `0`     |

### Search Suggestions

```bash
curl "http://localhost:8080/api/v1/search/suggest?q=fantasy"
```

| Parameter | Type  | Required |
|-----------|-------|----------|
| `q`       | query | yes      |

### Hot Search

```bash
curl "http://localhost:8080/api/v1/search/hot?offset=0&scene=10"
```

| Parameter | Type  | Default |
|-----------|-------|---------|
| `offset`  | query | `0`     |
| `scene`   | query | `10`    |

---

## Audio APIs

### Get Audio Book Detail

```bash
curl http://localhost:8080/api/v1/audio/books/7491705400958405694
```

### Get Audio Chapter Play Info

```bash
curl "http://localhost:8080/api/v1/audio/books/7491705400958405694/chapters/7491705434915488318?tone_id=1"
```

| Parameter | Type  | Default |
|-----------|-------|---------|
| `tone_id` | query | `0`     |

### Audio Playback

```bash
curl -X POST "http://localhost:8080/api/v1/audio/play?item_ids=7276663560427471412&book_id=7491705400958405694&tone_id=1"
```

| Parameter  | Type  | Required |
|------------|-------|----------|
| `item_ids` | query | yes      |
| `book_id`  | query | yes      |
| `tone_id`  | query | no (`0`) |

---

## Author APIs

### Get Author Info

```bash
curl http://localhost:8080/api/v1/authors/1988336383174046
```

### Get Author Bookshelf

```bash
curl "http://localhost:8080/api/v1/authors/1988336383174046/bookshelf?count=30&offset=0"
```

| Parameter | Type  | Default |
|-----------|-------|---------|
| `count`   | query | `30`    |
| `offset`  | query | `0`     |

---

## Manga / Video APIs

### Get Manga Images

```bash
curl "http://localhost:8080/api/v1/manga/7097103732478837255?show_html=0"
```

Decrypts images to `src/`. Set `show_html=1` for HTML page.

### Viewer Plugin System

```bash
curl "http://localhost:8080/api/v1/viewer?plugin=manga_reader&book_id=xxx&item_id=xxx"
```

All viewer plugins are standalone HTML files in `plugins/`. The server injects `window.PLUGIN_PARAMS` with all query parameters, and the plugin handles its own API calls and rendering. Plugins can be edited without rebuilding Go.

| Parameter | Type  | Required | Description |
|-----------|-------|----------|-------------|
| `plugin`  | query | yes      | Plugin name (without `.html`) |
| `*`       | query | —        | All other params passed to plugin |

**Built-in plugins:**

| Plugin | File | Description |
|--------|------|-------------|
| `manga_reader` | `plugins/manga_reader.html` | Scroll reader, chapter nav, fullscreen |
| `player` | `plugins/player.html` | Video player, swipe episodes, speed control |

### Get Manga Video Series Detail

```bash
curl http://localhost:8080/api/v1/manga/videos/7526874845758376985
```

### Get Video Model / Stream (legacy single)

```bash
curl http://localhost:8080/api/v1/videos/7553551995894762521
```

Legacy single-video local decrypt (best quality). Prefer `/videos/multi` for quality selection (aligned with HG_py `multi_video.py`).

### Multi Video Local Decrypt (`multi_video.py`)

Downloads + CENC-decrypts selected quality, replaces `main_url` with local `/src/` URL.
Response shape matches Python: `{status, video_ids, quality, response}`.

```bash
# decrypt with selected quality (or auto highest if omitted / not found)
curl "http://localhost:8080/api/v1/videos/multi?video_ids=7553551995894762521&quality=720p&book_id=7655547242555657241"

# path form
curl "http://localhost:8080/api/v1/videos/multi/7553551995894762521?quality=1080p"

# list available qualities (dynamic, not hard-coded)
curl "http://localhost:8080/api/v1/videos/multi?video_ids=7553551995894762521&list_qualities=1"
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_ids` / `item_ids` | query/path | required | Video ID(s), comma-separated |
| `quality` | query | *(auto highest)* | Definition from this video's `video_meta.definition` |
| `book_id` | query | empty | Passed into upstream body |
| `list_qualities` | query | `0` | `1` = only list available definitions |

### Resolve Video CDN URLs (no download)

Fetches the original fallback response and only decrypts `main_url` / `backup_url_1`.
Does **not** download, CENC-decrypt, strip fields, or wrap the payload.

```bash
curl "http://localhost:8080/api/v1/videos/resolve?item_ids=7553551995894762521&book_id=7562089466370722878"

# path form
curl "http://localhost:8080/api/v1/videos/resolve/7553551995894762521?book_id=7562089466370722878"
```

| Parameter  | Type  | Default | Description |
|------------|-------|---------|-------------|
| `item_ids` | query/path | required | Video ID(s), comma-separated |
| `video_id` | query | — | Alias of `item_ids` |
| `book_id`  | query | required | Book/series ID used in upstream request body |

---

## Discovery APIs

### Homepage Recommendations

```bash
curl "http://localhost:8080/api/v1/recommend/homepage?tab_type=2&offset=0"
```

| Parameter         | Type  | Default |
|-------------------|-------|---------|
| `client_template` | query | `0`     |
| `tab_type`        | query | `2`     |
| `offset`          | query | `0`     |

### Rank List

```bash
curl "http://localhost:8080/api/v1/rank/7098235271900037133?offset=0&genre_tab=2&rank_sub_info_id=2&algo_type=101"
```

| Parameter          | Type  | Default |
|--------------------|-------|---------|
| `offset`           | query | `0`     |
| `genre_tab`        | query | `2`     |
| `rank_sub_info_id` | query | `2`     |
| `algo_type`        | query | `101`   |

---

## Article APIs

### Get Toutiao Article

```bash
curl http://localhost:8080/api/v1/articles/7276663560427471412
```

---

## JS Response Filtering

All API responses can be transformed via JavaScript filters before being sent to the client. See [FILTER.md](FILTER.md) for full documentation.

### Quick Setup

1. Enable a route in `filter.json`:
```json
{
  "routes": {
    "/api/v1/chapters": { "enabled": true, "js": "filters/chapter.js" }
  }
}
```

2. Write `filter(data)` in the JS file:
```javascript
function filter(data) {
    // data is the parsed upstream API response JSON
    // modify and return
    return data;
}
```

3. Restart the server — JS files are compiled at startup.

### Built-in Templates

| Filter File | Route Prefix | Covers |
|---|---|---|
| `filters/chapter.js` | `/api/v1/chapters` | Single, batch, full, toutiao, novel, timeline, paragraph reviews, short paragraph reviews |
| `filters/book.js` | `/api/v1/books` | Detail, directory, share, reviews, tones, summary, related, legacy |
| `filters/search.js` | `/api/v1/search` | Reading search, fanqie, suggest, hot |
| `filters/audio.js` | `/api/v1/audio` | Detail, play, playback |
| `filters/author.js` | `/api/v1/authors` | Info, bookshelf |
| `filters/manga.js` | `/api/v1/manga` | Images, reader, video detail |
| `filters/novel.js` | `/api/v1/novels` | Novel detail |
| `filters/recommend.js` | `/api/v1/recommend` | Homepage |
| `filters/rank.js` | `/api/v1/rank` | Rank lists |
| `filters/article.js` | `/api/v1/articles` | Toutiao article |
| `filters/item.js` | `/api/v1/items` | Item info |
| `filters/video.js` | `/api/v1/videos` | Legacy stream, multi (local decrypt), resolve (CDN URLs), list_qualities |
| `filters/viewer.js` | `/api/v1/viewer` | Viewer plugin system |
| `filters/forum_id.js` | `/api/v1/forum-id` | Forum ID query |
| `filters/comment.js` | `/api/v1/comments` | Comment reply list |

---

## Configuration (`config.json`)

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

| Field | Description |
|---|---|
| `algorithm_type` | Signature algorithm: `8404` or `0404` |
| `port` | Server port (default `8080`) |
| `anti_crawler.enabled` | Redirect non-API traffic |
| `anti_crawler.redirect_url` | Redirect target URL |

---

## Authorization

The server requires a valid `auth/auth.json` file signed with RSA-SHA256 and **bound to a machine device code**.

### Device binding

1. On first failed authorization, the process writes `设备码.txt` in the working directory and exits.
2. Send that device code to the license issuer.
3. Issuer signs `auth_data` including field `device_code` (must match this machine).
4. Place the file at `auth/auth.json` and restart.

`auth_data` JSON fields:

| Field | Required | Description |
|-------|----------|-------------|
| `client_id` | yes | License client id |
| `timestamp` | yes | Issue time (unix) |
| `expire_time` | yes | Expiry (unix) |
| `expire_time_formatted` | yes | UTC `YYYY-MM-DD HH:MM:SS` of expire_time |
| `device_code` | yes | Machine fingerprint, e.g. `A1B2-C3D4-...` |

If authorization expires, device mismatches, or revalidation fails while running, all API requests receive HTTP 403.
