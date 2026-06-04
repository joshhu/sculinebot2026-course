# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案概觀

這是 **2026 年上半年東吳大學資料科學系 LINE Bot 進階課程**的教學範例集。整個 repo 不是單一應用，而是**多個獨立、可單獨執行的 LINE Bot 範例檔**，每一支對應課程的一個進度，從最簡單的單輪對話，逐步加上 system prompt、logging、多輪對話、Google Search、圖片／影片處理，以及 OpenAI 替代實作。

部署目標是 **Hugging Face Spaces（Docker SDK）**，README 的 frontmatter 指定 `sdk: docker`。

## 常用指令

### 本機開發

```powershell
# 建立虛擬環境（依專案規範一律用 uv，禁用 pip）
# Dockerfile 鎖在 python:3.12.10-slim，本機請對齊 3.12
uv venv --python 3.12
uv pip install -r requirements.txt

# 設定環境變數（見下方「環境變數」章節）
# 注意：程式碼只用 os.getenv()，沒有引入 python-dotenv，
# 因此 .env 檔不會被自動讀取，必須先手動 export / $env:。
$env:GEMINI_API_KEY = "..."
$env:LINE_CHANNEL_SECRET = "..."
$env:LINE_CHANNEL_ACCESS_TOKEN = "..."

# 用 Flask 開發伺服器直接跑某一支範例
uv run flask --app replybot run --port 7860
# 或用 gunicorn（與 Docker 部署一致）
uv run gunicorn -b 0.0.0.0:7860 replybot:app
```

`replybot` 可換成任一檔名（不含 `.py`）：`gemini`、`gpt4`、`multiturn`、`system_prompt`、`with_logs`、`with_search`、`example01`、`text2image`。

> macOS/Linux 等價的 env 設定：`export GEMINI_API_KEY=...`；若要從 `.env` 一次載入，可用 `set -a; source .env; set +a`。

### Docker

```powershell
docker build -t sculinebot .
docker run --rm -p 7860:7860 `
  -e GEMINI_API_KEY=$env:GEMINI_API_KEY `
  -e LINE_CHANNEL_SECRET=$env:LINE_CHANNEL_SECRET `
  -e LINE_CHANNEL_ACCESS_TOKEN=$env:LINE_CHANNEL_ACCESS_TOKEN `
  sculinebot
```

`Dockerfile` 目前的入口是 `shop:app`（手機商城旗艦版＝carousel.py 超集合，多了優惠專區與 Gemini 線上客服），若要 demo 其他範例，修改 `Dockerfile` 最後一行的 `CMD` 即可（例如改成 `carousel:app` 跑純電商版、`text2image:app` 跑文生圖、`replybot:app` 跑最基本的單次呼叫版本，或 `multiturn:app` 跑多輪對話版本）。`Dockerfile.old` 保留了舊版以 `gpt4:app` 為入口的設定（Python 3.12.2、沒有 healthcheck、也沒有切到非 root user），純粹作對照用，**不要直接拿來部署**。

## 架構與規範

### 各檔案的定位

所有檔案都是**同一個 Flask + LINE Webhook 樣板**的不同變體，POST `/` 接 LINE webhook、GET `/` 做 health check。差別在於 LLM 的呼叫方式：

- `replybot.py` — **唯一的「正典」**。其他檔案的環境變數命名都應該以這支為準（見下方）。Gemini 單次呼叫、無 chat session。
- `multiturn.py` — 改用 `client.chats.create(...)` 維持多輪對話。
- `system_prompt.py` — 在單次呼叫中加 `system_instruction`。
- `with_logs.py` — 加上 `logging.basicConfig` 的版本。
- `with_search.py` — 把 `GoogleSearch` 當 tool 傳入 chat。
- `gemini.py` / `example01.py` — 完整版：除文字外，多了 `ImageMessageContent`、`VideoMessageContent` handler、`MessagingApiBlob` 下載媒體、Gemini 圖片生成 (`AI ` 前綴觸發)，並透過 `SPACE_HOST` 組出靜態圖片回傳 URL。`example01.py` 使用 `gemini-2.5-pro-preview` 並要求文言文輸出。
- `gpt4.py` — 把 LLM 換成 OpenAI `responses` API + DALL·E 3，並用 `previous_response_id` 串多輪。是「同樣的 LINE 樣板、不同 LLM」的對照組。
- `text2image.py` — **純文生圖**版本。任何文字訊息直接當 prompt 餵給 Gemini `gemini-3.1-flash-image-preview`，把生成的 PNG 透過 `/images/<filename>` 路由回傳為 `ImageMessage`。比 `gemini.py` 簡潔（不混圖片解釋、影片解說、Google Search）；不靠 `AI ` 前綴觸發。
- `reminder.py` — **定時提醒**版本，示範主動發訊息（`push_message`）而非只回覆。用 `APScheduler` 的 `BackgroundScheduler`（記憶體保存、`Asia/Taipei`）排程；指令格式 `提醒 HH:MM 內容`，從 `event.source.user_id` 記住傳訊者，到點以 `PushMessageRequest` 推播。不需要 Gemini，只用 LINE 兩把金鑰。**部署時 `Dockerfile` 必須 `--workers 1`**（排程 job 存在 worker 記憶體，多 worker 會導致設定與觸發不在同一行程）。排程不持久化，Space 重啟/休眠喚醒後需重設，僅適合現場 demo。
- `carousel.py` — **手機商城 × Supabase × 熱賣輪播**版本，示範 `CarouselTemplate` 搭配雲端資料庫。傳關鍵字（`熱賣商品`／`熱賣`／`商品`…）時，從 Supabase `public.phones` 資料表（50 隻最新手機，含規格與真實照片）撈出 `is_hot=true` 的手機**隨機 5 隻**，組成可左右滑的商品卡（圖＋型號＋價格＋晶片／螢幕＋「加入購物車」「規格詳情」兩顆按鈕）；點按鈕送 `PostbackAction`，由 `PostbackEvent` handler 依卡片帶的 `id` 查整機規格回覆。重點：(1) carousel 是 bot 回覆的「訊息」（非底部選單）；(2) 卡片圖必須是**公開 HTTPS 直連網址**——用 `upload.wikimedia.org` 的真實手機照（LINE 不跟隨轉址，故不能用會 302 的佔位圖服務）；(3) bot 端只用 **publishable key**（`SUPABASE_PUBLISHABLE_KEY`）＋資料表的 **RLS 公開讀取政策**讀取，只讀不寫、金鑰可安全放 bot。Supabase client 採延遲建立，health check（GET `/`）不連資料庫也能通過。不需 Gemini，需 LINE 兩把金鑰＋`SUPABASE_URL`／`SUPABASE_PUBLISHABLE_KEY`。資料表 schema 與 50 筆種子資料是建置時一次性寫入（用 `SUPABASE_ACCESS_TOKEN` 這把 PAT 走 Management API，**bot 執行期完全不需要 PAT**）。**schema＋50 筆資料已匯出成 repo 根目錄的 `seed_phones.sql`**（含 `CREATE TABLE`、RLS 政策、`INSERT ... ON CONFLICT DO UPDATE`、`is_hot` 標記，冪等可重跑），讓資料來源進版控、可在任何 Supabase/Postgres 重建。商品資料本身住在 Supabase（非 repo），改資料不需動程式或重新部署。

  **完整迷你電商流程（per-user）**：示範「記得不同 LINE 使用者」。靠 `event.source.user_id` 區分人，串起 逛（熱賣商品）→ 加入購物車 → 我的購物車（卡片可「移除」「再加一個」）→ 結帳 → 我的訂單。文字指令：`熱賣商品`／`我的購物車`／`清空購物車`／`結帳`／`我的訂單`；底部 rich menu「我的訂單」(`menu=orders`) 也顯示訂單。資料表：`cart_items(user_id, phone_id, qty)`（購物車）、`orders(user_id, total, items jsonb)`（結帳後快照）。**雙金鑰雙用途是重點**：公開目錄 `phones` 用 **publishable key + RLS** 只讀；私有 `cart_items`／`orders` 用 **server 端 `service_role` 金鑰**（`SUPABASE_SERVICE_KEY`，繞過 RLS、只在後端、絕不外洩）讀寫，靠程式以 `user_id` 過濾隔離。三張表的 DDL 都在 `seed_phones.sql`。所有操作都有按鈕（rich menu、卡片 postback、**quick reply 快速回覆**結帳/清空/繼續逛），不必打字。

  **商品分類**：`phones` 表加了 `category` 欄（`手機`／`藍牙耳機`），目前 50 手機 + 10 藍牙耳機。底部「商品分類」(`menu=category`) → quick reply「📱手機／🎧藍牙耳機」→ 顯示該分類輪播（`action=cat&c=phone|earbuds`，`CATEGORY_MAP` 對應中文）。卡片副標與詳細頁 `/phone/<id>` 都**依 category 顯示不同規格**：手機看晶片/螢幕/相機；耳機看降噪/續航/驅動/藍牙/編解碼/防水（耳機規格存在 `specs` jsonb，手機專屬欄位留 NULL）。`category` 預設 `手機`，DDL 與資料都在 `seed_phones.sql`。

  **手機詳細展示頁**：商品卡的「詳細頁」是 `URIAction`，開 `https://{SPACE_HOST}/phone/<id>`，在 LINE 內建瀏覽器顯示一頁 HTML 商品頁（使用者留在 LINE）。資料即時查自 Supabase `phones`，但**頁面由本 bot（Flask 路由 `/phone/<id>`）提供，不是放 Supabase**——實測 Supabase 對自家 `*.supabase.co`（Storage 與 Edge Functions）一律回 `text/plain` + `x-content-type-options: nosniff` + `CSP: default-src 'none'; sandbox` 防釣魚，HTML 不會被瀏覽器渲染，所以無法在 Supabase 上 host 可渲染的網頁。`PUBLIC_HOST` 取自 `SPACE_HOST`（HF 自動注入），本機用預設主機名。
  > 踩雷紀錄：Management API `/api-keys` 會把**新版 `sb_secret_` 金鑰遮蔽**（第 15–40 位回傳 `·`/`0xb7`，非真值），拿去用會 `UnicodeEncodeError`。後端寫入請改用**完整回傳的 legacy `service_role` JWT**（`eyJ…`）；或像建置時改走 Management API（PAT）跑 SQL。

- `shop.py` — **手機商城旗艦版（線上入口，`Dockerfile` 指向這支）**。是 `carousel.py` 的**超集合**：原封沿用整套電商骨架（熱賣／分類／購物車／結帳／訂單／`/phone/<id>` 詳細頁、helper 函式），再把 rich menu 上原本還是 stub 的兩顆按鈕做成真功能：
  - **優惠專區（`menu=sale`／文字「優惠專區」等）**：撈 `phones.is_sale=true` 的特價品做輪播；`build_carousel` 對特價品的副標顯示「🎁特價 NT$X（原 NT$Y）」、詳細頁顯示刪除線原價＋「限時特價」標。特價資料以 `is_sale`／`original_price` 兩欄表示（DDL 與 7 筆示範特價都在 `seed_phones.sql`，冪等）。
  - **線上客服（`menu=support`／文字「客服」等）**：Gemini AI 客服。進入「客服模式」後（`SUPPORT_MODE` 記憶體 dict，**故 `--workers 1`**），自由文字→Gemini，`system_instruction` 限定「只回答本商城問題」、站外問題禮貌婉拒；context 注入「精簡型錄（每行 id｜品牌 型號｜分類｜售價｜關鍵規格）＋該顧客即時購物車/訂單」。回應走 `markdown`+`BeautifulSoup` 轉純文字。打到任何已知指令或點任何 rich menu 鍵會自動退出客服模式。**沒設 `GEMINI_API_KEY` 會友善降級、不會壞**。model 對齊 `gemini.py` 的 `gemini-3-flash-preview`。
  - rich menu 的按鈕鍵（hot/category/cart/orders/sale/support）已和這支對齊，切到 shop **毋需重做選單**。部署需在 LINE 兩把＋3 個 `SUPABASE_*` 之外，**多加 `GEMINI_API_KEY`**（線上客服用）。

### 環境變數命名規範（重要）

`replybot.py` 是正典，所有檔案的環境變數必須與它一致：

| 用途 | 環境變數名 | Python 變數名 |
|---|---|---|
| Gemini API 金鑰（LLM 範例＋`shop.py` 線上客服） | `GEMINI_API_KEY` | `GEMINI_API_KEY` |
| LINE Channel Secret | `LINE_CHANNEL_SECRET` | `line_channel_secret` |
| LINE Channel Access Token | `LINE_CHANNEL_ACCESS_TOKEN` | `line_channel_access_token` |
| OpenAI 金鑰（僅 `gpt4.py`） | `OPENAI_API_KEY` | `OPENAI_API_KEY` |
| Hugging Face Space 主機名（僅媒體版本） | `SPACE_HOST` | `base_url` |
| Supabase 專案 URL（手機商城 `carousel.py`／`shop.py`） | `SUPABASE_URL` | `SUPABASE_URL` |
| Supabase publishable key（手機商城 `carousel.py`／`shop.py`，讀公開 `phones`） | `SUPABASE_PUBLISHABLE_KEY` | `SUPABASE_PUBLISHABLE_KEY` |
| Supabase service_role 金鑰（手機商城 `carousel.py`／`shop.py`，**後端**讀寫私有 `cart_items`） | `SUPABASE_SERVICE_KEY` | `SUPABASE_SERVICE_KEY` |
| Supabase PAT（**僅建置／灌資料用**，bot 執行期不需要、勿放進 Space） | `SUPABASE_ACCESS_TOKEN` | （不在程式內，建置腳本用） |

Hugging Face Spaces 的 Secrets 介面也應該用以上名稱設定（`carousel.py` 需加 `SUPABASE_URL`／`SUPABASE_PUBLISHABLE_KEY`／`SUPABASE_SERVICE_KEY` 三個；**目前線上入口 `shop.py` 還要再加 `GEMINI_API_KEY`**——沒設線上客服會走友善降級；`service_role` 是後端機密金鑰、只放 Space 不外洩，**不要**把 `SUPABASE_ACCESS_TOKEN` PAT 放上去）。**新增範例檔時請延用同一組命名**，不要再引入 `GOOGLE_API_KEY` / `YOUR_CHANNEL_SECRET` / `YOUR_CHANNEL_ACCESS_TOKEN` 等舊名（這些已在 2026 年初統一掉了）。

### LINE SDK 版本

統一使用 **`linebot.v3`** 系列 API（`WebhookHandler`、`ApiClient`、`MessagingApi`、`MessagingApiBlob`、`ReplyMessageRequest`、`TextMessage`、`ImageMessage`、`MessageEvent`、`TextMessageContent`、`ImageMessageContent`、`VideoMessageContent`）。請勿混用舊版 `linebot`（v2）。

### Markdown → 純文字

Gemini／GPT 回應可能含 Markdown，但 LINE 不渲染 Markdown，因此所有範例的固定流程是：

```python
html = markdown.markdown(response_text)
text = BeautifulSoup(html, "html.parser").get_text()
```

新增 LLM 範例時請維持這個 pipeline。

### 圖片／影片處理約定（`gemini.py`、`example01.py`、`gpt4.py`）

- 透過 `MessagingApiBlob.get_message_content(message_id=...)` 下載原始 bytes。
- 暫存到 `tempfile.gettempdir()`，並用 `@app.route("/images/<filename>")` 提供回傳給 LINE 的公開 URL。
- 對外 URL 是 `https://{SPACE_HOST}/images/{filename}`——`SPACE_HOST` 是 Hugging Face Spaces 自動注入的環境變數，本機開發需要自己模擬或用 ngrok 等 tunneling 工具。
- `gpt4.py` 處理圖片時改用 base64 data URI 而非 URL（OpenAI vision input 的格式要求）。
- 文字訊息以 `AI ` 開頭代表「生成圖片」的命令，prompt 是去掉前綴的剩餘字串。

### Docker / 部署

`Dockerfile` 的 `CMD` 寫死了入口模組（目前是 `shop:app`，會隨課程進度切換）。若要切換要 demo 的範例：

1. 改 `Dockerfile` 最後一行的模組名。
2. Hugging Face Spaces 會自動 rebuild。

容器內部固定監聽 `0.0.0.0:7860`，這也是 HF Spaces 預期的 port。Healthcheck 打 `http://0.0.0.0:7860/`，所以新範例必須保留 GET `/` 的 health endpoint。

## 測試與 Lint 狀態

此 repo **不附測試也沒設定 lint**：沒有 `test_*.py`、`pytest.ini`、`pyproject.toml`、`ruff.toml`、`.flake8` 等任何相關檔案。不要試圖跑 `pytest` 或 `ruff` 並把結果視為「驗證」——對這個 repo 而言，「能跑起來」就是用 `uv run gunicorn -b 0.0.0.0:7860 <module>:app` 啟動後 `curl http://localhost:7860/` 拿到 `{"message": "Line Webhook Server"}`。

## 開發注意事項

- 修改任一範例時，**保持與 `replybot.py` 的變數命名一致**，這是這個 repo 的核心慣例。
- 加新範例時，沿用 `<檔名>:app` 可被 gunicorn 直接 serve 的結構（檔案頂層要有 `app = Flask(__name__)`）。
- `requirements.txt` 與 `test_requirements.txt` 內容幾乎相同，差別在於 `test_requirements.txt` 沒有註解、且少了 `Pillow`。**這名字會誤導——它不是測試框架依賴**，只是另一份精簡版的 runtime 依賴清單。新套件記得兩邊都加。
- 課程性質的 repo，**不要過度抽象**——把每個範例獨立、可單檔閱讀的特性保留下來，不要把共用程式抽成 module 而毀掉教學的可讀性。
