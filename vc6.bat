@ECHO OFF
IF '%1'=='/?' (
    ECHO Setup VC6 cmdline tools.
    GOTO :EOF
)
CALL C:\DevTools\VS6\VC98\Bin\VCVARS32.BAT
TITLE VC6
SET CL=/nologo
