import os
import sqlite3
import subprocess

CONVS_DIR = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\conversations"
BRAIN_DIR = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\brain"
BUILD_SCRIPT = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\scratch\build_agyhub.py"

def main():
    print("=" * 60)
    print("APAGANDO CONVERSAS VAZIAS (UNTITLED / 0 PASSOS)")
    print("=" * 60)
    
    db_files = [f for f in os.listdir(CONVS_DIR) if f.endswith(".db")]
    deleted_count = 0
    
    for db_file in db_files:
        db_path = os.path.join(CONVS_DIR, db_file)
        convo_id = os.path.splitext(db_file)[0]
        
        # Ignorar a conversa ativa atual por seguranca
        if "7a20de95" in db_file:
            continue
            
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cur = conn.cursor()
            
            # Verificar se a tabela steps existe
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='steps'")
            if cur.fetchone():
                cur.execute("SELECT COUNT(*) FROM steps")
                step_count = cur.fetchone()[0]
                conn.close()
                
                # Se nao tiver nenhum passo
                if step_count == 0:
                    print(f"  [VAZIA] Encontrada conversa {db_file[:8]} (0 passos). Apagando...")
                    
                    # Deletar os arquivos do banco de dados
                    for suffix in ["", "-wal", "-shm"]:
                        f_to_del = db_path + suffix
                        if os.path.exists(f_to_del):
                            try:
                                os.remove(f_to_del)
                            except Exception as del_err:
                                print(f"    x Erro ao deletar {os.path.basename(f_to_del)}: {del_err}")
                                
                    # Deletar a pasta brain correspondente
                    brain_path = os.path.join(BRAIN_DIR, convo_id)
                    if os.path.isdir(brain_path):
                        try:
                            import shutil
                            shutil.rmtree(brain_path)
                            print(f"    [OK] Pasta brain de {db_file[:8]} removida.")
                        except Exception as brain_err:
                            print(f"    x Erro ao deletar pasta brain {convo_id[:8]}: {brain_err}")
                            
                    deleted_count += 1
            else:
                conn.close()
        except Exception as e:
            print(f"  x Erro ao ler banco {db_file[:8]}: {e}")
            
    print(f"\nTotal de conversas vazias apagadas: {deleted_count}")
    
    if deleted_count > 0:
        print("\nRegenerando o indice com build_agyhub.py --apply...")
        try:
            subprocess.run(["python", BUILD_SCRIPT, "--apply"], check=True)
            print("Indice regenerado com sucesso!")
        except Exception as e:
            print(f"Erro ao regenerar o indice: {e}")
    else:
        print("\nNenhuma conversa vazia adicional encontrada.")

if __name__ == "__main__":
    main()
