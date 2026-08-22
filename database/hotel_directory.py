"""
database/hotel_directory.py
Danh bạ đầy đủ: Khách sạn → Lãnh đạo (GM / DOSM / Marcom / Owner)
Link LinkedIn search theo tên người + khách sạn để tìm chính xác nhất.
"""

# Format: (hotel_name, city, region, star, title, person_name, linkedin_url)
# linkedin_url: /in/ nếu đã biết, /search/ nếu chưa biết

HOTEL_DIRECTORY = [

    # ══════════════════════════════════════════════════════
    # ĐÀ NẴNG
    # ══════════════════════════════════════════════════════
    ("InterContinental Danang Sun Peninsula Resort", "Đà Nẵng", "Miền Trung", 5,
     "General Manager", "Seif Hamdy",
     "https://www.linkedin.com/search/results/people/?keywords=Seif+Hamdy+InterContinental+Danang"),

    ("Hyatt Regency Danang Resort & Spa", "Đà Nẵng", "Miền Trung", 5,
     "General Manager", "Michael Bretz",
     "https://www.linkedin.com/search/results/people/?keywords=Michael+Bretz+Hyatt+Danang"),

    ("Pullman Danang Beach Resort", "Đà Nẵng", "Miền Trung", 5,
     "General Manager", "Fraser Ross",
     "https://www.linkedin.com/search/results/people/?keywords=Fraser+Ross+Pullman+Danang"),

    ("Furama Resort Danang", "Đà Nẵng", "Miền Trung", 5,
     "General Director", "Nguyen Duc Quynh",
     "https://www.linkedin.com/search/results/people/?keywords=Nguyen+Duc+Quynh+Furama+Danang"),

    ("Furama Resort Danang", "Đà Nẵng", "Miền Trung", 5,
     "Complex GM", "Andre Pierre Gentzsch",
     "https://www.linkedin.com/search/results/people/?keywords=Andre+Gentzsch+Furama+Danang"),

    ("Melia Danang Beach Resort", "Đà Nẵng", "Miền Trung", 5,
     "General Manager", "Doo Hyun Shim",
     "https://www.linkedin.com/search/results/people/?keywords=Doo+Hyun+Shim+Melia+Danang"),

    ("Hilton Da Nang", "Đà Nẵng", "Miền Trung", 5,
     "General Manager", "Jesper Bach Larsen",
     "https://www.linkedin.com/search/results/people/?keywords=Jesper+Larsen+Hilton+Danang"),

    ("Hilton Da Nang", "Đà Nẵng", "Miền Trung", 5,
     "Commercial Head", "CamThu Nguyen",
     "https://www.linkedin.com/search/results/people/?keywords=CamThu+Nguyen+Hilton+Danang"),

    ("Fusion Resort & Villas Da Nang", "Đà Nẵng", "Miền Trung", 5,
     "General Manager", "Mario Mendis",
     "https://www.linkedin.com/search/results/people/?keywords=Mario+Mendis+Fusion+Danang"),

    ("Shilla Monogram Quangnam Danang", "Đà Nẵng", "Miền Trung", 5,
     "General Manager", "Piotr Madej",
     "https://www.linkedin.com/in/piotr-madej-5a863b82/"),

    ("Vinpearl Resort & Villas Da Nang", "Đà Nẵng", "Miền Trung", 5,
     "Area GM", "Brett Burton",
     "https://www.linkedin.com/search/results/people/?keywords=Brett+Burton+Vinpearl+Danang"),

    ("The Ocean Resort Da Nang", "Đà Nẵng", "Miền Trung", 5,
     "General Manager", "Manh Quan Le",
     "https://www.linkedin.com/search/results/people/?keywords=Manh+Quan+Le+Ocean+Resort+Danang"),

    ("Grand Tourane Hotel Da Nang", "Đà Nẵng", "Miền Trung", 4,
     "General Manager", "Quang Lam Tri",
     "https://www.linkedin.com/search/results/people/?keywords=Quang+Lam+Tri+Grand+Tourane"),

    ("Aria Grand Hotel & Spa Da Nang", "Đà Nẵng", "Miền Trung", 4,
     "General Manager", "Nguyen The",
     "https://www.linkedin.com/in/nguyen-the-80582b56/"),

    ("Maison Phuong Hotel", "Đà Nẵng", "Miền Trung", 4,
     "General Manager", "Bê Trần",
     "https://www.linkedin.com/in/b%C3%AA-tr%E1%BA%A7n-816a52127"),

    ("Novotel Danang Premier Han River", "Đà Nẵng", "Miền Trung", 4,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Novotel+Danang"),

    ("Crowne Plaza Danang", "Đà Nẵng", "Miền Trung", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Crowne+Plaza+Danang"),

    ("Premier Village Danang Resort", "Đà Nẵng", "Miền Trung", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Premier+Village+Danang"),

    # ══════════════════════════════════════════════════════
    # HỘI AN
    # ══════════════════════════════════════════════════════
    ("Four Seasons Resort The Nam Hai", "Hội An", "Miền Trung", 5,
     "General Manager", "Marcel Oostenbrink",
     "https://www.linkedin.com/search/results/people/?keywords=Marcel+Oostenbrink+Four+Seasons+Nam+Hai"),

    ("Hotel Royal Hoi An – MGallery", "Hội An", "Miền Trung", 5,
     "Managing Director", "Sven Saebel",
     "https://www.linkedin.com/search/results/people/?keywords=Sven+Saebel+Hotel+Royal+Hoi+An"),

    ("TUI BLUE Nam Hoi An Resort", "Hội An", "Miền Trung", 5,
     "General Manager", "Anton Bespalov",
     "https://www.linkedin.com/in/anton-bespalov-382a35a/"),

    ("Renaissance Hoi An Resort & Spa", "Hội An", "Miền Trung", 5,
     "General Manager", "Piyoros Naronglith",
     "https://www.linkedin.com/search/results/people/?keywords=Piyoros+Naronglith+Renaissance+Hoi+An"),

    ("Anantara Hoi An Resort", "Hội An", "Miền Trung", 5,
     "General Manager", "Christian Gerart",
     "https://www.linkedin.com/search/results/people/?keywords=Christian+Gerart+Anantara+Hoi+An"),

    ("Namia River Retreat Hoi An", "Hội An", "Miền Trung", 5,
     "General Manager", "Michelle Ford",
     "https://www.linkedin.com/search/results/people/?keywords=Michelle+Ford+Hoi+An"),

    ("Sunrise Premium Resort Hoi An", "Hội An", "Miền Trung", 4,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Sunrise+Premium+Hoi+An"),

    ("Vinpearl Resort & Spa Hoi An", "Hội An", "Miền Trung", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Vinpearl+Hoi+An"),

    # ══════════════════════════════════════════════════════
    # HUẾ & LĂNG CÔ
    # ══════════════════════════════════════════════════════
    ("Banyan Tree Lăng Cô", "Lăng Cô", "Miền Trung", 5,
     "General Manager", "Le Anh Tuan",
     "https://www.linkedin.com/search/results/people/?keywords=Le+Anh+Tuan+Banyan+Tree+Lang+Co"),

    ("Angsana Lăng Cô", "Lăng Cô", "Miền Trung", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Angsana+Lang+Co"),

    ("Vedana Resort Huế", "Huế", "Miền Trung", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Vedana+Resort+Hue"),

    ("Pilgrimage Village Boutique Resort", "Huế", "Miền Trung", 4,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Pilgrimage+Village+Hue"),

    ("La Residence Hotel & Spa Hue", "Huế", "Miền Trung", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+La+Residence+Hue"),

    # ══════════════════════════════════════════════════════
    # QUY NHƠN
    # ══════════════════════════════════════════════════════
    ("Anantara Quy Nhon Villas", "Quy Nhơn", "Miền Trung", 5,
     "General Manager", "Peter Steger",
     "https://www.linkedin.com/search/results/people/?keywords=Peter+Steger+Anantara+Quy+Nhon"),

    ("Avani Quy Nhon Resort", "Quy Nhơn", "Miền Trung", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Avani+Quy+Nhon"),

    ("FLC Luxury Resort Quy Nhon", "Quy Nhơn", "Miền Trung", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+FLC+Quy+Nhon"),

    # ══════════════════════════════════════════════════════
    # NHA TRANG
    # ══════════════════════════════════════════════════════
    ("Amiana Resort Nha Trang", "Nha Trang", "Miền Nam", 5,
     "General Manager", "Roland Svensson",
     "https://www.linkedin.com/search/results/people/?keywords=Roland+Svensson+Amiana+Nha+Trang"),

    ("Vinpearl Resort & Spa Nha Trang Bay", "Nha Trang", "Miền Nam", 5,
     "General Manager", "Giles Selves",
     "https://www.linkedin.com/search/results/people/?keywords=Giles+Selves+Vinpearl+Nha+Trang"),

    ("Sheraton Nha Trang Hotel & Spa", "Nha Trang", "Miền Nam", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Sheraton+Nha+Trang"),

    ("InterContinental Nha Trang", "Nha Trang", "Miền Nam", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+InterContinental+Nha+Trang"),

    ("Mia Resort Nha Trang", "Nha Trang", "Miền Nam", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Mia+Resort+Nha+Trang"),

    ("Six Senses Ninh Van Bay", "Nha Trang", "Miền Nam", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Six+Senses+Ninh+Van+Bay"),

    # ══════════════════════════════════════════════════════
    # CAM RANH
    # ══════════════════════════════════════════════════════
    ("Alma Resort Cam Ranh", "Cam Ranh", "Miền Nam", 5,
     "Managing Director", "Herbert Laubichler-Pichler",
     "https://www.linkedin.com/search/results/people/?keywords=Herbert+Laubichler+Alma+Resort"),

    ("The Anam Cam Ranh", "Cam Ranh", "Miền Nam", 5,
     "General Manager", "Thierry Le Ponner",
     "https://www.linkedin.com/search/results/people/?keywords=Thierry+Le+Ponner+Anam+Cam+Ranh"),

    ("Radisson Blu Resort Cam Ranh", "Cam Ranh", "Miền Nam", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Radisson+Cam+Ranh"),

    ("Mövenpick Resort Cam Ranh", "Cam Ranh", "Miền Nam", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Movenpick+Cam+Ranh"),

    # ══════════════════════════════════════════════════════
    # PHAN THIẾT / MŨI NÉ
    # ══════════════════════════════════════════════════════
    ("Centara Mirage Resort Mui Ne", "Phan Thiết", "Miền Nam", 5,
     "General Manager", "Fabian Singer",
     "https://www.linkedin.com/search/results/people/?keywords=Fabian+Singer+Centara+Mui+Ne"),

    ("Anantara Mui Ne Resort", "Phan Thiết", "Miền Nam", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Anantara+Mui+Ne"),

    ("TTC Resort Phan Thiet", "Phan Thiết", "Miền Nam", 4,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+TTC+Resort+Phan+Thiet"),

    # ══════════════════════════════════════════════════════
    # PHÚ QUỐC
    # ══════════════════════════════════════════════════════
    ("JW Marriott Phu Quoc Emerald Bay", "Phú Quốc", "Miền Nam", 5,
     "General Manager", "David Turnbull",
     "https://www.linkedin.com/search/results/people/?keywords=David+Turnbull+JW+Marriott+Phu+Quoc"),

    ("InterContinental Phu Quoc Long Beach", "Phú Quốc", "Miền Nam", 5,
     "General Manager", "Daniel Solombrino",
     "https://www.linkedin.com/search/results/people/?keywords=Daniel+Solombrino+InterContinental+Phu+Quoc"),

    ("Regent Phu Quoc", "Phú Quốc", "Miền Nam", 5,
     "General Manager", "Alexander Wong",
     "https://www.linkedin.com/search/results/people/?keywords=Alexander+Wong+Regent+Phu+Quoc"),

    ("Fusion Resort Phu Quoc", "Phú Quốc", "Miền Nam", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Fusion+Resort+Phu+Quoc"),

    ("Salinda Resort Phu Quoc", "Phú Quốc", "Miền Nam", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Salinda+Resort+Phu+Quoc"),

    ("Premier Residences Phu Quoc", "Phú Quốc", "Miền Nam", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Premier+Residences+Phu+Quoc"),

    ("Vinpearl Discovery Phu Quoc", "Phú Quốc", "Miền Nam", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Vinpearl+Discovery+Phu+Quoc"),

    # ══════════════════════════════════════════════════════
    # ĐÀ LẠT
    # ══════════════════════════════════════════════════════
    ("Ana Mandara Villas Dalat", "Đà Lạt", "Tây Nguyên", 5,
     "General Manager", "Jean-Philippe Jacopin",
     "https://www.linkedin.com/search/results/people/?keywords=Jean+Philippe+Jacopin+Ana+Mandara+Dalat"),

    ("Dalat Palace Heritage Hotel", "Đà Lạt", "Tây Nguyên", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Dalat+Palace+Heritage"),

    ("Terracotta Hotel & Resort Da Lat", "Đà Lạt", "Tây Nguyên", 4,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Terracotta+Dalat"),

    # ══════════════════════════════════════════════════════
    # HÀ NỘI
    # ══════════════════════════════════════════════════════
    ("Sofitel Legend Metropole Hanoi", "Hà Nội", "Miền Bắc", 5,
     "General Manager", "Nguyen Quang Hung",
     "https://www.linkedin.com/search/results/people/?keywords=Nguyen+Quang+Hung+Sofitel+Metropole+Hanoi"),

    ("Capella Hanoi", "Hà Nội", "Miền Bắc", 5,
     "General Manager", "Pham Duc Toan",
     "https://www.linkedin.com/search/results/people/?keywords=Pham+Duc+Toan+Capella+Hanoi"),

    ("Lotte Hotel Hanoi", "Hà Nội", "Miền Bắc", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Lotte+Hotel+Hanoi"),

    ("JW Marriott Hotel Hanoi", "Hà Nội", "Miền Bắc", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+JW+Marriott+Hanoi"),

    ("Sheraton Hanoi Hotel", "Hà Nội", "Miền Bắc", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Sheraton+Hanoi"),

    ("Melia Hanoi", "Hà Nội", "Miền Bắc", 5,
     "General Manager", "",
     "https://www.linkedin.com/search/results/people/?keywords=General+Manager+Melia+Hanoi"),
]

# Nhóm theo khu vực
def get_by_region():
    from collections import defaultdict
    grouped = defaultdict(list)
    for entry in HOTEL_DIRECTORY:
        hotel, city, region, star, title, name, url = entry
        grouped[region].append({
            "hotel": hotel, "city": city, "star": star,
            "title": title, "name": name, "url": url
        })
    return dict(grouped)

def get_by_city():
    from collections import defaultdict
    grouped = defaultdict(list)
    for entry in HOTEL_DIRECTORY:
        hotel, city, region, star, title, name, url = entry
        grouped[city].append({
            "hotel": hotel, "star": star,
            "title": title, "name": name, "url": url
        })
    return dict(grouped)

ALL_CITIES = sorted(set(e[1] for e in HOTEL_DIRECTORY))
ALL_REGIONS = sorted(set(e[2] for e in HOTEL_DIRECTORY))
