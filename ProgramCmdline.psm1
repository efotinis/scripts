# Functions to utilize specific programs via command line options.


Set-StrictMode -Version Latest


# Get path of PS external script or OS executable script.
function global:Get-CommandFile ($Name)
{
    function isTextScript ($cmd) {
        $ext = '.BAT;.CMD;.VBS;.JS;.WSH;.PY;.PYW;.PSM1' -split ';'
        $cmd.CommandType -eq 'Application' -and $cmd.Extension -in $ext
    }
    $cmd = Get-Command $Name
    if ($cmd.CommandType -eq 'ExternalScript' -or (isTextScript $cmd)) {
        return $cmd.Path
    }
    Write-Error "command '$Name' does not seem to be a file"
}


# Expand patterns containing wildcard characters to full paths
# and output non-wildcard containing patterns as-is.
# Writes warning for any patterns that did not match anything.
# Can optionally interpret brackets as literals, since they are traditionally
# used verbatim in file names.
function global:Get-ResolvedWildcardOrLiteral {
    param(
        [string[]]$Pattern,
        [switch]$LiteralBrackets
    )
    function IsWildcard ([string]$Pattern, [switch]$LiteralBrackets) {
        if ($LiteralBrackets) {
            return $Pattern -match '[*?]'
        } else {
            return $Pattern -match '[*?[\]]'
        }
    }
    function PrepareForUse ([string]$Pattern, [switch]$LiteralBrackets) {
        if ($LiteralBrackets) {
            return $Pattern -replace '([[\]])','`$1'
        } else {
            return $Pattern
        }
    }
    foreach ($p in $Pattern) {
        if (IsWildcard $p -LiteralBrackets:$LiteralBrackets) {
            $a = @(Resolve-Path -Path (PrepareForUse $p -LiteralBrackets:$LiteralBrackets))
            if ($a.Count -eq 0) {
                Write-Warning "No items match pattern: $p"
            } else {
                Write-Output $a.Path
            }
        } else {
            Write-Output $p
        }
    }
}


function global:Edit-FileInNotepad {
    param(
        [Parameter(ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [Alias('FullName', 'Path')]
        [SupportsWildcards()]
        [AllowEmptyString()]
        [string[]]$InputObject = '',

        [switch]$LiteralBrackets
    )
    process {
        global:Get-ResolvedWildcardOrLiteral $InputObject -LiteralBrackets:$LiteralBrackets | % {
            & "$Env:windir\system32\notepad.exe" $_
        }
    }
}


function global:Edit-FileInVSCode {
    param(
        [Parameter(ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [Alias('FullName', 'Path')]
        [SupportsWildcards()]
        [AllowEmptyString()]
        [string[]]$InputObject = '',

        [switch]$LiteralBrackets
    )
    begin {
        $p1 = "$Env:ProgramFiles\Microsoft VS Code\Code.exe"
        $p2 = "${Env:ProgramFiles(x86)}\Microsoft VS Code\Code.exe"
        if (Test-Path -LiteralPath $p1) {
            $exePath = $p1
        } else {
            $exePath = $p2
        }
    }
    process {
        global:Get-ResolvedWildcardOrLiteral $InputObject -LiteralBrackets:$LiteralBrackets | % {
            & $exePath $_ > $null
        }
    }
}


function global:Edit-ScriptInNotepad ([string]$InputObject) {
    $path = global:Get-CommandFile $InputObject
    if ($path) { global:Edit-FileInNotepad $path }
}


function global:Edit-ScriptInVSCode ([string]$InputObject) {
    $path = global:Get-CommandFile $InputObject
    if ($path) { global:Edit-FileInVSCode $path }
}


# Interafe with MPC-HC command line.
function global:Invoke-MediaPlayerClassic {
    param(
        [Parameter(ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [Alias('FullName')]
        [string[]]$InputObject,
        [switch]$Open,
        [switch]$Play,
        [switch]$Close,
        [switch]$PlayNext,
        [switch]$New,
        [switch]$Add,
        [switch]$Randomize,
        [int]$StartMsec,
        [ValidatePattern("^(\d+:)?\d+:\d+$")]
        [string]$StartPos,  # hh:mm:ss
        [ValidatePattern("^\d+,\d+$")]
        [string]$FixedSize,  # w,h
        [switch]$FullScreen,
        [switch]$Minimized,
        [switch]$NoFocus
    )
    begin {
        $regLoc = @{
            Path='HKCU:\Software\MPC-HC\MPC-HC'
            Name='ExePath'
        }
        $exe = Get-Item -LiteralPath (Get-ItemPropertyValue @regLoc -ea 0) -ea 0
        if (-not $exe) {
            throw 'MPC-HC executable not found'
        }
        $filePaths = [System.Collections.ArrayList]@()
        $opt = @(
            if ($Open)      { '/open' }
            if ($Play)      { '/play' }
            if ($Close)     { '/close' }
            if ($PlayNext)  { '/playnext' }
            if ($New)       { '/new' }
            if ($Add)       { '/add' }
            if ($Randomize) { '/randomize' }
            if ($StartMsec) { '/start',$StartMsec }
            if ($StartPos)  { '/startpos',$StartPos }
            if ($FixedSize) { '/fixedsize',$FixedSize }
            if ($FullScreen) { '/fullscreen' }
            if ($Minimized) { '/minimized' }
            if ($NoFocus)   { '/nofocus' }
        )
    }
    process {
        if ($InputObject) {
            [void]$filePaths.AddRange($InputObject)
        }
    }
    end {
        & $exe $filePaths @opt
    }

}


# Interafe with foobar2000 command line.
function global:Invoke-Foobar2000 {
    param(
        [Parameter(ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [Alias('FullName', 'Path')]
        [string[]]$InputObject,

        [switch]$Add,  # add instead of replace in current playlist
        [switch]$Immediate,  # suppress file adding delay
        [switch]$Play,
        [switch]$Pause,
        [switch]$Playpause,
        [switch]$Prev,
        [switch]$Next,
        [switch]$Rand,
        [switch]$Stop,
        [switch]$Exit,
        [switch]$Show,
        [switch]$Hide,
        [switch]$Config
    )
    begin {
        $inputItems = [System.Collections.ArrayList]@()
    }
    process {
        $inputItems += @($InputObject)
    }
    end {
        $args = @(
            if ($Add) { '/add' }
            if ($Immediate) { '/immediate' }
            if ($Play) { '/play' }
            if ($Pause) { '/pause' }
            if ($Playpause) { '/playpause' }
            if ($Prev) { '/prev' }
            if ($Next) { '/next' }
            if ($Rand) { '/rand' }
            if ($Stop) { '/stop' }
            if ($Exit) { '/exit' }
            if ($Show) { '/show' }
            if ($Hide) { '/hide' }
            if ($Config) { '/config' }
            if ($inputItems.Count -gt 0) {
                $inputItems
            }
        )
        & 'C:\Program Files (x86)\foobar2000\foobar2000.exe' @args
    }
}


Export-ModuleMember -Function *-*
