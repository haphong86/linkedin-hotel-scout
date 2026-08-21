"""
database/models.py — Quản lý dữ liệu Lãnh đạo Khách sạn trên LinkedIn
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DB_PATH = os.path.join(os.path.dirname(__file__), "linkedin_leads.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class HotelExecutive(Base):
    """Bảng lưu trữ thông tin Lãnh đạo Khách sạn / Resort (GM, DOSM, Marcom)"""
    __tablename__ = "hotel_executives"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    title = Column(String(200), index=True)          # General Manager, DOSM, Marcom Manager
    company = Column(String(250), index=True)        # Tên KS / Resort (Hilton, Furama, v.v.)
    location = Column(String(200))                   # Da Nang City, Vietnam
    city = Column(String(100), index=True)           # Đà Nẵng, Hội An, Huế...
    profile_url = Column(String(500), unique=True, index=True)
    headline = Column(Text)                          # Đoạn bio / headline
    avatar_url = Column(String(500))
    connection_degree = Column(String(50), default="2nd") # 1st, 2nd, 3rd
    
    # Trạng thái kết nối
    status = Column(String(50), default="Mới tìm thấy", index=True)
    lead_score = Column(Integer, default=90)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    invited_at = Column(DateTime, nullable=True)
    connected_at = Column(DateTime, nullable=True)

    logs = relationship("ConnectionLog", back_populates="executive", cascade="all, delete-orphan")


class ConnectionLog(Base):
    """Nhật ký gửi lời mời kết bạn"""
    __tablename__ = "connection_logs"

    id = Column(Integer, primary_key=True, index=True)
    executive_id = Column(Integer, ForeignKey("hotel_executives.id"))
    recipient_name = Column(String(200))
    recipient_title = Column(String(200))
    profile_url = Column(String(500))
    custom_note = Column(Text)
    status = Column(String(50), default="SUCCESS")
    sent_at = Column(DateTime, default=datetime.utcnow)

    executive = relationship("HotelExecutive", back_populates="logs")


class SystemSetting(Base):
    """Cấu hình hạn ngạch"""
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text)


INITIAL_LEADS = [
    ('Cath (CamThu) Nguyen', 'Commercial Head (Giám đốc Thương mại)', 'Hilton Da Nang', 'Đà Nẵng', 'https://www.linkedin.com/in/cath-camthu-nguyen', 'Commercial Head at Hilton Da Nang · South East Asia Commercial Leader', 98),
    ('John Dang Huy', 'General Manager (Tổng Giám Đốc)', 'Luxury Resort Mui Ne', 'Bình Thuận', 'https://www.linkedin.com/in/john-dang-huy', 'Passionate Hotelier · Experienced General Manager', 98),
    ('Jesper Bach Larsen', 'General Manager', 'Hilton Da Nang', 'Đà Nẵng', 'https://www.linkedin.com/in/jesper-bach-larsen', 'General Manager at Hilton Da Nang', 98),
    ('Kevin Park', 'Commercial Director (DOSM)', 'Hilton Da Nang', 'Đà Nẵng', 'https://www.linkedin.com/in/kevin-park-hilton', 'Commercial Director at Hilton Da Nang', 95),
    ('Gentzsch Brett', 'General Manager', 'Furama Resort Danang', 'Đà Nẵng', 'https://www.linkedin.com/in/gentzsch-brett-furama', 'General Manager at Furama Resort Danang', 98),
    ('Trần Thị Thúy', 'Director of Sales & Marketing (DOSM)', 'Furama Resort Danang', 'Đà Nẵng', 'https://www.linkedin.com/in/thuy-tran-furama', 'DOSM at Furama Resort Danang', 95),
    ('Seif Hamdy', 'General Manager', 'InterContinental Danang Sun Peninsula Resort', 'Đà Nẵng', 'https://www.linkedin.com/in/seif-hamdy', 'General Manager at InterContinental Danang', 98),
    ('Mai Lan Phương', 'Marcom Manager', 'InterContinental Danang', 'Đà Nẵng', 'https://www.linkedin.com/in/lanphuong-marcom', 'Marketing & Communications Manager at InterContinental Danang', 90),
    ('Adrian Ee', 'General Manager', 'Hyatt Regency Danang Resort and Spa', 'Đà Nẵng', 'https://www.linkedin.com/in/adrian-ee-hyatt', 'General Manager at Hyatt Regency Danang', 98),
    ('Nguyễn Hoàng Nam', 'Director of Sales', 'Hyatt Regency Danang', 'Đà Nẵng', 'https://www.linkedin.com/in/nam-nguyen-hyatt', 'Director of Sales at Hyatt Regency Danang', 95),
    ('Piotr Madej', 'General Manager', 'Shilla Monogram Quangnam Danang', 'Đà Nẵng', 'https://www.linkedin.com/in/piotr-madej', 'General Manager at Shilla Monogram Danang', 98),
    ('Lê Thị Bích Ngọc', 'Marketing & Communications Manager', 'Shilla Monogram Danang', 'Đà Nẵng', 'https://www.linkedin.com/in/bichngoc-shilla', 'Marcom Manager at Shilla Monogram', 90),
    ('Nguyễn Văn Tuấn', 'General Manager', 'Rosamia Da Nang Hotel', 'Đà Nẵng', 'https://www.linkedin.com/in/tuan-nguyen-rosamia', 'General Manager at Rosamia Danang Hotel', 98),
    ('Đặng Quốc Huy', 'General Manager', 'Balcona Hotel Da Nang', 'Đà Nẵng', 'https://www.linkedin.com/in/huy-dang-balcona', 'General Manager at Balcona Hotel Da Nang', 98),
    ('Phạm Minh Đức', 'Marketing Manager', 'Sala Danang Beach Hotel', 'Đà Nẵng', 'https://www.linkedin.com/in/duc-pham-sala', 'Marketing Manager at Sala Hotel Group', 90),
    ('Võ Hồng Quang', 'Hotel Manager', 'Paris Deli Danang Beach Hotel', 'Đà Nẵng', 'https://www.linkedin.com/in/quang-vo-parisdeli', 'Hotel Manager at Paris Deli Danang', 95),
    ('Christian Gerart', 'General Manager', 'Anantara Hoi An Resort', 'Hội An', 'https://www.linkedin.com/in/christian-gerart-anantara', 'General Manager at Anantara Hoi An Resort', 98),
    ('Phan Thị Mai', 'Director of Sales & Marketing', 'Anantara Hoi An Resort', 'Hội An', 'https://www.linkedin.com/in/mai-phan-anantara', 'DOSM at Anantara Hoi An Resort', 95),
    ('Lê Hữu Phúc', 'General Manager', 'Four Seasons Resort The Nam Hai', 'Hội An', 'https://www.linkedin.com/in/phuc-le-thenamhai', 'Hotel Manager at Four Seasons Resort The Nam Hai', 98),
    ('Nguyễn Thị Thanh Hà', 'Marketing & Communications Manager', 'Four Seasons Resort The Nam Hai', 'Hội An', 'https://www.linkedin.com/in/thanhha-thenamhai', 'Marcom Manager at Four Seasons The Nam Hai', 90),
    ('Vũ Đình Hiệp', 'General Manager', 'La Siesta Hoi An Resort & Spa', 'Hội An', 'https://www.linkedin.com/in/hiep-vu-lasiesta', 'General Manager at La Siesta Hoi An Resort', 98),
    ('Trần Đức Thắng', 'General Manager', 'Silk Sense Hoi An River Resort', 'Hội An', 'https://www.linkedin.com/in/thang-tran-silksense', 'General Manager at Silk Sense Hoi An River Resort', 98),
    ('Trần Hữu Dũng', 'General Manager', 'Azerai La Residence Hue', 'Huế', 'https://www.linkedin.com/in/dung-tran-azerai', 'General Manager at Azerai La Residence Hue', 98),
    ('Nguyễn Thị Diệu Thúy', 'Director of Sales & Marketing', 'Azerai La Residence Hue', 'Huế', 'https://www.linkedin.com/in/dieuthuy-azerai', 'DOSM at Azerai La Residence Hue', 95),
    ('Hoàng Minh Tuấn', 'General Manager', 'Silk Path Grand Hue Hotel', 'Huế', 'https://www.linkedin.com/in/tuan-hoang-silkpath', 'General Manager at Silk Path Grand Hue Hotel', 98),
    ('Lê Anh Tuấn', 'General Manager', 'Banyan Tree Lang Co', 'Lăng Cô', 'https://www.linkedin.com/in/tuan-le-banyantree', 'General Manager at Banyan Tree Lang Co', 98),
    ('Phạm Thu Trang', 'Marketing Manager', 'Angsana Lang Co Resort', 'Lăng Cô', 'https://www.linkedin.com/in/trang-pham-angsana', 'Marketing Manager at Angsana Lang Co', 90)
]


def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    if session.query(HotelExecutive).count() == 0:
        for name, title, company, city, url, headline, score in INITIAL_LEADS:
            session.add(HotelExecutive(
                name=name,
                title=title,
                company=company,
                city=city,
                location=f"{city}, Vietnam",
                profile_url=url,
                headline=headline,
                lead_score=score,
                status="Mới tìm thấy"
            ))
        session.commit()
    session.close()

def get_session():
    return SessionLocal()
