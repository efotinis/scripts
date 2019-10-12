<#
    Temporarily disable VirtuaWin while running an executable.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$FilePath,

    [string[]]$ArgumentList
)

Set-StrictMode -Version Latest


# Windows\WinUser.h
Set-Variable -Option Const WM_USER 0x400
# VirtuaWin\Defines.h
Set-Variable -Option Const CLSNAME 'VirtuaWinMainClass'
# VirtuaWin\Messages.h
Set-Variable -Option Const VW_ENABLE_STATE ($WM_USER + 42)  # wparam: EnableState
enum EnableState { NOP; TOGGLE; DISABLE; ENABLE }


function SetVWState ([int]$Mode) {
    # 'win' cmd ref: http://nircmd.nirsoft.net/win.html
    C:\tools\nircmdc.exe win sendmsg class $CLSNAME $VW_ENABLE_STATE $Mode 0
}


$options = @{
    Wait=$true
    FilePath=$FilePath
}
if ($ArgumentList) {
    $options.ArgumentList = $ArgumentList
}


SetVWState ([EnableState]::DISABLE)
Start-Process @options
SetVWState ([EnableState]::ENABLE)
