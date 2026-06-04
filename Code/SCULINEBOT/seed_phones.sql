-- =====================================================================
-- 東吳大學資料系 2026 LINEBOT — 手機商城 (shop.py / carousel.py) 種子資料
--
-- 用途：在 Supabase（或任何 Postgres）重建商品目錄 public.phones（含手機與藍牙耳機，
--       以 category 欄區分）、個人購物車 cart_items、訂單 orders，並灌入示範資料。
-- 來源：2026-06 上網查證之當下最新機種與台幣價；商品照皆為 upload.wikimedia.org 直連、
--       已逐張 curl 驗證 200 + image/*（少數最新機種 Commons 尚無實照，改用同廠牌最接近
--       的實照，屬已知取代）。
--
-- 執行：Supabase Dashboard SQL Editor 貼上；或 psql -f；或 Management API database/query。
-- 重建：truncate ... restart identity 先清空再灌，id 從 1 開始（cascade 會連動清空購物車，demo 用）。
-- 註：表名沿用 phones（歷史因素），實為「商品目錄」，靠 category 區分手機／藍牙耳機。
-- =====================================================================

create table if not exists public.phones (
  id            bigint generated always as identity primary key,
  brand         text not null,
  model         text not null,
  name          text not null,
  price         integer not null,
  release_year  integer,
  os            text,
  display       text,
  chip          text,
  ram_gb        integer,
  storage_gb    integer,
  rear_camera   text,
  battery_mah   integer,
  color         text,
  category      text not null default '手機',   -- 手機 / 藍牙耳機
  img_url       text not null,
  is_hot        boolean not null default false,
  is_sale       boolean not null default false,      -- 是否限時特價（優惠專區 menu=sale 用）
  original_price integer,                             -- 原價（特價時 > price；非特價為 null）
  specs         jsonb not null default '{}'::jsonb,  -- 分類專屬規格（耳機：anc/battery/driver/bluetooth/codec/water）
  created_at    timestamptz not null default now(),
  unique (brand, model)
);
alter table public.phones add column if not exists category text not null default '手機';
alter table public.phones add column if not exists is_sale boolean not null default false;
alter table public.phones add column if not exists original_price integer;
alter table public.phones enable row level security;
drop policy if exists "public read phones" on public.phones;
create policy "public read phones" on public.phones for select to anon, authenticated using (true);
grant select on public.phones to anon, authenticated;

-- 先清空再重灌（id 從 1 起算；cascade 連動清空 cart_items，demo 用）
truncate table public.phones restart identity cascade;

-- 商品種子資料（60 筆：50 手機 + 10 藍牙耳機，2026-06 最新）---------------------------
insert into public.phones (brand, model, name, price, release_year, os, display, chip, ram_gb, storage_gb, rear_camera, battery_mah, color, category, img_url, is_hot, specs) values
  ('Apple', 'iPhone 17', 'Apple iPhone 17', 29900, 2025, 'iOS 26', '6.3" LTPO Super Retina XDR OLED 120Hz', 'Apple A19', 8, 256, '48MP+48MP', 3692, 'White', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/White_iPhone_17.jpg/960px-White_iPhone_17.jpg', true, '{}'::jsonb),
  ('Apple', 'iPhone 17 (Black)', 'Apple iPhone 17 (Black)', 29900, 2025, 'iOS 26', '6.3" LTPO Super Retina XDR OLED 120Hz', 'Apple A19', 8, 256, '48MP+48MP', 3692, 'Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Black_iPhone_17.jpg/960px-Black_iPhone_17.jpg', false, '{}'::jsonb),
  ('Apple', 'iPhone Air', 'Apple iPhone Air', 36900, 2025, 'iOS 26', '6.5" LTPO Super Retina XDR OLED 120Hz', 'Apple A19 Pro', 12, 256, '48MP', 3149, 'Sky Blue', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Sky_Blue_iPhone_Air.jpg/960px-Sky_Blue_iPhone_Air.jpg', true, '{}'::jsonb),
  ('Apple', 'iPhone Air (Space Black)', 'Apple iPhone Air (Space Black)', 36900, 2025, 'iOS 26', '6.5" LTPO Super Retina XDR OLED 120Hz', 'Apple A19 Pro', 12, 256, '48MP', 3149, 'Space Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Space_Black_iPhone_Air.jpg/960px-Space_Black_iPhone_Air.jpg', false, '{}'::jsonb),
  ('Apple', 'iPhone 17 Pro', 'Apple iPhone 17 Pro', 39900, 2025, 'iOS 26', '6.3" LTPO Super Retina XDR OLED 120Hz', 'Apple A19 Pro', 12, 256, '48MP+48MP+48MP', 3988, 'Silver', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/IPhone_17_Pro_%282025-12-28%29.jpg/960px-IPhone_17_Pro_%282025-12-28%29.jpg', true, '{}'::jsonb),
  ('Apple', 'iPhone 17 Pro Max', 'Apple iPhone 17 Pro Max', 44900, 2025, 'iOS 26', '6.9" LTPO Super Retina XDR OLED 120Hz', 'Apple A19 Pro', 12, 256, '48MP+48MP+48MP', 5088, 'Cosmic Orange', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Cosmic_Orange_iPhone_17_Pro_Max.jpg/960px-Cosmic_Orange_iPhone_17_Pro_Max.jpg', true, '{}'::jsonb),
  ('Apple', 'iPhone 17 Pro Max (Deep Blue)', 'Apple iPhone 17 Pro Max (Deep Blue)', 49900, 2025, 'iOS 26', '6.9" LTPO Super Retina XDR OLED 120Hz', 'Apple A19 Pro', 12, 512, '48MP+48MP+48MP', 5088, 'Deep Blue', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Deep_Blue_iPhone_17_Pro_Max.jpg/960px-Deep_Blue_iPhone_17_Pro_Max.jpg', true, '{}'::jsonb),
  ('Apple', 'iPhone 17e', 'Apple iPhone 17e', 19900, 2026, 'iOS 26', '6.1" Super Retina XDR OLED 60Hz', 'Apple A19', 8, 256, '48MP', 4005, 'Soft Pink', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/IPhone_17e_Soft_Pink_Model_-_1.jpg/960px-IPhone_17e_Soft_Pink_Model_-_1.jpg', false, '{}'::jsonb),
  ('Samsung', 'Galaxy S26', 'Samsung Galaxy S26', 30900, 2026, 'Android 16 (One UI 8.5)', '6.3" LTPO AMOLED 2X 120Hz', 'Snapdragon 8 Elite Gen 5 for Galaxy', 12, 256, '50MP+12MP+10MP', 4300, 'Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Galaxy_S26.jpg/960px-Galaxy_S26.jpg', true, '{}'::jsonb),
  ('Samsung', 'Galaxy S26+', 'Samsung Galaxy S26+', 37900, 2026, 'Android 16 (One UI 8.5)', '6.7" LTPO AMOLED 2X 120Hz', 'Snapdragon 8 Elite Gen 5 for Galaxy', 12, 256, '50MP+12MP+10MP', 4900, 'Silver', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Galaxy_S26_Plus.jpg/960px-Galaxy_S26_Plus.jpg', true, '{}'::jsonb),
  ('Samsung', 'Galaxy S26 Ultra', 'Samsung Galaxy S26 Ultra', 44900, 2026, 'Android 16 (One UI 8.5)', '6.9" LTPO AMOLED 2X 120Hz', 'Snapdragon 8 Elite Gen 5 for Galaxy', 12, 256, '200MP+50MP+10MP+50MP', 5000, 'Titanium Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Galaxy_S26_Ultra_-_1.jpg/960px-Galaxy_S26_Ultra_-_1.jpg', true, '{}'::jsonb),
  ('Samsung', 'Galaxy S26 Ultra (Lavender)', 'Samsung Galaxy S26 Ultra (Lavender)', 50900, 2026, 'Android 16 (One UI 8.5)', '6.9" LTPO AMOLED 2X 120Hz', 'Snapdragon 8 Elite Gen 5 for Galaxy', 12, 512, '200MP+50MP+10MP+50MP', 5000, 'Lavender', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Galaxy_S26_Ultra_lavender.jpg/960px-Galaxy_S26_Ultra_lavender.jpg', true, '{}'::jsonb),
  ('Samsung', 'Galaxy Z Fold7', 'Samsung Galaxy Z Fold7', 62900, 2025, 'Android 16 (One UI 8)', '8.0" Foldable AMOLED 2X 120Hz', 'Snapdragon 8 Elite Gen 5 for Galaxy', 12, 256, '200MP+12MP+10MP', 4400, 'Blue Shadow', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Samsung_Galaxy_Fold7_Cover_Screen.jpg/960px-Samsung_Galaxy_Fold7_Cover_Screen.jpg', true, '{}'::jsonb),
  ('Samsung', 'Galaxy Z Fold7 (512GB)', 'Samsung Galaxy Z Fold7 (512GB)', 66900, 2025, 'Android 16 (One UI 8)', '8.0" Foldable AMOLED 2X 120Hz', 'Snapdragon 8 Elite Gen 5 for Galaxy', 12, 512, '200MP+12MP+10MP', 4400, 'Jetblack', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Samsung_Galaxy_Fold7_Main_Screen.jpg/960px-Samsung_Galaxy_Fold7_Main_Screen.jpg', false, '{}'::jsonb),
  ('Samsung', 'Galaxy Z Flip7', 'Samsung Galaxy Z Flip7', 35900, 2025, 'Android 16 (One UI 8)', '6.9" Foldable AMOLED 2X 120Hz', 'Exynos 2500', 12, 256, '50MP+12MP', 4300, 'Blue Shadow', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Samsung_Galaxy_Flip7_FE.jpg/960px-Samsung_Galaxy_Flip7_FE.jpg', true, '{}'::jsonb),
  ('Samsung', 'Galaxy A57 5G', 'Samsung Galaxy A57 5G', 17990, 2026, 'Android 16 (One UI 8)', '6.7" Super AMOLED 120Hz', 'Exynos 1680', 8, 256, '50MP+12MP+5MP', 5000, 'Awesome Icyblue', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Samsung_Galaxy_A57_5G.jpg/960px-Samsung_Galaxy_A57_5G.jpg', false, '{}'::jsonb),
  ('Google', 'Pixel 10', 'Google Pixel 10', 26490, 2025, 'Android 16', '6.3" OLED 120Hz', 'Google Tensor G5', 12, 128, '48MP+13MP+10.8MP', 4970, 'Indigo', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Pixel_9_Pro_XL_and_Pixel_9.jpg/960px-Pixel_9_Pro_XL_and_Pixel_9.jpg', true, '{}'::jsonb),
  ('Google', 'Pixel 10 Pro', 'Google Pixel 10 Pro', 33490, 2025, 'Android 16', '6.3" LTPO OLED 120Hz', 'Google Tensor G5', 16, 128, '50MP+48MP+48MP', 4870, 'Moonstone', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Arri%C3%A8re_du_Google_Pixel_10_Pro_pierre_de_lune_de_256_Go.jpg/960px-Arri%C3%A8re_du_Google_Pixel_10_Pro_pierre_de_lune_de_256_Go.jpg', true, '{}'::jsonb),
  ('Google', 'Pixel 10 Pro XL', 'Google Pixel 10 Pro XL', 39990, 2025, 'Android 16', '6.8" LTPO OLED 120Hz', 'Google Tensor G5', 16, 256, '50MP+48MP+48MP', 5200, 'Obsidian', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Google_Pixel_9_Pro_XL_%28front%29.jpg/960px-Google_Pixel_9_Pro_XL_%28front%29.jpg', false, '{}'::jsonb),
  ('Google', 'Pixel 10a', 'Google Pixel 10a', 15990, 2026, 'Android 16', '6.3" OLED 120Hz', 'Google Tensor G4', 8, 128, '64MP+13MP', 5100, 'Lavender', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Pixel_9a_back.jpg/960px-Pixel_9a_back.jpg', false, '{}'::jsonb),
  ('OnePlus', '15', 'OnePlus 15', 28000, 2025, 'Android 16 (OxygenOS 16)', '6.78" AMOLED 165Hz', 'Snapdragon 8 Elite Gen 5', 12, 256, '50MP+50MP+50MP', 7300, 'Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/OnePlus_15_back.jpg/960px-OnePlus_15_back.jpg', true, '{}'::jsonb),
  ('OnePlus', '13', 'OnePlus 13', 25900, 2025, 'Android 15 (OxygenOS 15)', '6.82" LTPO AMOLED 120Hz', 'Snapdragon 8 Elite', 12, 256, '50MP+50MP+50MP', 6000, 'Blue', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/OnePlus_13_back.jpg/960px-OnePlus_13_back.jpg', false, '{}'::jsonb),
  ('Nothing', 'Phone (3)', 'Nothing Phone (3)', 29990, 2025, 'Android 15 (Nothing OS 3.5)', '6.67" AMOLED 120Hz', 'Snapdragon 8s Gen 4', 12, 256, '50MP+50MP+50MP', 5150, 'White', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/%E5%8D%8A%E5%A4%9C%E9%A6%96%E5%8F%91%EF%BC%81%E7%AC%AC%E4%B8%80%E6%89%8B%E6%8B%BF%E5%88%B0%E4%BA%86Nothing_Phone_%283%29_%EF%BC%81%E7%81%AF%E6%9D%A1%E6%B2%A1%E4%BA%86%E3%80%81%E8%83%8C%E5%90%8E%E5%A4%9A%E4%B8%80%E4%B8%AAscreen%EF%BC%81-00.00.31.780.png/960px-%E5%8D%8A%E5%A4%9C%E9%A6%96%E5%8F%91%EF%BC%81%E7%AC%AC%E4%B8%80%E6%89%8B%E6%8B%BF%E5%88%B0%E4%BA%86Nothing_Phone_%283%29_%EF%BC%81%E7%81%AF%E6%9D%A1%E6%B2%A1%E4%BA%86%E3%80%81%E8%83%8C%E5%90%8E%E5%A4%9A%E4%B8%80%E4%B8%AAscreen%EF%BC%81-00.00.31.780.png', true, '{}'::jsonb),
  ('Nothing', 'Phone (3a)', 'Nothing Phone (3a)', 13990, 2025, 'Android 15 (Nothing OS 3.1)', '6.77" AMOLED 120Hz', 'Snapdragon 7s Gen 3', 12, 256, '50MP+50MP+8MP', 5000, 'Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/Nothing_Phone_%283a%29_Pro_20250628.jpg/960px-Nothing_Phone_%283a%29_Pro_20250628.jpg', false, '{}'::jsonb),
  ('Sony', 'Xperia 1 VIII', 'Sony Xperia 1 VIII', 46990, 2026, 'Android 16', '6.5" LTPO OLED 120Hz', 'Snapdragon 8 Elite Gen 5', 16, 256, '48MP+48MP+48MP', 5000, 'Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Sony_Xperia_1_V_White_Case_Kickstand_On.jpg/960px-Sony_Xperia_1_V_White_Case_Kickstand_On.jpg', true, '{}'::jsonb),
  ('Asus', 'Zenfone 12 Ultra', 'Asus Zenfone 12 Ultra', 32990, 2025, 'Android 15', '6.78" LTPO AMOLED 144Hz', 'Snapdragon 8 Elite', 16, 256, '50MP+32MP+13MP', 5500, 'Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Zenfone_12_Ultra.png/960px-Zenfone_12_Ultra.png', false, '{}'::jsonb),
  ('Motorola', 'Razr 2026', 'Motorola Razr 2026', 20990, 2026, 'Android 16', '6.9" Foldable pOLED 120Hz', 'MediaTek Dimensity 7450X', 8, 256, '50MP+50MP', 4800, 'Red', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Motorola_razr_40_ultra_-_3.jpg/960px-Motorola_razr_40_ultra_-_3.jpg', true, '{}'::jsonb),
  ('Motorola', 'Edge 60 Pro', 'Motorola Edge 60 Pro', 16990, 2025, 'Android 15', '6.7" pOLED 120Hz', 'MediaTek Dimensity 8350 Extreme', 12, 512, '50MP+50MP+10MP', 6000, 'Blue', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Motorola_Edge_60_Pro.jpg/960px-Motorola_Edge_60_Pro.jpg', false, '{}'::jsonb),
  ('Xiaomi', '17 Ultra', 'Xiaomi 17 Ultra', 41999, 2026, 'Android 16 (HyperOS 3)', '6.9" LTPO OLED 120Hz 3500nits', 'Snapdragon 8 Elite Gen 5', 16, 512, '50MP+50MP+200MP', 6000, 'White', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Xiaomi_17_Ultra.jpg/960px-Xiaomi_17_Ultra.jpg', true, '{}'::jsonb),
  ('Xiaomi', '17', 'Xiaomi 17', 24999, 2026, 'Android 16 (HyperOS 3)', '6.3" OLED 120Hz', 'Snapdragon 8 Elite Gen 5', 12, 256, '50MP+50MP+50MP', 6330, 'Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Xiaomi_17.jpg/960px-Xiaomi_17.jpg', true, '{}'::jsonb),
  ('Xiaomi', 'Redmi Note 15 Pro 5G', 'Xiaomi Redmi Note 15 Pro 5G', 10999, 2026, 'Android 16 (HyperOS 3)', '6.83" AMOLED 120Hz', 'MediaTek Dimensity 7400', 12, 256, '50MP+8MP', 6580, 'Gold', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Redmi_Note_15_Pro.jpg/960px-Redmi_Note_15_Pro.jpg', false, '{}'::jsonb),
  ('Xiaomi', 'Redmi 15 5G', 'Xiaomi Redmi 15 5G', 6999, 2025, 'Android 15 (HyperOS 2)', '6.9" FHD+ 144Hz', 'Snapdragon 6s Gen 3', 8, 256, '50MP', 7000, 'Blue', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Redmi_15_back.jpg/960px-Redmi_15_back.jpg', false, '{}'::jsonb),
  ('Oppo', 'Find X9 Pro', 'Oppo Find X9 Pro', 38990, 2025, 'Android 16 (ColorOS 16)', '6.78" OLED 120Hz 3600nits', 'MediaTek Dimensity 9500', 16, 512, '50MP+50MP+200MP', 7500, 'White', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/OPPO_Find_X8_Pro_white_back.png/960px-OPPO_Find_X8_Pro_white_back.png', true, '{}'::jsonb),
  ('Oppo', 'Find X9', 'Oppo Find X9', 28990, 2025, 'Android 16 (ColorOS 16)', '6.59" AMOLED 120Hz', 'MediaTek Dimensity 9500', 12, 256, '50MP+50MP+50MP', 7025, 'Grey', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Star_Grey_Oppo_Find_X8.jpg/960px-Star_Grey_Oppo_Find_X8.jpg', false, '{}'::jsonb),
  ('Oppo', 'Reno15 Pro', 'Oppo Reno15 Pro', 20990, 2025, 'Android 16 (ColorOS 16)', '6.32" AMOLED 120Hz', 'MediaTek Dimensity 8450', 12, 256, '200MP+50MP', 6200, 'Blue', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Oppo_Reno15_Pro_back.jpg/960px-Oppo_Reno15_Pro_back.jpg', false, '{}'::jsonb),
  ('Vivo', 'X300 Pro', 'Vivo X300 Pro', 37990, 2025, 'Android 16 (OriginOS 6)', '6.78" AMOLED Zeiss 120Hz', 'MediaTek Dimensity 9500', 16, 512, '50MP+50MP+200MP', 6510, 'White', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/The_back_of_the_vivo_X300_Pro.jpg/960px-The_back_of_the_vivo_X300_Pro.jpg', true, '{}'::jsonb),
  ('Vivo', 'X300', 'Vivo X300', 30990, 2025, 'Android 16 (OriginOS 6)', '6.31" AMOLED Zeiss 120Hz 4500nits', 'MediaTek Dimensity 9500', 12, 256, '200MP+50MP+50MP', 6040, 'Blue', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/The_back_of_the_colorful_vivo_X300.jpg/960px-The_back_of_the_colorful_vivo_X300.jpg', true, '{}'::jsonb),
  ('Vivo', 'X300 Ultra', 'Vivo X300 Ultra', 49990, 2026, 'Android 16 (OriginOS 6)', '6.82" AMOLED Zeiss 144Hz', 'Snapdragon 8 Elite Gen 5', 16, 512, '200MP+200MP+50MP', 6600, 'Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/The_back_of_the_vivo_X300_Pro.jpg/960px-The_back_of_the_vivo_X300_Pro.jpg', true, '{}'::jsonb),
  ('Honor', 'Magic8 Pro', 'Honor Magic8 Pro', 37990, 2026, 'Android 16 (MagicOS 10)', '6.71" AMOLED 120Hz 6000nits', 'Snapdragon 8 Elite Gen 5', 12, 512, '50MP+50MP+200MP', 7100, 'Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/The_Honor_Magic8_Pro%27s_display.jpg/960px-The_Honor_Magic8_Pro%27s_display.jpg', true, '{}'::jsonb),
  ('Honor', 'Magic V5', 'Honor Magic V5', 47990, 2025, 'Android 15 (MagicOS 9)', '7.95" Foldable OLED 120Hz', 'Snapdragon 8 Elite', 16, 512, '50MP+50MP+64MP', 5820, 'Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/54/Honor_Magic_V5.jpg/960px-Honor_Magic_V5.jpg', true, '{}'::jsonb),
  ('Realme', 'GT 8 Pro', 'Realme GT 8 Pro', 30990, 2025, 'Android 16 (realme UI 7)', '6.79" AMOLED 144Hz 7000nits', 'Snapdragon 8 Elite Gen 5', 16, 512, '50MP+50MP+200MP', 7000, 'Blue', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Realme_GT2_back.jpg/960px-Realme_GT2_back.jpg', true, '{}'::jsonb),
  ('Realme', '16 Pro', 'Realme 16 Pro', 16990, 2026, 'Android 16 (realme UI 7)', '6.8" AMOLED 144Hz', 'MediaTek Dimensity 7300-Max', 12, 256, '200MP+8MP', 7000, 'Purple', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Realme_14_Pro_Plus_back.jpg/960px-Realme_14_Pro_Plus_back.jpg', false, '{}'::jsonb),
  ('Samsung', 'Galaxy A56 5G', 'Samsung Galaxy A56 5G', 9590, 2025, 'Android 15 (One UI 7)', '6.7" Super AMOLED 120Hz', 'Samsung Exynos 1580', 8, 256, '50MP+12MP+5MP', 5000, 'Awesome Graphite', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/Samsung_Galaxy_A56_5G_2025.jpg/960px-Samsung_Galaxy_A56_5G_2025.jpg', true, '{}'::jsonb),
  ('Google', 'Pixel 9a', 'Google Pixel 9a', 13490, 2025, 'Android 15', '6.3" Actua OLED 120Hz', 'Google Tensor G4', 8, 128, '48MP+13MP', 5100, 'Obsidian', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Pixel_9a_back.jpg/960px-Pixel_9a_back.jpg', true, '{}'::jsonb),
  ('Xiaomi', 'Redmi Note 15 Pro+ 5G', 'Xiaomi Redmi Note 15 Pro+ 5G', 10790, 2026, 'Android 15 (HyperOS 2)', '6.83" AMOLED 120Hz', 'Snapdragon 7s Gen 4', 12, 256, '200MP+8MP', 6200, 'Frost Blue', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Redmi_Note_15_Pro%2B_backside.jpg/960px-Redmi_Note_15_Pro%2B_backside.jpg', true, '{}'::jsonb),
  ('Motorola', 'moto g86 Power 5G', 'Motorola moto g86 Power 5G', 8990, 2025, 'Android 15', '6.67" pOLED 120Hz', 'MediaTek Dimensity 7300', 8, 256, '50MP+8MP', 6720, 'Spellbound', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Motorola_Moto_g84_5g_and_Motorola_Moto_g54_Power_Edition_smartphones_in_Gliwice%2C_Silesian_Voivodeship%2C_Poland%2C_May_2024.jpg/960px-Motorola_Moto_g84_5g_and_Motorola_Moto_g54_Power_Edition_smartphones_in_Gliwice%2C_Silesian_Voivodeship%2C_Poland%2C_May_2024.jpg', false, '{}'::jsonb),
  ('Nothing', 'CMF Phone 2 Pro', 'Nothing CMF Phone 2 Pro', 10990, 2025, 'Android 15 (Nothing OS 3.2)', '6.77" AMOLED 120Hz', 'MediaTek Dimensity 7300 Pro', 8, 256, '50MP+50MP+8MP', 5000, 'White', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/CMF_Phone_2_Pro_%28white%29_2025-05-08.jpg/960px-CMF_Phone_2_Pro_%28white%29_2025-05-08.jpg', true, '{}'::jsonb),
  ('Realme', '14 5G', 'Realme 14 5G', 7290, 2025, 'Android 15 (realme UI 6.0)', '6.67" AMOLED 120Hz', 'Snapdragon 6 Gen 4', 8, 256, '50MP+2MP', 6000, 'Mecha Silver', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Realme_14_Pro_Plus_back.jpg/960px-Realme_14_Pro_Plus_back.jpg', false, '{}'::jsonb),
  ('Nothing', 'Phone (3a) Pro', 'Nothing Phone (3a) Pro', 15990, 2025, 'Android 15 (Nothing OS 3.1)', '6.77" AMOLED 120Hz', 'Snapdragon 7s Gen 3', 12, 256, '50MP+50MP+8MP', 5000, 'Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/Nothing_Phone_%283a%29_Pro_20250628.jpg/960px-Nothing_Phone_%283a%29_Pro_20250628.jpg', false, '{}'::jsonb),
  ('Samsung', 'Galaxy A17 5G', 'Samsung Galaxy A17 5G', 7490, 2025, 'Android 15 (One UI 7)', '6.7" Super AMOLED 90Hz', 'Samsung Exynos 1330', 6, 128, '50MP+5MP+2MP', 5000, 'Black', '手機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Samsung_Galaxy_A17_5G_2026.jpg/960px-Samsung_Galaxy_A17_5G_2026.jpg', false, '{}'::jsonb),
  ('Apple', 'AirPods Pro 3', 'Apple AirPods Pro 3', 7490, 2025, null, null, null, null, null, null, null, 'White', '藍牙耳機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/AirPods_Pro_3_with_case.jpg/960px-AirPods_Pro_3_with_case.jpg', true, '{"anc": "主動降噪 (H3 晶片)", "battery": "8h（含盒 24h）", "driver": "Apple 客製化動圈單體", "bluetooth": "藍牙 5.3", "codec": "AAC/SBC", "water": "IP57"}'::jsonb),
  ('Bose', 'QuietComfort Ultra Earbuds', 'Bose QuietComfort Ultra Earbuds', 9490, 2025, null, null, null, null, null, null, null, 'Black', '藍牙耳機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Bose_QuietComfort_Ultra_Earbuds_-_2.jpg/960px-Bose_QuietComfort_Ultra_Earbuds_-_2.jpg', true, '{"anc": "主動降噪 (CustomTune 自適應)", "battery": "6h（含盒 24h）", "driver": "Bose 客製化動圈單體", "bluetooth": "藍牙 5.3", "codec": "aptX Adaptive/AAC/SBC", "water": "IPX4"}'::jsonb),
  ('Bose', 'QuietComfort Earbuds II', 'Bose QuietComfort Earbuds II', 6990, 2022, null, null, null, null, null, null, null, 'Black', '藍牙耳機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Bose_QuietComfort_Earbuds_II_-_2.jpg/960px-Bose_QuietComfort_Earbuds_II_-_2.jpg', false, '{"anc": "主動降噪 (CustomTune)", "battery": "6h（含盒 24h）", "driver": "Bose 動圈單體", "bluetooth": "藍牙 5.3", "codec": "aptX Adaptive/AAC/SBC", "water": "IPX4"}'::jsonb),
  ('Sony', 'WF-1000XM4', 'Sony WF-1000XM4', 7990, 2021, null, null, null, null, null, null, null, 'Black', '藍牙耳機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Sony_WF-1000XM4.jpg/960px-Sony_WF-1000XM4.jpg', true, '{"anc": "主動降噪 (V1 整合處理器)", "battery": "8h（含盒 24h）", "driver": "6mm 動圈單體", "bluetooth": "藍牙 5.2", "codec": "LDAC/AAC/SBC", "water": "IPX4"}'::jsonb),
  ('Sony', 'LinkBuds Clip', 'Sony LinkBuds Clip', 5490, 2025, null, null, null, null, null, null, null, 'Black', '藍牙耳機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Sony_LinkBuds_Clip_-_3.jpg/960px-Sony_LinkBuds_Clip_-_3.jpg', false, '{"anc": "主動降噪 (開放夾耳式)", "battery": "5h（含盒 20h）", "driver": "12mm 環形單體", "bluetooth": "藍牙 5.4", "codec": "AAC/SBC/LC3", "water": "IP55"}'::jsonb),
  ('Nothing', 'Ear (3)', 'Nothing Ear (3)', 6360, 2025, null, null, null, null, null, null, null, 'White', '藍牙耳機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Nothing_ear_%281%29_earphones_%28black%29.jpg/960px-Nothing_ear_%281%29_earphones_%28black%29.jpg', false, '{"anc": "主動降噪 (最高 45dB 自適應)", "battery": "5.5h（含盒 38h）", "driver": "12mm 動圈單體", "bluetooth": "藍牙 5.4", "codec": "LDAC/AAC/SBC", "water": "IP54"}'::jsonb),
  ('Nothing', 'Ear (stick)', 'Nothing Ear (stick)', 3490, 2022, null, null, null, null, null, null, null, 'White', '藍牙耳機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Nothing_ear_%28stick%29_buds_%283%29.jpg/960px-Nothing_ear_%28stick%29_buds_%283%29.jpg', false, '{"anc": "無主動降噪（半入耳）", "battery": "7h（含盒 29h）", "driver": "12.6mm 動圈單體", "bluetooth": "藍牙 5.2", "codec": "AAC/SBC", "water": "IP54"}'::jsonb),
  ('Google', 'Pixel Buds Pro 2', 'Google Pixel Buds Pro 2', 6990, 2024, null, null, null, null, null, null, null, 'Hazel', '藍牙耳機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Pixel_Buds_Pro%2C_orange.jpg/960px-Pixel_Buds_Pro%2C_orange.jpg', false, '{"anc": "主動降噪 (Tensor A1)", "battery": "8h（含盒 30h）", "driver": "11mm 動圈單體", "bluetooth": "藍牙 5.4", "codec": "AAC/SBC", "water": "IP54"}'::jsonb),
  ('Google', 'Pixel Buds 2a', 'Google Pixel Buds 2a', 3990, 2025, null, null, null, null, null, null, null, 'Hazel', '藍牙耳機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Pixel_Buds_in_charging_case_with_product_box.jpg/960px-Pixel_Buds_in_charging_case_with_product_box.jpg', false, '{"anc": "主動降噪 (Silent Seal)", "battery": "7h（含盒 20h）", "driver": "11mm 動圈單體", "bluetooth": "藍牙 5.4", "codec": "AAC/SBC", "water": "IP54"}'::jsonb),
  ('Huawei', 'FreeBuds Pro 4', 'Huawei FreeBuds Pro 4', 5990, 2025, null, null, null, null, null, null, null, 'Black', '藍牙耳機', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/HUAWEI_Mate_50_and_HUAWEI_FreeBuds_5.jpg/960px-HUAWEI_Mate_50_and_HUAWEI_FreeBuds_5.jpg', true, '{"anc": "主動降噪 (智慧動態)", "battery": "6.5h（含盒 33h）", "driver": "雙單體（動圈＋微平板）", "bluetooth": "藍牙 5.2", "codec": "L2HC/LDAC/AAC", "water": "IP54"}'::jsonb);


-- 限時特價（優惠專區 menu=sale）：先全部清空再標記示範特價品，冪等可重跑 -------
-- 售價 price 維持「目前特價」，original_price 為原價（> price）；卡片顯示「原價 → 特價」。
update public.phones set is_sale = false, original_price = null;
update public.phones set is_sale = true, original_price = v.op
from (values
  ('Samsung', 'Galaxy S26 Ultra', 50900),
  ('Apple', 'iPhone 17 Pro', 45900),
  ('Xiaomi', '17 Ultra', 47999),
  ('Vivo', 'X300 Pro', 42990),
  ('Apple', 'AirPods Pro 3', 8990),
  ('Bose', 'QuietComfort Ultra Earbuds', 10900),
  ('Sony', 'WF-1000XM4', 9490)
) as v(brand, model, op)
where public.phones.brand = v.brand and public.phones.model = v.model;

-- =====================================================================
-- 個人購物車 cart_items（每位 LINE 使用者各自一份；後端 service_role 讀寫）
-- =====================================================================
create table if not exists public.cart_items (
  id          bigint generated always as identity primary key,
  user_id     text not null,
  phone_id    bigint not null references public.phones(id) on delete cascade,
  qty         integer not null default 1,
  created_at  timestamptz not null default now(),
  unique (user_id, phone_id)
);
alter table public.cart_items enable row level security;
grant all on public.cart_items to service_role;

-- =====================================================================
-- 訂單 orders（結帳後產生；items 為購物車快照）
-- =====================================================================
create table if not exists public.orders (
  id          bigint generated always as identity primary key,
  user_id     text not null,
  total       integer not null,
  items       jsonb not null,
  created_at  timestamptz not null default now()
);
alter table public.orders enable row level security;
grant all on public.orders to service_role;
