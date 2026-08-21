"""
engine/priority_queue.py — Hệ thống Hàng đợi 2 Tầng (Top 20 + Dự Bị 21+ Auto-Promotion)
Tích hợp Smart LinkedIn Direct Name Search + Google Direct Link
"""
import re
import urllib.parse
from typing import List, Dict
from database.models import get_session, HotelExecutive

def clean_person_name(name: str) -> str:
    """Loại bỏ ký tự thừa trong tên để tìm kiếm người thật 100%"""
    clean = re.sub(r'\(.*?\)', '', name).strip()
    return clean

def get_linkedin_people_url(name: str) -> str:
    """Tạo link LinkedIn Search theo Tên Lãnh Đạo (Ra ngay hồ sơ 100%)"""
    name_clean = clean_person_name(name)
    return f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(name_clean)}"

def get_google_xray_url(name: str, company: str) -> str:
    """Tạo link Google X-Ray dẫn thẳng tới Profile LinkedIn chính xác"""
    name_clean = clean_person_name(name)
    comp_clean = re.sub(r'\b(Hotels?|Resorts?|Villas?|Spa|Beach|Premier|By Fusion)\b', '', company, flags=re.I).strip()
    comp_clean = ' '.join(comp_clean.split()[:2])
    query = f'site:linkedin.com/in "{name_clean}" {comp_clean}'
    return f"https://www.google.com/search?q={urllib.parse.quote(query)}"

def get_prioritized_executives(selected_cities: List[str] = None, limit: int = 20, offset: int = 0) -> List[Dict]:
    """Lấy danh sách lãnh đạo chưa kết bạn theo thứ tự ưu tiên Lead Score"""
    session = get_session()
    query = session.query(HotelExecutive).filter(HotelExecutive.status == "Mới tìm thấy")
    
    if selected_cities:
        query = query.filter(HotelExecutive.city.in_(selected_cities))
        
    total_needed = offset + limit
    ordered_leads = query.order_by(
        HotelExecutive.lead_score.desc(),
        HotelExecutive.created_at.asc()
    ).limit(total_needed).all()
    
    sliced_leads = ordered_leads[offset:total_needed]
    
    result = []
    for idx, e in enumerate(sliced_leads):
        queue_idx = offset + idx + 1
        
        # Huy hiệu chức danh
        if e.lead_score >= 98:
            badge = "🔴 TỔNG GIÁM ĐỐC (GM)"
        elif e.lead_score >= 95:
            badge = "🟠 GIÁM ĐỐC SALES & MKT (DOSM)"
        elif e.lead_score >= 90:
            badge = "🟡 TRƯỞNG PHÒNG MARCOM"
        else:
            badge = "⚪ SALES MANAGER"

        linkedin_url = get_linkedin_people_url(e.name)
        google_url = get_google_xray_url(e.name, e.company)

        result.append({
            "queue_index": queue_idx,
            "id": e.id,
            "name": e.name,
            "title": e.title,
            "company": e.company,
            "city": e.city,
            "location": e.location,
            "linkedin_url": linkedin_url,
            "google_url": google_url,
            "headline": e.headline,
            "lead_score": e.lead_score,
            "priority_badge": badge,
            "status": e.status
        })
    
    session.close()
    return result


def get_daily_queue_20(selected_cities: List[str] = None) -> List[Dict]:
    return get_prioritized_executives(selected_cities=selected_cities, limit=20, offset=0)


def get_backlog_queue_21_plus(selected_cities: List[str] = None, limit: int = 100) -> List[Dict]:
    return get_prioritized_executives(selected_cities=selected_cities, limit=limit, offset=20)
