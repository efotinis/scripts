@ECHO OFF & SETLOCAL ENABLEEXTENSIONS
CALL :ren "2.1" "Head"
CALL :ren "2.2" "Bells"
CALL :ren "2.3" "Potato"
CALL :ren "2.4" "Money"
CALL :ren "2.5" "Beer"
CALL :ren "2.6" "Chains"
CALL :ren "3.1" "Dish and Dishonesty"
CALL :ren "3.2" "Ink and Incapability"
CALL :ren "3.3" "Nob and Nobility"
CALL :ren "3.4" "Sense and Senility"
CALL :ren "3.5" "Amy and Amiability"
CALL :ren "3.6" "Duel and Duality"
::----------------
:ren
REN "Black adder %~1.avi" "Black Adder %~1 - %~2.avi"
GOTO :EOF
