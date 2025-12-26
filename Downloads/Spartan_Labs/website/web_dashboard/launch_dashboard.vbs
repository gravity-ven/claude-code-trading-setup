Set WshShell = WScript.CreateObject("WScript.Shell")
' Start Server (Hidden)
WshShell.Run "pythonw.exe server.py", 0, False
WScript.Sleep 2000
' Open Browser
WshShell.Run "http://localhost:5000"
