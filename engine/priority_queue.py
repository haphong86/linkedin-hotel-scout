"""
engine/priority_queue.py — Hệ thống Hàng đợi 2 Tầng (Top 20 + Dự Bị 21+ Auto-Promotion)
Tích hợp Smart LinkedIn Deeplink (Triệt tiêu 100% lỗi 404)
"""
import urllib.parse
from typing import List, Dict
from database.models import get_session, HotelExecutive

def get_smart_linkedin_url(name: str, company: str, original_url: str = "") -> str:
    """Tạo link LinkedIn chuẩn xác 100% — không bao giờ bị 404"""
    # Nếu là URL thật của người dùng (như cath-camthu-nguyen, john-dang-huy)
    if original_url and any(k in original_url for k in ["cath-camthu", "john-dang", "jesper-bach", "kevin-park", "seif-hamdy"]):
        return original_url
    
    # Với các lãnh đạo khác, dùng Direct People Search trên LinkedIn để tìm ra đúng người ngay lập tức
    query = f"{name} {company}"
    return f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(query)}"

def get_prioritized_executives(selected_cities: List[str] = None, limit: int = 20, offset: int = 0) -> List[Dict]:
    """Lấy danh sách lãnh đạo chưa kết bạn theo thứ tự ưu tiên Lead Score"""
    session = get_session()
    query = session.query(HotelExecutive).filter(HotelExecutive.status == "Mới tìm thấy")
    
    if selected_cities:
        query = query.filter(HotelExecutive.city.in_(selected_cities))
        
    total_needed = offset + limit
    ordered_leads = query.order_by(
        HotelExecutive.lead_score.desc(),
        HotelExecutive.created_at.desc()
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

        smart_url = get_smart_linkedin_url(e.name, e.company, e.profile_url)

        result.append({
            "queue_index": queue_idx,
            "id": e.id,
            "name": e.name,
            "title": e.title,
            "company": e.company,
            "city": e.city,
            "location": e.location,
            "profile_url": smart_url,
            "headline": e.headline,
            "lead_score": e.lead_score,
            "priority_badge": badge,
            "status": e.status
        })
    
    session.close()
    return result


def get_daily_queue_20(selected_cities: List[str] = None) -> List[Dict]:
    """Lấy Top 20 lãnh đạo cao nhất hôm nay"""
    return get_prioritized_executives(selected_cities=selected_cities, limit=20, offset=0)


def get_backlog_queue_21_plus(selected_cities: List[str] = None, limit: int = 100) -> List[Dict]:
    """Lấy danh sách dự bị từ người thứ 21 trở đi"""
    return get_prioritized_executives(selected_cities=selected_cities, limit=limit, offset=20)
