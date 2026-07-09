Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batchPath = fso.BuildPath(scriptDir, "sync_auto.bat")

Set WshShell = CreateObject("WScript.Shell")
' Executa o script batch de sincronizacao de forma totalmente invisivel (0 = janela oculta)
WshShell.Run chr(34) & batchPath & chr(34), 0, True
Set WshShell = Nothing
