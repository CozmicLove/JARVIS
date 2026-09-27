Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
projectPath = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = projectPath
pythonPath = projectPath & "\kokoro_env\Scripts\pythonw.exe"
scriptPath = projectPath & "\src\ui\control_center.py"

If Not fso.FileExists(pythonPath) Then
    pythonPath = projectPath & "\kokoro_env\Scripts\python.exe"
End If

shell.Environment("PROCESS")("PYTHONUTF8") = "1"
shell.Environment("PROCESS")("PYTHONIOENCODING") = "utf-8"
shell.Run """" & pythonPath & """ """ & scriptPath & """", 1, False
