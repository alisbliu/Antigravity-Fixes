import os
import shutil
import subprocess

BACKUP_DIR = r"C:\Users\Eduardo Barbosa\.gemini\antigravity\scratch\antigravity-backup"
BACKUP_CONVS = os.path.join(BACKUP_DIR, "conversations")
BACKUP_BRAIN = os.path.join(BACKUP_DIR, "brain")

UNSUPPORTED_PREFIXES = ["880f264a", "4dc9260c", "4a22489b", "b8baca90", "d66eff4e"]

def main():
    print("=" * 60)
    print("LIMPANDO BANCOS DE DADOS INCOMPATIVEIS DO REPOSITORIO DE BACKUP")
    print("=" * 60)
    
    if not os.path.isdir(BACKUP_DIR):
        print(f"[ERRO] Diretorio de backup nao encontrado em {BACKUP_DIR}")
        return
        
    removed_files = 0
    removed_dirs = 0
    
    # 1. Remover arquivos do conversations/
    if os.path.isdir(BACKUP_CONVS):
        for fname in os.listdir(BACKUP_CONVS):
            for prefix in UNSUPPORTED_PREFIXES:
                if fname.startswith(prefix):
                    path = os.path.join(BACKUP_CONVS, fname)
                    if os.path.isfile(path):
                        os.remove(path)
                        print(f"  [DELETADO] arquivo: {os.path.join('conversations', fname)}")
                        removed_files += 1
                        
    # 2. Remover pastas do brain/
    if os.path.isdir(BACKUP_BRAIN):
        for dname in os.listdir(BACKUP_BRAIN):
            for prefix in UNSUPPORTED_PREFIXES:
                if dname.startswith(prefix):
                    path = os.path.join(BACKUP_BRAIN, dname)
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                        print(f"  [DELETADA] pasta brain: {os.path.join('brain', dname)}")
                        removed_dirs += 1
                        
    print(f"\nRemovidos do backup local: {removed_files} arquivos, {removed_dirs} pastas.")
    
    # 3. Commit e push no git do backup
    if removed_files > 0 or removed_dirs > 0:
        print("\nComitando e enviando as remocoes para o GitHub...")
        try:
            subprocess.run(["git", "add", "-A"], cwd=BACKUP_DIR, check=True)
            subprocess.run(["git", "commit", "-m", "chore: remove unsupported conversations (newer IDE version incompatibility)"], cwd=BACKUP_DIR, check=True)
            subprocess.run(["git", "push"], cwd=BACKUP_DIR, check=True)
            print("Atualizacao enviada ao GitHub com sucesso!")
        except Exception as e:
            print(f"Erro ao interagir com o Git: {e}")
    else:
        print("\nNenhuma conversa incompativel encontrada no repositorio de backup.")

if __name__ == "__main__":
    main()
