"""
app.py — LinkedIn Hotel VIP Auto-Scout & Growth Bot (Hà Phong Visuals)
Hệ thống Hàng Đợi 2 Tầng & Bộ Bóc Tách Hàng Loạt Tự Động 100%
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
from engine.linkedin_bot import (
    get_daily_quota_status, send_direct_connection, get_setting, set_setting
)
from engine.priority_queue import get_daily_queue_20, get_backlog_queue_21_plus
from engine.telegram_notifier import send_telegram_daily_report
from engine.linkedin_api import bulk_parse_and_save_leads
from scheduler.heartbeat_tracker import get_heartbeat_status, log_activity

# ── CẤU HÌNH TRANG STREAMLIT ─────────────────────────────────────────
st.set_page_config(
    page_title="Hà Phong Visuals · LinkedIn VIP Growth Bot",
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
      <div style="font-size:9px;letter-spacing:2px;color:#888;text-transform:uppercase;">LinkedIn VIP Growth System</div>
      <div style="font-size:10px;color:#FFFFFF;background:#1A0506;border:1px solid #E50914;border-radius:4px;padding:4px 8px;margin-top:8px;font-weight:700;">
        ⚡ 100% LINK PROFILE THẬT
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
session.close()

c1, c2, c3, c4 = st.columns(4)
c1.metric("HỒ SƠ VIP TRONG DANH BẠ", total_vip, "100% Link Thật")
c2.metric("ĐÃ BẤM KẾT NỐI", total_invited)
c3.metric("HÀNG ĐỢI TOP 20", min(20, total_vip))
c4.metric("DỰ BỊ (#21+)", max(0, total_vip - 20))

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

# ── 3 TABS ĐIỀU KHIỂN CHÍNH ──────────────────────────────────────────
tab_queue, tab_backlog, tab_bulk, tab_grabber = st.tabs([
    "🚀 TOP 20 HÔM NAY",
    "📋 DỰ BỊ (#21+)",
    "📥 DÁN HÀNG LOẠT (BULK AUTO-IMPORT)",
    "⚡ CÀO 1-CLICK TỪ TRÌNH DUYỆT"
])


# ─────────────────────────────────────────────────────────────────────
# TAB 1: TOP 20 HÔM NAY
# ─────────────────────────────────────────────────────────────────────
with tab_queue:
    st.markdown("""
    <div style="background:linear-gradient(135deg, #121212 0%, #0A0A0A 100%); border:1px solid #E50914; border-radius:4px; padding:20px 24px; margin-bottom:20px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
          <div style="font-size:10px; letter-spacing:2px; color:#E50914; font-weight:700; text-transform:uppercase;">100% LINK PROFILE GỐC TỪNG NGƯỜI CỤ THỂ</div>
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
        if st.button("🚀 BẮT ĐẦU KẾT NỐI TOP 20", type="primary", use_container_width=True):
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
                    time.sleep(1.0)
                st.success(f"🎉 Đã hoàn tất gửi kết bạn tới {success_count} lãnh đạo VIP!")
                send_telegram_daily_report()
                time.sleep(1.5)
                st.rerun()

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    if not queue_leads:
        st.info("Hàng đợi hiện đang trống. Hãy qua Tab 'Dán Hàng Loạt' hoặc 'Cào 1-Click' để nạp thêm!")
    else:
        for lead in queue_leads:
            with st.container():
                st.markdown(f"""
                <div style="background:#111; border:1px solid #222; border-left:3px solid #E50914; border-radius:4px; padding:16px 20px; margin-bottom:12px;">
                  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                      <div style="font-size:16px; font-weight:700; color:#FFF;">#{lead['queue_index']}. {lead['name']} <span style="font-size:10px; color:#4CAF50; border:1px solid #4CAF50; padding:2px 6px; border-radius:3px; margin-left:8px;">✓ 100% VERIFIED PROFILE</span></div>
                      <div style="font-size:13px; color:#E50914; font-weight:600; margin-top:2px;">{lead['title']} · <span style="color:#FFF;">{lead['company']}</span></div>
                      <div style="font-size:11px; color:#888; margin-top:4px;">📍 {lead['location']} | Link: <code style="color:#FFF;">{lead['profile_url']}</code></div>
                    </div>
                    <div style="text-align:right;">
                      <a href="{lead['profile_url']}" target="_blank"
                         style="display:inline-block; background:#E50914; color:#FFF; padding:9px 20px; border-radius:4px; font-size:12px; text-decoration:none; font-weight:700; box-shadow:0 2px 8px rgba(229,9,20,0.4);">
                         ➕ Mở Profile & Bấm Connect
                      </a>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# TAB 2: DỰ BỊ (#21+)
# ─────────────────────────────────────────────────────────────────────
with tab_backlog:
    st.markdown("""
    <div style="background:#111; border:1px solid #222; border-left:4px solid #FFA500; border-radius:4px; padding:16px 20px; margin-bottom:18px;">
      <div style="font-size:15px; font-weight:700; color:#FFF;">📋 Hàng Đợi Dự Bị (Xếp hàng từ vị trí #21 trở đi)</div>
      <div style="font-size:12px; color:#AAA; margin-top:4px;">
        Toàn bộ các General Manager, DOSM, Marcom Manager đã được lưu với <b>Link Profile Cá Nhân Chính Xác 100%</b>. Khi bạn kết nối 1 người ở Tab 1, người đứng đầu danh sách này sẽ <b>tự động được đẩy bù lên Top 20</b>.
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
                         ➕ Mở Profile & Connect
                      </a>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# TAB 3: DÁN HÀNG LOẠT (BULK AUTO-IMPORT)
# ─────────────────────────────────────────────────────────────────────
with tab_bulk:
    st.markdown("### 📥 Dán Hàng Loạt Danh Sách Profile (Bóc Tách Tự Động 1 Giây)")
    st.markdown("""
    Anh có thể dán bất kỳ danh sách link nào (hoặc copy toàn bộ trang tìm kiếm LinkedIn dán vào đây), hệ thống sẽ **tự động bóc tách 100% đường link sạch** và nạp thẳng vào hàng đợi!
    """)

    with st.form("bulk_import_form"):
        bulk_city = st.selectbox("Chọn Khu Vực Cho Danh Sách Này:", ["Đà Nẵng", "Hội An", "Huế", "Nha Trang", "Phú Quốc", "Phan Thiết", "Đà Lạt"])
        raw_text_input = st.text_area(
            "Dán danh sách các đường link hoặc văn bản tìm kiếm vào đây:",
            height=200,
            placeholder="https://www.linkedin.com/in/b%C3%AA-tr%E1%BA%A7n-816a52127\nhttps://www.linkedin.com/in/nguyen-the-80582b56/\nhttps://www.linkedin.com/in/dibi-le-b61239198/..."
        )
        submit_bulk = st.form_submit_button("⚡ BÓC TÁCH VÀ NẠP HÀNG LOẠT VÀO HÀNG ĐỢI", type="primary", use_container_width=True)

        if submit_bulk:
            saved, msg = bulk_parse_and_save_leads(raw_text_input, default_city=bulk_city)
            if saved > 0:
                st.success(msg)
                time.sleep(1.5)
                st.rerun()
            else:
                st.warning(msg)


# ─────────────────────────────────────────────────────────────────────
# TAB 4: CÀO 1-CLICK TỪ TRÌNH DUYỆT (GRABBER SCRIPT)
# ─────────────────────────────────────────────────────────────────────
with tab_grabber:
    st.markdown("### ⚡ Cào Tự Động 1-Click Trực Tiếp Trên Trình Duyệt LinkedIn")
    st.markdown("""
    Khi anh đang mở tab tìm kiếm trên LinkedIn (như trên màn hình anh đang mở), chỉ cần chạy lệnh 1 dòng này để **tự động lấy toàn bộ link sạch của tất cả sếp lớn trên trang trong 0.1 giây**:
    
    #### 🛠️ CÁCH SỬ DỤNG 1 LẦN DUY NHẤT:
    1. Mở tab **LinkedIn Search** trên Chrome.
    2. Bấm phím **`F12`** ➔ Chọn tab **`Console`**.
    3. Dán đoạn mã bên dưới vào và bấm **`Enter`**:
    """)

    st.code("""
// LẤY TOÀN BỘ LINK PROFILE SẠCH TRÊN TRANG LINKEDIN ĐANG MỞ
var links = Array.from(document.querySelectorAll('a[href*="/in/"]'))
  .map(a => a.href.split('?')[0])
  .filter((v, i, a) => a.indexOf(v) === i && !v.endsWith('/in/'));
console.log(links.join('\\n'));
copy(links.join('\\n'));
alert('🎉 ĐÃ COPY ' + links.length + ' LINK PROFILE VÀO BỘ NHỚ TẠM! Hãy chuyển sang Tab Dán Hàng Loạt để nạp!');
    """, language="javascript")

    st.caption("Sau khi chạy xong, danh sách link sẽ tự động được lưu vào bộ nhớ tạm (Clipboard), anh chỉ cần qua Tab 'Dán Hàng Loạt' bấm Cmd+V (Paste) là xong!")
