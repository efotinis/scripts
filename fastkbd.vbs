' Set keyboard rate/delay to my preferred settings.
' Used for my LG laptop which arbitrarily changes these
' whenever it starts up.
' Using a VBS script so that it can be run via the Task Scheduler
' without showing any UI (could also have used a link to a batch
' and set the link startup window option to 'hide'.)
Const SW_HIDE = 0
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c mode con rate=31 delay=0", SW_HIDE
