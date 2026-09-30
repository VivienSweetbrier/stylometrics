import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "synoptics.db"

def inject_john_the_baptist_pericope():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Pericope 2 (Double Tradition / Q Source)
    cursor.execute("INSERT OR IGNORE INTO pericopes (id, tradition_type) VALUES (2, 'Double')")
    
    # Matthew 3:7-10
    mat_refs = ['MAT 3:7', 'MAT 3:8', 'MAT 3:9', 'MAT 3:10']
    # Luke 3:7-9
    luk_refs = ['LUK 3:7', 'LUK 3:8', 'LUK 3:9']
    
    all_refs = mat_refs + luk_refs
    
    # Update verses using LIKE to catch any sub-verse tags like 'MAT 3:7!1'
    for ref in all_refs:
        cursor.execute(f"UPDATE verses SET pericope_id = 2 WHERE verse_ref LIKE '{ref}%'")
        
    conn.commit()
    conn.close()
    print("Successfully mapped Pericope 2: John the Baptist (Double Tradition)")

if __name__ == "__main__":
    inject_john_the_baptist_pericope()
