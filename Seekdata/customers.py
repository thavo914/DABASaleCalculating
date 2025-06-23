import sqlite3

# 1. Connect (or create) the database file
conn = sqlite3.connect("sales.db")
cur  = conn.cursor()

# 2. Create the table with CustomerCode, FullName, Role and SuperiorCode
cur.execute("""
CREATE TABLE IF NOT EXISTS customers (
    CustomerCode TEXT PRIMARY KEY,
    FullName     TEXT NOT NULL,
    Role         TEXT NOT NULL,
    SuperiorCode TEXT
)
""")

# 3. Seed exactly your sample data
sample_customers = [
    ("NV001", "Nguyen Van A", "Catalyst",    "NV003"),
    ("NV002", "Tran Thi B",   "Catalyst",    "NV003"),
    ("NV003", "Le Van C",     "Visionary",   "NV007"),
    ("NV004", "Pham Thi D",   "Visionary",   "NV007"),
    ("NV005", "Vu Van E",     "Catalyst",    "NV004"),
    ("NV006", "Hoang Thi F",  "Catalyst",    "NV004"),
    ("NV007", "Dang Van G",   "Trailblazer", None),
]

cur.executemany("""
    INSERT OR REPLACE INTO customers
      (CustomerCode, FullName, Role, SuperiorCode)
    VALUES (?, ?, ?, ?)
""", sample_customers)

# 4. Commit & close
conn.commit()
conn.close()

print("✅ sales.db created/updated and customers table seeded with hierarchy data.")
