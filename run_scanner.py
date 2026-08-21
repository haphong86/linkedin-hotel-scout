#!/usr/bin/env python3
"""
run_scanner.py — Chạy TRÊN MÁY ANH (không phải Railway)
LinkedIn không chặn IP nhà/văn phòng.
Kết quả scan được lưu vào SQLite local → anh xem qua app Railway hoặc local.

Cách dùng:
  python3 run_scanner.py --cookie "AQEDATxxxxx..." --region "Đà Nẵng"
  python3 run_scanner.py --cookie "AQEDATxxxxx..."               ← scan toàn quốc
  python3 run_scanner.py --cookie "AQEDATxxxxx..." --pages 5     ← giới hạn 5 trang/query
"""
import argparse, sys, time
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="LinkedIn Hotel Scout — Local Scanner")
    parser.add_argument("--cookie", required=True, help="Cookie li_at từ LinkedIn (F12 → Application → Cookies)")
    parser.add_argument("--region",  default=None,  help="Tên khu vực muốn scan (bỏ trống = toàn quốc)")
    parser.add_argument("--pages",   type=int, default=10, help="Số trang / query (mặc định 10)")
    parser.add_argument("--batch",   type=int, default=0,  help="Chỉ chạy N query rồi dừng (0 = chạy hết)")
    args = parser.parse_args()

    # Import engine
    sys.path.insert(0, ".")
    from engine.continuous_scanner import (
        seed_scan_jobs, get_scan_stats, run_scan_jobs,
        ScanJob, REGIONS
    )
    from database.models import get_session

    # Nạp jobs
    added = seed_scan_jobs()
    stats = get_scan_stats()
    print(f"\n{'='*60}")
    print(f"  HÀ PHONG VISUALS · LinkedIn Hotel Scout")
    print(f"  Local Scanner — chạy trên máy của anh")
    print(f"{'='*60}")
    print(f"  Tổng query:     {stats['total']}")
    print(f"  Đã xong:        {stats['done']}")
    print(f"  Chờ scan:       {stats['pending']}")
    print(f"  Người mới thêm: {stats['total_new_added']}")
    print(f"{'='*60}\n")

    # Lọc theo khu vực nếu có
    job_ids = None
    if args.region:
        session = get_session()
        region_jobs = session.query(ScanJob).filter(
            ScanJob.region == args.region,
            ScanJob.status.in_(["pending", "done"])
        ).all()
        job_ids = [j.id for j in region_jobs]
        session.close()
        if not job_ids:
            print(f"⚠️  Không tìm thấy query nào cho khu vực '{args.region}'")
            print(f"   Các khu vực hợp lệ: {[r[0] for r in REGIONS]}")
            sys.exit(1)
        print(f"🎯 Scan khu vực: {args.region} ({len(job_ids)} query)\n")
    else:
        print(f"🌐 Scan toàn quốc ({stats['pending']} query đang chờ)\n")

    # Progress callback
    start_time = datetime.now()
    def on_progress(ji, total, job, total_new):
        elapsed = (datetime.now() - start_time).seconds
        eta_sec = int(elapsed / (ji + 1) * (total - ji - 1)) if ji > 0 else 0
        eta_min = eta_sec // 60
        bar = "█" * int((ji+1)/total*30) + "░" * (30 - int((ji+1)/total*30))
        print(f"\r[{bar}] {ji+1:>4}/{total} | "
              f"+{total_new} người mới | "
              f"ETA: ~{eta_min}p | "
              f"{job['region']}: {job['title'][:25]:<25}",
              end="", flush=True)
        # Dừng sau N query nếu --batch được set
        if args.batch > 0 and ji >= args.batch - 1:
            return True  # stop signal

    print("▶  Bắt đầu scan...\n")
    try:
        result = run_scan_jobs(
            li_at_cookie=args.cookie,
            job_ids=job_ids,
            max_pages=args.pages,
            progress_callback=on_progress,
        )
        print(f"\n\n{'='*60}")
        if result.get("status") == "cookie_expired":
            print("🔴 Cookie li_at hết hạn!")
            print("   → Lấy cookie mới: Chrome → F12 → Application → Cookies → li_at")
        else:
            print(f"✅ XONG!")
            print(f"   Đã xử lý: {result['jobs_processed']} query")
            print(f"   Người mới thêm vào queue: +{result['total_new']}")
            stats2 = get_scan_stats()
            print(f"   Tổng trong DB: {stats2['total_new_added']} người")
        print(f"{'='*60}\n")

    except KeyboardInterrupt:
        print(f"\n\n⏸  Đã dừng! Lần sau chạy lại, hệ thống sẽ tiếp tục từ chỗ dở.\n")

if __name__ == "__main__":
    main()
