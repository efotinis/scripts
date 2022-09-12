# Console utilities.

Import-Module $Env:Scripts\WindowUtil.psm1


$TitleStack = [System.Collections.ArrayList]::new()

$WindowHideCount = 0
$ConsoleWindowHandle = $null


function Get-ConsoleTitle {
    [CmdletBinding()]
    param()
    Write-Output $Host.UI.RawUI.WindowTitle
}


function Set-ConsoleTitle {
    [CmdletBinding()]
    param(
        [string]$Text
    )
    $Host.UI.RawUI.WindowTitle = $Text
}


function Push-ConsoleTitle {
    [CmdletBinding()]
    param(
        [string]$Text
    )
    [void]$script:TitleStack.Add((Get-ConsoleTitle))
    if ($PSBoundParameters.ContainsKey('Text')) {
        Set-ConsoleTitle $Text
    }
}


function Pop-ConsoleTitle {
    [CmdletBinding()]
    param()
    $n = $script:TitleStack.Count
    if ($n -lt 1) {
        Write-Error 'Console title stack is empty.'
    } else {
        Set-ConsoleTitle $script:TitleStack[$n - 1]
        $script:TitleStack.RemoveAt($n - 1)
    }
}


function Show-ConsoleWindow {
    if ($script:WindowHideCount -le 0) {
        Write-Error 'Console window is already visible.'
        return
    }
    if ($script:WindowHideCount -eq 1) {
        if (-not [WinApi]::ShowWindow($script:ConsoleWindowHandle, [ShowStatus]::Show)) {
            Write-Error 'Could not show console window.'
            return
        }
        $script:ConsoleWindowHandle = $null
    }
    --$script:WindowHideCount
}


function Hide-ConsoleWindow {
    if ($script:WindowHideCount -eq 0) {
        $script:ConsoleWindowHandle = (Get-Process -Id $PID).MainWindowHandle
        if (-not [WinApi]::ShowWindow($script:ConsoleWindowHandle, [ShowStatus]::Hide)) {
            Write-Error 'Could not hide console window.'
            return
        }
    }
    ++$script:WindowHideCount
}


function Get-ConsoleWindowVisibility {
    return $script:WindowHideCount
}


<#
# Set PowerShell console visibility.
function global:ShowConsole ([bool]$Mode) {
    # cache the handle, since MainWindowHandle is 0
    # when the main window of a process is hidden
    $hwnd = (Get-Process -Id $PID).MainWindowHandle
    if ($hwnd -ne [IntPtr]::Zero) {
        $global:_ShowConsole_hwnd = $hwnd
    } else {
        $hwnd = $global:_ShowConsole_hwnd
    }

    $cmd = switch ($Mode) {
        $true { [ShowStatus]::Show }
        $false { [ShowStatus]::Hide }
    }
    $null = [WinApi]::ShowWindow($hwnd, $cmd)
}#>



Export-ModuleMember *-*
