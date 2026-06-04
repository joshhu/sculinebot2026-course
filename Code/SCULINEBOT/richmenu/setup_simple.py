"""
建立「單張、不切換頁籤」的簡單 Rich Menu，並設為官方帳號的預設選單。

這是最單純的版本：一張圖、六顆按鈕、沒有 alias 也沒有 RichMenuSwitchAction。
六顆按鈕用 PostbackAction，點了會在聊天室顯示一句話（display_text），
之後若要讓 bot 回應，再到 webhook 加 PostbackEvent handler 即可。

需要環境變數 LINE_CHANNEL_ACCESS_TOKEN。本機跑法（金鑰不會打在指令上）：
    set -a; source .env; set +a
    python richmenu/setup_simple.py

可重複執行：會先刪掉帳號上所有舊的 rich menu / alias 再建立這一張。
圖片請先用 richmenu/make_simple_image.py 產生。
"""

import os
import sys

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    RichMenuRequest,
    RichMenuSize,
    RichMenuArea,
    RichMenuBounds,
    PostbackAction,
)

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "menu_simple.png")

W, H = 1200, 810
HEADER_H = 210

# 六顆按鈕（順序要與 make_simple_image.py 的格子一致）：key, 顯示名
BUTTONS = [
    ("hot", "熱賣推薦"), ("cart", "我的購物車"), ("orders", "我的訂單"),
    ("category", "商品分類"), ("coupon", "領優惠券"), ("support", "線上客服"),
]


def build_areas():
    """2x3 六格，每格一個 PostbackAction。"""
    areas = []
    cell_w = W // 3
    cell_h = (H - HEADER_H) // 2
    for idx, (key, label) in enumerate(BUTTONS):
        r, c = divmod(idx, 3)
        x0 = c * cell_w
        y0 = HEADER_H + r * cell_h
        width = cell_w if c < 2 else (W - x0)
        areas.append(
            RichMenuArea(
                bounds=RichMenuBounds(x=x0, y=y0, width=width, height=cell_h),
                action=PostbackAction(data=f"menu={key}", display_text=f"你點了「{label}」"),
            )
        )
    return areas


def main():
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        sys.exit("缺 LINE_CHANNEL_ACCESS_TOKEN。請先： set -a; source .env; set +a")

    config = Configuration(access_token=token)
    with ApiClient(config) as client:
        api = MessagingApi(client)
        blob = MessagingApiBlob(client)

        # 1) 清掉帳號上舊的 alias 與 rich menu（讓本程式可重複執行）
        for alias in api.get_rich_menu_alias_list().aliases:
            try:
                api.delete_rich_menu_alias(alias.rich_menu_alias_id)
            except Exception:
                pass
        for rm in api.get_rich_menu_list().richmenus:
            try:
                api.delete_rich_menu(rm.rich_menu_id)
            except Exception:
                pass
        print("已清除舊的 rich menu / alias")

        # 2) 建立這一張 rich menu
        req = RichMenuRequest(
            size=RichMenuSize(width=W, height=H),
            selected=True,
            name="簡易商城選單",
            chat_bar_text="購物選單 ▾",
            areas=build_areas(),
        )
        rich_menu_id = api.create_rich_menu(req).rich_menu_id
        print(f"建立選單 -> {rich_menu_id}")

        # 3) 上傳圖片
        with open(IMG, "rb") as f:
            # 注意：SDK 不會自動帶圖片的 Content-Type，必須用 _headers 明確指定，
            # 否則 bytes 會被當成 JSON 編碼而報錯。
            blob.set_rich_menu_image_with_http_info(
                rich_menu_id=rich_menu_id,
                body=f.read(),
                _headers={"Content-Type": "image/png"},
            )
        print("已上傳圖片")

        # 4) 設為所有人的預設選單
        api.set_default_rich_menu(rich_menu_id)
        print("已設為預設選單")

    print("完成！打開與這個 LINE 官方帳號的聊天室（關掉重開），最下面就會看到選單。")


if __name__ == "__main__":
    main()
