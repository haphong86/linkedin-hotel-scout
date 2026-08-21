"""
scheduler/background_worker.py — TIẾN TRÌNH TỰ ĐỘNG HÓA AUTO-PILOT 24/7/365 TRÊN CLOUD
Chạy ngầm liên tục 365 ngày trên Railway không cần mở máy tính.
"""
import time
import threading
from datetime import datetime, timezone, timedelta
from database.models import get_session, HotelExecutive, ConnectionLog, SystemSetting
from scheduler.heartbeat_tracker import log_activity, get_now_vn_str
from engine.priority_queue import get_daily_queue_20
from engine.telegram_notifier import send_telegram_daily_report

VN_TZ = timezone(timedelta(hours=7))
_worker_started = False

def is_autopilot_active() -> bool:
    session = get_session()
    setting = session.query(SystemSetting).filter(SystemSetting.key == "autopilot_247").first()
    active = setting.value == "true" if setting else True  # Mặc định kích hoạt
    session.close()
    return active

def set_autopilot_status(active: bool):
    session = get_session()
    setting = session.query(SystemSetting).filter(SystemSetting.key == "autopilot_247").first()
    val_str = "true" if active else "false"
    if not setting:
        session.add(SystemSetting(key="autopilot_247", value=val_str))
    else:
        setting.value = val_str
    session.commit()
    session.close()
    
    status_text = "🟢 ĐÃ BẬT" if active else "⚪ ĐÃ TẮT"
    log_activity("⚙️ Cấu Hình Auto-Pilot 24/7/365", f"Trạng thái: {status_text}")


def execute_daily_autopilot_cycle():
    """Thực hiện 1 chu kỳ kết bạn tự động trong ngày (Top 15–20 người)"""
    session = get_session()
    today_start = datetime.combine(datetime.now(VN_TZ).date(), datetime.min.time())
    
    sent_today = session.query(ConnectionLog).filter(
        ConnectionLog.sent_at >= today_start,
        ConnectionLog.status == "SUCCESS"
    ).count()
    
    if sent_today >= 20:
        log_activity("🛡️ Hạn Ngạch 24/7", f"Hôm nay đã gửi đủ {sent_today}/20 kết nối an toàn. Đang nghỉ ngơi chờ ngày mai.")
        session.close()
        return

    leads = get_daily_queue_20()
    needed = 20 - sent_today
    candidates = leads[:needed]
    session.close()

    if not candidates:
        log_activity("ℹ️ Hàng Đợi 24/7", "Đang quét thêm hồ sơ sếp lớn mới để nạp vào hàng đợi...")
        return

    log_activity("🚀 Auto-Pilot 24/7", f"Bắt đầu chu kỳ kết nối tự động cho {len(candidates)} Lãnh đạo VIP...")
    
    from engine.linkedin_bot import send_direct_connection
    success_count = 0
    for idx, c in enumerate(candidates):
        ok, msg = send_direct_connection(c["id"])
        if ok:
            success_count += 1
            log_activity("➕ Auto-Connect 24/7", f"[{idx+1}/{len(candidates)}] Đã kết bạn {c['name']} ({c['title']} · {c['company']})")
        # Giãn cách an toàn giữa các lượt
        time.sleep(2.0)

    log_activity("🎉 Hoàn Tất Chu Kỳ 24/7", f"Đã kết nối thành công +{success_count} lãnh đạo VIP hôm nay.")
    send_telegram_daily_report()


def continuous_autopilot_thread():
    """Vòng lặp vĩnh cửu 24/7/365 chạy ngầm trên Cloud"""
    time.sleep(3)
    log_activity("🚀 Khởi Động Auto-Pilot 24/7/365", "Hệ thống tự động hóa đám mây sẵn sàng hoạt động 365 ngày")
    
    last_run_day = None

    while True:
        try:
            now_vn = datetime.now(VN_TZ)
            current_day = now_vn.date()

            if is_autopilot_active():
                # Thực hiện chu kỳ tự động mỗi ngày (hoặc ngay khi khởi động)
                if last_run_day != current_day:
                    execute_daily_autopilot_cycle()
                    last_run_day = current_day

            # Ngủ 15 phút rồi kiểm tra lại trạng thái
            time.sleep(900)
            log_activity("💓 Heartbeat 24/7/365", f"Hệ thống đang chạy ngầm liên tục trên Cloud · {get_now_vn_str()}")
        except Exception as e:
            time.sleep(60)


def start_background_worker():
    global _worker_started
    if not _worker_started:
        _worker_started = True
        t = threading.Thread(target=continuous_autopilot_thread, daemon=True)
        t.start()
