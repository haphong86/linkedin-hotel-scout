import requests, re, urllib.parse, time
from bs4 import BeautifulSoup
from database.models import get_session, HotelExecutive
from scheduler.heartbeat_tracker import log_activity

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

QUERIES = [
    'site:vn.linkedin.com/in/ "General Manager" "hotel" "Da Nang"',
    'site:vn.linkedin.com/in/ "General Manager" "resort" "Hoi An"',
    'site:vn.linkedin.com/in/ "Director of Sales" "hotel" "Da Nang"',
    'site:vn.linkedin.com/in/ "General Manager" "hotel" "Nha Trang"',
    'site:vn.linkedin.com/in/ "General Manager" "resort" "Phu Quoc"',
    'site:vn.linkedin.com/in/ "General Manager" "resort" "Phan Thiet"',
    'site:vn.linkedin.com/in/ "General Manager" "resort" "Dalat"'
]

session = get_session()
saved = 0
for q in QUERIES:
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for item in soup.select("div.result__body"):
                title_el = item.select_one("a.result__title")
                snippet_el = item.select_one("a.result__snippet")
                url_el = item.select_one("a.result__url")
                if not title_el:
                    continue
                raw_title = title_el.get_text(strip=True)
                raw_snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                raw_href = title_el.get("href", "")
                
                actual_link = ""
                if "linkedin.com/in/" in raw_href:
                    if "uddg=" in raw_href:
                        actual_link = urllib.parse.unquote(raw_href.split("uddg=")[1].split("&")[0])
                    else:
                        actual_link = raw_href
                elif url_el and "linkedin.com/in/" in url_el.get_text(strip=True):
                    actual_link = f"https://{url_el.get_text(strip=True).strip()}"

                if not actual_link or "/in/" not in actual_link:
                    continue

                actual_link = actual_link.split("?")[0].rstrip("/")
                if not actual_link.startswith("http"):
                    actual_link = f"https://{actual_link}"
                actual_link = actual_link.replace("vn.linkedin.com", "www.linkedin.com")

                parts = raw_title.replace(" | LinkedIn", "").replace(" - LinkedIn", "").split(" - ")
                name = parts[0].strip()
                ex_title = parts[1].strip() if len(parts) > 1 else "General Manager"
                ex_company = parts[2].strip() if len(parts) > 2 else "Luxury Hotel"
                
                if len(name) < 2 or any(k in name.lower() for k in ["profile", "members", "top"]):
                    continue

                city = "Đà Nẵng"
                for c in ["Hội An", "Huế", "Nha Trang", "Cam Ranh", "Phú Quốc", "Phan Thiết", "Đà Lạt"]:
                    if c.lower() in (raw_snippet + raw_title).lower():
                        city = c
                        break

                exists = session.query(HotelExecutive).filter(HotelExecutive.profile_url == actual_link).first()
                if not exists:
                    session.add(HotelExecutive(
                        name=name,
                        title=ex_title,
                        company=ex_company,
                        city=city,
                        location=f"{city}, Vietnam",
                        profile_url=actual_link,
                        headline=raw_snippet[:300],
                        lead_score=98,
                        status="Mới tìm thấy"
                    ))
                    saved += 1
                    print(f"  ✅ [ĐÃ LƯU PERMALINK GỐC] {name} ({ex_company}) ➔ {actual_link}")
            session.commit()
    except Exception as e:
        pass
    time.sleep(0.3)

total = session.query(HotelExecutive).count()
print(f"🎉 TỔNG SỐ HỒ SƠ PERMALINK TRONG DB: {total} (MỚI THÊM: +{saved})")
session.close()
