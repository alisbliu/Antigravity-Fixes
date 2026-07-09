"""
DEFINITIVE FIX: Repair all conversation databases so they are visible in the sidebar.

Root causes identified:
1. field_18 in trajectory_metadata_blob must contain a plain UTF-8 string with the 
   project ID ("e1d2e2cc-71fe-4fe5-86cd-f6ecf0deaa4f"), NOT a nested protobuf message.
   The sync script was encoding it as nested protobuf bytes, which the Language Server rejects.

2. field_1 (workspace URI blob) may use backslash-encoded paths in some DBs vs forward-slash.
   The active DB uses forward-slash in field_1 sub-fields but backslash-encoded in field_7.
   This seems acceptable since the active DB (c0ba3c1c) is visible with backslash in field_7.

Strategy:
- Read the active DB's trajectory_metadata_blob as the "golden template"
- For each restored DB, preserve ONLY the core identity fields (field_1, field_2, field_3, field_7, field_15, field_18)
- Write field_18 as a plain UTF-8 string, not a nested protobuf
- Copy the exact bytes from the active DB for field_1 (workspace URI blob)
"""
import os
import sqlite3
import struct
import shutil
from datetime import datetime

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

def encode_varint(value):
    bits = value & 0x7F
    value >>= 7
    result = b''
    while value:
        result += bytes([0x80 | bits])
        bits = value & 0x7F
        value >>= 7
    result += bytes([bits])
    return result

def encode_field(field_num, wire_type, value):
    tag = (field_num << 3) | wire_type
    tag_bytes = encode_varint(tag)
    if wire_type == 0:
        return tag_bytes + encode_varint(value)
    elif wire_type == 2:
        return tag_bytes + encode_varint(len(value)) + value
    raise ValueError(f"Unsupported wire type {wire_type}")

def parse_top_level_fields_raw(data):
    """Return dict of field_num -> (wire_type, raw_bytes_or_value, original_bytes)"""
    fields = {}
    pos = 0
    while pos < len(data):
        start_pos = pos
        try:
            tag, pos = decode_varint(data, pos)
        except (ValueError, IndexError):
            break
        wire = tag & 7
        field_num = tag >> 3
        
        if wire == 0:
            val, pos = decode_varint(data, pos)
            fields[field_num] = (wire, val, data[start_pos:pos])
        elif wire == 1:
            val = data[pos:pos+8]
            pos += 8
            fields[field_num] = (wire, val, data[start_pos:pos])
        elif wire == 2:
            length, pos = decode_varint(data, pos)
            raw = data[pos:pos+length]
            pos += length
            fields[field_num] = (wire, raw, data[start_pos:pos])
        elif wire == 5:
            val = data[pos:pos+4]
            pos += 4
            fields[field_num] = (wire, val, data[start_pos:pos])
        else:
            break
    return fields

def build_clean_metadata(active_fields, restored_fields, project_id="e1d2e2cc-71fe-4fe5-86cd-f6ecf0deaa4f"):
    """Build clean metadata blob using active DB's template with proper field_18"""
    result = b''
    
    # field_1: workspace URI blob - use ACTIVE db's version (has correct forward-slash encoding)
    if 1 in active_fields:
        result += active_fields[1][2]  # original bytes
    
    # field_2: timestamp - use RESTORED db's own timestamp (preserve original conversation time)
    if 2 in restored_fields:
        result += restored_fields[2][2]
    elif 2 in active_fields:
        result += active_fields[2][2]
    
    # field_3: workspace ID - use active DB's workspace ID
    workspace_id = "3ae525be-9700-4a3c-82f5-ba518b35516a"
    if 3 in active_fields:
        result += active_fields[3][2]
    
    # field_7: URI - use active DB's version
    if 7 in active_fields:
        result += active_fields[7][2]
    
    # field_15: use active DB's field_15 if available
    if 15 in active_fields:
        result += active_fields[15][2]
    
    # field_18: CRITICAL - must be a plain UTF-8 string, NOT nested protobuf
    # The active DB reads this as a plain string "e1d2e2cc-71fe-4fe5-86cd-f6ecf0deaa4f"
    project_id_bytes = project_id.encode('utf-8')
    result += encode_field(18, 2, project_id_bytes)
    
    return result

def fix_all_databases(dry_run=True):
    gemini_dir = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\conversations"
    active_db_path = os.path.join(gemini_dir, "c0ba3c1c-82bb-4d23-b556-7bdaaa801bfe.db")
    
    print(f"=== {'DRY RUN' if dry_run else 'LIVE FIX'}: Repairing conversation databases ===\n")
    
    # Load active DB's template fields
    conn = sqlite3.connect(active_db_path)
    cur = conn.cursor()
    cur.execute("SELECT data FROM trajectory_metadata_blob WHERE id='main'")
    active_data = cur.fetchone()[0]
    conn.close()
    
    active_fields = parse_top_level_fields_raw(active_data)
    print(f"Active DB fields: {sorted(active_fields.keys())}")
    
    # Verify field_18 in active DB
    if 18 in active_fields:
        f18 = active_fields[18]
        try:
            f18_text = f18[1].decode('utf-8') if isinstance(f18[1], bytes) else str(f18[1])
            print(f"Active DB field_18 (should be plain string): \"{f18_text}\"")
        except:
            print(f"Active DB field_18 (bytes): {f18[1].hex()}")
    
    print()
    
    # Process all databases
    db_files = sorted([f for f in os.listdir(gemini_dir) if f.endswith(".db") and not f.endswith(("-shm", "-wal"))])
    
    skipped = 0
    fixed = 0
    errors = 0
    
    for filename in db_files:
        if filename == "c0ba3c1c-82bb-4d23-b556-7bdaaa801bfe.db":
            print(f"  SKIP (active): {filename}")
            skipped += 1
            continue
        
        db_path = os.path.join(gemini_dir, filename)
        
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT data FROM trajectory_metadata_blob WHERE id='main'")
            row = cur.fetchone()
            conn.close()
            
            if not row or not row[0]:
                print(f"  SKIP (no metadata): {filename}")
                skipped += 1
                continue
            
            restored_fields = parse_top_level_fields_raw(row[0])
            
            # Check if field_18 is correct (plain string)
            f18_ok = False
            if 18 in restored_fields:
                f18_raw = restored_fields[18][1]
                if isinstance(f18_raw, bytes):
                    try:
                        f18_text = f18_raw.decode('utf-8')
                        if 'e1d2e2cc' in f18_text or len(f18_text) == 36:
                            f18_ok = True
                    except:
                        pass
            
            if f18_ok and sorted(restored_fields.keys()) == sorted(active_fields.keys()):
                # Already correct format
                print(f"  OK (already correct): {filename}")
                skipped += 1
                continue
            
            # Build clean metadata
            new_data = build_clean_metadata(active_fields, restored_fields)
            
            if dry_run:
                print(f"  WOULD FIX: {filename} ({len(row[0])} -> {len(new_data)} bytes)")
                print(f"    Old fields: {sorted(restored_fields.keys())}")
                print(f"    New size: {len(new_data)} bytes (active is {len(active_data)} bytes)")
            else:
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("UPDATE trajectory_metadata_blob SET data=? WHERE id='main'", (new_data,))
                conn.commit()
                conn.close()
                print(f"  FIXED: {filename}")
                fixed += 1
                
        except Exception as e:
            print(f"  ERROR: {filename}: {e}")
            errors += 1
    
    print(f"\n=== Summary: skipped={skipped}, fixed={fixed}, errors={errors} ===")
    
    if dry_run:
        print("\nRun with dry_run=False to apply fixes.")

if __name__ == "__main__":
    import sys
    dry_run = "--apply" not in sys.argv
    fix_all_databases(dry_run=dry_run)
