@echo off
chcp 65001 > nul
echo ===============================================================
echo      Recuperador de Conversas do Antigravity IDE
echo ===============================================================
echo.
echo IMPORTANTE: Feche o Antigravity IDE COMPLETAMENTE antes de continuar.
echo Se a IDE estiver aberta, as alteracoes serao sobrescritas ao fechar.
echo.
pause
echo.
echo Executando reindexação de conversas...
py "%~dp0util\non_interactive_rebuild.py"
echo.
echo ===============================================================
echo PROCESSO CONCLUÍDO!
echo Agora você pode abrir o Antigravity IDE novamente.
echo ===============================================================
echo.
pause
