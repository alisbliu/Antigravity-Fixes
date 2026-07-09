import sqlite3
import os

src_db = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\conversations\b8baca90-476f-48c4-a351-40fb7c1417dd.db"
dest_db = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\scratch\b8baca90_repaired.db"

if os.path.exists(dest_db):
    os.remove(dest_db)

def repair_database(src, dest):
    print(f"Iniciando reparo de {os.path.basename(src)} para {os.path.basename(dest)}...")
    conn_src = sqlite3.connect(src)
    cur_src = conn_src.cursor()
    
    conn_dest = sqlite3.connect(dest)
    cur_dest = conn_dest.cursor()
    
    # 1. Obter a lista de tabelas e seus comandos CREATE
    cur_src.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cur_src.fetchall()
    
    for table_name, create_sql in tables:
        print(f"  Processando tabela: {table_name}...")
        try:
            cur_dest.execute(create_sql)
        except Exception as e:
            print(f"    Erro ao criar tabela {table_name}: {e}")
            continue
            
        # Obter informacoes das colunas
        cur_src.execute(f"PRAGMA table_info({table_name})")
        cols = [r[1] for r in cur_src.fetchall()]
        placeholders = ", ".join(["?"] * len(cols))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({placeholders})"
        
        # Copiar dados linha por linha salvando o maximo possivel
        # Vamos tentar ler todas de uma vez primeiro. Se falhar, lemos uma por uma.
        try:
            cur_src.execute(f"SELECT * FROM {table_name}")
            rows = cur_src.fetchall()
            cur_dest.executemany(insert_sql, rows)
            print(f"    Copiadas {len(rows)} linhas com sucesso.")
        except Exception:
            print(f"    Falha na leitura em lote da tabela {table_name}. Tentando recuperar registro por registro...")
            # Recuperar registro por registro usando OFFSET
            offset = 0
            success_count = 0
            fail_count = 0
            while True:
                try:
                    cur_src.execute(f"SELECT * FROM {table_name} LIMIT 1 OFFSET {offset}")
                    row = cur_src.fetchone()
                    if row is None:
                        break
                    cur_dest.execute(insert_sql, row)
                    success_count += 1
                except Exception as row_error:
                    # Se falhar, pulamos esse registro
                    fail_count += 1
                offset += 1
            print(f"    Recuperacao individual finalizada: {success_count} salvas, {fail_count} ignoradas por corrupcao.")
            
    conn_dest.commit()
    
    # Executar integrity check no destino
    cur_dest.execute("PRAGMA integrity_check")
    check = cur_dest.fetchone()[0]
    print(f"Integrity check no banco destino: {check}")
    
    # Obter contagem de steps no destino
    try:
        cur_dest.execute("SELECT COUNT(*) FROM steps")
        print(f"Steps count no destino: {cur_dest.fetchone()[0]}")
    except Exception as e:
        print(f"Erro ao contar steps no destino: {e}")
        
    conn_src.close()
    conn_dest.close()

if __name__ == "__main__":
    repair_database(src_db, dest_db)
