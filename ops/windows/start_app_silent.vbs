Option Explicit

Dim shell, fso, scriptDir, batPath, cmd
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batPath = scriptDir & "\start_app.bat"

cmd = Chr(34) & batPath & Chr(34)
' 0 = hidden window, False = do not wait
shell.Run cmd, 0, False
