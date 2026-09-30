import sqlite3
import pandas as pd
from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "processed" / "synoptics.db"
CSV_PATH = BASE_DIR / "data" / "raw" / "gospel_parallels.csv"

def expand_references(book_prefix, ref_string):
    """
    Expands European notation ('1.2-5; 2.1') into Macula SQL notation (['MAT 1:2', 'MAT 1:3'...])
    """
    if pd.isna(ref_string) or not str(ref_string).strip():
        return []
    
    expanded = []
    # Split by semicolon or comma (e.g. "1.1-4; 2.3")
    blocks = re.split(r'[;,]', str(ref_string))
    
    for block in blocks:
        block = block.strip()
        if not block: continue
        
        # Strip brackets if any e.g. "[18.11]"
        block = block.replace('[', '').replace(']', '')
        
        if '-' in block:
            parts = block.split('-')
            start = parts[0]
            end = parts[1]
            try:
                ch, v_start = start.split('.')
                # Sometimes end has chapter too, e.g. "1.25-2.5", but we checked and none exist.
                # However, if they do, we'll gracefully skip to avoid crashing
                if '.' not in end:
                    v_end = int(end)
                    for v in range(int(v_start), v_end + 1):
                        expanded.append(f"{book_prefix} {ch}:{v}")
            except Exception:
                pass # skip malformed
        else:
            try:
                ch, v = block.split('.')
                expanded.append(f"{book_prefix} {ch}:{v}")
            except Exception:
                pass
                
    return expanded

def import_gospel_parallels():
    if not CSV_PATH.exists():
        print(f"Error: Could not find {CSV_PATH}")
        return

    print(f"Loading Gospel Parallels from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Clearing old pericope assignments...")
    cursor.execute("UPDATE verses SET pericope_id = 0")
    cursor.execute("DELETE FROM pericopes")
    
    cursor.execute("INSERT INTO pericopes (id, tradition_type) VALUES (0, 'Unassigned')")

    mapped_count = 0
    for _, row in df.iterrows():
        p_id = row['pericope_id']
        trad_type = row.get('tradition_type', 'Mapped')
        
        cursor.execute("INSERT OR REPLACE INTO pericopes (id, tradition_type) VALUES (?, ?)", (p_id, trad_type))
        
        refs = []
        refs.extend(expand_references('MAT', row.get('mat_refs', '')))
        refs.extend(expand_references('MRK', row.get('mrk_refs', '')))
        refs.extend(expand_references('LUK', row.get('luk_refs', '')))
        refs.extend(expand_references('JHN', row.get('jhn_refs', '')))
        
        for ref in refs:
            # Using LIKE to catch sub-verses like 'MAT 3:7!1'
            cursor.execute("UPDATE verses SET pericope_id = ? WHERE verse_ref LIKE ?", (p_id, f"{ref}%"))
            
        mapped_count += 1
            
    conn.commit()
    conn.close()
    
    print(f"✅ Successfully mapped {mapped_count} pericopes into the database!")

if __name__ == "__main__":
    import_gospel_parallels()
