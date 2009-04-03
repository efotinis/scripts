@ECHO OFF & SETLOCAL ENABLEEXTENSIONS

IF '%1'=='/?' (
    ECHO Set interpreter prompt to an 80-char separator line and the specified PROMPT
    ECHO format {$P$G if none specified}.
    GOTO :EOF
)

SET sep=…………………………………………………………………………………………………………………………………………………………………………………………………………………$_
IF '%1'=='' (SET fmt=$P$G) ELSE (SET fmt=%1)

ENDLOCAL & PROMPT %sep%%fmt%
