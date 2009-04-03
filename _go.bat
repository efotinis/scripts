@ECHO OFF

IF '%1' == 'prj'  GOTO prj
IF '%1' == 'proj' GOTO prj
IF '%1' == 'tst'  GOTO test
IF '%1' == 'test' GOTO test
IF '%1' == 'py'   GOTO python
IF '%1' == 'python' GOTO python
IF '%1' == 'opt'  GOTO opt
IF '%1' == 'rasmon'  GOTO rasmon

ECHO.Invalid id.
GOTO :EOF

:prj
CD /D E:\Projects
GOTO :EOF

:test
CD /D E:\Projects\test\test\debug
GOTO :EOF

:python
CD /D F:\temp\python
GOTO :EOF

:opt
CD /D C:\DOCUME~1\Elias\Desktop\TESTPR~1\opt\Debug
PROMPT ------------------------------------------------------------------------------$_$G$S
GOTO :EOF

:rasmon
CD /D C:\DOCUME~1\Elias\Desktop\TESTPR~1\rasmon\Debug
GOTO :EOF


