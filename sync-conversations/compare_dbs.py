"""
Determine exactly what field_6 contains and compare with field_3 (workspace ID).
Also check if the active DB has field_6 or not.
"""
import os
import sqlite3

def decode_varint(data, pos):
    result, shift = 0, 0
    while pos < len(data):
        b = data[pos]
        result |= (b & 0x7F) << shift
        pos += 1
        if (b & 0x80) == 0:
            return result, pos
        shift += 7
    raise ValueError(f"Varint extends past end at pos {pos}")

def parse_top_level_fields(data):
    """Return dict of field_num -> (wire_type, raw_bytes_or_value)"""
    fields = {}
    pos = 0
    while pos < len(data):
        try:
            tag, pos = decode_varint(data, pos)
        except (ValueError, IndexError):
            break
        wire = tag & 7
        field_num = tag >> 3
        
        if wire == 0:
            val, pos = decode_varint(data, pos)
            fields[field_num] = ('varint', val)
        elif wire == 1:
            val = data[pos:pos+8]
            pos += 8
            fields[field_num] = ('64bit', val)
        elif wire == 2:
            length, pos = decode_varint(data, pos)
            raw = data[pos:pos+length]
            pos += length
            try:
                text = raw.decode('utf-8')
                fields[field_num] = ('string', text)
            except Exception:
                fields[field_num] = ('bytes', raw)
        elif wire == 5:
            val = data[pos:pos+4]
            pos += 4
            fields[field_num] = ('32bit', val)
        else:
            break
    return fields

def compare_databases():
    gemini_dir = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\conversations"
    
    # Get the active conversation file (the one visible in sidebar)
    active_path = os.path.join(gemini_dir, "c0ba3c1c-82bb-4d23-b556-7bdaaa801bfe.db")
    
    # Select a few DBs with different characteristics
    test_dbs = {
        "ACTIVE (c0ba3c1c)": active_path,
        "backslash+extra_field6 (0d6e5f90)": os.path.join(gemini_dir, "0d6e5f90-2278-42f9-9bb3-9092f3987df8.db"),
        "forward+extra_fields (0487250a)": os.path.join(gemini_dir, "0487250a-f075-480d-b75b-f151cc69e805.db"),
        "backslash_no_extra (880f264a)": os.path.join(gemini_dir, "880f264a-8f2d-4c06-80e4-10e99a6b1724.db"),
    }
    
    print("=== FIELD-BY-FIELD COMPARISON ===\n")
    
    for label, db_path in test_dbs.items():
        if not os.path.exists(db_path):
            print(f"{label}: FILE NOT FOUND\n")
            continue
        
        size = os.path.getsize(db_path)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT data FROM trajectory_metadata_blob WHERE id='main'")
        row = cur.fetchone()
        conn.close()
        
        if not row or not row[0]:
            print(f"{label}: NO METADATA\n")
            continue
        
        fields = parse_top_level_fields(row[0])
        
        print(f"--- {label} ({size/1024:.0f} KB) ---")
        print(f"  field_3 (workspace_id): {fields.get(3, ('N/A',))[1] if 3 in fields else 'MISSING'}")
        print(f"  field_5 (parent/subagent?): {fields.get(5, ('N/A',))[1] if 5 in fields else 'MISSING'}")
        print(f"  field_6 (second workspace?): {fields.get(6, ('N/A',))[1] if 6 in fields else 'MISSING'}")
        print(f"  field_7 (URI): {fields.get(7, ('N/A',))[1] if 7 in fields else 'MISSING'}")
        print(f"  All field numbers: {sorted(fields.keys())}")
        print()
    
    # Now check the active DB in deep - is field_6 really absent?
    print("\n=== ACTIVE DB DEEP CHECK ===")
    conn = sqlite3.connect(active_path)
    cur = conn.cursor()
    cur.execute("SELECT data FROM trajectory_metadata_blob WHERE id='main'")
    row = cur.fetchone()
    conn.close()
    
    data = row[0]
    fields = parse_top_level_fields(data)
    print(f"Active DB metadata blob hex (first 100 bytes): {data[:100].hex()}")
    print(f"Active DB all fields: {sorted(fields.keys())}")
    for k, v in sorted(fields.items()):
        if v[0] == 'string':
            print(f"  field_{k}: \"{v[1][:80]}\"")
        elif v[0] == 'varint':
            print(f"  field_{k}: {v[1]}")
        else:
            print(f"  field_{k}: <{v[0]} len={len(v[1])}>")

if __name__ == "__main__":
    compare_databases()
