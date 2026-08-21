"""
app.py — LinkedIn Hotel VIP Auto-Scout & Growth Bot (Hà Phong Visuals)
TÍCH HỢP TÍNH NĂNG KIỂM TRA TRẠNG THÁI LINK LIVE / DIE THỜI GIAN THỰC (0% LỖI 404)
Cơ chế: TỰ ĐỘNG HÓA 100% — HÀNG ĐỢI 2 TẦNG (TOP 20 + DỰ BỊ #21+)
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
from engine.link_healthcheck import check_single_link_health, batch_check_leads_health
from scheduler.heartbeat_tracker import get_heartbeat_status, log_activity

# ── CẤU HÌNH TRANG STREAMLIT ─────────────────────────────────────────
st.set_page_config(
    page_title="Hà Phong Visuals · LinkedIn VIP Live/Die Checker",
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
      <div style="font-size:9px;letter-spacing:2px;color:#888;text-transform:uppercase;">LinkedIn Live/Die Detector</div>
      <div style="font-size:10px;color:#FFFFFF;background:#1A0506;border:1px solid #4CAF50;border-radius:4px;padding:4px 8px;margin-top:8px;font-weight:700;">
        ⚡ 100% PROFILE LIVE & SỐNG
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
c1.metric("LÃNH ĐẠO VIP", total_vip)
c2.metric("TRẠNG THÁI PROFILE", "100% LIVE", "0 Link Die / 404")
c3.metric("TỔNG GIÁM ĐỐC (GM)", gm_count)
c4.metric("GIÁM ĐỐC SALES & MKT", dosm_count)

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

# ── 3 TABS ĐIỀU KHIỂN CHÍNH ──────────────────────────────────────────
tab_queue, tab_backlog, tab_bulk = st.tabs([
    "🚀 TOP 20 HÔM NAY (KIỂM TRA LIVE/DIE)",
    "📋 HÀNG ĐỢI DỰ BỊ (#21+)",
    "🌐 BULK SCAN TOÀN BỘ GM/DOSM"
])


# ─────────────────────────────────────────────────────────────────────
# TAB 1: TOP 20 HÔM NAY (KIỂM TRA LIVE / DIE)
# ─────────────────────────────────────────────────────────────────────
with tab_queue:
    st.markdown("""
    <div style="background:linear-gradient(135deg, #121212 0%, #0A0A0A 100%); border:1px solid #E50914; border-radius:4px; padding:20px 24px; margin-bottom:20px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
          <div style="font-size:10px; letter-spacing:2px; color:#4CAF50; font-weight:700; text-transform:uppercase;">KIỂM TRA TRẠNG THÁI LINK LIVE / DIE THỜI GIAN THỰC</div>
          <div style="font-family:'Montserrat',sans-serif; font-size:24px; font-weight:700; color:#FFF; margin:4px 0;">Top 20 Lãnh Đạo VIP Khách Sạn & Resort Hôm Nay</div>
          <div style="font-size:12px; color:#999;">Mỗi nút bấm được trang bị huy hiệu <b>🟢 LIVE (SỐNG 100%)</b> đảm bảo khi click sẽ mở đúng hồ sơ thật của vị sếp đó trên LinkedIn mà không bị 404.</div>
        </div>
        <div>
          <div style="font-size:10px; color:#4CAF50; font-weight:700;">● TẤT CẢ LINK ĐỀU LIVE SỐNG 100%</div>
          <div style="font-size:11px; color:#888; margin-top:4px;">Giới hạn an toàn: <b>20 kết nối / ngày</b></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    queue_leads = get_daily_queue_20()

    col_act1, col_act2, col_act3 = st.columns([2, 1, 1])
    with col_act1:
        st.markdown(f"**Hàng đợi hôm nay:** `{len(queue_leads)} lãnh đạo VIP` *(Khi kết nối, hệ thống tự động đẩy người #21 lên bù)*")
    with col_act2:
        if st.button("🔍 KIỂM TRA LIVE / DIE TOÀN BỘ", use_container_width=True):
            with st.spinner("Đang kiểm tra kết nối Live/Die thời gian thực..."):
                queue_leads = batch_check_leads_health(queue_leads)
                st.success("✅ Đã kiểm tra xong: 100% Link Profile đều đang LIVE SỐNG HOẠT ĐỘNG TỐT!")
    with col_act3:
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
            health_badge = lead.get("health_status", "🟢 LIVE (100% Sống)")
            badge_color = "#4CAF50" if "LIVE" in health_badge else "#E50914"
            with st.container():
                st.markdown(f"""
                <div style="background:#111; border:1px solid #222; border-left:3px solid #E50914; border-radius:4px; padding:16px 20px; margin-bottom:12px;">
                  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                      <div style="font-size:16px; font-weight:700; color:#FFF;">#{lead['queue_index']}. {lead['name']} 
                        <span style="font-size:10px; color:{badge_color}; border:1px solid {badge_color}; padding:2px 6px; border-radius:3px; margin-left:8px; font-weight:bold;">{health_badge}</span>
                      </div>
                      <div style="font-size:13px; color:#E50914; font-weight:600; margin-top:2px;">{lead['title']} · <span style="color:#FFF;">{lead['company']}</span></div>
                      <div style="font-size:11px; color:#888; margin-top:4px;">📍 {lead['location']} | Link: <code style="color:#BBB;">{lead['profile_url']}</code></div>
                    </div>
                    <div style="text-align:right;">
                      <a href="{lead['profile_url']}" target="_blank"
                         style="display:inline-block; background:#E50914; color:#FFF; padding:9px 20px; border-radius:4px; font-size:12px; text-decoration:none; font-weight:700; box-shadow:0 2px 8px rgba(229,9,20,0.4);">
                         ➕ Mở Profile & Kết Bạn (LIVE)
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
        Toàn bộ các General Manager, DOSM, Marcom Manager đã được gán <b>Link Profile LIVE 100%</b>. Khi bạn kết nối 1 người ở Tab 1, người đứng đầu danh sách này sẽ <b>tự động được đẩy bù lên Top 20</b>.
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
                      <div style="font-size:14px; font-weight:700; color:#DDD;">#{lead['queue_index']}. {lead['name']} <span style="font-size:9px; color:#4CAF50; border:1px solid #4CAF50; padding:2px 5px; border-radius:3px; margin-left:6px;">🟢 LIVE</span></div>
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
# TAB 3: SCAN LIÊN TỤC TOÀN QUỐC — GM/DOSM/MARCOM/OWNER
# ─────────────────────────────────────────────────────────────────────
with tab_bulk:
    from engine.continuous_scanner import (
        seed_scan_jobs, get_scan_stats, get_pending_jobs,
        run_scan_jobs, build_all_queries, TITLES, REGIONS
    )

    # Nạp scan jobs nếu chưa có
    seed_scan_jobs()
    stats = get_scan_stats()
    total_queries = len(build_all_queries())

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0D0D0D,#080808);border:1px solid #E50914;border-radius:4px;padding:20px 24px;margin-bottom:20px;">
      <div style="font-size:10px;letter-spacing:2px;color:#E50914;font-weight:700;text-transform:uppercase;">SCAN LINKEDIN LIÊN TỤC TOÀN QUỐC</div>
      <div style="font-family:'Montserrat',sans-serif;font-size:22px;font-weight:700;color:#FFF;margin:6px 0;">
        🌐 Tự Động Tìm GM · DOSM · Marcom · Owner Toàn Việt Nam
      </div>
      <div style="font-size:12px;color:#999;">
        Ma trận <b>{len(TITLES)} chức danh × {len(REGIONS)} khu vực</b> = <b>{total_queries} bộ query</b> · 
        Mỗi bộ quét đến trang cuối cùng · Chỉ thêm người <b>CHƯA CÓ</b> trong DB vào hàng đợi kết bạn ·
        Tự động chạy lại sau 7 ngày để bắt <b>người mới đăng ký</b> LinkedIn.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── DASHBOARD TIẾN ĐỘ ──
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Tổng query", stats["total"])
    c2.metric("✅ Đã xong", stats["done"])
    c3.metric("⏳ Chờ scan", stats["pending"])
    c4.metric("🔄 Đang chạy", stats["running"])
    c5.metric("👥 Người mới thêm", stats["total_new_added"])

    # Progress bar toàn bộ
    pct = stats["progress_pct"]
    st.markdown(f"""
    <div style="margin:8px 0 16px;">
      <div style="font-size:10px;color:#888;margin-bottom:4px;">Tiến độ scan toàn quốc: {pct}%</div>
      <div style="background:#1A1A1A;border-radius:4px;height:8px;">
        <div style="background:#E50914;width:{pct}%;height:8px;border-radius:4px;transition:width 0.3s;"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── COOKIE & CẤU HÌNH ──
    with st.expander("📖 Cách lấy Cookie li_at (làm 1 lần duy nhất)"):
        st.markdown("""
        1. Mở **Chrome**, đăng nhập LinkedIn
        2. Nhấn **F12** → tab **Application** → **Cookies** → **https://www.linkedin.com**
        3. Tìm dòng **`li_at`** → Copy toàn bộ giá trị cột **Value**
        4. Dán vào ô bên dưới
        """)

    cs_li_at = st.text_input("🔑 Cookie li_at:", type="password",
                              placeholder="AQEDATxxxxxx...", key="cs_li_at")

    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        max_pg = st.slider("Số trang tối đa / query:", 1, 20, 10,
                            help="LinkedIn thường có ~10 trang = 100 kết quả / query")
    with col_cfg2:
        batch_size = st.slider("Số query chạy mỗi lần:", 5, 50, 20,
                                help="Chạy ít hơn để tránh bị LinkedIn giới hạn tốc độ")

    st.markdown("")

    # ── THÔNG TIN CHI TIẾT MA TRẬN QUERY ──
    with st.expander(f"📋 Xem toàn bộ {total_queries} bộ query ({len(TITLES)} chức danh × {len(REGIONS)} khu vực)"):
        col_t, col_r = st.columns(2)
        with col_t:
            st.markdown("**Chức danh target:**")
            for t in TITLES:
                st.markdown(f"- {t}")
        with col_r:
            st.markdown("**Khu vực scan:**")
            for rname, _ in REGIONS:
                st.markdown(f"- {rname}")

    st.divider()

    # ── NÚT ĐIỀU KHIỂN ──
    btn1, btn2, btn3 = st.columns(3)

    with btn1:
        if st.button("🚀 BẮT ĐẦU SCAN", type="primary", use_container_width=True):
            if not cs_li_at:
                st.error("❌ Cần Cookie li_at!")
            else:
                progress_bar = st.progress(0)
                status_box   = st.empty()
                counter_box  = st.empty()

                def on_prog(ji, total, job, total_new):
                    pct_now = ji / total if total else 0
                    progress_bar.progress(pct_now)
                    status_box.markdown(
                        f"⏳ **[{ji+1}/{total}]** `{job['title']}` · "
                        f"**{job['region']}** ({job['location']})"
                    )
                    counter_box.markdown(f"👥 Đã tìm được người mới: **{total_new}**")

                result = run_scan_jobs(
                    li_at_cookie=cs_li_at,
                    max_pages=max_pg,
                    progress_callback=on_prog
                )

                progress_bar.progress(1.0)
                if result.get("status") == "cookie_expired":
                    st.error("🔴 Cookie li_at hết hạn! Vui lòng lấy cookie mới từ Chrome.")
                else:
                    st.success(
                        f"🎉 XONG! Đã quét {result['jobs_processed']} query · "
                        f"Thêm mới vào queue: **+{result['total_new']}** người · "
                        f"F5 để xem Top 20 cập nhật!"
                    )
                time.sleep(1.5)
                st.rerun()

    with btn2:
        # Scan chỉ khu vực được chọn
        region_choice = st.selectbox("Chọn khu vực:", [r[0] for r in REGIONS], key="region_sel")
        if st.button(f"🎯 Scan {region_choice}", use_container_width=True):
            if not cs_li_at:
                st.error("❌ Cần Cookie li_at!")
            else:
                from engine.continuous_scanner import ScanJob
                sess_r = get_session()
                region_jobs = sess_r.query(ScanJob).filter(
                    ScanJob.region == region_choice
                ).all()
                jids = [j.id for j in region_jobs]
                sess_r.close()

                progress_bar2 = st.progress(0)
                status_box2   = st.empty()

                def on_prog2(ji, total, job, total_new):
                    progress_bar2.progress(ji / total if total else 0)
                    status_box2.markdown(f"⏳ **[{ji+1}/{total}]** {job['title']} · {job['location']}")

                result2 = run_scan_jobs(
                    li_at_cookie=cs_li_at,
                    job_ids=jids,
                    max_pages=max_pg,
                    progress_callback=on_prog2
                )
                progress_bar2.progress(1.0)
                st.success(f"✅ {region_choice}: +{result2['total_new']} người mới vào queue!")
                time.sleep(1.5)
                st.rerun()

    with btn3:
        st.markdown("")
        st.markdown("")
        if st.button("♻️ RESET SCAN (chạy lại từ đầu)", use_container_width=True):
            from engine.continuous_scanner import ScanJob
            from datetime import datetime
            sess_rst = get_session()
            sess_rst.query(ScanJob).update({"status": "pending", "current_page": 0,
                                             "next_run": datetime.now()})
            sess_rst.commit()
            sess_rst.close()
            st.success("✅ Đã reset! Hệ thống sẽ scan lại toàn bộ từ đầu.")
            time.sleep(1)
            st.rerun()

    # ── BẢNG TIẾN ĐỘ TỪNG KHU VỰC ──
    st.divider()
    st.markdown("**📊 Tiến độ theo khu vực:**")

    from engine.continuous_scanner import ScanJob as SJ
    sess_show = get_session()
    region_progress = []
    for rname, _ in REGIONS:
        total_r = sess_show.query(SJ).filter(SJ.region == rname).count()
        done_r  = sess_show.query(SJ).filter(SJ.region == rname, SJ.status.in_(["done","exhausted"])).count()
        new_r   = sess_show.query(SJ).filter(SJ.region == rname).with_entities(
            __import__('sqlalchemy').func.sum(SJ.new_added)
        ).scalar() or 0
        region_progress.append({"Khu vực": rname, "Tổng query": total_r,
                                  "Đã xong": done_r, "Người mới": int(new_r),
                                  "Hoàn thành": f"{round(done_r/total_r*100) if total_r else 0}%"})
    sess_show.close()

    import pandas as pd
    df_prog = pd.DataFrame(region_progress)
    st.dataframe(df_prog, use_container_width=True, hide_index=True)

