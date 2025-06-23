import sqlite3
import pandas as pd

# === 1. Load data from Excel ===
# adjust the path to wherever your file is
excel_path = "customers.xlsx"
df = pd.read_excel(excel_path)

# ensure these columns exist in your sheet:
# ['CustomerCode', 'FullName', 'Role', 'SuperiorCode']
expected = {"CustomerCode","FullName","Role","SuperiorCode"}
if not expected.issubset(df.columns):
    missing = expected - set(df.columns)
    raise RuntimeError(f"Missing columns in Excel: {missing}")

# === 2. Connect to (or create) the database ===
conn = sqlite3.connect("sales.db")
cur  = conn.cursor()

# === 3. Create the table if it doesn't exist ===
cur.execute("""
CREATE TABLE IF NOT EXISTS customers (
    CustomerCode TEXT PRIMARY KEY,
    FullName     TEXT NOT NULL,
    Role         TEXT NOT NULL,
    SuperiorCode TEXT
)
""")

# === 4. Seed from the DataFrame ===
# Convert to a list of tuples
records = df[["CustomerCode","FullName","Role","SuperiorCode"]].itertuples(
    index=False, name=None
)

cur.executemany("""
    INSERT OR REPLACE INTO customers
      (CustomerCode, FullName, Role, SuperiorCode)
    VALUES (?, ?, ?, ?)
""", records)

# === 5. Commit & clean up ===
conn.commit()
conn.close()

print("✅ sales.db updated from Excel source!") 
