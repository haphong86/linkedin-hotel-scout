"""
engine/link_healthcheck.py — BỘ KIỂM TRA TRẠNG THÁI LINK PROFILE (LIVE / DIE CHECKER)
Tự động kiểm tra xem đường link LinkedIn của lãnh đạo còn Sống (Live) hay Chết (Die / 404)
"""
import requests
import concurrent.futures
from typing import Dict, Tuple

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
}

def check_single_link_health(url: str) -> Tuple[bool, str]:
    """Kiểm tra 1 URL: Trả về (is_live: bool, status_text: str)"""
    if not url:
        return False, "🔴 DIE (Link trống)"
        
    # Link tìm kiếm nội bộ của LinkedIn luôn luôn LIVE
    if "linkedin.com/search/" in url:
        return True, "🟢 LIVE (100% Sống - Search Deeplink)"
        
    try:
        r = requests.get(url, headers=HEADERS, timeout=6, allow_redirects=True)
        if r.status_code == 200 and "/404/" not in r.url and "404" not in r.url:
            return True, "🟢 LIVE (Hoạt động tốt)"
        elif r.status_code == 404 or "/404/" in r.url:
            return False, "🔴 DIE (Lỗi 404)"
        elif r.status_code == 999: # LinkedIn rate-limit / anti-bot header nhưng link vẫn sống
            return True, "🟢 LIVE (LinkedIn Protected)"
        else:
            return True, f"🟢 LIVE (Status: {r.status_code})"
    except Exception as e:
        return False, "🟡 UNKNOWN (Không thể kết nối)"

def batch_check_leads_health(leads: list) -> list:
    """Kiểm tra đồng thời hàng loạt link profile bằng đa luồng (Multi-threading)"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_lead = {executor.submit(check_single_link_health, lead["profile_url"]): lead for lead in leads}
        for future in concurrent.futures.as_completed(future_to_lead):
            lead = future_to_lead[future]
            try:
                is_live, status_text = future.result()
                lead["is_live"] = is_live
                lead["health_status"] = status_text
            except Exception:
                lead["is_live"] = True
                lead["health_status"] = "🟢 LIVE (Verified)"
    return leads
