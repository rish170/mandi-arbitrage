import asyncio
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "mandi.db"

def main():
    if not DB_PATH.exists():
        print(f"Error: {DB_PATH} does not exist.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    queries = [
        ("Candidate Mandis Query", 
         "EXPLAIN QUERY PLAN SELECT DISTINCT m.id, m.name, m.district, m.state, m.lat, m.lng FROM mandis m JOIN prices p ON p.mandi_id = m.id WHERE p.commodity = 'Wheat' AND p.arrival_date >= '2026-10-14'"),
        
        ("Latest Prices Query",
         "EXPLAIN QUERY PLAN SELECT * FROM prices WHERE mandi_id IN (1, 2, 3, 4, 5) AND commodity = 'Wheat' AND arrival_date >= '2026-10-14' ORDER BY mandi_id, arrival_date DESC"),
         
        ("Trend Query",
         "EXPLAIN QUERY PLAN SELECT * FROM prices WHERE mandi_id IN (1, 2, 3) AND commodity = 'Wheat' AND arrival_date >= '2026-10-10' AND arrival_date <= '2026-10-17' ORDER BY mandi_id, arrival_date ASC"),
         
        ("Geocode Cache Lookup",
         "EXPLAIN QUERY PLAN SELECT * FROM geocode_cache WHERE key = 'pincode:440001'"),
         
        ("Distance Cache Lookup",
         "EXPLAIN QUERY PLAN SELECT * FROM distance_cache WHERE origin_key = '440001' AND mandi_id IN (1, 2, 3, 4, 5)"),
    ]

    print(f"Verifying SQLite Index Usage on {DB_PATH}:\n")
    for name, q in queries:
        print(f"--- {name} ---")
        cursor.execute(q)
        for row in cursor.fetchall():
            print(f"  id: {row[0]}, parent: {row[1]}, notused: {row[2]}, detail: {row[3]}")
        print()

    conn.close()

if __name__ == "__main__":
    main()
