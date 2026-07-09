@echo off
setlocal enabledelayedexpansion

:: 1. Localiza a pasta do repositorio antigravity-backup
set "BACKUP_DIR="
if exist "C:\Users\Eduardo Barbosa\antigravity-backup" set "BACKUP_DIR=C:\Users\Eduardo Barbosa\antigravity-backup"
if not defined BACKUP_DIR if exist "%USERPROFILE%\antigravity-backup" set "BACKUP_DIR=%USERPROFILE%\antigravity-backup"
if not defined BACKUP_DIR if exist "%~dp0..\..\..\scratch\antigravity-backup" set "BACKUP_DIR=%~dp0..\..\..\scratch\antigravity-backup"

if not defined BACKUP_DIR (
    echo [ERRO] Pasta 'antigravity-backup' nao encontrada.
    exit /b 1
)

:: 2. Atualiza o repositorio de backup (Git Pull)
cd /d "!BACKUP_DIR!"
git pull --ff-only

:: 3. Importa e localiza as conversas do backup para a IDE local
python "%~dp0sync_antigravity.py" --pull --backup-dir "!BACKUP_DIR!"

:: 4. Exporta e normaliza as conversas locais para o backup
python "%~dp0sync_antigravity.py" --push --backup-dir "!BACKUP_DIR!"

:: 5. Envia as atualizacoes para o Github (Git Commit & Push)
cd /d "!BACKUP_DIR!"
git add .
git diff-index --quiet HEAD --
if errorlevel 1 (
    git commit -m "sync: auto-sync conversations"
    git push
)
