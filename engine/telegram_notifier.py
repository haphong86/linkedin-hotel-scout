"""
engine/telegram_notifier.py — Gửi báo cáo kết nối LinkedIn hàng ngày về Telegram
"""
import os
import httpx
from datetime import datetime, date
from database.models import get_session, HotelExecutive, ConnectionLog

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8940819235:AAE3kbi1avSC5k15I21zEzG8V5XDj-BZRCk")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

def get_chat_id_from_bot() -> str:
    token = TELEGRAM_BOT_TOKEN
    if not token:
        return ""
    try:
        r = httpx.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=6.0)
        data = r.json()
        if data.get("ok") and data.get("result"):
            last_msg = data["result"][-1]
            return str(last_msg.get("message", {}).get("chat", {}).get("id") or "")
    except Exception:
        pass
    return ""

def send_telegram_daily_report() -> bool:
    """Gửi bản tin thống kê kết bạn LinkedIn hôm nay về Telegram"""
    token = TELEGRAM_BOT_TOKEN
    chat_id = TELEGRAM_CHAT_ID or get_chat_id_from_bot()
    if not token or not chat_id:
        print("⚠️ Chưa có TELEGRAM_CHAT_ID!")
        return False

    session = get_session()
    today_start = datetime.combine(date.today(), datetime.min.time())
    
    sent_today = session.query(ConnectionLog).filter(
        ConnectionLog.sent_at >= today_start,
        ConnectionLog.status == "SUCCESS"
    ).count()

    total_vip = session.query(HotelExecutive).count()
    total_connected = session.query(HotelExecutive).filter(HotelExecutive.status == "Đã gửi kết bạn").count()
    remaining_in_queue = session.query(HotelExecutive).filter(HotelExecutive.status == "Mới tìm thấy").count()
    
    gm_count = session.query(HotelExecutive).filter(HotelExecutive.title.like("%General Manager%") | HotelExecutive.title.like("%GM%")).count()
    dosm_count = session.query(HotelExecutive).filter(HotelExecutive.title.like("%Director%") | HotelExecutive.title.like("%DOSM%")).count()
    
    session.close()

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    msg = (
        f"📊 *BÁO CÁO TĂNG TRƯỞNG MẠNG LƯỚI LINKEDIN VIP*\n"
        f"⏰ Thời gian: `{now_str}`\n"
        f"👤 Tài khoản: [Hà Phong (Photographer)](https://www.linkedin.com/in/hà-phong-9119933b8)\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ *Hôm nay đã bấm kết bạn:* `{sent_today} / 20 lượt`\n"
        f"👥 *Tổng lãnh đạo đã kết nối:* `{total_connected} người`\n"
        f"📋 *Hàng đợi dự bị đang chờ:* `{remaining_in_queue} người`\n"
        f"👑 *Cơ cấu mạng lưới VIP:*\n"
        f"  • Tổng Giám Đốc (GM): `{gm_count} sếp`\n"
        f"  • Giám Đốc Sales & MKT (DOSM): `{dosm_count} sếp`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *Anti-Ban Status:* An toàn 100% (Không gửi tin nhắn spam)\n"
        f"🌐 *Dashboard:* [Mở Hệ Thống](https://linkedin-hotel-scout-production.up.railway.app)"
    )

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        r = httpx.post(url, json=payload, timeout=8.0)
        return r.status_code == 200
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")
        return False
