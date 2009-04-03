@ECHO OFF & SETLOCAL ENABLEEXTENSIONS & hasHelp.py %* || GOTO skipHelp
ECHO.Setup environment for command-line development tools.
ECHO.(C) Elias Fotinis
ECHO.
ECHO.TOOLS.BAT id
ECHO.
ECHO.Valid ids are:
ECHO.  vs6  Visual C++ 6.0 (*)
ECHO.  vs7  Visual Studio .NET 2003
ECHO.  tk7  Visual C++ ToolKit 2003
ECHO.  n2r  .NET Framework 2.0 Runtime
ECHO.  n2s  .NET Framework 2.0 SDK
ECHO.
ECHO.  (*) Jam is also set up for the specified tools.
GOTO :EOF
:skipHelp

:: allow SETs to persist
ENDLOCAL

IF /I "%2" EQU "vs6"  GOTO vs6

IF /I "%1" EQU "vs6"  GOTO vs6
IF /I "%1" EQU "vs7"  GOTO vs7
IF /I "%1" EQU "tk7"  GOTO tk7
IF /I "%1" EQU "n2r"  GOTO n2r
IF /I "%1" EQU "n2s"  GOTO n2s
ECHO.ERROR: Invalid tool id.
GOTO :EOF

REM ==== TODO ====
REM Also setup PSDK *after* setting each toolkit.

::-----------
:vs6
CALL "C:\Program Files\Dev\VS6\VC98\Bin\VCVARS32.BAT"
SET JAM_TOOLSET=VISUALC
SET VISUALC=C:\Program Files\Dev\VS6\VC98
GOTO :EOF

::-----------
:vs7
CALL "C:\Program Files\Dev\VS .NET 2003\Common7\Tools\vsvars32.bat"
GOTO :EOF

::-----------
:tk7
CALL "%VCToolkitInstallDir%\vcvars32.bat"
GOTO :EOF

::-----------
:n2r
SET PATH=C:\WINDOWS\MICROS~1.NET\FRAMEW~1\V20~1.507;%PATH%
GOTO :EOF

::-----------
:n2s
CALL "C:\Program Files\Dev\Microsoft.NET\SDK\v2.0\Bin\sdkvars.bat"
GOTO :EOF
