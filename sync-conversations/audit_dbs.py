"""
Comprehensive audit of all 68 conversation databases.
Identifies:
1. URI encoding differences (forward-slash vs backslash-encoded)
2. Unusual field structures that may indicate subagent/teamwork conversations
3. Size anomalies
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

def parse_protobuf_shallow(data):
    """Parse top-level protobuf fields only"""
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

def audit_all_dbs():
    gemini_dir = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\conversations"
    db_files = sorted([f for f in os.listdir(gemini_dir) if f.endswith(".db") and not f.endswith(("-shm", "-wal"))])
    
    print(f"Total databases: {len(db_files)}\n")
    
    # Categories
    forward_slash_uri = []    # file:///e:/Cofre... (correct)
    backslash_encoded_uri = [] # file:///e%3A%5C... (possibly wrong)
    no_metadata = []
    unusual_structure = []    # has extra fields (4, 5, 6, 8, etc.)
    large_dbs = []            # >50KB - likely subagent conversations
    
    for filename in db_files:
        db_path = os.path.join(gemini_dir, filename)
        size = os.path.getsize(db_path)
        
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT data FROM trajectory_metadata_blob WHERE id='main'")
            row = cur.fetchone()
            conn.close()
            
            if not row or not row[0]:
                no_metadata.append((filename, size))
                continue
            
            data = row[0]
            fields = parse_protobuf_shallow(data)
            
            # Check field 3 (workspace ID)
            workspace_id = ""
            if 3 in fields and fields[3][0] == 'string':
                workspace_id = fields[3][1]
            
            # Check field 7 (URI)
            uri = ""
            if 7 in fields and fields[7][0] == 'string':
                uri = fields[7][1]
            
            # Check field 1 (main URI blob)
            uri_f1 = ""
            if 1 in fields and fields[1][0] == 'bytes':
                f1_data = fields[1][1]
                # First sub-field of field_1 is the URI string
                try:
                    sub_fields = parse_protobuf_shallow(f1_data)
                    if 1 in sub_fields and sub_fields[1][0] == 'string':
                        uri_f1 = sub_fields[1][1]
                except:
                    pass
            
            # Determine URI encoding
            has_backslash = "%3A%5C" in uri or "%3A%5C" in uri_f1
            has_forward = "e:/Cofre" in uri or "e:/Cofre" in uri_f1
            
            # Check for unusual fields (subagent conversations have fields 4, 5, 6, 8, etc.)
            field_keys = set(fields.keys())
            unusual = field_keys - {1, 2, 3, 7, 15, 18}  # expected normal fields
            
            if size > 50000:
                large_dbs.append((filename, size, uri or uri_f1, list(field_keys)))
            
            if unusual:
                unusual_structure.append((filename, size, list(sorted(unusual)), uri or uri_f1))
            
            if has_backslash:
                backslash_encoded_uri.append((filename, size, uri or uri_f1))
            elif has_forward or ("Cofre" in uri) or ("Cofre" in uri_f1):
                forward_slash_uri.append((filename, size, uri or uri_f1))
                
        except Exception as e:
            no_metadata.append((filename, size, str(e)))
    
    print(f"=== URI ENCODING SUMMARY ===")
    print(f"Forward-slash URI (correct, like active DB): {len(forward_slash_uri)}")
    print(f"Backslash-encoded URI (e%3A%5C format): {len(backslash_encoded_uri)}")
    print(f"No metadata: {len(no_metadata)}")
    print(f"Unusual field structure (subagent?): {len(unusual_structure)}")
    print(f"Large DBs (>50KB): {len(large_dbs)}")
    
    print(f"\n=== BACKSLASH-ENCODED URI DBs (first 10) ===")
    for item in backslash_encoded_uri[:10]:
        print(f"  {item[0]} ({item[1]} bytes): {item[2][:60]}")
    
    print(f"\n=== UNUSUAL FIELD STRUCTURE (first 10) ===")
    for item in unusual_structure[:10]:
        print(f"  {item[0]} ({item[1]} bytes) extra_fields={item[2]}: {item[3][:50]}")
    
    print(f"\n=== NO METADATA ===")
    for item in no_metadata:
        print(f"  {item}")
    
    print(f"\n=== LARGE DBs ===")
    for item in sorted(large_dbs, key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {item[0]} ({item[1]} bytes) fields={item[3]}: {item[2][:50]}")

if __name__ == "__main__":
    audit_all_dbs()
