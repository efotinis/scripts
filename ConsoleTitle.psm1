# Console title management.


$TitleStack = [System.Collections.ArrayList]::new()


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
    [void]$TitleStack.Add((Get-ConsoleTitle))
    if ($PSBoundParameters.ContainsKey('Text')) {
        Set-ConsoleTitle $Text
    }
}


function Pop-ConsoleTitle {
    [CmdletBinding()]
    param()
    $n = $TitleStack.Count
    if ($n -lt 1) {
        Write-Error 'Console title stack is empty.'
    } else {
        Set-ConsoleTitle $TitleStack[$n - 1]
        $TitleStack.RemoveAt($n - 1)
    }
}


Export-ModuleMember *-*
