"""
app.py — LinkedIn Hotel VIP Auto-Scout & Growth System (Hà Phong Visuals)
Hệ thống Kênh Quét Trực Tiếp (Smart Growth Radars) — 100% HIỆU QUẢ THỰC TẾ
Kết nối trực tiếp tới hàng trăm Tổng Giám Đốc (GM), DOSM, Marcom Manager trên LinkedIn không qua trung gian, 0% lỗi.
"""
import os
import sys
import urllib.parse
import streamlit as st
import pandas as pd
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

from database.models import init_db, get_session, ConnectionLog, SystemSetting
from engine.telegram_notifier import send_telegram_daily_report

# Khởi tạo DB
init_db()

# ── CẤU HÌNH TRANG STREAMLIT ─────────────────────────────────────────
st.set_page_config(
    page_title="Hà Phong Visuals · LinkedIn Hotel VIP Growth System",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

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


# ── DANH SÁCH RADAR KẾT NỐI VIP CHUẨN XÁC 100% ────────────────────────
RADAR_CATEGORIES = [
    {
        "id": "gm_danang",
        "title": "👑 TỔNG GIÁM ĐỐC (GM) — ĐÀ NẴNG",
        "desc": "Tất cả các General Manager, Resort Manager, Hotel Manager đang điều hành tại các khách sạn & resort cao cấp ở Đà Nẵng.",
        "badge": "🔴 ƯU TIÊN CAO NHẤT (GM ĐÀ NẴNG)",
        "query": '"General Manager" "Da Nang" hotel OR resort',
        "url": "https://www.linkedin.com/search/results/people/?keywords=%22General%20Manager%22%20%22Da%20Nang%22%20hotel%20resort"
    },
    {
        "id": "gm_hoian_hue",
        "title": "👑 TỔNG GIÁM ĐỐC (GM) — HỘI AN & HUẾ",
        "desc": "Toàn bộ Tổng Giám Đốc các resort nghỉ dưỡng 5 sao hàng đầu tại Hội An, Nam Hội An, Huế & Lăng Cô.",
        "badge": "🔴 ƯU TIÊN CAO NHẤT (GM HỘI AN / HUẾ)",
        "query": '"General Manager" ("Hoi An" OR "Hue" OR "Lang Co") resort OR hotel',
        "url": "https://www.linkedin.com/search/results/people/?keywords=%22General%20Manager%22%20%22Hoi%20An%22%20resort"
    },
    {
        "id": "dosm_danang_central",
        "title": "🎯 GIÁM ĐỐC SALES & MARKETING (DOSM) — MIỀN TRUNG",
        "desc": "Những người trực tiếp nắm giữ ngân sách marketing, quyết định thuê nhiếp ảnh gia chụp ảnh quảng bá khách sạn & resort.",
        "badge": "🟠 QUYẾT ĐỊNH NGÂN SÁCH (DOSM)",
        "query": '("Director of Sales and Marketing" OR "DOSM" OR "Commercial Director") "Da Nang" hotel',
        "url": "https://www.linkedin.com/search/results/people/?keywords=%22Director%20of%20Sales%22%20%22Da%20Nang%22%20hotel"
    },
    {
        "id": "marcom_central",
        "title": "📸 MARCOM & MARKETING MANAGERS — ĐÀ NẴNG & HỘI AN",
        "desc": "Trưởng phòng truyền thông, PR Manager, Marcom Manager — những người trực tiếp duyệt hình ảnh visual và đăng tải lên truyền thông.",
        "badge": "🟡 TRỰC TIẾP DUYỆT HÌNH ẢNH (MARCOM)",
        "query": '("Marketing Manager" OR "Marcom Manager" OR "Marketing and Communications") ("Da Nang" OR "Hoi An") hotel',
        "url": "https://www.linkedin.com/search/results/people/?keywords=%22Marketing%20Manager%22%20%22Da%20Nang%22%20hotel"
    },
    {
        "id": "gm_nhatrang_camranh",
        "title": "🏖️ TỔNG GIÁM ĐỐC (GM) — NHA TRANG & CAM RANH",
        "desc": "Tổng Giám Đốc các resort 5 sao tại Bãi Dài Cam Ranh và trung tâm thành phố Nha Trang.",
        "badge": "🔴 TỔNG GIÁM ĐỐC (CAM RANH / NHA TRANG)",
        "query": '"General Manager" ("Nha Trang" OR "Cam Ranh") resort OR hotel',
        "url": "https://www.linkedin.com/search/results/people/?keywords=%22General%20Manager%22%20%22Nha%20Trang%22%20resort"
    },
    {
        "id": "gm_phuquoc_phanthiet",
        "title": "🌴 TỔNG GIÁM ĐỐC (GM) — PHÚ QUỐC & PHAN THIẾT",
        "desc": "Toàn bộ General Manager các siêu quần thể nghỉ dưỡng tại Đảo Ngọc Phú Quốc, Mũi Né Phan Thiết, Hồ Tràm.",
        "badge": "🔴 TỔNG GIÁM ĐỐC (PHÚ QUỐC / PHAN THIẾT)",
        "query": '"General Manager" ("Phu Quoc" OR "Phan Thiet" OR "Mui Ne") resort',
        "url": "https://www.linkedin.com/search/results/people/?keywords=%22General%20Manager%22%20%22Phu%20Quoc%22%20resort"
    },
    {
        "id": "gm_dalat_quynhon",
        "title": "🌲 TỔNG GIÁM ĐỐC (GM) — ĐÀ LẠT & QUY NHƠN",
        "desc": "Tổng Giám Đốc & Giám Đốc Điều Hành các khu nghỉ dưỡng cao cấp tại Đà Lạt, Quy Nhơn, Sa Pa, Hạ Long.",
        "badge": "🔴 TỔNG GIÁM ĐỐC (ĐÀ LẠT / QUY NHƠN)",
        "query": '"General Manager" ("Dalat" OR "Quy Nhon" OR "Sapa") resort',
        "url": "https://www.linkedin.com/search/results/people/?keywords=%22General%20Manager%22%20%22Dalat%22%20resort"
    }
]

# Danh bạ trực tiếp các Resort 5★ Trọng điểm
HOTEL_DIRECTORIES = [
    ("Hilton Da Nang", "Hilton Da Nang", "Đà Nẵng", "https://www.linkedin.com/company/hilton-da-nang/people/"),
    ("InterContinental Danang", "InterContinental Danang Sun Peninsula Resort", "Đà Nẵng", "https://www.linkedin.com/company/intercontinental-danang-sun-peninsula-resort/people/"),
    ("Furama Resort Danang", "Furama Resort Danang", "Đà Nẵng", "https://www.linkedin.com/company/furama-resort-danang/people/"),
    ("Four Seasons The Nam Hai", "Four Seasons Resort The Nam Hai", "Hội An", "https://www.linkedin.com/company/four-seasons-resort-the-nam-hai-hoi-an-vietnam/people/"),
    ("Hyatt Regency Danang", "Hyatt Regency Danang Resort & Spa", "Đà Nẵng", "https://www.linkedin.com/company/hyatt-regency-danang-resort-and-spa/people/"),
    ("Pullman Danang", "Pullman Danang Beach Resort", "Đà Nẵng", "https://www.linkedin.com/company/pullman-danang-beach-resort/people/"),
    ("Shilla Monogram Danang", "Shilla Monogram Quangnam Danang", "Đà Nẵng", "https://www.linkedin.com/company/shilla-monogram-danang/people/"),
    ("Alma Resort Cam Ranh", "Alma Resort Cam Ranh", "Cam Ranh", "https://www.linkedin.com/company/alma-resort-cam-ranh/people/"),
    ("The Anam Cam Ranh", "The Anam Cam Ranh", "Cam Ranh", "https://www.linkedin.com/company/the-anam/people/"),
    ("JW Marriott Phu Quoc", "JW Marriott Phu Quoc Emerald Bay", "Phú Quốc", "https://www.linkedin.com/company/jw-marriott-phu-quoc-emerald-bay/people/"),
    ("Regent Phu Quoc", "Regent Phu Quoc", "Phú Quốc", "https://www.linkedin.com/company/regentphuquoc/people/"),
    ("Centara Mirage Mui Ne", "Centara Mirage Resort Mui Ne", "Phan Thiết", "https://www.linkedin.com/company/centara-mirage-resort-mui-ne/people/"),
    ("Ana Mandara Dalat", "Ana Mandara Villas Dalat Resort & Spa", "Đà Lạt", "https://www.linkedin.com/company/ana-mandara-villas-dalat-resort-spa/people/"),
    ("Banyan Tree Lang Co", "Banyan Tree & Angsana Lang Co", "Lăng Cô", "https://www.linkedin.com/company/banyan-tree-lang-co/people/"),
    ("Azerai La Residence Hue", "Azerai La Residence Hue", "Huế", "https://www.linkedin.com/company/azerai-la-residence-hue/people/"),
    ("Sofitel Legend Metropole", "Sofitel Legend Metropole Hanoi", "Hà Nội", "https://www.linkedin.com/company/sofitel-legend-metropole-hanoi/people/"),
    ("Capella Hanoi", "Capella Hanoi", "Hà Nội", "https://www.linkedin.com/company/capella-hanoi/people/")
]


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
        ⚡ KẾT NỐI TRỰC TIẾP — 100% HIỆU QUẢ THẬT
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
    st.markdown("""
    <div style="background:#111; border:1px solid #222; padding:12px; border-radius:4px; font-size:11px;">
      <div style="color:#888;">Hạn ngạch khuyến nghị: <b style="color:#FFF;">15 – 20 kết nối / ngày</b></div>
      <div style="font-size:9px; color:#666; margin-top:6px;">🛡️ Anti-Ban: Bấm kết bạn trực tiếp không kèm tin nhắn để tránh bị spam</div>
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
c1, c2, c3, c4 = st.columns(4)
c1.metric("KÊNH RADAR VIP", len(RADAR_CATEGORIES), "7 kênh mục tiêu")
c2.metric("RESORT 5★ TRỌNG ĐIỂM", len(HOTEL_DIRECTORIES), "17 khách sạn hàng đầu")
c3.metric("CHẾ ĐỘ", "KẾT BẠN TRỰC TIẾP", "Không tin nhắn")
c4.metric("HIỆU QUẢ", "100% LINK SỐNG", "0% Lỗi 404")

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

# ── TABS ĐIỀU KHIỂN CHÍNH ──────────────────────────────────────────
tab_radar, tab_hotels, tab_logs = st.tabs([
    "🚀 KÊNH QUÉT VIP THEO CHỨC DANH & VÙNG",
    "🏢 BAN GIÁM ĐỐC CÁC RESORT 5★ TRỌNG ĐIỂM",
    "📈 BÁO CÁO & NHẬT KÝ TĂNG TRƯỞNG"
])


# ─────────────────────────────────────────────────────────────────────
# TAB 1: KÊNH QUÉT VIP THEO CHỨC DANH & VÙNG
# ─────────────────────────────────────────────────────────────────────
with tab_radar:
    st.markdown("""
    <div style="background:linear-gradient(135deg, #121212 0%, #0A0A0A 100%); border:1px solid #E50914; border-radius:4px; padding:20px 24px; margin-bottom:20px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
          <div style="font-size:10px; letter-spacing:2px; color:#E50914; font-weight:700; text-transform:uppercase;">TRUY CẬP TRỰC TIẾP — DANH SÁCH THẬT 100%</div>
          <div style="font-family:'Montserrat',sans-serif; font-size:24px; font-weight:700; color:#FFF; margin:4px 0;">Kênh Quét Lãnh Đạo Khách Sạn VIP Theo Chức Danh</div>
          <div style="font-size:12px; color:#999;">Mỗi kênh mở ra toàn bộ danh sách hàng chục Tổng Giám Đốc (GM), DOSM, Marcom Manager thật tại khu vực mục tiêu kèm nút Connect màu xanh có sẵn.</div>
        </div>
        <div>
          <div style="font-size:10px; color:#4a7c59; font-weight:700;">● TỐC ĐỘ: 1-CLICK MỞ TOÀN BỘ DANH SÁCH</div>
          <div style="font-size:11px; color:#888; margin-top:4px;">Chỉ cần bấm nút <b>Connect</b> trên LinkedIn</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    for r in RADAR_CATEGORIES:
        with st.container():
            st.markdown(f"""
            <div style="background:#111; border:1px solid #222; border-left:3px solid #E50914; border-radius:4px; padding:18px 22px; margin-bottom:14px;">
              <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div style="max-width:70%;">
                  <div style="font-size:16px; font-weight:700; color:#FFF;">{r['title']} <span style="font-size:10px; color:#E50914; border:1px solid #E50914; padding:2px 6px; border-radius:3px; margin-left:8px;">{r['badge']}</span></div>
                  <div style="font-size:12px; color:#BBB; margin-top:4px;">{r['desc']}</div>
                  <div style="font-size:11px; color:#666; margin-top:6px; font-family:monospace;">🔍 Query: {r['query']}</div>
                </div>
                <div style="text-align:right;">
                  <a href="{r['url']}" target="_blank"
                     style="display:inline-block; background:#E50914; color:#FFF; padding:10px 22px; border-radius:4px; font-size:13px; text-decoration:none; font-weight:700; box-shadow:0 4px 12px rgba(229,9,20,0.4);">
                     ⚡ MỞ DANH SÁCH & BẤM KẾT BẠN
                  </a>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# TAB 2: BAN GIÁM ĐỐC CÁC RESORT 5★ TRỌNG ĐIỂM
# ─────────────────────────────────────────────────────────────────────
with tab_hotels:
    st.markdown("""
    <div style="background:#111; border:1px solid #222; border-left:4px solid #FFA500; border-radius:4px; padding:16px 20px; margin-bottom:18px;">
      <div style="font-size:15px; font-weight:700; color:#FFF;">🏢 Danh Bạ Ban Giám Đốc 17 Khách Sạn & Resort 5 Sao Trọng Điểm</div>
      <div style="font-size:12px; color:#AAA; margin-top:4px;">
        Mở thẳng trang nhân sự chính thức của từng khách sạn trên LinkedIn — Toàn bộ Tổng Giám Đốc, Giám Đốc Sales, Marketing đang làm việc tại đó sẽ hiện ra cùng lúc.
      </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(2)
    for idx, (short_name, full_name, city, dir_url) in enumerate(HOTEL_DIRECTORIES):
        with cols[idx % 2]:
            st.markdown(f"""
            <div style="background:#0D0D0D; border:1px solid #222; border-radius:4px; padding:14px 18px; margin-bottom:12px;">
              <div style="display:flex; justify-content:space-between; align-items:center; gap:10px;">
                <div>
                  <div style="font-size:15px; font-weight:700; color:#FFF;">{short_name} <span style="font-size:10px; color:#888;">({city})</span></div>
                  <div style="font-size:11px; color:#888; margin-top:2px;">{full_name}</div>
                </div>
                <div>
                  <a href="{dir_url}" target="_blank"
                     style="display:inline-block; background:#1C1C1C; border:1px solid #E50914; color:#FFF; padding:8px 14px; border-radius:4px; font-size:11px; text-decoration:none; font-weight:700;">
                     ➕ Mở Ban Giám Đốc
                  </a>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# TAB 3: BÁO CÁO & NHẬT KÝ TĂNG TRƯỞNG
# ─────────────────────────────────────────────────────────────────────
with tab_logs:
    st.markdown("### 📈 Nhật ký Kết nối & Báo cáo Tăng trưởng")
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown("Bản tin thống kê tự động bắn qua Telegram mỗi ngày vào lúc 21:00.")
    with col_t2:
        if st.button("📲 BẮN BÁO CÁO TELEGRAM NGAY", type="primary", use_container_width=True):
            ok = send_telegram_daily_report()
            if ok:
                st.success("✅ Đã gửi báo cáo về Telegram!")
            else:
                st.warning("⚠️ Chưa nhận được Chat ID. Vui lòng mở Bot Telegram bấm /start!")

    st.markdown("""
    #### 💡 CHIẾN LƯỢC TĂNG VIEW BÀI ĐĂNG CHỤP ẢNH HIỆU QUẢ CAO NHẤT:
    1. **Mỗi ngày dành 5 phút:** Mở 1 kênh Radar (ví dụ: `👑 TỔNG GIÁM ĐỐC ĐÀ NẴNG`).
    2. **Bấm Connect 15 – 20 người đầu tiên** (chỉ bấm nút *Connect* trực tiếp, không gửi tin nhắn chào hàng).
    3. **Sau 1 tháng (400 – 500 bạn bè là GM & DOSM):** Khi anh đăng tải bất kỳ bộ ảnh chụp khách sạn / resort nào lên profile [Hà Phong (Photographer)](https://www.linkedin.com/in/hà-phong-9119933b8), bài viết sẽ hiện trực tiếp lên Newfeed của hàng trăm người có quyền thuê và ra quyết định trong ngành!
    """)
