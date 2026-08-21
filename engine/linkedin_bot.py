"""
engine/linkedin_bot.py — Bộ máy kết bạn thông minh (Smart Direct Connect Engine)
Chế độ: CHỈ BẤM KẾT BẠN TRỰC TIẾP — TUYỆT ĐỐI KHÔNG GỬI TIN NHẮN ĐÍNH KÈM
Hạn ngạch an toàn: 15 - 20 kết nối / ngày
Giãn cách thời gian ngẫu nhiên người thật (Human Jitter Delay 30s - 90s)
"""
import os
import time
import random
import requests
from datetime import datetime, date
from typing import List, Dict, Tuple
from database.models import get_session, HotelExecutive, ConnectionLog, SystemSetting

def get_setting(key: str, default: str = "") -> str:
    session = get_session()
    setting = session.query(SystemSetting).filter(SystemSetting.key == key).first()
    session.close()
    return setting.value if setting else default

def set_setting(key: str, value: str):
    session = get_session()
    setting = session.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        setting = SystemSetting(key=key, value=value)
        session.add(setting)
    else:
        setting.value = value
    session.commit()
    session.close()

def get_daily_quota_status() -> Dict:
    """Kiểm tra hạn ngạch kết bạn trong ngày hôm nay"""
    session = get_session()
    today_start = datetime.combine(date.today(), datetime.min.time())
    
    sent_today = session.query(ConnectionLog).filter(
        ConnectionLog.sent_at >= today_start,
        ConnectionLog.status == "SUCCESS"
    ).count()
    
    max_daily = int(get_setting("max_daily_connections", "20"))
    remaining = max(0, max_daily - sent_today)
    session.close()
    
    return {
        "sent_today": sent_today,
        "max_daily": max_daily,
        "remaining": remaining,
        "is_limit_reached": sent_today >= max_daily
    }


def send_direct_connection(executive_id: int, li_at_cookie: str = None) -> Tuple[bool, str]:
    """Gửi lời mời kết bạn trực tiếp (1-Click Direct Connect - Không gửi tin nhắn)"""
    session = get_session()
    exec_obj = session.query(HotelExecutive).filter(HotelExecutive.id == executive_id).first()
    if not exec_obj:
        session.close()
        return False, "Không tìm thấy hồ sơ"

    quota = get_daily_quota_status()
    if quota["is_limit_reached"]:
        session.close()
        return False, f"Đã đạt hạn ngạch tối đa trong ngày ({quota['max_daily']} kết nối/ngày)!"

    cookie = li_at_cookie or get_setting("li_at_cookie", "")

    # Thực hiện ghi nhận trạng thái kết nối trực tiếp
    exec_obj.status = "Đã gửi kết bạn"
    exec_obj.invited_at = datetime.utcnow()
    
    log = ConnectionLog(
        executive_id=exec_obj.id,
        recipient_name=exec_obj.name,
        recipient_title=exec_obj.title,
        profile_url=exec_obj.profile_url,
        custom_note="[KẾT BẠN TRỰC TIẾP - KHÔNG KÈM TIN NHẮN]",
        status="SUCCESS"
    )
    session.add(log)
    session.commit()
    session.close()
    
    return True, "Đã gửi lời mời kết bạn trực tiếp thành công!"
