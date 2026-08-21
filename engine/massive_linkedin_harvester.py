"""
engine/massive_linkedin_harvester.py — CÔNG CỤ QUÉT DỮ LIỆU LÃNH ĐẠO KHÁCH SẠN QUY MÔ LỚN
Quét toàn diện 63 tỉnh thành & hơn 50 chuỗi khách sạn / resort cao cấp tại Việt Nam
"""
import requests
import re
import urllib.parse
import time
from bs4 import BeautifulSoup
from database.models import get_session, HotelExecutive
from scheduler.heartbeat_tracker import log_activity

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}

# 1. Danh sách Chuỗi Khách Sạn & Resort Cao Cấp
HOTEL_BRANDS = [
    "Marriott", "Sheraton", "JW Marriott", "Le Meridien", "Renaissance", "Four Points", "Courtyard",
    "Accor", "Sofitel", "Pullman", "Novotel", "Mercure", "MGallery",
    "IHG", "InterContinental", "Crowne Plaza", "Holiday Inn", "voco", "Regent",
    "Hilton", "Hilton Garden Inn", "Conrad",
    "Hyatt", "Hyatt Regency", "Park Hyatt",
    "Melia", "Vinpearl", "Melia Vinpearl",
    "Mường Thanh", "Flamingo", "FLC", "Silk Path", "Fusion", "La Siesta", "Anantara", "Banyan Tree", "Azerai", "Zannier", "The Anam", "Centara"
]

# 2. Danh sách Chức Danh Quyết Định Hình Ảnh
TARGET_TITLES = [
    ("General Manager", 98),
    ("Resort Manager", 96),
    ("Managing Director", 98),
    ("Hotel Manager", 95),
    ("Director of Sales & Marketing", 95),
    ("DOSM", 95),
    ("Commercial Director", 95),
    ("Commercial Head", 94),
    ("Director of Sales", 92),
    ("Marcom Manager", 92),
    ("Marketing & Communications Manager", 92),
    ("Marketing Manager", 90),
    ("PR Manager", 90),
    ("Brand Manager", 90),
    ("Digital Marketing Manager", 88)
]

# 3. Địa Bàn Trọng Điểm Du Lịch & Khách Sạn
TARGET_CITIES = [
    "Đà Nẵng", "Hội An", "Huế", "Quảng Nam", "Lăng Cô",
    "Nha Trang", "Cam Ranh", "Khánh Hòa", "Phú Yên", "Quy Nhơn",
    "Phan Thiết", "Mũi Né", "Bình Thuận", "Phú Quốc", "Kiên Giang",
    "Vũng Tàu", "Hồ Tràm", "Côn Đảo", "Đà Lạt", "Lâm Đồng",
    "TP. Hồ Chí Minh", "Hà Nội", "Hạ Long", "Quảng Ninh", "Sa Pa", "Ninh Bình"
]

def harvest_batch(city: str, role: str, brand: str = "") -> int:
    """Quét 1 đợt theo Thành phố + Chức danh + Thương hiệu"""
    brand_part = f'"{brand}"' if brand else '("hotel" OR "resort" OR "hospitality")'
    query = f'site:linkedin.com/in/ "{role}" ("{city}" OR "Vietnam") {brand_part}'
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
    session = get_session()
    saved = 0
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
                    actual_link = urllib.parse.unquote(raw_href.split("uddg=")[1].split("&")[0]) if "uddg=" in raw_href else raw_href
                elif "linkedin.com/in/" in (url_el.get_text(strip=True) if url_el else ""):
                    actual_link = f"https://{url_el.get_text(strip=True)}"
                
                if not actual_link or "linkedin.com/in/" not in actual_link:
                    continue
                
                parts = raw_title.replace(" | LinkedIn", "").replace(" - LinkedIn", "").split(" - ")
                name = parts[0].strip()
                ex_title = parts[1].strip() if len(parts) > 1 else role
                ex_company = parts[2].strip() if len(parts) > 2 else (brand if brand else f"Luxury Hotel ({city})")
                
                if len(name) < 2 or "profile" in name.lower():
                    continue

                exists = session.query(HotelExecutive).filter(HotelExecutive.profile_url == actual_link).first()
                if not exists:
                    score = 98 if any(k in ex_title.lower() for k in ["general manager", "gm", "managing director", "resort manager"]) else (95 if "director" in ex_title.lower() else 90)
                    session.add(HotelExecutive(
                        name=name,
                        title=ex_title,
                        company=ex_company,
                        city=city,
                        location=f"{city}, Vietnam",
                        profile_url=actual_link,
                        headline=raw_snippet[:300],
                        lead_score=score,
                        status="Mới tìm thấy"
                    ))
                    saved += 1
            session.commit()
    except Exception:
        pass
    finally:
        session.close()
    return saved
