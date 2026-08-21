"""
database/models.py — Quản lý dữ liệu Lãnh đạo Khách sạn trên LinkedIn
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from database.verified_vips import VERIFIED_VIP_LEADS

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
    connection_degree = Column(String(50), default="2nd")
    
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
    """Cấu hình hạn ngạch & Auto-pilot"""
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text)


def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    if session.query(HotelExecutive).count() == 0:
        for name, title, company, city, keyword, score in VERIFIED_VIP_LEADS:
            session.add(HotelExecutive(
                name=name,
                title=title,
                company=company,
                city=city,
                location=f"{city}, Vietnam",
                profile_url=keyword,
                headline=f"{title} at {company}",
                lead_score=score,
                status="Mới tìm thấy"
            ))
        session.commit()
    session.close()

def get_session():
    return SessionLocal()
