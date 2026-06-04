"""
產生「單張、不切換頁籤」的簡單 LINE Rich Menu 圖片（電商風 2x3 六顆按鈕）。

這是最單純的選單：一張圖、六個按鈕、沒有頁籤切換。
輸出 1200x810 PNG；可點擊區座標在 setup_simple.py 用相同座標系定義。

字型：STHeiti（繁中）＋ Apple Color Emoji（彩色圖示）。
執行：python richmenu/make_simple_image.py
"""

import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 810
HEADER_H = 210          # 上方標題帶高度
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "menu_simple.png")

CJK = "/System/Library/Fonts/STHeiti Medium.ttc"
EMOJI = "/System/Library/Fonts/Apple Color Emoji.ttc"

BRAND = (230, 0, 18)        # 主色（紅）
BRAND_DARK = (170, 0, 12)

SHOP_TITLE = "購物商城"
SHOP_SUB = "會員專屬 ‧ 天天優惠"

# 2 列 x 3 欄共 6 顆按鈕：(emoji, 文字)
# 第一排放 bot 真正有的三大功能（熱賣／購物車／訂單），第二排為示範用占位。
BUTTONS = [
    ("🔥", "熱賣推薦"), ("🛒", "我的購物車"), ("📦", "我的訂單"),
    ("🛍️", "商品分類"), ("🎟️", "領優惠券"), ("💬", "線上客服"),
]


def font(size):
    return ImageFont.truetype(CJK, size)


def render_emoji(ch, target_px):
    """用 Apple Color Emoji 畫單一 emoji 到透明小圖再縮放，回傳 RGBA Image。"""
    strike = None
    for s in (137, 160, 96, 128, 109, 64):
        try:
            f = ImageFont.truetype(EMOJI, s)
            strike = s
            break
        except OSError:
            continue
    if strike is None:
        return None
    canvas = strike * 2
    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((canvas // 2, canvas // 2), ch, font=f, embedded_color=True, anchor="mm")
    bbox = img.getbbox()
    if not bbox:
        return None
    img = img.crop(bbox)
    w, h = img.size
    scale = target_px / h
    return img.resize((max(1, int(w * scale)), target_px), Image.LANCZOS)


def main():
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 標題帶（垂直漸層）
    for y in range(HEADER_H):
        t = y / HEADER_H
        col = tuple(int(BRAND[k] + (BRAND_DARK[k] - BRAND[k]) * t) for k in range(3))
        draw.line([0, y, W, y], fill=col)
    draw.text((60, 80), SHOP_TITLE, font=font(64), fill=(255, 255, 255), anchor="lm")
    draw.text((62, 150), SHOP_SUB, font=font(32), fill=(255, 255, 255), anchor="lm")

    # 2x3 按鈕格
    cell_w, cell_h = W // 3, (H - HEADER_H) // 2
    for idx, (emoji, label) in enumerate(BUTTONS):
        r, c = divmod(idx, 3)
        x0, y0 = c * cell_w, HEADER_H + r * cell_h
        cx = x0 + cell_w // 2
        em = render_emoji(emoji, 92)
        icon_cy = y0 + 110
        if em:
            img.alpha_composite(em, (cx - em.width // 2, icon_cy - em.height // 2))
        else:
            draw.ellipse([cx - 44, icon_cy - 44, cx + 44, icon_cy + 44], fill=BRAND)
        draw.text((cx, y0 + 215), label, font=font(36), fill=(60, 60, 60), anchor="mm")

    # 分隔線
    for c in (1, 2):
        draw.line([c * cell_w, HEADER_H + 30, c * cell_w, H - 30], fill=(238, 238, 238), width=2)
    draw.line([40, HEADER_H + cell_h, W - 40, HEADER_H + cell_h], fill=(238, 238, 238), width=2)

    img.convert("RGB").save(OUT, "PNG")
    print(f"寫出 {OUT}  ({os.path.getsize(OUT) // 1024} KB)")


if __name__ == "__main__":
    main()
