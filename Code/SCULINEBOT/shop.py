"""
東吳大學資料系 2026 LINEBOT —— 手機商城旗艦版（carousel.py 的超集合）

在 carousel.py 的完整電商骨架（熱賣／分類／購物車／結帳／訂單／詳細頁）之上，
把原本 rich menu 上還是 stub 的兩顆按鈕做成真功能：

  - 優惠專區（menu=sale）：撈 phones.is_sale=true 的特價品做輪播，
    卡片副標顯示「特價 NT$X（原 NT$Y）」，原價/特價一眼可見。
  - 線上客服（menu=support）：Gemini AI 客服。進入客服模式後，自由打字 → Gemini，
    system_instruction 限定「只回答本商城的問題」，並把『精簡型錄 + 這位顧客的購物車/訂單』
    注入 context，讓它能依實際商品與這個人的狀態回答。沒設 GEMINI_API_KEY 時友善降級、不會壞。

其餘行為與 carousel.py 完全一致（同樣三張表、兩種金鑰、全按鈕操作）。
rich menu 的按鈕鍵（hot/category/cart/orders/sale/support）已和這支對齊，毋需重做選單。

需要的環境變數：
  LINE_CHANNEL_SECRET / LINE_CHANNEL_ACCESS_TOKEN /
  SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY / SUPABASE_SERVICE_KEY /
  GEMINI_API_KEY（線上客服用；沒設則客服降級）
"""

import os
import random
from urllib.parse import parse_qs

import markdown
from bs4 import BeautifulSoup
from flask import Flask, abort, request
from supabase import create_client

from google import genai
from google.genai import types

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    TemplateMessage,
    CarouselTemplate,
    CarouselColumn,
    PostbackAction,
    URIAction,
    QuickReply,
    QuickReplyItem,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent


# Initialize Flask app
app = Flask(__name__)
line_channel_secret = os.getenv("LINE_CHANNEL_SECRET")
line_channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
configuration = Configuration(access_token=line_channel_access_token)
handler = WebhookHandler(line_channel_secret)

# Supabase 連線資訊
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY")  # 讀 phones（公開）
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")          # 讀寫 cart_items/orders（機密）

# Gemini（線上客服用）。延遲建立 client；沒設金鑰時 get_gemini() 回 None，客服走友善降級。
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3-flash-preview"  # 對齊 gemini.py 現行可用的文字模型
_gemini = None

# 手機詳細頁的對外主機名。HF Spaces 會自動注入 SPACE_HOST；本機/其他環境用預設值。
# 註：詳細頁由本 bot 提供（/phone/<id>），不是放 Supabase——因為 Supabase 對自家
# *.supabase.co（Storage 與 Edge Functions）一律回 text/plain + CSP sandbox 防釣魚，
# HTML 不會被瀏覽器渲染。頁面資料仍即時查自 Supabase 的 phones 表。
PUBLIC_HOST = os.getenv("SPACE_HOST") or "joshhu-sculinebot.hf.space"

# 觸發關鍵字（文字指令，仍可用；示範用按鈕即可）
TRIGGERS = {"熱賣商品", "熱賣", "熱門", "熱門手機", "商品", "購物"}
CART_VIEW_TRIGGERS = {"我的購物車", "購物車", "查看購物車", "看購物車"}
CART_CLEAR_TRIGGERS = {"清空購物車", "清空"}
CHECKOUT_TRIGGERS = {"結帳", "我要結帳", "下單", "結賬"}
ORDERS_VIEW_TRIGGERS = {"我的訂單", "訂單", "查訂單"}
CATEGORY_PICKER_TRIGGERS = {"商品分類", "分類", "逛商品"}
SALE_TRIGGERS = {"優惠專區", "優惠", "特價", "折扣", "優惠商品"}
SUPPORT_TRIGGERS = {"線上客服", "客服", "聯絡客服", "我要問問題"}
SUPPORT_END_TRIGGERS = {"結束客服", "退出客服", "結束", "離開"}
# 直接輸入分類名 → 顯示該分類（值為 DB 的 category）
CATEGORY_NAME_TRIGGERS = {"手機": "手機", "藍牙耳機": "藍牙耳機", "耳機": "藍牙耳機"}
HOT_COUNT = 5  # 一次輪播幾隻手機（LINE carousel 最多 10）

# 已知文字指令（在客服模式中打到這些字 → 自動退出客服、改走正常處理）
ALL_COMMANDS = (
    TRIGGERS | CART_VIEW_TRIGGERS | CART_CLEAR_TRIGGERS | CHECKOUT_TRIGGERS
    | ORDERS_VIEW_TRIGGERS | CATEGORY_PICKER_TRIGGERS | SALE_TRIGGERS
    | SUPPORT_TRIGGERS | set(CATEGORY_NAME_TRIGGERS)
)

# 線上客服「模式」狀態：{user_id: True}。存記憶體 → 故 Dockerfile 必須 --workers 1。
# （沿用 reminder.py 的記憶體狀態做法；Space 重啟/休眠會清空，demo 用無虞。）
SUPPORT_MODE = {}

# 兩個 Supabase client 都延遲建立：health check（GET /）不需連資料庫也能通過。
_supabase = None        # publishable key：讀公開的 phones
_supabase_admin = None  # service_role：讀寫私有的 cart_items / orders（繞過 RLS）


def get_supabase():
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)
    return _supabase


def get_supabase_admin():
    global _supabase_admin
    if _supabase_admin is None:
        _supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _supabase_admin


def get_gemini():
    """延遲建立 Gemini client；沒設 GEMINI_API_KEY 時回 None（客服降級用）。"""
    global _gemini
    if _gemini is None and GEMINI_API_KEY:
        _gemini = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini


# ---- phones（公開商品目錄）-------------------------------------------------

# 商品分類：rich menu/quick reply 用英文 code（避免 postback 中文編碼問題），對到 DB 的 category 值
CATEGORY_MAP = {"phone": "手機", "earbuds": "藍牙耳機"}


def fetch_hot_phones(n=HOT_COUNT):
    db = get_supabase()
    rows = db.table("phones").select("*").eq("is_hot", True).execute().data
    if len(rows) < n:
        rows = db.table("phones").select("*").execute().data
    return random.sample(rows, min(n, len(rows)))


def fetch_by_category(category, n=10):
    """撈某分類的商品，隨機最多 n 筆（carousel 上限 10）。"""
    rows = get_supabase().table("phones").select("*").eq("category", category).execute().data
    return random.sample(rows, min(n, len(rows)))


def fetch_sale(n=10):
    """撈特價商品（is_sale=true），隨機最多 n 筆。優惠專區（menu=sale）用。"""
    rows = get_supabase().table("phones").select("*").eq("is_sale", True).execute().data
    return random.sample(rows, min(n, len(rows))) if rows else []


def get_phone(pid):
    """依 id 撈單一手機。pid 非純數字時回 None（避免 bigint 22P02 把 webhook 弄崩）。"""
    if not str(pid).isdigit():
        return None
    rows = get_supabase().table("phones").select("*").eq("id", int(pid)).limit(1).execute().data
    return rows[0] if rows else None


# ---- cart_items / orders（私有，跟人綁）------------------------------------

def get_user_id(event):
    return getattr(event.source, "user_id", None)


def add_to_cart(user_id, phone_id):
    db = get_supabase_admin()
    existing = (
        db.table("cart_items").select("qty")
        .eq("user_id", user_id).eq("phone_id", phone_id).limit(1).execute().data
    )
    if existing:
        qty = existing[0]["qty"] + 1
        db.table("cart_items").update({"qty": qty}).eq("user_id", user_id).eq("phone_id", phone_id).execute()
    else:
        qty = 1
        db.table("cart_items").insert({"user_id": user_id, "phone_id": phone_id, "qty": 1}).execute()
    return qty


def remove_from_cart(user_id, phone_id):
    get_supabase_admin().table("cart_items").delete().eq("user_id", user_id).eq("phone_id", phone_id).execute()


def get_cart(user_id):
    return (
        get_supabase_admin().table("cart_items")
        .select("phone_id, qty, phones(name, price, img_url)")
        .eq("user_id", user_id).order("created_at").execute().data
    )


def clear_cart(user_id):
    get_supabase_admin().table("cart_items").delete().eq("user_id", user_id).execute()


def cart_total(items):
    return sum((it.get("phones") or {}).get("price", 0) * it["qty"] for it in items)


def checkout(user_id):
    """購物車做成一筆訂單、清空購物車。回傳 (order_id, total)；空車回 None。"""
    items = get_cart(user_id)
    if not items:
        return None
    snapshot = [
        {
            "phone_id": it["phone_id"],
            "name": (it.get("phones") or {}).get("name"),
            "price": (it.get("phones") or {}).get("price"),
            "qty": it["qty"],
        }
        for it in items
    ]
    total = sum((s["price"] or 0) * s["qty"] for s in snapshot)
    res = get_supabase_admin().table("orders").insert(
        {"user_id": user_id, "total": total, "items": snapshot}
    ).execute()
    clear_cart(user_id)
    return res.data[0]["id"], total


def get_orders(user_id, limit=5):
    return (
        get_supabase_admin().table("orders")
        .select("id, total, items, created_at")
        .eq("user_id", user_id).order("id", desc=True).limit(limit).execute().data
    )


# ---- 訊息組裝 --------------------------------------------------------------

def _clip(s, limit):
    s = s or ""
    return s if len(s) <= limit else s[: limit - 1] + "…"


def quick(*items):
    """組 quick reply（浮在鍵盤上方的可點按鈕）。items: (label, postback_data)。"""
    return QuickReply(items=[
        QuickReplyItem(action=PostbackAction(label=l, data=d, display_text=l))
        for (l, d) in items
    ])


# 各情境的快速回覆按鈕組
QR_AFTER_ADD = lambda: quick(("🛒 我的購物車", "menu=cart"), ("💳 結帳", "action=checkout"), ("🔥 繼續逛", "menu=hot"))
QR_AFTER_REMOVE = lambda: quick(("🛒 我的購物車", "menu=cart"), ("🔥 繼續逛", "menu=hot"))
QR_IN_CART = lambda: quick(("💳 結帳", "action=checkout"), ("🗑️ 清空購物車", "action=clearcart"), ("🔥 繼續逛", "menu=hot"))
QR_AFTER_CHECKOUT = lambda: quick(("📦 我的訂單", "menu=orders"), ("🔥 繼續逛", "menu=hot"))
QR_EMPTY = lambda: quick(("🔥 看熱賣商品", "menu=hot"), ("🎁 優惠專區", "menu=sale"))
QR_IN_ORDERS = lambda: quick(("🛒 我的購物車", "menu=cart"), ("🔥 繼續逛", "menu=hot"))
QR_SUPPORT = lambda: quick(("✅ 結束客服", "action=support_end"), ("🔥 熱賣商品", "menu=hot"), ("🛒 我的購物車", "menu=cart"))


def build_carousel(phones):
    """商品輪播（每張卡：加入購物車／詳細頁）。卡片副標依分類顯示重點規格；特價品顯示原價/特價。"""
    columns = []
    for p in phones:
        specs = p.get("specs") or {}
        if p.get("category") == "藍牙耳機":
            sub = "｜".join(x for x in [specs.get("anc"), specs.get("battery")] if x)
        else:
            sub = "｜".join(x for x in [p.get("chip"), p.get("display")] if x)
        if p.get("is_sale") and p.get("original_price"):
            price_str = f"🎁特價 NT${p['price']:,}（原 NT${p['original_price']:,}）"
        else:
            price_str = f"NT${p['price']:,}"
        detail_url = f"https://{PUBLIC_HOST}/phone/{p['id']}"  # 在 LINE 內建瀏覽器開的詳細頁
        columns.append(
            CarouselColumn(
                thumbnail_image_url=p["img_url"],
                title=_clip(p["name"], 40),
                text=_clip(f"{price_str}｜{sub}", 60),
                default_action=URIAction(label="詳細頁", uri=detail_url),  # 點圖開詳細頁
                actions=[
                    PostbackAction(label="加入購物車", data=f"action=cart&id={p['id']}",
                                   display_text=f"把「{p['name']}」加入購物車"),
                    URIAction(label="詳細頁", uri=detail_url),
                ],
            )
        )
    return TemplateMessage(
        alt_text="🛍 商品輪播（請在手機上查看）",
        template=CarouselTemplate(columns=columns, image_aspect_ratio="rectangle", image_size="contain"),
    )


def build_cart_carousel(items):
    """購物車輪播（每張卡：移除／再加一個）。LINE carousel 最多 10 張。"""
    columns = []
    for it in items[:10]:
        ph = it.get("phones") or {}
        pid = it["phone_id"]
        qty = it["qty"]
        subtotal = (ph.get("price") or 0) * qty
        columns.append(
            CarouselColumn(
                thumbnail_image_url=ph.get("img_url"),
                title=_clip(ph.get("name", "商品"), 40),
                text=_clip(f"數量 ×{qty}　小計 NT${subtotal:,}", 60),
                actions=[
                    PostbackAction(label="移除", data=f"action=remove&id={pid}",
                                   display_text=f"從購物車移除「{ph.get('name', '')}」"),
                    PostbackAction(label="再加一個", data=f"action=cart&id={pid}",
                                   display_text=f"再加一個「{ph.get('name', '')}」"),
                ],
            )
        )
    return TemplateMessage(
        alt_text="🛒 你的購物車（請在手機上查看）",
        template=CarouselTemplate(columns=columns, image_aspect_ratio="rectangle", image_size="contain"),
    )


# ---- 各「意圖」回傳要回的訊息（文字指令與按鈕共用，確保行為一致）-----------

def msg_hot():
    phones = fetch_hot_phones()
    if not phones:
        return TextMessage(text="目前沒有熱賣商品資料 😅")
    return build_carousel(phones)


def msg_sale():
    """優惠專區：特價商品輪播。沒有特價品時友善提示。"""
    products = fetch_sale()
    if not products:
        return TextMessage(text="目前沒有特價商品，先逛逛熱賣商品吧 🙌", quick_reply=QR_EMPTY())
    note = TextMessage(text="🎁 優惠專區｜以下為限時特價（原價 → 特價）👇")
    return [note, build_carousel(products)]


def msg_category_picker():
    """商品分類入口：請使用者選「手機 / 藍牙耳機」（用 quick reply 按鈕）。"""
    return TextMessage(
        text="想逛哪個分類？👇",
        quick_reply=quick(
            ("📱 手機", "action=cat&c=phone"),
            ("🎧 藍牙耳機", "action=cat&c=earbuds"),
            ("🔥 熱賣商品", "menu=hot"),
        ),
    )


def msg_category(code):
    """顯示某分類（code: phone/earbuds，或直接給中文分類名）的商品輪播。"""
    cat = CATEGORY_MAP.get(code, code)
    products = fetch_by_category(cat)
    if not products:
        return TextMessage(text=f"「{cat}」目前沒有商品 😅")
    return build_carousel(products)


def msg_cart(user_id):
    items = get_cart(user_id)
    if not items:
        return TextMessage(text="🛒 你的購物車是空的\n點下方按鈕去逛逛吧！", quick_reply=QR_EMPTY())
    note = f"🛒 合計：NT${cart_total(items):,}\n用下方按鈕結帳或清空 👇"
    return [build_cart_carousel(items), TextMessage(text=note, quick_reply=QR_IN_CART())]


def msg_clear(user_id):
    if user_id:
        clear_cart(user_id)
    return TextMessage(text="🗑️ 已清空購物車", quick_reply=QR_EMPTY())


def msg_checkout(user_id):
    result = checkout(user_id)
    if not result:
        return TextMessage(text="🛒 購物車是空的，先去逛逛吧！", quick_reply=QR_EMPTY())
    oid, total = result
    return TextMessage(
        text=f"✅ 訂單成立！\n訂單編號 #{oid}\n合計：NT${total:,}",
        quick_reply=QR_AFTER_CHECKOUT(),
    )


def msg_orders(user_id):
    orders = get_orders(user_id)
    if not orders:
        return TextMessage(text="📦 你還沒有訂單\n加入購物車後按「結帳」就會成立訂單。", quick_reply=QR_EMPTY())
    lines = ["📦 你的訂單（最近 5 筆）："]
    for o in orders:
        items = o.get("items") or []
        names = "、".join(f"{i['name']}×{i['qty']}" for i in items)
        date = (o.get("created_at") or "")[:10]
        lines.append(f"#{o['id']}　NT${o['total']:,}　{date}")
        lines.append(f"　{_clip(names, 60)}")
    return TextMessage(text="\n".join(lines), quick_reply=QR_IN_ORDERS())


# ---- 線上客服（Gemini）-----------------------------------------------------

SUPPORT_SYSTEM = (
    "你是「SCU 手機商城」的線上客服小幫手，只用繁體中文（台灣用語）回答，語氣親切、回答簡短口語。"
    "你只回答和本商城有關的問題：商品介紹、規格、價格、比較、推薦、購物車、訂單、運送、付款、優惠/特價。"
    "若顧客的問題和本商城無關（例如天氣、寫程式、時事、閒聊），請禮貌婉拒並引導回購物，"
    "例如：『這我幫不上忙耶 😅 我只負責商城的問題，要不要看看熱賣商品或優惠專區？』，不要嘗試回答無關問題。"
    "回答時可引用下方『商品型錄』的真實商品與價格，以及『這位顧客的狀態』中的購物車/訂單來個人化回覆。"
    "不要編造型錄裡沒有的商品或價格。"
)


def msg_support_intro():
    return TextMessage(
        text=(
            "🤖 我是「SCU 手機商城」客服小幫手！\n"
            "商品、規格、價格、比較、推薦、購物車、訂單、運送、付款、優惠都可以問我～\n"
            "（隨時點下方「結束客服」離開）"
        ),
        quick_reply=QR_SUPPORT(),
    )


def _md_to_text(s):
    """Gemini 回應可能含 Markdown，LINE 不渲染 → 轉純文字（沿用專案慣例）。"""
    return BeautifulSoup(markdown.markdown(s or ""), "html.parser").get_text().strip()


def _catalog_context():
    """精簡型錄：每行 id｜品牌 型號｜分類｜售價(特價標注)｜關鍵規格。注入給客服 Gemini。"""
    rows = (
        get_supabase().table("phones")
        .select("id,brand,model,category,price,original_price,is_sale,chip,display,specs")
        .execute().data
    )
    lines = []
    for p in rows:
        specs = p.get("specs") or {}
        if p.get("category") == "藍牙耳機":
            key = "｜".join(x for x in [specs.get("anc"), specs.get("battery")] if x)
        else:
            key = "｜".join(x for x in [p.get("chip"), p.get("display")] if x)
        sale = f"（特價，原 NT${p['original_price']:,}）" if p.get("is_sale") and p.get("original_price") else ""
        lines.append(f"{p['id']}｜{p['brand']} {p['model']}｜{p['category']}｜NT${p['price']:,}{sale}｜{key}")
    return "\n".join(lines)


def _user_context(uid):
    """這位顧客的即時購物車與最近訂單（客服個人化用）。"""
    parts = []
    cart = get_cart(uid)
    if cart:
        c = "、".join(f"{(it.get('phones') or {}).get('name')}×{it['qty']}" for it in cart)
        parts.append(f"購物車：{c}（合計 NT${cart_total(cart):,}）")
    else:
        parts.append("購物車：空")
    orders = get_orders(uid, limit=3)
    if orders:
        o = "；".join(f"#{od['id']} NT${od['total']:,}" for od in orders)
        parts.append(f"最近訂單：{o}")
    else:
        parts.append("最近訂單：無")
    return "\n".join(parts)


def support_answer(uid, text):
    """客服模式中的自由文字 → Gemini 回答。沒金鑰/出錯時友善降級。"""
    client = get_gemini()
    if client is None:
        return TextMessage(
            text="客服小幫手暫時休息中（尚未設定 Gemini 金鑰）🙏\n你可以直接用下方選單逛商品、看購物車或優惠。",
            quick_reply=QR_SUPPORT(),
        )
    try:
        system = (
            SUPPORT_SYSTEM
            + "\n\n【商品型錄】\n" + _catalog_context()
            + "\n\n【這位顧客的狀態】\n" + _user_context(uid)
        )
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_modalities=["TEXT"],
            ),
            contents=text,
        )
        answer = _md_to_text(resp.text)
    except Exception as e:
        app.logger.error(f"客服 Gemini 例外：{e}")
        answer = "抱歉，客服暫時無法回覆，請稍後再試，或直接用下方選單操作 🙏"
    return TextMessage(text=answer or "（我沒有想到答案，換個問法試試？）", quick_reply=QR_SUPPORT())


def reply(reply_token, messages):
    if not isinstance(messages, list):
        messages = [messages]
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=messages)
        )


# ---- 手機詳細展示頁（HTML，給 LINE 內建瀏覽器開）---------------------------

def _esc(s):
    s = "—" if s is None else str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


_PAGE_CSS = (
    ":root{--brand:#e60012;--ink:#1a1a1a;--sub:#6b7280;--line:#eee;--bg:#f5f6f8}"
    "*{box-sizing:border-box;margin:0;padding:0}"
    "body{font-family:-apple-system,'PingFang TC','Microsoft JhengHei',sans-serif;background:var(--bg);color:var(--ink);line-height:1.5}"
    ".wrap{max-width:520px;margin:0 auto;background:#fff;min-height:100vh}"
    ".hero{text-align:center;padding:28px 20px 8px}"
    ".hero img{max-width:78%;height:260px;object-fit:contain}"
    ".body{padding:4px 22px 40px}"
    ".brand{display:inline-block;font-size:12px;font-weight:700;color:var(--brand);border:1px solid var(--brand);border-radius:999px;padding:2px 10px;margin-bottom:8px}"
    "h1{font-size:23px;font-weight:800;margin:2px 0 6px}"
    ".price{font-size:30px;font-weight:900;color:var(--brand);margin:6px 0 2px}"
    ".price small{font-size:14px;color:var(--sub);font-weight:600;margin-left:4px}"
    ".was{font-size:15px;color:var(--sub);text-decoration:line-through;margin-left:8px;font-weight:600}"
    ".hot{display:inline-block;background:#fff3f3;color:var(--brand);font-size:12px;font-weight:700;border-radius:6px;padding:3px 8px;margin-top:6px}"
    ".sale{display:inline-block;background:#fff7e6;color:#b45309;font-size:12px;font-weight:700;border-radius:6px;padding:3px 8px;margin-top:6px;margin-left:6px}"
    "table{width:100%;border-collapse:collapse;margin-top:18px}"
    "th,td{text-align:left;padding:12px 4px;border-bottom:1px solid var(--line);font-size:15px;vertical-align:top}"
    "th{color:var(--sub);font-weight:600;width:34%;white-space:nowrap}td{font-weight:600}"
    ".foot{padding:18px 22px 36px;color:var(--sub);font-size:13px;text-align:center}"
    ".tag{color:var(--sub);font-size:13px;margin-top:16px}"
)


def _page(title, inner):
    return (
        '<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{_esc(title)}</title><style>{_PAGE_CSS}</style></head>"
        f'<body><div class="wrap">{inner}</div></body></html>'
    )


def render_phone_page(p):
    """商品詳細頁 HTML。資料 p 來自 Supabase phones 表（get_phone）。依分類顯示不同規格列。"""
    if not p:
        return _page("找不到", '<div class="body" style="padding:40px 22px"><h1>找不到這項商品 😅</h1></div>')

    def row(label, val):
        return f"<tr><th>{_esc(label)}</th><td>{_esc(val)}</td></tr>"

    specs = p.get("specs") or {}
    if p.get("category") == "藍牙耳機":
        rows_html = (
            row("降噪", specs.get("anc")) + row("續航", specs.get("battery"))
            + row("驅動單體", specs.get("driver")) + row("藍牙版本", specs.get("bluetooth"))
            + row("音訊編解碼", specs.get("codec")) + row("防水/防塵", specs.get("water"))
            + row("顏色", p.get("color")) + row("上市年份", p.get("release_year"))
        )
    else:
        ramrom = f"{_esc(p.get('ram_gb'))}GB / {_esc(p.get('storage_gb'))}GB"
        battery = f"{p['battery_mah']} mAh" if p.get("battery_mah") else "—"
        rows_html = (
            row("作業系統", p.get("os")) + row("螢幕", p.get("display"))
            + row("處理器", p.get("chip")) + row("記憶體 / 儲存", ramrom)
            + row("後置相機", p.get("rear_camera")) + row("電池", battery)
            + row("顏色", p.get("color")) + row("上市年份", p.get("release_year"))
        )
    was = (
        f'<span class="was">原 NT${p["original_price"]:,}</span>'
        if p.get("is_sale") and p.get("original_price") else ""
    )
    badges = ('<span class="hot">🔥 熱賣商品</span>' if p.get("is_hot") else "") + (
        '<span class="sale">🎁 限時特價</span>' if p.get("is_sale") else "")
    inner = (
        f'<div class="hero"><img src="{_esc(p.get("img_url"))}" alt="{_esc(p.get("name"))}"></div>'
        '<div class="body">'
        f'<span class="brand">{_esc(p.get("brand"))}</span>'
        f"<h1>{_esc(p.get('name'))}</h1>"
        f'<div class="price">NT${p.get("price", 0):,}<small>含稅</small>{was}</div>{badges}'
        "<table>" + rows_html + "</table>"
        '<p class="tag">＊資料即時取自 Supabase。回 LINE 即可加入購物車。</p></div>'
        '<div class="foot">東吳大學資料系 2026 ‧ 手機商城 Demo</div>'
    )
    return _page(str(p.get("name")), inner)


# ---- 路由與事件 handler ----------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return {"message": "Line Webhook Server"}


@app.route("/phone/<int:pid>", methods=["GET"])
def phone_page(pid):
    """手機詳細展示頁（HTML）。商品卡「詳細頁」按鈕的 URIAction 指向這裡，
    在 LINE 內建瀏覽器開啟（使用者留在 LINE）。資料即時查自 Supabase。"""
    return app.response_class(render_phone_page(get_phone(pid)), mimetype="text/html")


@app.route("/", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


def _need_dm(uid):
    """購物車/訂單需要 user_id；群組沒有時回提示（否則回 None）。"""
    if not uid:
        return TextMessage(text="購物車／訂單功能請在 1:1 聊天室使用 🙏")
    return None


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    text = event.message.text.strip()
    uid = get_user_id(event)

    # 客服模式中：先處理「結束」與「已知指令」（已知指令會自動退出客服），其餘自由文字交給 Gemini
    if uid in SUPPORT_MODE:
        if text in SUPPORT_END_TRIGGERS:
            SUPPORT_MODE.pop(uid, None)
            reply(event.reply_token, TextMessage(text="👋 已結束客服，祝你購物愉快！", quick_reply=QR_EMPTY()))
            return
        if text not in ALL_COMMANDS:
            reply(event.reply_token, support_answer(uid, text))
            return
        SUPPORT_MODE.pop(uid, None)  # 打到已知指令 → 退出客服模式，往下正常處理

    if text in TRIGGERS:
        reply(event.reply_token, msg_hot())
    elif text in SALE_TRIGGERS:
        reply(event.reply_token, msg_sale())
    elif text in SUPPORT_TRIGGERS:
        reply(event.reply_token, _need_dm(uid) or _enter_support(uid))
    elif text in CART_VIEW_TRIGGERS:
        reply(event.reply_token, _need_dm(uid) or msg_cart(uid))
    elif text in CART_CLEAR_TRIGGERS:
        reply(event.reply_token, _need_dm(uid) or msg_clear(uid))
    elif text in CHECKOUT_TRIGGERS:
        reply(event.reply_token, _need_dm(uid) or msg_checkout(uid))
    elif text in ORDERS_VIEW_TRIGGERS:
        reply(event.reply_token, _need_dm(uid) or msg_orders(uid))
    elif text in CATEGORY_PICKER_TRIGGERS:
        reply(event.reply_token, msg_category_picker())
    elif text in CATEGORY_NAME_TRIGGERS:
        reply(event.reply_token, msg_category(CATEGORY_NAME_TRIGGERS[text]))
    else:
        reply(event.reply_token, TextMessage(
            text="用下方選單操作 👇 或輸入「熱賣商品」「優惠專區」「線上客服」",
            quick_reply=quick(("🔥 熱賣商品", "menu=hot"), ("🎁 優惠專區", "menu=sale"), ("💬 線上客服", "menu=support"))))


def _enter_support(uid):
    """進入客服模式並回開場白（需先確保有 uid）。"""
    SUPPORT_MODE[uid] = True
    return msg_support_intro()


@handler.add(PostbackEvent)
def handle_postback(event):
    data = parse_qs(event.postback.data)
    menu = data.get("menu", [""])[0]
    action = data.get("action", [""])[0]
    uid = get_user_id(event)

    # 點任何 rich menu 鍵或「結束客服」→ 先退出客服模式（menu=support 下面會再開）
    if uid in SUPPORT_MODE and (menu or action == "support_end"):
        SUPPORT_MODE.pop(uid, None)

    # 1) rich menu 底部選單
    if menu:
        if menu == "hot":
            reply(event.reply_token, msg_hot())
        elif menu == "sale":
            reply(event.reply_token, msg_sale())
        elif menu == "cart":
            reply(event.reply_token, _need_dm(uid) or msg_cart(uid))
        elif menu == "orders":
            reply(event.reply_token, _need_dm(uid) or msg_orders(uid))
        elif menu == "category":
            reply(event.reply_token, msg_category_picker())
        elif menu == "support":
            reply(event.reply_token, _need_dm(uid) or _enter_support(uid))
        else:
            reply(event.reply_token, TextMessage(
                text=f"「{menu}」功能示範中，敬請期待 🙌",
                quick_reply=quick(("🔥 熱賣商品", "menu=hot"), ("🎁 優惠專區", "menu=sale"))))
        return

    # 2) 結帳 / 清空 / 選分類 / 結束客服（無商品 id 的按鈕）
    if action == "support_end":
        reply(event.reply_token, TextMessage(text="👋 已結束客服，祝你購物愉快！", quick_reply=QR_EMPTY()))
        return
    if action == "checkout":
        reply(event.reply_token, _need_dm(uid) or msg_checkout(uid))
        return
    if action == "clearcart":
        reply(event.reply_token, _need_dm(uid) or msg_clear(uid))
        return
    if action == "cat":
        reply(event.reply_token, msg_category(data.get("c", [""])[0]))
        return

    # 3) 商品卡／購物車卡按鈕（加入購物車 / 移除 / 規格詳情）
    pid = data.get("id", [""])[0]
    phone = get_phone(pid)
    if action in ("cart", "remove"):
        if not phone:
            reply(event.reply_token, TextMessage(text="找不到這項商品 😅"))
        elif not uid:
            reply(event.reply_token, TextMessage(text="購物車功能請在 1:1 聊天室使用 🙏"))
        elif action == "cart":
            n = add_to_cart(uid, int(pid))
            reply(event.reply_token, TextMessage(
                text=f"🛒 已把「{phone['name']}」加入購物車（這項 ×{n}）！",
                quick_reply=QR_AFTER_ADD()))
        else:  # remove
            remove_from_cart(uid, int(pid))
            reply(event.reply_token, TextMessage(
                text=f"🗑️ 已從購物車移除「{phone['name']}」", quick_reply=QR_AFTER_REMOVE()))
    elif action == "detail" and phone:
        reply(event.reply_token, TextMessage(text="\n".join([
            f"📱 {phone['name']}",
            f"💰 NT${phone['price']:,}",
            f"🧠 {phone.get('chip') or '-'}",
            f"🖥️ {phone.get('display') or '-'}",
            f"💾 {phone.get('ram_gb') or '-'}GB / {phone.get('storage_gb') or '-'}GB",
            f"📷 {phone.get('rear_camera') or '-'}",
            f"🔋 {phone.get('battery_mah') or '-'} mAh",
            f"🎨 {phone.get('color') or '-'}",
        ]), quick_reply=quick(("🛒 加入購物車", f"action=cart&id={phone['id']}"), ("🔥 繼續逛", "menu=hot"))))
    else:
        reply(event.reply_token, TextMessage(text="收到你的選擇了！"))
