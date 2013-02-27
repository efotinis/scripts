:: Setup CLI tools for different versions of Visual Studio.

@ECHO OFF

SET CL_DEFAULT_PARAMS=/nologo

IF '%1'=='' GOTO usage
IF '%1'=='/?' GOTO usage
IF '%1'=='-h' GOTO usage

SET VER=%1
SHIFT
rem IF %VER%==6 GOTO VC60
rem IF %VER%==6.0 GOTO VC60
rem IF %VER%==71 GOTO VC71
rem IF %VER%==7.1 GOTO VC71
rem IF %VER%==2003 GOTO VC71
IF %VER%==9 GOTO VC90
IF %VER%==9.0 GOTO VC90
IF %VER%==2008 GOTO VC90
IF %VER%==10 GOTO VC100
IF %VER%==10.0 GOTO VC100
IF %VER%==2010 GOTO VC100
ECHO ERROR: Unsupported version ID.
GOTO usage

:usage
ECHO Usage: VC.CMD id [args...]
ECHO    id      the Visual Studio version (X, X.Y, or year)
ECHO    args    up to 9 params to pass to the Visual Studio script
ECHO            that sets up the environment (mainly the platform)
GOTO :EOF


rem :VC60
rem SET NAME=Visual Studio 6.0
rem SET BATCH=C:\DevTools\VS6\VC98\Bin\VCVARS32.BAT %1 %2 %3 %4 %5 %6 %7 %8 %9
rem GOTO exec

rem :VC71
rem SET NAME=Visual Studio .NET 2003
rem SET BATCH=D:\dev\VS7.1\Common7\Tools\vsvars32.bat %1 %2 %3 %4 %5 %6 %7 %8 %9
rem GOTO exec

:VC90
SET NAME=Visual Studio 2008
SET BATCH="%VS90COMNTOOLS%\..\..\VC\vcvarsall.bat" %1 %2 %3 %4 %5 %6 %7 %8 %9
GOTO exec

:VC100
SET NAME=Visual Studio 2010
SET BATCH="%VS100COMNTOOLS%\..\..\VC\vcvarsall.bat" %1 %2 %3 %4 %5 %6 %7 %8 %9
GOTO exec


:exec
TITLE %NAME%
CALL %BATCH%
SET CL=%CL% %CL_DEFAULT_PARAMS%
ECHO CL=%CL%

:: cleanup vars, since we can't use SETLOCAL
SET VER=
SET NAME=
SET BATCH=
SET CL_DEFAULT_PARAMS%=
