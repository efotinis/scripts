<#
.SYNOPSIS
    Temporarily disable VirtuaWin while running an executable.

.DESCRIPTION
    Starts a program by first disabling desktop switching in VirtuaWin. This is useful for fullscreen applications, like games, where accidental desktop switching may be undesirable.

    The script waits for the started process to end before re-enabling desktop switching.

    Note that this script assumes that desktop switching is always enabled beforehand.

.PARAMETER FilePath
    Path of executable to run using Start-Process.

.PARAMETER ArgumentList
    Optional list of string arguments to pass to the executable.

.INPUTS
    None

.OUTPUTS
    None
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
