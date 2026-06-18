import subprocess
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
target_script = os.path.join(script_dir, "rebuild_conversations.py")

print("--- Executando Reindexação Não-Interativa ---")

# Inputs to accept default options in rebuild_conversations.py:
# First enter to skip update check, second enter to bypass backup warnings,
# '1' to auto-assign workspaces from brain files, and subsequent enters to close.
inputs = "\n\n1\n\n\n\n"

try:
    proc = subprocess.run(
        ["py", target_script],
        input=inputs,
        text=True,
        capture_output=True,
        cwd=script_dir
    )
    
    print("LOG DA EXECUÇÃO (STDOUT):")
    print(proc.stdout)
    
    if proc.stderr:
        print("LOG DE ERROS (STDERR):")
        print(proc.stderr)
        
    print(f"Execução finalizada com código de retorno: {proc.returncode}")
except Exception as e:
    print(f"Erro ao executar o subprocesso: {e}")
