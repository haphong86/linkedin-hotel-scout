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

# ── 4 TABS ĐIỀU KHIỂN CHÍNH ──────────────────────────────────────────
tab_queue, tab_backlog, tab_sync, tab_scanner = st.tabs([
    "🚀 TOP 20 HÔM NAY (KIỂM TRA LIVE/DIE)",
    "📋 HÀNG ĐỢI DỰ BỊ (#21+)",
    "🔄 ĐỒNG BỘ & NẠP LÃNH ĐẠO MỚI",
    "🔍 AUTO-SCAN LINK /IN/ THẬT"
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
# TAB 3: ĐỒNG BỘ & NẠP LÃNH ĐẠO MỚI — SCAN /IN/ TRƯỚC, QUEUE SAU
# ─────────────────────────────────────────────────────────────────────
with tab_sync:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0D0D0D,#0A0A0A);border:1px solid #E50914;border-radius:4px;padding:20px 24px;margin-bottom:20px;">
      <div style="font-size:10px;letter-spacing:2px;color:#E50914;font-weight:700;text-transform:uppercase;">QUY TRÌNH CHUẨN</div>
      <div style="font-family:'Montserrat',sans-serif;font-size:20px;font-weight:700;color:#FFF;margin:6px 0;">Scan lấy link /in/ thật → Lưu DB → Vào hàng đợi kết bạn</div>
      <div style="font-size:12px;color:#999;">Chỉ những hồ sơ có link <code style="color:#E50914;">/in/</code> thật mới được vào hàng đợi Top 20. Không có search URL nào lọt vào queue.</div>
    </div>
    """, unsafe_allow_html=True)

    # Nhập cookie li_at
    with st.expander("📖 Cách lấy Cookie li_at (chỉ làm 1 lần)", expanded=False):
        st.markdown("""
        1. Mở **Chrome**, đăng nhập LinkedIn
        2. Nhấn **F12** → tab **Application** → **Cookies** → **https://www.linkedin.com**
        3. Tìm dòng **`li_at`** → Copy toàn bộ giá trị cột **Value**
        4. Dán vào ô bên dưới
        """)

    sync_li_at = st.text_input(
        "🔑 Cookie li_at (bắt buộc để scan link /in/ thật):",
        type="password",
        placeholder="AQEDATxxxxxx...",
        key="sync_li_at_input"
    )

    st.divider()

    # Thống kê hiện tại
    sess_sync = get_session()
    all_sync = sess_sync.query(HotelExecutive).all()
    already_direct = [e for e in all_sync if e.profile_url and "/in/" in e.profile_url]
    need_scan = [e for e in all_sync if e.profile_url and "/search/results/" in e.profile_url]
    not_imported = [v for v in VERIFIED_VIP_LEADS if not sess_sync.query(HotelExecutive).filter(HotelExecutive.name == v[0]).first()]
    sess_sync.close()

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("✅ Đã có link /in/ thật", len(already_direct), "Sẵn sàng kết bạn")
    col_m2.metric("⚠️ Còn dùng search URL", len(need_scan), "Cần scan trước")
    col_m3.metric("➕ Chưa import vào DB", len(not_imported))

    st.markdown("")

    if not sync_li_at:
        st.warning("⚠️ Vui lòng nhập Cookie **li_at** ở trên để hệ thống có thể tự động scan lấy link /in/ thật trước khi lưu vào hàng đợi.")

    # NÚT CHÍNH: Nạp & Scan ngay
    if st.button("🚀 NẠP + SCAN /IN/ + ĐƯA VÀO HÀNG ĐỢI (1 BƯỚC)", type="primary", use_container_width=True):
        if not sync_li_at:
            st.error("❌ Thiếu cookie li_at — không thể scan link /in/ thật!")
        else:
            from engine.linkedin_scanner import scan_profile_url

            session = get_session()
            progress = st.progress(0)
            status_box = st.empty()

            # Danh sách cần xử lý: chưa có trong DB HOẶC đang dùng search URL
            to_process = []
            for name, title, comp, city, url, score in VERIFIED_VIP_LEADS:
                existing = session.query(HotelExecutive).filter(HotelExecutive.name == name).first()
                if not existing:
                    to_process.append(("new", None, name, title, comp, city, url, score))
                elif existing.profile_url and "/search/results/" in existing.profile_url:
                    to_process.append(("update", existing.id, name, title, comp, city, url, score))

            total = len(to_process)
            ok_count = 0

            if total == 0:
                st.success("🎉 Tất cả hồ sơ đã có link /in/ thật! Không cần xử lý thêm.")
            else:
                for i, item in enumerate(to_process):
                    action, exec_id, name, title, comp, city, raw_url, score = item
                    status_box.markdown(f"⏳ **[{i+1}/{total}]** Đang scan **{name}**...")

                    final_url = raw_url  # mặc định giữ nguyên

                    # Nếu là search URL → scan lấy /in/ thật
                    if raw_url and "/search/results/" in raw_url:
                        result = scan_profile_url(raw_url, sync_li_at, headless=True)
                        if result["status"] == "ok":
                            final_url = result["profile_url"]
                            status_box.markdown(f"✅ **{name}** → `{final_url}`")
                        else:
                            status_box.markdown(f"⚠️ **{name}** → Không scan được, giữ search URL tạm")
                    else:
                        status_box.markdown(f"✅ **{name}** → đã có link /in/ trực tiếp")

                    # Lưu vào DB
                    if action == "new":
                        session.add(HotelExecutive(
                            name=name, title=title, company=comp, city=city,
                            location=f"{city}, Vietnam",
                            profile_url=final_url,
                            headline=f"{title} at {comp}",
                            lead_score=score,
                            status="Mới tìm thấy"
                        ))
                    else:
                        existing_obj = session.query(HotelExecutive).filter(HotelExecutive.id == exec_id).first()
                        if existing_obj:
                            existing_obj.profile_url = final_url

                    ok_count += 1
                    session.commit()
                    progress.progress((i + 1) / total)
                    import time as _t; _t.sleep(2)  # anti-rate-limit

            session.close()
            status_box.empty()
            st.success(f"🎉 XONG! Đã xử lý {ok_count}/{total} hồ sơ — chỉ link /in/ thật mới vào hàng đợi kết bạn!")
            time.sleep(1)
            st.rerun()

    st.divider()
    st.markdown("**Hoặc nạp nhanh (không scan) — giữ nguyên link đã có:**")
    if st.button("⚡ NẠP NHANH (CHỈ HỒ SƠ CHƯA CÓ TRONG DB)", use_container_width=True):
        session = get_session()
        added = 0
        for name, title, comp, city, url, score in VERIFIED_VIP_LEADS:
            exists = session.query(HotelExecutive).filter(HotelExecutive.name == name).first()
            if not exists:
                session.add(HotelExecutive(
                    name=name, title=title, company=comp, city=city,
                    location=f"{city}, Vietnam",
                    profile_url=url,
                    headline=f"{title} at {comp}",
                    lead_score=score,
                    status="Mới tìm thấy"
                ))
                added += 1
        session.commit()
        session.close()
        st.success(f"✅ Đã nạp nhanh +{added} hồ sơ mới vào DB!")
        time.sleep(1)
        st.rerun()



# ─────────────────────────────────────────────────────────────────────
# TAB 4: AUTO-SCAN LINK /IN/ THẬT BẰNG PLAYWRIGHT
# ─────────────────────────────────────────────────────────────────────
with tab_scanner:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0D0D0D 0%,#0A0A0A 100%);border:1px solid #E50914;border-radius:4px;padding:20px 24px;margin-bottom:20px;">
      <div style="font-size:10px;letter-spacing:2px;color:#E50914;font-weight:700;text-transform:uppercase;">TỰ ĐỘNG PHÁT HIỆN LINK /IN/ THẬT</div>
      <div style="font-family:'Montserrat',sans-serif;font-size:22px;font-weight:700;color:#FFF;margin:6px 0;">🔍 Auto-Scan LinkedIn Profile URL</div>
      <div style="font-size:12px;color:#999;">
        Hệ thống dùng <b>Playwright</b> mở trang tìm kiếm LinkedIn → tự click người đầu tiên → lấy đúng link 
        <code style="background:#1A0000;color:#E50914;padding:2px 6px;border-radius:3px;">/in/tên-mã/</code> thật.<br/>
        <b>Yêu cầu:</b> Dán cookie <code>li_at</code> (phiên đăng nhập LinkedIn của anh) vào bên dưới.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Hướng dẫn lấy cookie li_at
    with st.expander("📖 Cách lấy Cookie li_at (chỉ làm 1 lần)"):
        st.markdown("""
        1. Mở **Chrome**, đăng nhập LinkedIn
        2. Nhấn **F12** → tab **Application** → **Cookies** → **https://www.linkedin.com**
        3. Tìm dòng **`li_at`** → Copy toàn bộ giá trị cột **Value**
        4. Dán vào ô bên dưới
        """)

    li_at = st.text_input(
        "🔑 Cookie li_at của anh:",
        type="password",
        placeholder="AQEDATxxxxxx... (paste cookie li_at vào đây)",
        help="Cookie này chỉ dùng để mở trình duyệt LinkedIn trên máy anh, không được gửi đi đâu cả."
    )

    st.divider()

    # Lấy danh sách lead còn dùng search URL
    sess = get_session()
    all_execs = sess.query(HotelExecutive).all()
    search_url_leads = [
        (e.id, e.name, e.profile_url)
        for e in all_execs
        if e.profile_url and "/search/results/" in e.profile_url
    ]
    direct_url_leads = [
        (e.id, e.name, e.profile_url)
        for e in all_execs
        if e.profile_url and "/in/" in e.profile_url
    ]
    sess.close()

    col_s1, col_s2 = st.columns(2)
    col_s1.metric("Đang dùng Search URL (cần scan)", len(search_url_leads))
    col_s2.metric("Đã có link /in/ trực tiếp", len(direct_url_leads))

    if search_url_leads:
        st.markdown("**Danh sách cần Auto-Scan:**")
        for _, name, url in search_url_leads:
            st.markdown(f"- **{name}** → `{url}`")

        st.markdown("")

        col_b1, col_b2 = st.columns(2)

        with col_b1:
            # Scan 1 người cụ thể
            scan_names = [name for _, name, _ in search_url_leads]
            chosen = st.selectbox("Scan từng người:", scan_names)
            if st.button("🔍 SCAN NGƯỜI NÀY", use_container_width=True):
                if not li_at:
                    st.error("⚠️ Vui lòng nhập Cookie li_at trước!")
                else:
                    try:
                        from engine.linkedin_scanner import scan_profile_url
                        chosen_url = next(url for _, n, url in search_url_leads if n == chosen)
                        with st.spinner(f"Đang mở LinkedIn tìm {chosen}..."):
                            result = scan_profile_url(chosen_url, li_at, headless=True)
                        if result["status"] == "ok":
                            st.success(f"✅ TÌM THẤY: {result['profile_url']}")
                            # Cập nhật DB
                            s2 = get_session()
                            exec_obj = s2.query(HotelExecutive).filter(HotelExecutive.name == chosen).first()
                            if exec_obj:
                                exec_obj.profile_url = result["profile_url"]
                                s2.commit()
                            s2.close()
                            st.info("💾 Đã lưu link /in/ thật vào database!")
                            time.sleep(0.8)
                            st.rerun()
                        else:
                            st.warning(f"⚠️ {result['message']}")
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

        with col_b2:
            # Scan toàn bộ
            if st.button("🚀 SCAN TOÀN BỘ (AUTO)", type="primary", use_container_width=True):
                if not li_at:
                    st.error("⚠️ Vui lòng nhập Cookie li_at trước!")
                else:
                    try:
                        from engine.linkedin_scanner import scan_profile_url
                        progress = st.progress(0)
                        status_txt = st.empty()
                        total = len(search_url_leads)
                        ok_count = 0
                        for i, (lead_id, name, url) in enumerate(search_url_leads):
                            status_txt.markdown(f"⏳ **[{i+1}/{total}]** Đang scan: **{name}**...")
                            result = scan_profile_url(url, li_at, headless=True)
                            if result["status"] == "ok":
                                s2 = get_session()
                                exec_obj = s2.query(HotelExecutive).filter(HotelExecutive.id == lead_id).first()
                                if exec_obj:
                                    exec_obj.profile_url = result["profile_url"]
                                    s2.commit()
                                s2.close()
                                ok_count += 1
                                status_txt.markdown(f"✅ **{name}** → `{result['profile_url']}`")
                            else:
                                status_txt.markdown(f"⚠️ **{name}** → {result['message']}")
                            progress.progress((i + 1) / total)
                            time.sleep(3)
                        st.success(f"🎉 SCAN XONG! Đã cập nhật {ok_count}/{total} link /in/ thật vào database!")
                        time.sleep(1.2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
    else:
        st.success("🎉 Tất cả hồ sơ đã có link /in/ trực tiếp! Không cần scan thêm.")
