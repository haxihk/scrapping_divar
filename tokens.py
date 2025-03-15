import requests
import time

# URL API دیوار
url = "https://api.divar.ir/v8/postlist/w/search"

# هدرهای درخواست برای جلوگیری از بلاک شدن
headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

# تعداد آگهی‌هایی که می‌خواهیم دریافت کنیم
MAX_TOKENS = 2000
RETRY_LIMIT = 5  # تعداد تلاش مجدد در صورت خطا
DELAY_BETWEEN_REQUESTS = 0.5  # کاهش تأخیر برای افزایش سرعت

# استفاده از `requests.Session()` برای افزایش سرعت و پایداری
session = requests.Session()
session.headers.update(headers)

list_of_tokens = []
last_post_date = None
count = 0
page = 1

while count < MAX_TOKENS:
    payload = {
        "city_ids": ["1"],
        "pagination_data": {
            "@type": "type.googleapis.com/post_list.PaginationData",
            "last_post_date": last_post_date if last_post_date else None,
            "page": page,
            "layer_page": 1
        },
        "disable_recommendation": False,
        "map_state": {"camera_info": {"bbox": {}}},
        "search_data": {
            "form_data": {
                "data": {
                    "category": {"str": {"value": "apartment-sell"}}
                }
            },
            "server_payload": {
                "@type": "type.googleapis.com/widgets.SearchData.ServerPayload",
                "additional_form_data": {
                    "data": {"sort": {"str": {"value": "sort_date"}}}
                }
            }
        }
    }

    # حذف `last_post_date` در درخواست اول
    if last_post_date is None:
        del payload["pagination_data"]["last_post_date"]

    retries = 0
    while retries < RETRY_LIMIT:
        try:
            res = session.post(url, json=payload)
            res.raise_for_status()

            if res.status_code == 429:
                print("🚫 درخواست زیاد ارسال شده، منتظر بمانید...")
                time.sleep(10)
                retries += 1
                continue

            data = res.json()
            last_post_date = data.get("last_post_date")
            page += 1  # افزایش شماره صفحه

            # پردازش هر آگهی در `list_widgets`
            for widget in data.get("list_widgets", []):
                try:
                    token = widget["data"]["action"]["payload"]["token"]
                    if token and token not in list_of_tokens:
                        list_of_tokens.append(token)
                        count += 1
                        print(f"✅ {count}: {token}")
                except KeyError:
                    continue  # رد کردن آگهی‌های نامعتبر

            time.sleep(DELAY_BETWEEN_REQUESTS)  # کاهش تأخیر برای افزایش سرعت

            if not data.get("list_widgets"):
                print("🚫 دیگر آگهی جدیدی یافت نشد.")
                break

            break  # اگر موفق شد، از حلقه `retry` خارج شود

        except requests.exceptions.RequestException as e:
            print(f"❌ خطا در دریافت داده: {e}")
            retries += 1
            time.sleep(3)  # انتظار برای تلاش مجدد

    if retries == RETRY_LIMIT:
        print("🚨 چندین تلاش ناموفق، توقف برنامه.")
        break

# ذخیره توکن‌ها در فایل یکجا برای بهبود سرعت
with open("tokens.txt", "w", encoding="utf-8") as txt_file:
    txt_file.write("\n".join(list_of_tokens))

print(f"\n✅ تعداد {len(list_of_tokens)} توکن ذخیره شد در tokens.txt")
