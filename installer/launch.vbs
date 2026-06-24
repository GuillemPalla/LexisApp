Set objShell = CreateObject("WScript.Shell")
objShell.Run """" & Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\")) & "launch.bat""", 0, False