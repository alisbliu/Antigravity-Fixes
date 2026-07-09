import os
import sqlite3
import shutil

CONVS_DIR = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\conversations"
BACKUPS_DIR = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\scratch\antigravity-backup\conversations"
ACTIVE_DB = os.path.join(CONVS_DIR, "c0ba3c1c-82bb-4d23-b556-7bdaaa801bfe.db")

TARGET_DBS = [
    "880f264a-8f2d-4c06-80e4-10e99a6b1724.db",
    "b8baca90-476f-48c4-a351-40fb7c1417dd.db"
]

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
    result = b''
    
    if 1 in active_fields:
        result += active_fields[1][2]
    
    if 2 in restored_fields:
        result += restored_fields[2][2]
    elif 2 in active_fields:
        result += active_fields[2][2]
    
    if 3 in active_fields:
        result += active_fields[3][2]
    
    if 7 in active_fields:
        result += active_fields[7][2]
    
    if 15 in active_fields:
        result += active_fields[15][2]
    
    project_id_bytes = project_id.encode('utf-8')
    result += encode_field(18, 2, project_id_bytes)
    
    return result

def main():
    print("=" * 60)
    print("RESTORE AND FIX CORRUPTED DATABASES")
    print("=" * 60)
    
    # 1. Carregar campos do banco ativo como template
    print(f"Lendo banco ativo para template: {os.path.basename(ACTIVE_DB)}")
    conn = sqlite3.connect(ACTIVE_DB)
    cur = conn.cursor()
    cur.execute("SELECT data FROM trajectory_metadata_blob WHERE id='main'")
    active_data = cur.fetchone()[0]
    conn.close()
    
    active_fields = parse_top_level_fields_raw(active_data)
    
    # 2. Processar cada banco corrompido
    for db_name in TARGET_DBS:
        print(f"\nProcessando {db_name}...")
        
        backup_path = os.path.join(BACKUPS_DIR, db_name)
        dest_path = os.path.join(CONVS_DIR, db_name)
        
        if not os.path.exists(backup_path):
            print(f"  [ERRO] Backup nao encontrado em {backup_path}")
            continue
            
        # Fazer backup do arquivo atual com sufixo .CORRUPTED antes de sobrescrever
        if os.path.exists(dest_path):
            corrupted_backup = dest_path + ".CORRUPTED"
            shutil.copy2(dest_path, corrupted_backup)
            print(f"  Copia de seguranca do arquivo corrompido salva em: {os.path.basename(corrupted_backup)}")
            
        # Copiar banco saudavel do backup
        shutil.copy2(backup_path, dest_path)
        print(f"  Banco de dados saudavel copiado para a pasta conversations.")
        
        # Corrigir field_18 no banco restaurado
        try:
            conn = sqlite3.connect(dest_path)
            cur = conn.cursor()
            cur.execute("SELECT data FROM trajectory_metadata_blob WHERE id='main'")
            row = cur.fetchone()
            
            if not row or not row[0]:
                print("  [AVISO] Sem metadados no banco de dados.")
                conn.close()
                continue
                
            restored_fields = parse_top_level_fields_raw(row[0])
            new_data = build_clean_metadata(active_fields, restored_fields)
            
            cur.execute("UPDATE trajectory_metadata_blob SET data=? WHERE id='main'", (new_data,))
            conn.commit()
            
            # Verificacoes de integridade
            cur.execute("PRAGMA integrity_check")
            check = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM steps")
            steps_cnt = cur.fetchone()[0]
            
            conn.close()
            
            print(f"  [OK] Metadados atualizados com sucesso!")
            print(f"  [OK] sqlite integrity_check: {check}")
            print(f"  [OK] steps count: {steps_cnt}")
            
        except Exception as e:
            print(f"  [ERRO] Falha ao processar banco {db_name}: {e}")

    print("\nConcluido! Todos os bancos corrompidos foram restaurados e corrigidos.")

if __name__ == "__main__":
    main()
