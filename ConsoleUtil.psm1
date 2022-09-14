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
    --$script:WindowHideCount
    if ($script:WindowHideCount -eq 0) {
        [WinApi]::ShowWindow($script:ConsoleWindowHandle, [ShowStatus]::Show)
        $script:ConsoleWindowHandle = $null
    }
}


function Hide-ConsoleWindow {
    if ($script:WindowHideCount -eq 0) {
        $script:ConsoleWindowHandle = (Get-Process -Id $PID).MainWindowHandle
    }
    ++$script:WindowHideCount
    if ($script:WindowHideCount -eq 1) {
        [WinApi]::ShowWindow($script:ConsoleWindowHandle, [ShowStatus]::Hide)
    }
}


function Get-ConsoleWindowHideDepth {
    return $script:WindowHideCount
}


Export-ModuleMember *-*
