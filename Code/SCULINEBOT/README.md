---
title: SCU LINEBot 2026
emoji: 🐢
colorFrom: yellow
colorTo: green
sdk: docker
pinned: false
---

# 東吳大學資料科學系 2026 LINE Bot 進階課程範例集

> 部署於 Hugging Face Spaces（Docker SDK）：<https://huggingface.co/spaces/joshhu/SCULINEBOT>

這個 repo 是 **2026 年上半年東吳大學資料科學系「LINE Bot 進階」課程**的教學範例集。
它**不是單一應用**，而是**多支獨立、可單獨執行的 LINE Bot 範例檔**，對應課程的不同進度——
從最簡單的單輪對話，逐步加上 system prompt、logging、多輪對話、Google Search、圖片／影片處理、
OpenAI 替代實作，一路到完整的 **Supabase 雲端資料庫手機商城**。

每支範例都是同一個 **Flask + LINE v3 Webhook 樣板**的變體：`POST /` 接 webhook、`GET /` 做 health check，
差別在 LLM 的呼叫方式或功能。

---

## 🛒 旗艦範例：`shop.py` —— 手機商城 × Supabase × Gemini 客服

目前 `Dockerfile` 的入口（線上跑的就是這支）。`shop.py` 是 `carousel.py` 的**超集合**：
沿用整套電商骨架，再把 rich menu 上原本還是 stub 的兩顆按鈕做成真功能——**🎁 優惠專區**與 **💬 線上客服**。
（`carousel.py` 保留為教學的前一步，純電商、不含客服。）

示範一條**完整的迷你電商流程，全部用按鈕操作**：

```
逛（熱賣商品 / 商品分類 / 優惠專區）→ 加入購物車 → 我的購物車（移除 / 再加一個）→ 結帳 → 我的訂單
隨時可問 💬 線上客服（Gemini，只答商城問題）
```

| 功能 | 說明 |
|---|---|
| **雲端商品目錄** | 商品資料放 Supabase（Postgres）`phones` 表，共 **60 筆**：50 支手機 + 10 款藍牙耳機，以 `category` 欄區分。含規格、台幣價、Wikimedia 真實照片。 |
| **熱賣商品** | 從 `is_hot=true` 隨機抽 5 件組 `CarouselTemplate`。 |
| **商品分類** | 底部選單「商品分類」→ quick reply「📱手機 / 🎧藍牙耳機」→ 該分類輪播。卡片副標與詳細頁**依分類顯示不同規格**。 |
| **🎁 優惠專區** | 底部選單「優惠專區」(`menu=sale`) → 撈 `is_sale=true` 特價品輪播，卡片與詳細頁顯示「特價 → ~~原價~~」。 |
| **💬 線上客服** | 底部選單「線上客服」(`menu=support`) → 進入 Gemini 客服模式：**只回答本商城問題**（商品/規格/價格/購物車/訂單/運送/付款/優惠），站外問題禮貌婉拒。context 注入精簡型錄 + 該顧客的即時購物車/訂單。沒設 `GEMINI_API_KEY` 時友善降級、不會壞。|
| **個人購物車** | 靠 `event.source.user_id` 記住「每位 LINE 使用者各自的購物車」（`cart_items` 表），可加入 / 移除 / 調整數量 / 結帳。 |
| **結帳與訂單** | 結帳把購物車做成 `orders` 一筆（快照 + 總價）並清空，「我的訂單」查歷史。 |
| **手機詳細頁** | 卡片「詳細頁」是 `URIAction`，在 **LINE 內建瀏覽器**開一頁 HTML 商品頁（`/phone/<id>`，資料即時查 Supabase）。 |
| **全按鈕操作** | rich menu、卡片 postback、quick reply 快速回覆——示範時不必打字。 |

### 雙金鑰、雙用途（重要教學點）

| 對象 | 金鑰 | 用途 |
|---|---|---|
| `phones`（公開商品目錄） | **publishable key** + 資料表 RLS 公開讀取政策 | 只讀，金鑰可安全放 bot |
| `cart_items` / `orders`（私有，跟人綁） | **server 端 service_role 金鑰** | 後端讀寫、繞過 RLS、絕不外洩；靠程式以 `user_id` 隔離 |

> ⚠️ 注意：Supabase 對自家 `*.supabase.co`（Storage 與 Edge Functions）一律回 `text/plain` + CSP `sandbox` 防釣魚，
> **無法在 Supabase 上 host 會渲染的 HTML 網頁**，所以詳細頁由本 bot 提供、資料才查自 Supabase。

---

## 📂 其他範例檔

所有檔案都是同一個 LINE Webhook 樣板的變體，可用 `gunicorn -b 0.0.0.0:7860 <檔名>:app` 單獨啟動：

| 檔案 | 重點 |
|---|---|
| `replybot.py` | **正典**：Gemini 單次呼叫，無 chat session。所有檔案的環境變數命名以它為準。 |
| `multiturn.py` | 改用 `client.chats.create(...)` 維持多輪對話。 |
| `system_prompt.py` | 單次呼叫中加 `system_instruction`。 |
| `with_logs.py` | 加上 `logging.basicConfig`。 |
| `with_search.py` | 把 `GoogleSearch` 當 tool 傳入 chat。 |
| `gemini.py` / `example01.py` | 完整版：文字 + 圖片 / 影片 handler、媒體下載、Gemini 圖片生成（`AI ` 前綴觸發）。 |
| `gpt4.py` | LLM 換成 OpenAI `responses` API + DALL·E 3，`previous_response_id` 串多輪。 |
| `text2image.py` | 純文生圖：文字直接當 prompt 餵給 Gemini，回傳生成 PNG。 |
| `reminder.py` | 定時提醒：`APScheduler` + `push_message` 主動推播（指令 `提醒 HH:MM 內容`）。 |
| `carousel.py` | **手機商城**純電商版（`shop.py` 的前一步，不含優惠專區/客服）。 |
| `shop.py` | **手機商城旗艦版**（線上入口）：carousel.py + 🎁優惠專區 + 💬 Gemini 線上客服。 |
| `richmenu/` | 單張不切換頁籤的 Rich Menu 圖片產生器與設定腳本（鍵：hot/category/cart/orders/sale/support）。 |
| `seed_phones.sql` | 手機商城的 **schema + 60 筆種子資料**（含 `cart_items` / `orders` DDL），冪等可重跑，能在任何 Supabase/Postgres 重建。 |

---

## ⚙️ 環境變數

```bash
# LINE（所有範例）
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...

# Gemini（LLM 範例；shop.py 的線上客服也用這把）
GEMINI_API_KEY=...

# OpenAI（僅 gpt4.py）
OPENAI_API_KEY=...

# Supabase（僅手機商城 carousel.py）
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...   # 讀公開 phones
SUPABASE_SERVICE_KEY=eyJ...                   # 後端讀寫私有 cart_items/orders（legacy service_role JWT）
# SUPABASE_ACCESS_TOKEN（PAT）僅建置/灌資料用，bot 執行期不需要，勿放進 Space
```

> 程式只用 `os.getenv()`，**不會自動讀 `.env`**。本機請先手動載入：
> `set -a; source .env; set +a`（macOS/Linux）。

---

## 🚀 本機開發

```bash
# 依專案規範一律用 uv（禁用 pip）；對齊 Python 3.12
uv venv --python 3.12
uv pip install -r requirements.txt

set -a; source .env; set +a

# 用 gunicorn 跑某一支（與 Docker 部署一致；--workers 1 因 shop.py 客服模式狀態存記憶體）
uv run gunicorn -b 0.0.0.0:7860 --timeout 120 --workers 1 shop:app
# 健康檢查
curl http://localhost:7860/      # → {"message": "Line Webhook Server"}
```

`shop` 可換成任一檔名（不含 `.py`）。

## 🐳 Docker / Hugging Face Spaces

```bash
docker build -t sculinebot .
docker run --rm -p 7860:7860 --env-file .env sculinebot
```

`Dockerfile` 的 `CMD` 寫死入口模組（目前 `shop:app`，會隨課程進度切換）。
容器固定監聽 `0.0.0.0:7860`（HF Spaces 預期的 port），新範例請保留 `GET /` health endpoint。
部署到 HF Spaces 時，於 Space 的 Secrets 介面填入上方環境變數（`shop.py` 需 LINE 2 把 + 3 個 `SUPABASE_*` + `GEMINI_API_KEY`(線上客服)，**勿放 PAT**）。

---

## 🗄️ 重建資料庫

在任何 Supabase / Postgres 執行 `seed_phones.sql` 即可重建商品目錄與購物車/訂單表（冪等）：

- Supabase Dashboard → SQL Editor 貼上整份執行
- `psql "$DATABASE_URL" -f seed_phones.sql`

---

## 📝 慣例

- 統一使用 **`linebot.v3`** API（勿混用舊版 `linebot` v2）。
- 新增範例請延用 `replybot.py` 的環境變數命名；沿用 `<檔名>:app` 可被 gunicorn 直接 serve 的結構。
- LLM 回應的 Markdown 一律經 `markdown` + `BeautifulSoup` 轉純文字（LINE 不渲染 Markdown）。
- 課程性質的 repo，保留每支範例「獨立、可單檔閱讀」的特性，**不要過度抽象**。

更多細節見 [`CLAUDE.md`](./CLAUDE.md)。
