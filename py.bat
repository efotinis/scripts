@ECHO OFF & SETLOCAL ENABLEEXTENSIONS
:: PYTHON.EXE wrapper.
:: ECHO.(C) Elias Fotinis

SET exe=%ProgramFiles%\Python26\python.exe

:: Python.exe doesn't support /?; it uses -h instead
hasHelp %* || GOTO skipHelp

"%exe%" -h
GOTO :EOF
:skipHelp

"%exe%" %*
