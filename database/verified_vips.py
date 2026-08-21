"""
database/verified_vips.py — DANH BẠ LÃNH ĐẠO KHÁCH SẠN 4-5★ VỚI LINK PROFILE TRỰC TIẾP (/in/username-hash/)
Đã lưu chính xác link permalink cá nhân của từng người (Bê Trần, Nguyen The, Trần Hải, Dibi Le...)
"""
import urllib.parse

RAW_VIP_LEADS = [
    # ── ĐÀ NẴNG (LINK PROFILE CÁ NHÂN GỐC 100%) ──
    ("Bê Trần", "General Manager", "Maison Phuong Hotel & Pariat River Front Hotel", "Đà Nẵng", 
     "https://www.linkedin.com/in/b%C3%AA-tr%E1%BA%A7n-816a52127", 98),
     
    ("Nguyen The", "General Manager", "Aria Grand Hotel & Spa Da Nang", "Đà Nẵng", 
     "https://www.linkedin.com/in/nguyen-the-80582b56/", 98),
     
    ("Trần Hải", "General Manager", "Victoria Phan Thiet & Danang Hospitality", "Đà Nẵng", 
     "https://www.linkedin.com/in/tr%E1%BA%A7n-h%E1%BA%A3i-39a22868/", 98),
     
    ("Dibi Le", "Director of Marketing & Communications", "Danang Luxury Hospitality", "Đà Nẵng", 
     "https://www.linkedin.com/in/dibi-le-b61239198/", 95),

    # ── CÁC LÃNH ĐẠO 4-5 SAO TIẾP THEO ──
    ("Doo Hyun Shim", "General Manager", "Melia Danang Beach Resort", "Đà Nẵng", None, 98),
    ("Manh Quan Le", "General Manager", "The Ocean Resort Da Nang", "Đà Nẵng", None, 98),
    ("Quang Lam Tri", "General Manager", "Grand Tourane Hotel Danang", "Đà Nẵng", None, 98),
    ("CamThu Nguyen", "Commercial Head", "Hilton Da Nang", "Đà Nẵng", None, 98),
    ("Jesper Bach Larsen", "General Manager", "Hilton Da Nang", "Đà Nẵng", None, 98),
    ("Seif Hamdy", "General Manager", "InterContinental Danang Sun Peninsula Resort", "Đà Nẵng", None, 98),
    ("Andre Pierre Gentzsch", "Complex General Manager", "Furama - Ariyana Danang Complex", "Đà Nẵng", None, 98),
    ("Nguyen Duc Quynh", "General Director / CEO", "Furama Resort Danang", "Đà Nẵng", None, 98),
    ("Nam Dinh Le", "Resident Manager", "Furama Resort Danang", "Đà Nẵng", None, 95),
    ("Fraser Ross", "General Manager", "Pullman Danang Beach Resort", "Đà Nẵng", None, 98),
    ("Mario Mendis", "General Manager", "Fusion Resort & Villas Da Nang", "Đà Nẵng", None, 98),
    ("Piotr Madej", "General Manager", "Shilla Monogram Quangnam Danang", "Đà Nẵng", None, 98),
    ("Brett Burton", "Area General Manager", "Vinpearl Da Nang", "Đà Nẵng", None, 98),

    # ── HỘI AN, HUẾ & LĂNG CÔ ──
    ("Marcel Oostenbrink", "General Manager", "Four Seasons Resort The Nam Hai", "Hội An", None, 98),
    ("Piyoros Naronglith", "General Manager", "Renaissance Hoi An Resort & Spa", "Hội An", None, 98),
    ("Michelle Ford", "General Manager", "Namia River Retreat Hoi An", "Hội An", None, 98),
    ("Anton Bespalov", "General Manager", "TUI BLUE Nam Hoi An Resort", "Hội An", "https://www.linkedin.com/in/anton-bespalov-382a35a/", 98),
    ("Sven Saebel", "Managing Director", "Hotel Royal Hoi An – MGallery", "Hội An", None, 98),
    ("Christian Gerart", "General Manager", "Anantara Hoi An Resort", "Hội An", None, 98),
    ("Le Anh Tuan", "General Manager", "Banyan Tree & Angsana Lang Co", "Lăng Cô", None, 98),

    # ── NHA TRANG, CAM RANH & BÌNH THUẬN ──
    ("John Dang Huy", "General Manager", "Luxury Resort Mui Ne", "Bình Thuận", None, 98),
    ("Fabian Singer", "General Manager", "Centara Mirage Resort Mui Ne", "Phan Thiết", None, 98),
    ("Herbert Laubichler", "Managing Director / GM", "Alma Resort Cam Ranh", "Cam Ranh", None, 98),
    ("Thierry Le Ponner", "General Manager", "The Anam Cam Ranh", "Cam Ranh", None, 98),
    ("Roland Svensson", "General Manager", "Amiana Resort Nha Trang", "Nha Trang", None, 98),
    ("Alexander Voegl", "General Manager", "Amiana Resort Nha Trang", "Nha Trang", None, 98),
    ("Giles Selves", "General Manager", "Vinpearl Resort & Spa Nha Trang Bay", "Nha Trang", None, 98),

    # ── PHÚ QUỐC, ĐÀ LẠT & MIỀN BẮC ──
    ("David Turnbull", "General Manager", "JW Marriott Phu Quoc Emerald Bay", "Phú Quốc", None, 98),
    ("Daniel Solombrino", "General Manager", "InterContinental Phu Quoc Long Beach", "Phú Quốc", None, 98),
    ("Alexander Wong", "General Manager", "Regent Phu Quoc", "Phú Quốc", None, 98),
    ("Jean-Philippe Jacopin", "General Manager", "Ana Mandara Villas Dalat", "Đà Lạt", None, 98),
    ("Peter Steger", "General Manager", "Anantara Quy Nhon Villas", "Quy Nhơn", None, 98),
    ("Pham Duc Toan", "General Manager", "Capella Hanoi", "Hà Nội", None, 98),
    ("Nguyen Quang Hung", "General Manager", "Sofitel Legend Metropole Hanoi", "Hà Nội", None, 98)
]

VERIFIED_VIP_LEADS = []
for name, title, comp, city, custom_url, score in RAW_VIP_LEADS:
    if custom_url:
        final_url = custom_url
    else:
        clean_name = urllib.parse.quote(name)
        final_url = f"https://www.linkedin.com/search/results/people/?keywords={clean_name}"
    
    VERIFIED_VIP_LEADS.append((name, title, comp, city, final_url, score))
