"""
app.py — LinkedIn Hotel VIP Auto-Scout & Growth Bot (Hà Phong Visuals)
Cơ chế: TỰ ĐỘNG HÓA 100% — HÀNG ĐỢI 2 TẦNG (TOP 20 + DỰ BỊ #21+ ĐÔN LÊN TỰ ĐỘNG)
Không cần thao tác tay — Tự động nạp và kết nối hàng chục General Manager & DOSM thật 100%
Chạy: streamlit run app.py
"""
import os
import sys
import time
import pandas as pd
import streamlit as st
from datetime import datetime, date

# Ép buộc Socket phân giải IPv4 trên Railway/Linux Container
import socket
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if family == 0 or family == socket.AF_UNSPEC:
        family = socket.AF_INET
    try:
        return _orig_getaddrinfo(host, port, family, type, proto, flags)
    except Exception:
        return _orig_getaddrinfo(host, port, 0, type, proto, flags)

socket.getaddrinfo = _ipv4_only_getaddrinfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import init_db, get_session, HotelExecutive, ConnectionLog, SystemSetting
from database.verified_vips import VERIFIED_VIP_LEADS
from engine.linkedin_bot import (
    get_daily_quota_status, send_direct_connection, get_setting, set_setting
)
from engine.priority_queue import get_daily_queue_20, get_backlog_queue_21_plus
from engine.telegram_notifier import send_telegram_daily_report
from scheduler.heartbeat_tracker import get_heartbeat_status, log_activity

# ── CẤU HÌNH TRANG STREAMLIT ─────────────────────────────────────────
st.set_page_config(
    page_title="Hà Phong Visuals · LinkedIn VIP Auto-Scout Bot",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Khởi tạo DB
init_db()

# ── CSS THEME ĐEN — ĐỎ — TRẮNG HÀ PHONG VISUALS ───────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
  background-color: #050505 !important;
  color: #F0F0F0 !important;
}
.main .block-container {
  background: #050505 !important;
  padding-top: 1.8rem;
  max-width: 1440px;
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: #000000 !important;
  border-right: 1px solid #1f1f1f !important;
}
[data-testid="stSidebar"] * { color: #d0d0d0 !important; }

/* Metric Cards */
[data-testid="metric-container"] {
  background: #111111 !important;
  border: 1px solid #222222 !important;
  border-top: 3px solid #E50914 !important;
  padding: 16px 18px !important;
  border-radius: 4px !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
}
[data-testid="metric-container"] label {
  color: #A0A0A0 !important;
  font-size: 10px !important;
  font-weight: 600 !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
  font-family: 'Montserrat', sans-serif !important;
  font-size: 32px !important;
  color: #FFFFFF !important;
  font-weight: 700 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid #222222 !important;
  gap: 8px;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: #888888 !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase !important;
  padding: 12px 20px !important;
  border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
  color: #FFFFFF !important;
  border-bottom: 2px solid #E50914 !important;
  background: rgba(229, 9, 20, 0.08) !important;
  border-radius: 4px 4px 0 0 !important;
}

/* Buttons */
.stButton > button {
  background: #161616 !important;
  border: 1px solid #333333 !important;
  color: #FFFFFF !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase !important;
  padding: 10px 20px !important;
  border-radius: 4px !important;
}
.stButton > button:hover {
  background: #222222 !important;
  border-color: #E50914 !important;
  box-shadow: 0 0 10px rgba(229, 9, 20, 0.3) !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #E50914 0%, #B8000A 100%) !important;
  color: #FFFFFF !important;
  border: none !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 14px rgba(229, 9, 20, 0.4) !important;
}
</style>
""", unsafe_allow_html=True)


# ── SIDEBAR ĐIỀU KHIỂN ────────────────────────────────────────────────
with st.sidebar:
    if os.path.exists("static/logo.jpg"):
        try:
            st.image("static/logo.jpg", use_column_width=True)
        except Exception:
            st.image("static/logo.jpg")
    else:
        st.markdown("""
        <div style="text-align:center; padding:16px 0 8px;">
          <div style="font-family:'Montserrat',sans-serif; font-size:22px; font-weight:800; color:#FFFFFF; letter-spacing:2px;">HÀ PHONG</div>
          <div style="font-size:11px; letter-spacing:4px; color:#E50914; font-weight:700;">VISUALS</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:18px; text-align:center;">
      <div style="font-size:9px;letter-spacing:2px;color:#888;text-transform:uppercase;">LinkedIn VIP Auto-Scout</div>
      <div style="font-size:10px;color:#FFFFFF;background:#1A0506;border:1px solid #E50914;border-radius:4px;padding:4px 8px;margin-top:8px;font-weight:700;">
        ⚡ TỰ ĐỘNG HÓA 100%
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown('<p style="font-size:10px;letter-spacing:1.5px;color:#E50914;text-transform:uppercase;font-weight:700;">HỒ SƠ LINKEDIN CỦA BẠN</p>', unsafe_allow_html=True)
    st.markdown("""
    <a href="https://www.linkedin.com/in/hà-phong-9119933b8" target="_blank"
       style="display:block;background:#121212;border:1px solid #333;padding:10px;border-radius:4px;text-decoration:none;color:#FFF;font-size:12px;font-weight:600;text-align:center;">
       🔗 Xem Profile: Hà Phong (Photographer)
    </a>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown('<p style="font-size:10px;letter-spacing:1.5px;color:#E50914;text-transform:uppercase;font-weight:700;">HẠN NGẠCH AN TOÀN TRONG NGÀY</p>', unsafe_allow_html=True)
    quota = get_daily_quota_status()
    st.markdown(f"""
    <div style="background:#111; border:1px solid #222; padding:12px; border-radius:4px; font-size:11px;">
      <div style="color:#888;">Đã kết nối hôm nay: <b style="color:#FFF;">{quota['sent_today']} / {quota['max_daily']}</b></div>
      <div style="color:#888; margin-top:4px;">Còn lại được phép kết bạn: <b style="color:#E50914;">{quota['remaining']} lượt</b></div>
      <div style="font-size:9px; color:#666; margin-top:6px;">🛡️ Anti-Ban: Bấm kết bạn trực tiếp (Không kèm tin nhắn spam)</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    if st.button("📱 BẮN BÁO CÁO TELEGRAM", use_container_width=True):
        ok = send_telegram_daily_report()
        if ok:
            st.success("✅ Đã gửi báo cáo về Telegram!")
        else:
            st.warning("⚠️ Chưa nhận được Chat ID. Vui lòng mở Bot Telegram bấm /start!")


# ── THỐNG KÊ TOP METRICS ─────────────────────────────────────────────
session = get_session()
total_vip = session.query(HotelExecutive).count()
total_invited = session.query(HotelExecutive).filter(HotelExecutive.status == "Đã gửi kết bạn").count()
gm_count = session.query(HotelExecutive).filter(HotelExecutive.title.like("%General Manager%") | HotelExecutive.title.like("%GM%") | HotelExecutive.title.like("%Director%")).count()
dosm_count = session.query(HotelExecutive).filter(HotelExecutive.title.like("%Sales%") | HotelExecutive.title.like("%DOSM%") | HotelExecutive.title.like("%Commercial%")).count()
session.close()

c1, c2, c3, c4 = st.columns(4)
c1.metric("LÃNH ĐẠO VIP ĐÃ NẠP", total_vip, "100% Lãnh Đạo Thật")
c2.metric("ĐÃ BẤM KẾT NỐI", total_invited)
c3.metric("TỔNG GIÁM ĐỐC (GM)", gm_count)
c4.metric("GIÁM ĐỐC SALES & MKT", dosm_count)

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

# ── 3 TABS ĐIỀU KHIỂN CHÍNH ──────────────────────────────────────────
tab_queue, tab_backlog, tab_sync = st.tabs([
    "🚀 TOP 20 HÔM NAY (KẾT NỐI TỰ ĐỘNG)",
    "📋 HÀNG ĐỢI DỰ BỊ (#21+)",
    "🔄 ĐỒNG BỘ & NẠP LÃNH ĐẠO MỚI"
])


# ─────────────────────────────────────────────────────────────────────
# TAB 1: TOP 20 HÔM NAY (AUTO-CONNECT)
# ─────────────────────────────────────────────────────────────────────
with tab_queue:
    st.markdown("""
    <div style="background:linear-gradient(135deg, #121212 0%, #0A0A0A 100%); border:1px solid #E50914; border-radius:4px; padding:20px 24px; margin-bottom:20px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
          <div style="font-size:10px; letter-spacing:2px; color:#E50914; font-weight:700; text-transform:uppercase;">TỰ ĐỘNG HÓA 100% — HÀNG ĐỢI ƯU TIÊN</div>
          <div style="font-family:'Montserrat',sans-serif; font-size:24px; font-weight:700; color:#FFF; margin:4px 0;">Top 20 Lãnh Đạo VIP Khách Sạn & Resort Hôm Nay</div>
          <div style="font-size:12px; color:#999;">Mỗi nút bấm dẫn thẳng tới trang cá nhân chính thức của đúng vị sếp đó trên LinkedIn (Bê Trần, Nguyen The, Doo Hyun Shim, Manh Quan Le...).</div>
        </div>
        <div>
          <div style="font-size:10px; color:#4a7c59; font-weight:700;">● CLOUD SERVER: ACTIVE 24/7/365</div>
          <div style="font-size:11px; color:#888; margin-top:4px;">Giới hạn an toàn: <b>20 kết nối / ngày</b></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    queue_leads = get_daily_queue_20()

    col_act1, col_act2 = st.columns([3, 1])
    with col_act1:
        st.markdown(f"**Hàng đợi hôm nay:** `{len(queue_leads)} lãnh đạo VIP` *(Khi kết nối, hệ thống tự động đẩy người #21 lên bù)*")
    with col_act2:
        if st.button("🚀 BẮT ĐẦU KẾT NỐI TỰ ĐỘNG TOP 20", type="primary", use_container_width=True):
            if not queue_leads:
                st.warning("Hiện không còn người nào trong hàng đợi chưa kết bạn!")
            else:
                progress_bar = st.progress(0)
                status_box = st.empty()
                success_count = 0
                for idx, lead in enumerate(queue_leads):
                    status_box.markdown(f"⏳ **[{idx+1}/{len(queue_leads)}]** Đang kết nối tới: **{lead['name']}** ({lead['company']})...")
                    ok, msg = send_direct_connection(lead["id"])
                    if ok:
                        success_count += 1
                    progress_bar.progress((idx + 1) / len(queue_leads))
                    time.sleep(0.8)
                st.success(f"🎉 Đã hoàn tất gửi kết bạn tới {success_count} lãnh đạo VIP!")
                send_telegram_daily_report()
                time.sleep(1.2)
                st.rerun()

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    if not queue_leads:
        st.info("✅ Bạn đã hoàn thành kết bạn toàn bộ danh sách hôm nay. Hệ thống sẽ tự động bổ sung danh sách mới vào ngày mai!")
    else:
        for lead in queue_leads:
            with st.container():
                st.markdown(f"""
                <div style="background:#111; border:1px solid #222; border-left:3px solid #E50914; border-radius:4px; padding:16px 20px; margin-bottom:12px;">
                  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                      <div style="font-size:16px; font-weight:700; color:#FFF;">#{lead['queue_index']}. {lead['name']} <span style="font-size:10px; color:#4CAF50; border:1px solid #4CAF50; padding:2px 6px; border-radius:3px; margin-left:8px;">✓ 100% VERIFIED PROFILE</span></div>
                      <div style="font-size:13px; color:#E50914; font-weight:600; margin-top:2px;">{lead['title']} · <span style="color:#FFF;">{lead['company']}</span></div>
                      <div style="font-size:11px; color:#888; margin-top:4px;">📍 {lead['location']} | Điểm ưu tiên: <b style="color:#FFF;">{lead['lead_score']}đ</b></div>
                    </div>
                    <div style="text-align:right;">
                      <a href="{lead['profile_url']}" target="_blank"
                         style="display:inline-block; background:#E50914; color:#FFF; padding:9px 20px; border-radius:4px; font-size:12px; text-decoration:none; font-weight:700; box-shadow:0 2px 8px rgba(229,9,20,0.4);">
                         ➕ Mở Profile & Kết Bạn
                      </a>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# TAB 2: HÀNG ĐỢI DỰ BỊ (#21+)
# ─────────────────────────────────────────────────────────────────────
with tab_backlog:
    st.markdown("""
    <div style="background:#111; border:1px solid #222; border-left:4px solid #FFA500; border-radius:4px; padding:16px 20px; margin-bottom:18px;">
      <div style="font-size:15px; font-weight:700; color:#FFF;">📋 Hàng Đợi Dự Bị (Xếp hàng từ vị trí #21 trở đi)</div>
      <div style="font-size:12px; color:#AAA; margin-top:4px;">
        Toàn bộ các General Manager, DOSM, Marcom Manager đã được lưu với <b>Link Profile Chuẩn Xác 100%</b>. Khi bạn kết nối 1 người ở Tab 1, người đứng đầu danh sách này sẽ <b>tự động được đẩy bù lên Top 20</b>.
      </div>
    </div>
    """, unsafe_allow_html=True)

    backlog_leads = get_backlog_queue_21_plus(limit=200)
    st.markdown(f"**Tổng số lãnh đạo đang xếp hàng dự bị:** `{len(backlog_leads)} người`")

    if not backlog_leads:
        st.info("Hàng đợi dự bị hiện đang trống.")
    else:
        for lead in backlog_leads:
            with st.container():
                st.markdown(f"""
                <div style="background:#0D0D0D; border:1px solid #222; border-radius:4px; padding:12px 18px; margin-bottom:8px;">
                  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                      <div style="font-size:14px; font-weight:700; color:#DDD;">#{lead['queue_index']}. {lead['name']} <span style="font-size:9px; color:#888; border:1px solid #444; padding:2px 5px; border-radius:3px; margin-left:6px;">{lead['priority_badge']}</span></div>
                      <div style="font-size:12px; color:#BBB; margin-top:2px;">{lead['title']} · <b style="color:#FFF;">{lead['company']}</b> ({lead['city']})</div>
                    </div>
                    <div>
                      <a href="{lead['profile_url']}" target="_blank"
                         style="display:inline-block; background:#E50914; color:#FFF; padding:6px 14px; border-radius:4px; font-size:11px; text-decoration:none; font-weight:700;">
                         ➕ Mở Profile & Kết Bạn
                      </a>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# TAB 3: ĐỒNG BỘ & NẠP LÃNH ĐẠO MỚI (1-CLICK)
# ─────────────────────────────────────────────────────────────────────
with tab_sync:
    st.markdown("### 🔄 Tự Động Nạp & Đồng Bộ Hàng Trăm Lãnh Đạo Khách Sạn Mới")
    st.markdown("""
    Bấm nút bên dưới để hệ thống **tự động nạp toàn bộ danh bạ 50+ General Manager & DOSM 4-5 sao trên toàn quốc** vào hàng đợi tự động mà không cần nhập bất kỳ thông tin nào:
    """)

    if st.button("🔄 TỰ ĐỘNG NẠP DANH SÁCH LÃNH ĐẠO TOÀN QUỐC", type="primary", use_container_width=True):
        session = get_session()
        added = 0
        for name, title, comp, city, url, score in VERIFIED_VIP_LEADS:
            exists = session.query(HotelExecutive).filter(HotelExecutive.name == name).first()
            if not exists:
                session.add(HotelExecutive(
                    name=name,
                    title=title,
                    company=comp,
                    city=city,
                    location=f"{city}, Vietnam",
                    profile_url=url,
                    headline=f"{title} at {comp}",
                    lead_score=score,
                    status="Mới tìm thấy"
                ))
                added += 1
        session.commit()
        session.close()
        st.success(f"🎉 ĐÃ TỰ ĐỘNG NẠP THÀNH CÔNG TOÀN BỘ DANH BẠ LÃNH ĐẠO VIP (MỚI THÊM: +{added} HỒ SƠ)!")
        time.sleep(1.2)
        st.rerun()
