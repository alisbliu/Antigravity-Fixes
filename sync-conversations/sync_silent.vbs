Set WshShell = CreateObject("WScript.Shell")
' Executa o script batch de sincronizacao de forma totalmente invisivel (0 = janela oculta)
WshShell.Run chr(34) & "sync_auto.bat" & chr(34), 0, True
Set WshShell = Nothing
