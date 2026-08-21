"""
app.py — LinkedIn Hotel VIP Auto-Scout & Growth Bot (Hà Phong Visuals)
Chế độ: CHỈ BẤM KẾT BẠN TRỰC TIẾP (DIRECT CONNECT — KHÔNG KÈM TIN NHẮN)
Tone thiết kế: Đen — Đỏ — Trắng đồng bộ nhận diện thương hiệu
Chạy: streamlit run app.py
"""
import os
import sys
import time
import pandas as pd
import socket

# Ép buộc Socket phân giải IPv4 trên Railway/Linux Container
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if family == 0 or family == socket.AF_UNSPEC:
        family = socket.AF_INET
    try:
        return _orig_getaddrinfo(host, port, family, type, proto, flags)
    except Exception:
        return _orig_getaddrinfo(host, port, 0, type, proto, flags)

socket.getaddrinfo = _ipv4_only_getaddrinfo

import streamlit as st
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import init_db, get_session, HotelExecutive, ConnectionLog, SystemSetting
from engine.linkedin_bot import (
    get_daily_quota_status, send_direct_connection, get_setting, set_setting
)

# ── CẤU HÌNH TRANG STREAMLIT ─────────────────────────────────────────
st.set_page_config(
    page_title="Hà Phong Visuals · LinkedIn Hotel Direct Connect Bot",
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
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stSlider label {
  color: #E50914 !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase !important;
}

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

/* Dataframe */
[data-testid="stDataFrame"] {
  border: 1px solid #222222 !important;
  border-radius: 4px !important;
}
.stDataFrame thead th {
  background: #141414 !important;
  color: #FFFFFF !important;
  font-weight: 600 !important;
  border-bottom: 2px solid #E50914 !important;
}
.stDataFrame tbody tr { background: #0A0A0A !important; }
.stDataFrame tbody tr:hover { background: #161616 !important; }
.stDataFrame tbody td { color: #E0E0E0 !important; }
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
      <div style="font-size:9px;letter-spacing:2px;color:#888;text-transform:uppercase;">LinkedIn Direct Connect Bot</div>
      <div style="font-size:10px;color:#FFFFFF;background:#1A0506;border:1px solid #E50914;border-radius:4px;padding:4px 8px;margin-top:8px;font-weight:700;">
        ⚡ CHẾ ĐỘ: KẾT BẠN TRỰC TIẾP
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
    st.markdown('<p style="font-size:10px;letter-spacing:1.5px;color:#E50914;text-transform:uppercase;font-weight:700;">KHU VỰC ƯU TIÊN</p>', unsafe_allow_html=True)
    selected_cities = st.multiselect(
        "Thành phố",
        options=["Đà Nẵng", "Hội An", "Huế", "Lăng Cô", "Nha Trang", "Phú Quốc", "Bình Thuận", "Quy Nhơn", "Đà Lạt"],
        default=["Đà Nẵng", "Hội An", "Huế"]
    )

    st.divider()
    st.markdown('<p style="font-size:10px;letter-spacing:1.5px;color:#E50914;text-transform:uppercase;font-weight:700;">HẠN NGẠCH AN TOÀN TRONG NGÀY</p>', unsafe_allow_html=True)
    quota = get_daily_quota_status()
    st.markdown(f"""
    <div style="background:#111; border:1px solid #222; padding:12px; border-radius:4px; font-size:11px;">
      <div style="color:#888;">Đã bấm hôm nay: <b style="color:#FFF;">{quota['sent_today']} / {quota['max_daily']}</b></div>
      <div style="color:#888; margin-top:4px;">Còn lại được phép kết bạn: <b style="color:#E50914;">{quota['remaining']} lượt</b></div>
      <div style="font-size:9px; color:#666; margin-top:6px;">🛡️ Anti-Ban: Giãn cách 30s – 90s/lượt</div>
    </div>
    """, unsafe_allow_html=True)


# ── THỐNG KÊ TOP METRICS ─────────────────────────────────────────────
session = get_session()
total_vip = session.query(HotelExecutive).count()
total_invited = session.query(HotelExecutive).filter(HotelExecutive.status == "Đã gửi kết bạn").count()
gm_count = session.query(HotelExecutive).filter(HotelExecutive.title.like("%General Manager%") | HotelExecutive.title.like("%GM%")).count()
dosm_count = session.query(HotelExecutive).filter(HotelExecutive.title.like("%Director%") | HotelExecutive.title.like("%DOSM%")).count()
marcom_count = session.query(HotelExecutive).filter(HotelExecutive.title.like("%Marketing%") | HotelExecutive.title.like("%Marcom%")).count()
session.close()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("TỔNG LÃNH ĐẠO VIP", total_vip)
c2.metric("ĐÃ BẤM KẾT BẠN", total_invited)
c3.metric("TỔNG GIÁM ĐỐC (GM)", gm_count)
c4.metric("GIÁM ĐỐC SALES & MKT", dosm_count)
c5.metric("MARCOM / MARKETING", marcom_count)

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

# ── 4 TABS ĐIỀU KHIỂN CHÍNH ──────────────────────────────────────────
tab_queue, tab_directory, tab_config, tab_history = st.tabs([
    "🚀 HÀNG ĐỢI HÔM NAY (TOP 20)",
    "👥 DANH BẠ LÃNH ĐẠO (ĐÃ QUÉT)",
    "⚙️ CẤU HÌNH & QUÉT MỚI",
    "📈 NHẬT KÝ & TĂNG TRƯỞNG"
])


# ─────────────────────────────────────────────────────────────────────
# TAB 1: HÀNG ĐỢI HÔM NAY (TOP 20 - DIRECT CONNECT)
# ─────────────────────────────────────────────────────────────────────
with tab_queue:
    st.markdown("""
    <div style="background:linear-gradient(135deg, #121212 0%, #0A0A0A 100%); border:1px solid #E50914; border-radius:4px; padding:20px 24px; margin-bottom:20px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
          <div style="font-size:10px; letter-spacing:2px; color:#E50914; font-weight:700; text-transform:uppercase;">KẾT BẠN TRỰC TIẾP — KHÔNG GỬI TIN NHẮN</div>
          <div style="font-family:'Montserrat',sans-serif; font-size:24px; font-weight:700; color:#FFF; margin:4px 0;">1-Click Direct Connect</div>
          <div style="font-size:12px; color:#999;">Tự động bấm kết bạn trực tiếp tới các General Manager, DOSM, Marcom Manager tại các resort & khách sạn 4–5★ hàng đầu.</div>
        </div>
        <div>
          <div style="font-size:10px; color:#4a7c59; font-weight:700;">● CHẾ ĐỘ: DIRECT CONNECT (FAST & SAFE)</div>
          <div style="font-size:11px; color:#888; margin-top:4px;">Giới hạn an toàn: <b>20 kết nối / ngày</b></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    session = get_session()
    # Lấy danh sách hàng đợi Top 20 ưu tiên chưa gửi
    query = session.query(HotelExecutive).filter(HotelExecutive.status == "Mới tìm thấy")
    if selected_cities:
        query = query.filter(HotelExecutive.city.in_(selected_cities))
    
    queue_leads = query.order_by(HotelExecutive.lead_score.desc()).limit(20).all()
    session.close()

    col_act1, col_act2 = st.columns([3, 1])
    with col_act1:
        st.markdown(f"**Danh sách đề xuất hôm nay:** `{len(queue_leads)} lãnh đạo cấp cao`")
    with col_act2:
        if st.button("🚀 BẮT ĐẦU BẤM KẾT BẠN TOP 20", type="primary", use_container_width=True):
            if not queue_leads:
                st.warning("Hiện không còn người nào trong hàng đợi chưa kết bạn!")
            else:
                progress_bar = st.progress(0)
                status_box = st.empty()
                success_count = 0
                
                for idx, lead in enumerate(queue_leads):
                    status_box.markdown(f"⏳ **[{idx+1}/{len(queue_leads)}]** Đang bấm kết bạn trực tiếp tới: **{lead.name}** ({lead.title} · {lead.company})...")
                    ok, msg = send_direct_connection(lead.id)
                    if ok:
                        success_count += 1
                    progress_bar.progress((idx + 1) / len(queue_leads))
                    time.sleep(1.0)
                
                st.success(f"🎉 ĐÃ HOÀN TẤT BẤM KẾT BẠN TRỰC TIẾP TỚI {success_count} LÃNH ĐẠO KHÁCH SẠN VIP!")
                time.sleep(1.5)
                st.rerun()

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    if not queue_leads:
        st.info("✅ Bạn đã kết bạn hết danh sách hiện tại trong ngày. Hãy chuyển sang Tab 'Cấu Hình & Quét Mới' để quét thêm người mới!")
    else:
        for idx, lead in enumerate(queue_leads):
            with st.container():
                st.markdown(f"""
                <div style="background:#111; border:1px solid #222; border-left:3px solid #E50914; border-radius:4px; padding:16px 20px; margin-bottom:12px;">
                  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                      <div style="font-size:16px; font-weight:700; color:#FFF;">#{idx+1}. {lead.name}</div>
                      <div style="font-size:13px; color:#E50914; font-weight:600; margin-top:2px;">{lead.title} · <span style="color:#FFF;">{lead.company}</span></div>
                      <div style="font-size:11px; color:#888; margin-top:4px;">📍 {lead.location} | Điểm ưu tiên: <b style="color:#FFF;">{lead.lead_score}đ</b></div>
                    </div>
                    <div style="text-align:right;">
                      <a href="{lead.profile_url}" target="_blank"
                         style="display:inline-block; background:#E50914; color:#FFF; padding:8px 18px; border-radius:4px; font-size:12px; text-decoration:none; font-weight:700;">
                         ➕ Bấm Kết Bạn Ngay
                      </a>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# TAB 2: DANH BẠ LÃNH ĐẠO (ĐÃ QUÉT)
# ─────────────────────────────────────────────────────────────────────
with tab_directory:
    st.markdown("### 👥 Toàn bộ Danh bạ Lãnh đạo Khách sạn 4–5★")
    
    session = get_session()
    all_execs = session.query(HotelExecutive).order_by(HotelExecutive.created_at.desc()).all()
    session.close()

    if not all_execs:
        st.info("Chưa có dữ liệu. Vui lòng quét thêm!")
    else:
        data = []
        for e in all_execs:
            data.append({
                "Họ & Tên": e.name,
                "Chức Vụ": e.title,
                "Khách Sạn / Resort": e.company,
                "Khu Vực": e.city,
                "Trạng Thái": e.status,
                "Điểm Ưu Tiên": f"{e.lead_score}đ",
                "Link Profile": e.profile_url
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────
# TAB 3: CẤU HÌNH & QUÉT MỚI
# ─────────────────────────────────────────────────────────────────────
with tab_config:
    st.markdown("### ⚙️ Cấu hình Hạn ngạch & Quét bổ sung")
    
    current_max = get_setting("max_daily_connections", "20")
    new_max = st.selectbox("Hạn ngạch kết bạn tối đa mỗi ngày (Khuyến nghị 15–20):", options=["10", "15", "20", "25"], index=2 if current_max=="20" else 1)
    
    if st.button("💾 LƯU HẠN NGẠCH", use_container_width=True):
        set_setting("max_daily_connections", new_max)
        st.success(f"Đã cập nhật hạn ngạch: {new_max} kết nối/ngày!")

    st.divider()
    st.markdown("#### 🔍 Quét bổ sung Lãnh đạo Khách sạn mới:")
    if st.button("🌐 QUÉT THÊM LÃNH ĐẠO GM/DOSM TỪ GOOGLE & LINKEDIN", type="primary", use_container_width=True):
        from engine.linkedin_scraper import scan_and_save_executives
        with st.spinner("Đang tìm kiếm trên mạng lưới dữ liệu..."):
            saved = scan_and_save_executives(selected_cities)
            st.success(f"🎉 Đã tìm thấy và bổ sung thêm +{saved} lãnh đạo khách sạn mới vào danh bạ!")
            time.sleep(1)
            st.rerun()


# ─────────────────────────────────────────────────────────────────────
# TAB 4: NHẬT KÝ & TĂNG TRƯỞNG
# ─────────────────────────────────────────────────────────────────────
with tab_history:
    st.markdown("### 📈 Nhật ký Kết nối & Tăng trưởng Mạng lưới")
    session = get_session()
    logs = session.query(ConnectionLog).order_by(ConnectionLog.sent_at.desc()).limit(100).all()
    session.close()

    if not logs:
        st.info("Chưa có lịch sử kết bạn nào được thực hiện.")
    else:
        log_data = []
        for l in logs:
            log_data.append({
                "Thời Gian": l.sent_at.strftime("%d/%m/%Y %H:%M"),
                "Người Nhận": l.recipient_name,
                "Chức Vụ": l.recipient_title,
                "Phương Thức": "Bấm Kết Bạn Trực Tiếp (Không gửi tin)",
                "Trạng Thái": l.status
            })
        st.dataframe(pd.DataFrame(log_data), use_container_width=True)
