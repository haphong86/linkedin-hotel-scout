"""
engine/linkedin_bulk_scanner.py
Tự động tìm kiếm hàng loạt lãnh đạo khách sạn trên LinkedIn theo chức danh + thành phố.
Playwright + cookie li_at → lấy toàn bộ link /in/ thật từ kết quả tìm kiếm.
"""

import re
import time
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ── DANH SÁCH TÌM KIẾM: CHỨC DANH × THÀNH PHỐ ──────────────────────
SEARCH_TARGETS = [
    # Chức danh VIP nhất
    ("General Manager", "Da Nang Hotel"),
    ("General Manager", "Hoi An Resort"),
    ("General Manager", "Nha Trang Hotel"),
    ("General Manager", "Phu Quoc Resort"),
    ("General Manager", "Da Lat Hotel"),
    ("General Manager", "Hanoi Hotel"),
    ("General Manager", "Ho Chi Minh Hotel"),
    ("General Manager", "Cam Ranh Resort"),
    ("General Manager", "Phan Thiet Resort"),
    ("General Manager", "Quy Nhon Resort"),
    ("Managing Director", "Vietnam Hotel"),
    ("Managing Director", "Vietnam Resort"),
    
    # DOSM & Sales Director
    ("Director of Sales Marketing", "Vietnam Hotel"),
    ("DOSM", "Vietnam Hotel"),
    ("Director of Sales", "Da Nang Hotel"),
    ("Director of Sales", "Hoi An Resort"),
    ("Director of Sales Marketing", "Nha Trang"),
    ("Director of Sales Marketing", "Phu Quoc"),
    
    # Revenue & Commercial
    ("Director of Revenue", "Vietnam Hotel"),
    ("Commercial Director", "Vietnam Hotel"),
    ("Revenue Manager", "Da Nang Hotel"),
    
    # Marcom
    ("Director of Marketing Communications", "Vietnam Hotel"),
    ("Marketing Communications Manager", "Da Nang Hotel"),
    ("Marcom Manager", "Vietnam Hotel"),
    
    # GM by brand
    ("General Manager", "Marriott Vietnam"),
    ("General Manager", "Hilton Vietnam"),
    ("General Manager", "IHG Vietnam"),
    ("General Manager", "Accor Vietnam"),
    ("General Manager", "Hyatt Vietnam"),
    ("General Manager", "Sofitel Vietnam"),
    ("General Manager", "Sheraton Vietnam"),
    ("General Manager", "Melia Vietnam"),
    ("General Manager", "Four Seasons Vietnam"),
    ("General Manager", "Banyan Tree Vietnam"),
    ("General Manager", "Anantara Vietnam"),
    ("General Manager", "Fusion Hotel Vietnam"),
    ("General Manager", "Vinpearl"),
]


def _extract_profile_urls_from_page(page) -> list[str]:
    """Lấy tất cả link /in/ từ trang kết quả tìm kiếm hiện tại."""
    urls = []
    try:
        # Đợi kết quả load
        page.wait_for_selector("a[href*='/in/']", timeout=8000)
        
        raw_links = page.eval_on_selector_all(
            "a[href*='/in/']",
            "els => els.map(e => e.href)"
        )
        
        seen = set()
        for href in raw_links:
            # Lọc chỉ lấy profile permalink thật
            m = re.search(r'(https?://www\.linkedin\.com/in/[a-zA-Z0-9\-_%\.]+)', href)
            if m:
                clean = re.sub(r'\?.*$', '', m.group(1)).rstrip('/') + '/'
                # Loại bỏ URL nội bộ không phải profile người dùng
                skip_patterns = ['/in/messaging', '/in/search', '/in/jobs', '/in/feed']
                if clean not in seen and not any(p in clean for p in skip_patterns):
                    seen.add(clean)
                    urls.append(clean)
    except PlaywrightTimeoutError:
        pass
    except Exception:
        pass
    return urls


def bulk_search_linkedin(
    li_at_cookie: str,
    max_pages_per_query: int = 3,
    progress_callback=None,
    headless: bool = True
) -> list[dict]:
    """
    Tìm kiếm hàng loạt theo SEARCH_TARGETS.
    Trả về list các dict: {name_hint, profile_url, source_query}
    """
    all_found = {}  # url -> dict (dedup by URL)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            locale="vi-VN"
        )
        context.add_cookies([{
            "name": "li_at",
            "value": li_at_cookie.strip(),
            "domain": ".linkedin.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
        }])

        page = context.new_page()
        total_queries = len(SEARCH_TARGETS)

        for qi, (title, location) in enumerate(SEARCH_TARGETS):
            if progress_callback:
                progress_callback(qi, total_queries, f"{title} · {location}")

            import urllib.parse
            query = f"{title} {location}"
            encoded = urllib.parse.quote(query)
            
            for pg in range(max_pages_per_query):
                # LinkedIn search results: page offset = pg * 10
                start = pg * 10
                search_url = (
                    f"https://www.linkedin.com/search/results/people/"
                    f"?keywords={encoded}&origin=GLOBAL_SEARCH_HEADER&start={start}"
                )
                
                try:
                    page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                    
                    # Kiểm tra đã đăng nhập chưa
                    if "login" in page.url or "authwall" in page.url:
                        browser.close()
                        return list(all_found.values()), "Cookie li_at hết hạn"

                    time.sleep(random.uniform(2.5, 4))
                    
                    # Scroll xuống để load lazy content
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    time.sleep(1)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    
                    # Lấy URL từ trang
                    found_urls = _extract_profile_urls_from_page(page)
                    
                    # Không có kết quả → bỏ qua trang sau
                    if not found_urls:
                        break
                    
                    for url in found_urls:
                        if url not in all_found:
                            all_found[url] = {
                                "profile_url": url,
                                "source_query": f"{title} · {location}",
                                "title_hint": title,
                            }
                    
                    # Nếu ít hơn 5 kết quả → không có trang tiếp
                    if len(found_urls) < 5:
                        break
                        
                except Exception:
                    break
                
                # Nghỉ giữa mỗi trang
                time.sleep(random.uniform(2, 3.5))
            
            # Nghỉ giữa mỗi query
            time.sleep(random.uniform(3, 5))

        browser.close()

    return list(all_found.values())
