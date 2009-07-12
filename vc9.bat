@ECHO OFF
IF '%1'=='/?' (
    ECHO Setup VC9 cmdline tools.
    GOTO :EOF
)
CALL "%vs90comntools%\..\..\VC\vcvarsall.bat" %*
TITLE VC9
SET CL=/nologo
