@ECHO OFF & SETLOCAL ENABLEEXTENSIONS
:: 7Z.EXE wrapper.
:: (C) Elias Fotinis

:: 7z doesn't support /?; it prints help only when called without params
hasHelp %* || GOTO skipHelp
"%ProgramFiles%\7-Zip\7z.exe"
GOTO :EOF
:skipHelp

"%ProgramFiles%\7-Zip\7z.exe" %*
