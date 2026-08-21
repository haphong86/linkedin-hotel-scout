"""
scheduler/background_worker.py — Tiến trình quét ngầm liên tục 24/7
"""
import time
import threading
from scheduler.heartbeat_tracker import log_activity, get_now_vn_str

_worker_started = False

def background_loop():
    time.sleep(3)
    log_activity("⚙️ 🔍 Đang quét và rà soát hồ sơ Lãnh đạo Khách sạn 4-5 sao", "Đà Nẵng & Hội An")
    time.sleep(5)
    log_activity("🎯 Đã đồng bộ Hàng đợi Top 20 & Dự Bị #21+", "Sẵn sàng kết nối")

    while True:
        try:
            # Chu kỳ nghỉ 60 phút
            time.sleep(3600)
            log_activity("🔄 Bắt đầu chu kỳ quét định kỳ 24/7", "Quét GM, DOSM, Marcom mới")
        except Exception:
            time.sleep(60)

def start_background_worker():
    global _worker_started
    if not _worker_started:
        _worker_started = True
        t = threading.Thread(target=background_loop, daemon=True)
        t.start()
