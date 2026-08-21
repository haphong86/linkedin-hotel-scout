"""
engine/linkedin_scanner.py
Playwright-based LinkedIn scanner.
- Nhận cookie li_at của người dùng (đã đăng nhập LinkedIn)
- Vào trang search URL dạng /search/results/people/?keywords=Piotr+Madej
- Tự động click kết quả đầu tiên
- Lấy đúng link /in/piotr-madej-5a863b82/ thật
"""

import re
import time
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def _extract_in_url(page_url: str) -> str | None:
    """Kiểm tra URL hiện tại có phải dạng /in/ không."""
    m = re.search(r'(https?://www\.linkedin\.com/in/[^/?&#\s]+)', page_url)
    return m.group(1).rstrip('/') if m else None


def scan_profile_url(search_url: str, li_at_cookie: str, headless: bool = True) -> dict:
    """
    Mở search_url bằng Playwright, inject cookie li_at để đăng nhập,
    click người đầu tiên trong kết quả, trả về link /in/ thật.

    Returns:
        {
            "status": "ok" | "not_found" | "error",
            "profile_url": "https://www.linkedin.com/in/piotr-madej-5a863b82/",
            "name": "Piotr Madej",
            "message": "..."
        }
    """
    result = {"status": "error", "profile_url": None, "name": None, "message": ""}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/126.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="vi-VN"
            )

            # Inject cookie LinkedIn (li_at = session token)
            context.add_cookies([{
                "name": "li_at",
                "value": li_at_cookie.strip(),
                "domain": ".linkedin.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
            }])

            page = context.new_page()

            # 1. Mở trang search
            page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(random.uniform(2, 3))

            # 2. Kiểm tra đã đăng nhập chưa
            if "login" in page.url or "authwall" in page.url:
                result["status"] = "error"
                result["message"] = "Cookie li_at không hợp lệ hoặc đã hết hạn"
                browser.close()
                return result

            # 3. Tìm link profile /in/ đầu tiên trong kết quả tìm kiếm
            # Selector LinkedIn search result: các card người dùng
            profile_link = None

            # Thử selector chính xác của search result
            selectors = [
                "a[href*='/in/']",
                ".entity-result__title-text a",
                ".search-results-container a[href*='/in/']",
                "li.reusable-search__result-container a[href*='/in/']",
            ]

            for sel in selectors:
                try:
                    page.wait_for_selector(sel, timeout=8000)
                    links = page.locator(sel).all()
                    for link in links:
                        href = link.get_attribute("href") or ""
                        if "/in/" in href and "/search/" not in href:
                            profile_link = href
                            break
                    if profile_link:
                        break
                except PlaywrightTimeoutError:
                    continue

            if not profile_link:
                # Thử lấy từ toàn bộ anchor tags
                all_links = page.eval_on_selector_all(
                    "a[href*='/in/']",
                    "els => els.map(e => e.href)"
                )
                for href in all_links:
                    if "/in/" in href and "/search/" not in href and "miniProfile" not in href:
                        profile_link = href
                        break

            if profile_link:
                # Lấy phần /in/username-hash/ chuẩn xác
                clean_url = re.sub(r'\?.*$', '', profile_link).rstrip('/') + '/'
                # Lấy tên người dùng từ search URL
                kw = re.search(r'keywords=([^&]+)', search_url)
                name = kw.group(1).replace('%20', ' ') if kw else ""
                result["status"] = "ok"
                result["profile_url"] = clean_url
                result["name"] = name
                result["message"] = f"✅ Tìm thấy: {clean_url}"
            else:
                result["status"] = "not_found"
                result["message"] = "Không tìm thấy profile /in/ trong kết quả"

            browser.close()

    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Lỗi: {str(e)}"

    return result


def batch_scan_missing_profiles(leads: list, li_at_cookie: str, progress_callback=None) -> list:
    """
    Quét hàng loạt tất cả lead đang dùng search URL (/search/results/)
    để tìm link /in/ thật sự.

    leads: list of (id, name, search_url)
    Returns: list of (id, name, found_profile_url)
    """
    results = []
    total = len(leads)

    for i, (lead_id, name, search_url) in enumerate(leads):
        if "/search/results/" not in search_url:
            # Đã có link /in/ rồi, bỏ qua
            results.append((lead_id, name, search_url, "skipped"))
            continue

        if progress_callback:
            progress_callback(i, total, name)

        r = scan_profile_url(search_url, li_at_cookie, headless=True)
        found_url = r.get("profile_url") or search_url
        results.append((lead_id, name, found_url, r["status"]))

        # Nghỉ giữa mỗi lần quét để không bị block
        time.sleep(random.uniform(3, 5))

    return results
