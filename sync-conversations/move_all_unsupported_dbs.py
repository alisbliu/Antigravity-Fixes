import os
import sqlite3
import shutil
import subprocess

CONVS_DIR = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\conversations"
UNSUPPORTED_DIR = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\scratch\unsupported_dbs"
BUILD_SCRIPT = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\scratch\build_agyhub.py"

UNSUPPORTED_TYPES = {31, 33, 38, 90, 91, 138}

def main():
    print("=" * 60)
    print("DETECTANDO E ISOLANDO BANCOS DE DADOS COM TIPOS INCOMPATIVEIS")
    print("=" * 60)
    
    if not os.path.exists(UNSUPPORTED_DIR):
        os.makedirs(UNSUPPORTED_DIR)
        
    db_files = [f for f in os.listdir(CONVS_DIR) if f.endswith(".db")]
    
    moved_count = 0
    
    for db_file in db_files:
        db_path = os.path.join(CONVS_DIR, db_file)
        
        # Ignorar o banco de dados da conversa ativa atual por seguranca
        # (Nao queremos mover a conversa onde o usuario esta digitando!)
        if "7a20de95" in db_file:
            continue
            
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cur = conn.cursor()
            
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='steps'")
            if cur.fetchone():
                cur.execute("SELECT DISTINCT step_type FROM steps")
                step_types = set(r[0] for r in cur.fetchall())
                
                # Se tiver algum tipo incompativel
                bad_types = step_types.intersection(UNSUPPORTED_TYPES)
                if bad_types:
                    conn.close() # Fechar conexao antes de mover
                    
                    src = db_path
                    dest = os.path.join(UNSUPPORTED_DIR, db_file)
                    
                    print(f"  [BAD_TYPES={list(bad_types)}] Mover {db_file[:8]}...")
                    
                    # Tentar mover o banco
                    try:
                        shutil.move(src, dest)
                        moved_count += 1
                        print(f"    [MOVIDO] {db_file[:8]} -> scratch/unsupported_dbs/")
                        
                        # Mover arquivos auxiliares do SQLite se existirem (-wal, -shm)
                        for suffix in ["-wal", "-shm"]:
                            aux_src = src + suffix
                            aux_dest = dest + suffix
                            if os.path.exists(aux_src):
                                shutil.move(aux_src, aux_dest)
                    except Exception as move_err:
                        print(f"    [ERRO AO MOVER] {db_file[:8]}: {move_err}")
                else:
                    conn.close()
            else:
                conn.close()
        except Exception as e:
            print(f"  [ERRO AO LER] {db_file[:8]}: {e}")
            
    print(f"\nTotal de bancos incompatíveis isolados: {moved_count}")
    
    # Executar a regeneracao do agyhub_summaries_proto.pb
    if moved_count > 0:
        print("\nRegenerando o indice com build_agyhub.py --apply...")
        try:
            subprocess.run(["python", BUILD_SCRIPT, "--apply"], check=True)
            print("Indice regenerado com sucesso!")
        except Exception as e:
            print(f"Erro ao regenerar o indice: {e}")
    else:
        print("\nNenhum banco de dados adicional precisou ser movido.")

if __name__ == "__main__":
    main()
