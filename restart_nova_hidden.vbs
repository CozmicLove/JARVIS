Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
projectPath = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = projectPath
WScript.Sleep 5000
shell.Run "wscript.exe """ & projectPath & "\start_nova_hidden.vbs" & """", 0, False
