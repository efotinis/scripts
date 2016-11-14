if ($host.name -eq 'ConsoleHost') {

    function IsAdmin {
        ([Security.Principal.WindowsPrincipal] `
          [Security.Principal.WindowsIdentity]::GetCurrent()
        ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    }
    if (IsAdmin) {
        $host.UI.RawUI.BackgroundColor = 'darkred'
        Clear-Host
    }

    # invert prompt text color intensities; helps tell each command apart
    function global:prompt {
        $s = "$($executionContext.SessionState.Path.CurrentLocation)$('>' * ($nestedPromptLevel + 1))"
        Write-Host  $s -NoNewline `
            -ForegroundColor ($host.UI.RawUI.ForegroundColor -bxor 8) `
            -BackgroundColor ($host.UI.RawUI.BackgroundColor -bxor 8)
        Write-Output ' '
    }

    # customize output stream colors
    function ConClr ($type, $fg, $bg = $host.UI.RawUI.BackgroundColor) {
        $host.PrivateData.$($type + 'ForegroundColor') = $fg
        $host.PrivateData.$($type + 'BackgroundColor') = $bg
    }
    ConClr Error   magenta
    ConClr Warning yellow
    ConClr Debug   cyan
    ConClr Verbose green

}