import sqlite3

DB_PATH = "directors_match.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            image_path  TEXT NOT NULL,
            area        TEXT NOT NULL,
            tags        TEXT,
            crowd_level TEXT,
            cam_iso     TEXT,
            cam_ss      TEXT,
            cam_ap      TEXT,
            cam_focal   TEXT,
            cam_ev      TEXT,
            cam_wb      TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS image_vectors (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER NOT NULL,
            vector      TEXT,
            FOREIGN KEY (location_id) REFERENCES locations(id)
        )
    """)

    existing = cur.execute("SELECT COUNT(*) FROM locations").fetchone()[0]

    if existing == 0:
        locations = [
            ("Central courtyard — Library view",    "central_courtyard.jpg",   "Between blocks, Library right",       "Wide Angle,Aerial,Green,Establishing",          "Low",    "ISO 200", "1/500s",  "f/5.6", "24mm", "+0.3 EV", "Daylight"),
            ("F Block staircase — window view",      "f_staircase_window.jpg",  "F Block, 3rd floor",                  "Geometric,Interior,Sunlit,Shadow",              "Low",    "ISO 400", "1/125s",  "f/2.8", "35mm", "0 EV",    "Auto"),
            ("F Block stairwell — top-down spiral",  "f_stairwell_spiral.jpg",  "F Block, 3rd floor",                  "Dramatic,Overhead,Graphic,Spiral",              "Low",    "ISO 800", "1/60s",   "f/4",   "16mm", "-0.3 EV", "Auto"),
            ("F Block atrium — back side",           "f_atrium_back.jpg",       "F Block, back facing",                "Multi-floor,Open,Institutional,Columns",        "Low",    "ISO 400", "1/200s",  "f/4",   "28mm", "0 EV",    "Fluorescent"),
            ("F Block corridor — balcony side",      "f_corridor.jpg",          "F Block, interior",                   "Minimalist,Long Hallway,Empty,Perspective",     "Low",    "ISO 200", "1/250s",  "f/5.6", "24mm", "0 EV",    "Daylight"),
            ("Main gate parking area",               "main_parking.jpg",        "Near main entrance gate",             "Moody,Rainy,Raw,Urban,Real Life",               "High",   "ISO 800", "1/250s",  "f/2.8", "35mm", "-0.7 EV", "Cloudy"),
            ("F Block facade — garden side",         "f_facade_garden.jpg",     "F Block, exterior front",             "Red Brick,Lush Garden,Cinematic,Colours",       "Low",    "ISO 100", "1/500s",  "f/8",   "50mm", "+0.3 EV", "Daylight"),
            ("F Block classroom — golden hour",      "f_classroom_golden.jpg",  "F Block, 3rd floor",                  "Silhouette,Golden Hour,Warm,Backlit,Emotional", "Low",    "ISO 400", "1/100s",  "f/1.8", "50mm", "-1 EV",   "Tungsten"),
            ("Main entrance tree-lined road",        "tree_lined_road.jpg",     "Main gate entrance road",             "Canopy,Arrival,Serene,Nature,Road",             "Low",    "ISO 200", "1/500s",  "f/5.6", "35mm", "0 EV",    "Shade"),
            ("Drone courtyard overview",             "drone_courtyard.jpg",     "Central campus aerial",               "Spacious,Overhead,Wide,Academic",               "Low",    "ISO 100", "1/1000s", "f/5.6", "24mm", "0 EV",    "Daylight"),
            ("Auto stand — roundabout area",         "auto_stand.jpg",          "Just outside main gate",              "Raw,Urban,Real Life,Street,Auto",               "High",   "ISO 400", "1/500s",  "f/4",   "28mm", "-0.3 EV", "Daylight"),
            ("Main ornate gate entrance",            "main_gate.jpg",           "Main gate, campus entry",             "Grand,Iconic,Arrival,Heritage,Arch",            "Medium", "ISO 100", "1/500s",  "f/8",   "35mm", "+0.3 EV", "Daylight"),
            ("SAGE 3D letters — welcome plaza",      "sage_letters_plaza.jpg",  "Inside main gate, Brahmagiri block",  "Prestigious,Poster-worthy,Identity,Plaza",      "Low",    "ISO 100", "1/640s",  "f/8",   "35mm", "+0.3 EV", "Daylight"),
        ]

        cur.executemany("""
            INSERT INTO locations
            (name, image_path, area, tags, crowd_level, cam_iso, cam_ss, cam_ap, cam_focal, cam_ev, cam_wb)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, locations)

        print(f"✅ Seeded {len(locations)} Sage University campus locations.")

    conn.commit()
    conn.close()

def get_all_locations():
    conn = get_db()
    rows = conn.execute("SELECT * FROM locations").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_location(name, image_path, area, tags, crowd_level,
                 cam_iso="", cam_ss="", cam_ap="", cam_focal="", cam_ev="", cam_wb=""):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO locations
        (name, image_path, area, tags, crowd_level, cam_iso, cam_ss, cam_ap, cam_focal, cam_ev, cam_wb)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (name, image_path, area, tags, crowd_level,
          cam_iso, cam_ss, cam_ap, cam_focal, cam_ev, cam_wb))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id
