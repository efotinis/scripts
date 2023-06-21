#requires -Modules WindowUtil, ColorUtil

# Console utilities.


Add-Type -Name Window -Namespace Console -MemberDefinition @'

    [DllImport("Kernel32.dll")]
    public static extern IntPtr GetConsoleWindow();

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, Int32 nCmdShow);

'@


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
        Set-WindowShow $script:ConsoleWindowHandle ([ShowStatus]::Show)
        $script:ConsoleWindowHandle = $null
    }
}


function Hide-ConsoleWindow {
    if ($script:WindowHideCount -eq 0) {
        $script:ConsoleWindowHandle = (Get-Process -Id $PID).MainWindowHandle
    }
    ++$script:WindowHideCount
    if ($script:WindowHideCount -eq 1) {
        Set-WindowShow $script:ConsoleWindowHandle ([ShowStatus]::Hide)
    }
}


function Get-ConsoleWindowHideDepth {
    return $script:WindowHideCount
}


function Get-IsConsoleWindowVisible {
    return (Get-Process -Id $PID).MainWindowHandle -ne 0
}


function Switch-ConsoleFullScreen {
    $sysVer = [System.Environment]::OsVersion
    if ($sysVer.Platform -eq 'Win32NT' -and $sysVer.Version.Major -gt 7) {
        # TODO: toggle maximized state
        throw 'system supports native console window maximizing'
    }
    $maxWidth = $Env:FullScreenWidth -as [int]
    if (-not $maxWidth) {
        throw "Missing environment variable: FullScreenWidth"
    }
    $conWnd = [Console.Window]::GetConsoleWindow()
    $SW_MAXIMIZE = 3
    $SW_RESTORE = 9
    if ($Env:FullScrPreviousWidth) {
        [void][Console.Window]::ShowWindow($conWnd, $SW_RESTORE)
        cols $Env:FullScrPreviousWidth
        $Env:FullScrPreviousWidth = $null
    } else {
        $Env:FullScrPreviousWidth = $Host.UI.RawUI.BufferSize.Width
        cols $maxWidth
        [void][Console.Window]::ShowWindow($conWnd, $SW_MAXIMIZE)
    }
}


function Get-ConsoleColor {
    [ordered]@{
        OutputSpec = script:GetNiceStreamSpec 'Output'
        ErrorSpec = script:GetNiceStreamSpec 'Error'
        WarningSpec = script:GetNiceStreamSpec 'Warning'
        VerboseSpec = script:GetNiceStreamSpec 'Verbose'
        DebugSpec = script:GetNiceStreamSpec 'Debug'
        # NOTE: no special color for Information
    }
}


function Set-ConsoleColor {
    [CmdletBinding()]
    param(
        [string]$OutputSpec = '',
        [string]$ErrorSpec = '',
        [string]$WarningSpec = '',
        [string]$VerboseSpec = '',
        [string]$DebugSpec = ''
    )
    foreach ($name in @('Output', 'Error', 'Warning', 'Verbose', 'Debug')) {
        $paramName = $name + 'Spec'
        if ($PSBoundParameters.ContainsKey($paramName)) {
            script:SetNiceStreamSpec $name $PSBoundParameters.$paramName
        }
    }
}


function GetNiceStreamSpec ($Name) {
    $f, $b = if ($Name -eq 'Output') {
        $Host.UI.RawUI.ForegroundColor
        $Host.UI.RawUI.BackgroundColor
    } else {
        $Host.PrivateData.$($Name + 'ForegroundColor')
        $Host.PrivateData.$($Name + 'BackgroundColor')
    }
    ConvertFrom-ConsoleColor $f $b
}


function SetNiceStreamSpec ($Name, $Spec) {
    $f, $b = ConvertTo-ConsoleColor $Spec
    if ($Name -eq 'Output') {
        if ($null -ne $f) { $Host.UI.RawUI.ForegroundColor = $f }
        if ($null -ne $b) { $Host.UI.RawUI.BackgroundColor = $b }
    } else {
        if ($null -ne $f) { $Host.PrivateData.$($Name + 'ForegroundColor') = $f }
        if ($null -ne $b) { $Host.PrivateData.$($Name + 'BackgroundColor') = $b }
    }
}


Export-ModuleMember -Function *-*
