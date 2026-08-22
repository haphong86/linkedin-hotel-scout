"""
engine/continuous_scanner.py
Hệ thống scan LinkedIn liên tục toàn quốc — tìm GM/DOSM/Marcom/Owner khách sạn resort.

Cơ chế:
1. Ma trận query: Chức danh × Khu vực
2. Playwright + cookie li_at → lấy link /in/ thật từng kết quả
3. Dedup với DB — chỉ thêm người MỚI vào queue kết bạn
4. Lưu trạng thái scan vào DB → resume được khi bị ngắt
5. Chạy lại định kỳ để bắt người mới đăng ký LinkedIn
"""
import re, time, random, urllib.parse
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from database.models import Base, engine, get_session, HotelExecutive

# ─── BẢNG SCAN STATE ────────────────────────────────────────────────────────
class ScanJob(Base):
    __tablename__ = "scan_jobs"
    __table_args__ = {"extend_existing": True}
    id           = Column(Integer, primary_key=True)
    query_title  = Column(String(200))
    query_loc    = Column(String(200))
    region       = Column(String(100))
    current_page = Column(Integer, default=0)       # trang đã scan đến
    total_found  = Column(Integer, default=0)        # tổng profile tìm được
    new_added    = Column(Integer, default=0)         # tổng người mới thêm vào queue
    status       = Column(String(20), default="pending")  # pending/running/done/exhausted
    last_run     = Column(DateTime)
    next_run     = Column(DateTime)                  # lịch chạy lại

Base.metadata.create_all(engine)

# ─── MA TRẬN QUERY ───────────────────────────────────────────────────────────

TITLES = [
    # Tier 1: Ra quyết định trực tiếp
    "General Manager",
    "Managing Director",
    "Director of Sales Marketing",
    "Director of Marketing Communications",
    "Marketing Communications Manager",
    # Tier 2: Người ảnh hưởng / đề xuất
    "Marketing Manager",
    "PR Manager",
    "Brand Manager",
    "Digital Marketing Manager",
    "Social Media Manager",
    "Revenue Manager",
    "F&B Director",
    "Event Manager",
    # Tier 3: Chủ sở hữu
    "Owner",
    "CEO",
    "Co-Founder",
]

REGIONS = [
    ("Đà Nẵng",    ["Da Nang Hotel", "Da Nang Resort", "Danang Hotel"]),
    ("Hội An",     ["Hoi An Resort", "Hoi An Hotel", "Hoi An Boutique"]),
    ("Huế",        ["Hue Hotel", "Hue Resort", "Hue Vietnam"]),
    ("Quy Nhơn",   ["Quy Nhon Resort", "Quy Nhon Hotel", "Binh Dinh Resort"]),
    ("Nha Trang",  ["Nha Trang Resort", "Nha Trang Hotel"]),
    ("Phú Quốc",   ["Phu Quoc Resort", "Phu Quoc Hotel"]),
    ("Đà Lạt",     ["Da Lat Hotel", "Dalat Resort", "Da Lat Resort"]),
    ("Cam Ranh",   ["Cam Ranh Resort", "Cam Ranh Hotel"]),
    ("Phan Thiết", ["Phan Thiet Resort", "Mui Ne Resort", "Mui Ne Hotel"]),
    ("Hà Nội",     ["Hanoi Hotel", "Hanoi Resort"]),
    ("Hồ Chí Minh",["Ho Chi Minh Hotel", "Saigon Hotel", "HCMC Hotel"]),
    ("Hạ Long",    ["Ha Long Resort", "Halong Bay Resort", "Ha Long Hotel"]),
    ("Ninh Bình",  ["Ninh Binh Resort", "Ninh Binh Hotel"]),
    ("Sapa",       ["Sapa Hotel", "Sapa Resort"]),
    ("Phú Yên",    ["Phu Yen Resort", "Phu Yen Hotel"]),
    ("Quảng Bình", ["Quang Binh Resort", "Phong Nha Hotel"]),
]

def build_all_queries():
    """Tạo toàn bộ danh sách query: title × location"""
    queries = []
    for title in TITLES:
        for region_name, locs in REGIONS:
            for loc in locs:
                queries.append({
                    "title": title,
                    "location": loc,
                    "region": region_name,
                    "keywords": f"{title} {loc}"
                })
    return queries


def seed_scan_jobs():
    """Nạp tất cả query vào bảng scan_jobs (chỉ thêm query chưa có)"""
    session = get_session()
    queries = build_all_queries()
    added = 0
    for q in queries:
        exists = session.query(ScanJob).filter_by(
            query_title=q["title"],
            query_loc=q["location"]
        ).first()
        if not exists:
            session.add(ScanJob(
                query_title=q["title"],
                query_loc=q["location"],
                region=q["region"],
                current_page=0,
                status="pending",
                next_run=datetime.now()
            ))
            added += 1
    session.commit()
    session.close()
    return added


def get_pending_jobs(limit=5):
    """Lấy các job cần chạy (pending hoặc đến lịch next_run)"""
    session = get_session()
    jobs = session.query(ScanJob).filter(
        ScanJob.status.in_(["pending", "done"]),
        ScanJob.next_run <= datetime.now()
    ).order_by(ScanJob.id.asc()).limit(limit).all()
    # Tách khỏi session để dùng an toàn
    result = [{
        "id": j.id,
        "title": j.query_title,
        "location": j.query_loc,
        "region": j.region,
        "current_page": j.current_page,
        "keywords": f"{j.query_title} {j.query_loc}",
    } for j in jobs]
    session.close()
    return result


def get_scan_stats():
    """Thống kê tổng quan tiến độ scan"""
    session = get_session()
    total   = session.query(ScanJob).count()
    done    = session.query(ScanJob).filter(ScanJob.status == "done").count()
    pending = session.query(ScanJob).filter(ScanJob.status == "pending").count()
    running = session.query(ScanJob).filter(ScanJob.status == "running").count()
    exhaust = session.query(ScanJob).filter(ScanJob.status == "exhausted").count()
    total_new = session.query(ScanJob).with_entities(
        __import__('sqlalchemy').func.sum(ScanJob.new_added)
    ).scalar() or 0
    session.close()
    return {
        "total": total, "done": done, "pending": pending,
        "running": running, "exhausted": exhaust,
        "total_new_added": int(total_new),
        "progress_pct": round(done / total * 100, 1) if total else 0
    }


def _extract_profiles(page) -> list:
    """Lấy link /in/ từ trang hiện tại — dùng nhiều selector để không bỏ sót."""
    urls = []
    seen = set()
    bad  = {'/in/messaging', '/in/search', '/in/jobs', '/in/feed',
            '/in/notifications', '/in/mynetwork', '/in/settings', '/in/learning'}

    try:
        # Chờ bất kỳ link /in/ nào xuất hiện
        try:
            page.wait_for_selector("a[href*='/in/']", timeout=6000)
        except Exception:
            return []

        # Lấy TẤT CẢ href có /in/ từ toàn bộ DOM (kể cả lazy-load)
        raw = page.eval_on_selector_all(
            "a[href*='/in/']",
            "els => els.map(e => e.getAttribute('href') || e.href)"
        )

        # Cũng lấy từ page source (bắt các link trong JSON-LD hoặc data attribute)
        try:
            html = page.content()
            extra = re.findall(r'linkedin\.com/in/([a-zA-Z0-9\-_%\.]{5,80})', html)
            for slug in extra:
                raw.append(f"https://www.linkedin.com/in/{slug}")
        except Exception:
            pass

        for href in raw:
            if not href:
                continue
            # Chuẩn hóa URL
            if href.startswith('/in/'):
                href = f"https://www.linkedin.com{href}"
            m = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_%\.]+)', href)
            if not m:
                continue
            clean = re.sub(r'\?.*$', '', m.group(1)).rstrip('/') + '/'
            # Lọc slug quá ngắn (dưới 3 ký tự) hoặc là trang hệ thống
            slug = clean.split('/in/')[-1].rstrip('/')
            if len(slug) < 3:
                continue
            if clean in seen or any(b in clean for b in bad):
                continue
            seen.add(clean)
            urls.append(clean)

    except Exception:
        pass

    return urls


def _save_new_profiles(found_urls: list, job: dict) -> int:
    """So sánh với DB, chỉ thêm URL chưa có. Trả về số người mới thêm."""
    session = get_session()
    added = 0
    for url in found_urls:
        exists = session.query(HotelExecutive).filter(
            HotelExecutive.profile_url == url
        ).first()
        if not exists:
            slug = url.split('/in/')[1].rstrip('/') if '/in/' in url else 'unknown'
            session.add(HotelExecutive(
                name=f"[{job['region']}] {slug}",
                title=job["title"],
                company=f"{job['region']} Hospitality",
                city=job["region"],
                location=f"{job['region']}, Vietnam",
                profile_url=url,
                headline=f"{job['title']} - {job['region']}",
                lead_score=85,
                status="Mới tìm thấy"
            ))
            added += 1
    session.commit()
    session.close()
    return added


def run_scan_jobs(
    li_at_cookie: str,
    job_ids: list = None,
    max_pages: int = 10,
    progress_callback=None,
    stop_flag=None
):
    """
    Chạy scan cho các job được chỉ định (hoặc toàn bộ pending).
    stop_flag: callable trả về True nếu muốn dừng sớm.
    Timing tối ưu: đủ chậm để tránh bị block, đủ nhanh để hoàn thành.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

    if job_ids:
        session = get_session()
        jobs = []
        for jid in job_ids:
            j = session.query(ScanJob).filter_by(id=jid).first()
            if j:
                jobs.append({
                    "id": j.id, "title": j.query_title, "location": j.query_loc,
                    "region": j.region, "current_page": j.current_page,
                    "keywords": f"{j.query_title} {j.query_loc}",
                })
        session.close()
    else:
        jobs = get_pending_jobs(limit=999)

    total_jobs = len(jobs)
    total_new  = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled",
                  "--disable-dev-shm-usage", "--disable-gpu"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        context.add_cookies([{
            "name": "li_at", "value": li_at_cookie.strip(),
            "domain": ".linkedin.com", "path": "/",
            "httpOnly": True, "secure": True
        }])
        page = context.new_page()

        consecutive_empty = 0  # đếm query liên tiếp không có kết quả

        for ji, job in enumerate(jobs):
            if stop_flag and stop_flag():
                break

            if progress_callback:
                progress_callback(ji, total_jobs, job, total_new)

            # Đánh dấu running
            session = get_session()
            db_job = session.query(ScanJob).filter_by(id=job["id"]).first()
            if db_job:
                db_job.status = "running"
                db_job.last_run = datetime.now()
                session.commit()
            session.close()

            job_new   = 0
            job_found = 0
            exhausted = False

            for pg in range(max_pages):
                if stop_flag and stop_flag():
                    break

                start   = pg * 10
                encoded = urllib.parse.quote(job["keywords"])
                url     = (f"https://www.linkedin.com/search/results/people/"
                           f"?keywords={encoded}&origin=GLOBAL_SEARCH_HEADER&start={start}")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)

                    if "login" in page.url or "authwall" in page.url:
                        browser.close()
                        return {"status": "cookie_expired", "total_new": total_new}

                    # ── TĂNG TỐC: chỉ chờ 1.5-2.5s thay vì 2.5-4s ──
                    time.sleep(random.uniform(1.5, 2.5))

                    # Scroll để load lazy content
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    time.sleep(0.5)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(0.5)

                    found = _extract_profiles(page)

                    if not found:
                        exhausted = True
                        break  # query này không có kết quả → bỏ qua trang tiếp

                    new = _save_new_profiles(found, job)
                    job_found += len(found)
                    job_new   += new
                    total_new += new
                    consecutive_empty = 0  # reset counter khi tìm được

                    if len(found) < 5:  # ít hơn 5 = trang cuối rồi
                        exhausted = True
                        break

                except Exception:
                    break

                # ── TĂNG TỐC: nghỉ 1.5-2.5s giữa trang thay vì 2.5-4s ──
                time.sleep(random.uniform(1.5, 2.5))

            # Cập nhật trạng thái job
            session = get_session()
            db_job = session.query(ScanJob).filter_by(id=job["id"]).first()
            if db_job:
                db_job.total_found += job_found
                db_job.new_added   += job_new
                db_job.current_page = max_pages
                db_job.status       = "exhausted" if exhausted else "done"
                db_job.last_run     = datetime.now()
                db_job.next_run     = datetime.now() + timedelta(days=7)
                session.commit()
            session.close()

            if job_found == 0:
                consecutive_empty += 1
            
            # ── TĂNG TỐC: nghỉ 1.5-3s giữa query thay vì 3-6s ──
            # Nếu 10 query liên tiếp không có kết quả → nghỉ 15s (có thể bị throttle)
            if consecutive_empty >= 10:
                time.sleep(15)
                consecutive_empty = 0
            else:
                time.sleep(random.uniform(1.5, 3.0))

        browser.close()

    return {"status": "ok", "total_new": total_new, "jobs_processed": total_jobs}
