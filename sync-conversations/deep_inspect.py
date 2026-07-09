"""
Deep inspection of agyhub_summaries_proto.pb and conversation databases.
Goal: understand why conversations don't appear in the sidebar.
"""
import os
import sqlite3
import struct

def decode_varint(data, pos):
    result, shift = 0, 0
    while pos < len(data):
        b = data[pos]
        result |= (b & 0x7F) << shift
        pos += 1
        if (b & 0x80) == 0:
            return result, pos
        shift += 7
    raise ValueError(f"Varint extends past end of data at pos {pos}")

def parse_protobuf_full(data, depth=0):
    """Parse protobuf data, returning list of (field_num, wire_type, value) tuples"""
    fields = []
    pos = 0
    indent = "  " * depth
    while pos < len(data):
        try:
            tag, pos = decode_varint(data, pos)
        except (ValueError, IndexError):
            break
        wire = tag & 7
        field_num = tag >> 3

        if wire == 0:  # varint
            val, pos = decode_varint(data, pos)
            fields.append((field_num, wire, val))
        elif wire == 1:  # 64-bit
            val = data[pos:pos+8]
            pos += 8
            fields.append((field_num, wire, val))
        elif wire == 2:  # length-delimited
            length, pos = decode_varint(data, pos)
            raw = data[pos:pos+length]
            pos += length
            # Try to parse as nested protobuf, otherwise keep as bytes
            try:
                nested = parse_protobuf_full(raw, depth+1)
                if nested:
                    fields.append((field_num, wire, ('NESTED', nested, raw)))
                else:
                    fields.append((field_num, wire, raw))
            except Exception:
                fields.append((field_num, wire, raw))
        elif wire == 5:  # 32-bit
            val = data[pos:pos+4]
            pos += 4
            fields.append((field_num, wire, val))
        else:
            break  # unknown wire type, stop parsing
    return fields

def format_value(val, depth=0):
    indent = "  " * depth
    if isinstance(val, tuple) and len(val) == 3 and val[0] == 'NESTED':
        lines = ["{"]
        for fn, wt, v in val[1]:
            lines.append(f"  {indent}field_{fn}: {format_value(v, depth+1)}")
        lines.append(f"{indent}}}")
        return "\n".join(lines)
    elif isinstance(val, bytes):
        try:
            text = val.decode('utf-8')
            if all(32 <= ord(c) < 128 or c in '\n\r\t' for c in text):
                return f'"{text}"'
        except Exception:
            pass
        if len(val) <= 16:
            return f'<hex: {val.hex()}>'
        return f'<bytes len={len(val)}: {val[:16].hex()}...>'
    return str(val)

def inspect_summaries_pb():
    pb_path = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\agyhub_summaries_proto.pb"
    print(f"=== Inspecting: {pb_path} ===")
    print(f"Size: {os.path.getsize(pb_path)} bytes\n")
    
    with open(pb_path, 'rb') as f:
        data = f.read()
    
    print(f"Raw hex (first 256 bytes): {data[:256].hex()}\n")
    
    fields = parse_protobuf_full(data)
    print(f"Top-level fields count: {len(fields)}")
    for fn, wt, val in fields:
        print(f"\n  field_{fn} (wire={wt}):")
        if isinstance(val, tuple) and val[0] == 'NESTED':
            for sfn, swt, sv in val[1]:
                print(f"    field_{sfn} (wire={swt}): {format_value(sv, 2)}")
        else:
            print(f"    {format_value(val, 1)}")

def inspect_single_db(db_path, label=""):
    print(f"\n=== DB: {label or os.path.basename(db_path)} ===")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT data FROM trajectory_metadata_blob WHERE id='main'")
    row = cur.fetchone()
    if not row or not row[0]:
        print("  No trajectory_metadata_blob data!")
        conn.close()
        return
    
    data = row[0]
    print(f"  trajectory_metadata_blob size: {len(data)} bytes")
    
    fields = parse_protobuf_full(data)
    for fn, wt, val in fields:
        print(f"\n  field_{fn} (wire={wt}):")
        if isinstance(val, tuple) and val[0] == 'NESTED':
            for sfn, swt, sv in val[1]:
                print(f"    field_{sfn} (wire={swt}): {format_value(sv, 2)}")
        else:
            print(f"    {format_value(val, 1)}")
    
    conn.close()

if __name__ == "__main__":
    inspect_summaries_pb()
    
    gemini_dir = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\conversations"
    active_db = os.path.join(gemini_dir, "c0ba3c1c-82bb-4d23-b556-7bdaaa801bfe.db")
    restored_db = os.path.join(gemini_dir, "0d6e5f90-2278-42f9-9bb3-9092f3987df8.db")
    
    inspect_single_db(active_db, "ACTIVE (visible in sidebar)")
    inspect_single_db(restored_db, "RESTORED (not visible in sidebar)")
    
    print("\n\n=== FIELD-BY-FIELD DIFF ===")
    print("Comparing field values between active and restored databases...")
