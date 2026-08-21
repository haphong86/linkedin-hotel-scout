"""
engine/linkedin_scraper.py — Bộ máy tìm kiếm & bóc tách Lãnh đạo Khách sạn trên LinkedIn
Dùng kỹ thuật Google X-Ray Search công khai, an toàn, không sợ bị chặn.
"""
import requests
import re
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Dict
from database.models import get_session, HotelExecutive

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}

KEYWORD_ROLES = [
    ("General Manager", "Tổng Giám Đốc (GM)", 98),
    ("Resort Manager", "Tổng Quản Lý Resort", 96),
    ("Hotel Manager", "Quản Lý Khách Sạn", 95),
    ("Director of Sales & Marketing", "Giám Đốc Sales & Marketing (DOSM)", 95),
    ("DOSM", "Giám Đốc Sales & Marketing (DOSM)", 95),
    ("Marketing & Communications Manager", "Trưởng Phòng Truyền Thông & Marcom", 92),
    ("Marcom Manager", "Trưởng Phòng Marcom", 92),
    ("Marketing Manager", "Trưởng Phòng Marketing", 90),
    ("Sales Manager", "Trưởng Phòng Kinh Doanh (SM)", 88),
    ("Commercial Head", "Giám Đốc Thương Mại", 94),
    ("Cluster Director", "Giám Đốc Cụm Khách Sạn", 96),
]

HOTEL_CITIES = ["Đà Nẵng", "Hội An", "Huế", "Quảng Nam", "Nha Trang", "Phú Quốc", "Quy Nhơn", "Phan Thiết", "Đà Lạt"]

def calculate_lead_score(title: str) -> int:
    title_lower = title.lower()
    if any(k in title_lower for k in ["general manager", "gm", "tổng giám đốc", "resort manager", "managing director", "owner"]):
        return 98
    if any(k in title_lower for k in ["dosm", "director of sales", "commercial head", "cluster director"]):
        return 95
    if any(k in title_lower for k in ["marcom", "marketing manager", "communications", "pr manager"]):
        return 90
    return 85

def search_executives_xray(city: str, role_keyword: str = "General Manager") -> List[Dict]:
    """Tìm kiếm hồ sơ LinkedIn lãnh đạo khách sạn tại thành phố cụ thể"""
    query = f'site:linkedin.com/in/ "{role_keyword}" ("{city}" OR "Vietnam") ("hotel" OR "resort" OR "hospitality")'
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
    results = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
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
                
                # Trích xuất link LinkedIn sạch
                actual_link = ""
                if "linkedin.com/in/" in raw_href:
                    if "uddg=" in raw_href:
                        actual_link = urllib.parse.unquote(raw_href.split("uddg=")[1].split("&")[0])
                    else:
                        actual_link = raw_href
                elif "linkedin.com/in/" in (url_el.get_text(strip=True) if url_el else ""):
                    actual_link = f"https://{url_el.get_text(strip=True)}"
                
                if not actual_link or "linkedin.com/in/" not in actual_link:
                    continue
                
                # Phân tách Tên và Chức danh từ Title: "John Doe - General Manager - Hilton | LinkedIn"
                parts = raw_title.replace(" | LinkedIn", "").replace(" - LinkedIn", "").split(" - ")
                name = parts[0].strip()
                title = parts[1].strip() if len(parts) > 1 else role_keyword
                company = parts[2].strip() if len(parts) > 2 else "Luxury Hotel / Resort"
                
                results.append({
                    "name": name,
                    "title": title,
                    "company": company,
                    "city": city,
                    "location": f"{city}, Vietnam",
                    "profile_url": actual_link,
                    "headline": raw_snippet[:300],
                    "lead_score": calculate_lead_score(title),
                })
    except Exception as e:
        print(f"Lỗi tìm kiếm: {e}")
    return results


def scan_and_save_executives(cities: List[str] = None) -> int:
    """Quét và lưu danh bạ Lãnh đạo Khách sạn vào Database"""
    session = get_session()
    target_cities = cities or ["Đà Nẵng", "Hội An", "Huế", "Nha Trang", "Phú Quốc"]
    
    saved_count = 0
    for city in target_cities:
        for role_kw, role_label, score in KEYWORD_ROLES[:4]:
            leads = search_executives_xray(city, role_kw)
            for l in leads:
                exists = session.query(HotelExecutive).filter(HotelExecutive.profile_url == l["profile_url"]).first()
                if not exists:
                    exec_obj = HotelExecutive(
                        name=l["name"],
                        title=l["title"],
                        company=l["company"],
                        location=l["location"],
                        city=l["city"],
                        profile_url=l["profile_url"],
                        headline=l["headline"],
                        lead_score=l["lead_score"],
                        status="Mới tìm thấy"
                    )
                    session.add(exec_obj)
                    saved_count += 1
    session.commit()
    session.close()
    return saved_count
