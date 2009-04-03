@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Creates a CBZ file for every subdir in the current dir.
ECHO.(C) Elias Fotinis
ECHO.
ECHO.(Each CBZ contains all the files of the...)
GOTO :EOF
:skipHelp

FOR /D %%D IN (*) DO @(
	PUSHD %%D
	CALL 7z a "..\%%D.cbz" -tzip -mx=0 *
	IF ERRORLEVEL 1 GOTO :EOF
	POPD
)
GOTO :EOF

