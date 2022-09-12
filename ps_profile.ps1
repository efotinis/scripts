using module .\WindowUtil.psm1

Set-StrictMode -Version Latest

Import-Module $Env:Scripts\AnsiColor.psm1
Import-Module $Env:Scripts\ConsoleUtil.psm1
Import-Module $Env:Scripts\EFUtil.psm1
Import-Module $Env:Scripts\NiceConvert.psm1
Import-Module $Env:Scripts\PipelineUtil.psm1
Import-Module $Env:Scripts\StringUtil.psm1
Import-Module $Env:Scripts\YoutubeUtil.psm1

Update-FormatData $Env:Scripts\EF.Format.ps1xml
Update-FormatData $Env:Scripts\DataLength.Format.ps1xml


# NOTE: this script is getting large; must break it up

if ($Env:COMPUTERNAME -eq 'VOID') {
    chcp 65001  # Win10 can handle UTF-8
}

# shorthands and aliases
function global:m ($i, $b, $c) {
    # multiply value by ten, preserving leading sign (if any);
    # note that $b/$c params will be either numeric or string,
    # depending on whether they include a leading sign or not
    function Value ($n) {
        if ($n -match '([+-])(.*)') {
            $Matches[1] + [int]([double]$Matches[2] * 10)
        } else {
            $n * 10
        }
    }
    if ($null -ne $b) { $b = Value $b }
    if ($null -ne $c) { $c = Value $c }

    if ($null -eq $i) {
        monctl
    } elseif ($null -eq $b) {
        monctl -m $i
    } elseif ($null -eq$c) {
        monctl -m $i -b $b -c $b
    } else {
        monctl -m $i -b $b -c $c
    }
}
function global:x {
    function HasNoJobs {
        return $null -eq (Get-Job -HasMoreData:$true)
    }
    function ConfirmExit {
        $T = [System.Management.Automation.Host.ChoiceDescription]
        $options = @(
            $T::new('&Yes', 'Exit session and abort existing jobs.')
            $T::new('&No', 'Cancel and return to session.')
        )
        msgbeep.py w
        $msg = 'Abort running jobs and discard collected data?'
        $res = $Host.UI.PromptForChoice('Exit session', $msg, $options, 1)
        return $res -eq 0
    }
    if ((HasNoJobs) -or (ConfirmExit)) {
        exit
    }
}
function global:z ($time) { & $Env:Scripts\suspend.py -l $time }
Function global:.. { Set-Location .. }
Function global:... { Set-Location ..\.. }
function global:slc { Set-Location -LiteralPath (Get-Clipboard) }
function global:glc { Get-Location | % Path | Set-Clipboard }
Function global:?? ($Cmd) { help $Cmd -Full }
function global:cdef ([string]$Name) { gcm $Name | % Definition }
if ($Env:COMPUTERNAME -eq 'CORE') {
    # backup/list main Firefox profile
    function global:fxb { E:\backups\firefox\backup.ps1 kgfe1h9i.default-1510666418771 }
    function global:fxl { E:\backups\firefox\list_file_age.ps1 kgfe1h9i.default-1510666418771 }

}
function global:ss { nircmdc.exe screensaver }
function global:fr ([int]$a, [int]$b) {
    # print simplified fraction a/b
    py -c '
import sys
import fractions
x, y = map(int, sys.argv[1:])
print(fractions.Fraction(x, y))
    ' $a $b
}
Set-Alias -Scope global yd C:\tools\yt-dlp.exe
Set-Alias -Scope global minf C:\tools\MediaInfo\MediaInfo.exe
Set-Alias -Scope global 7z "$Env:ProgramFiles\7-Zip\7z.exe"
Set-Alias -Scope global fn $Env:Scripts\filternames.ps1
Set-Alias -Scope global go goto.ps1
Set-Alias -Scope Global mc MinecraftUtil.ps1
switch ($env:COMPUTERNAME) {
    'core' {
        Set-Alias -Scope global srip 'C:\Program Files (x86)\Streamripper\streamripper.exe'
        Set-Alias -Scope global slink 'C:\Program Files\Python37\Scripts\streamlink.exe'
    }
    'lap7' {
        Set-Alias -Scope global srip 'C:\tools\streamripper\streamripper.exe'
        Set-Alias -Scope global slink 'C:\Program Files\Python36-32\Scripts\streamlink.exe'
    }
}
Set-Alias -Scope global ddmver 'D:\docs\apps\dell display manager\check-version.ps1'


# ---- file editing -------------------

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
    process {
        global:Get-ResolvedWildcardOrLiteral $InputObject -LiteralBrackets:$LiteralBrackets | % {
            & "$Env:ProgramFiles\Microsoft VS Code\Code.exe" $_ > $null
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


# -------------------------------------


function global:Set-DefaultConsoleTitle {
    Set-ConsoleTitle -Text (
        'PowerShell {0}.{1}' -f @(
            $PSVersionTable.PSVersion.Major
            $PSVersionTable.PSVersion.Minor
    ))
}


# play audio file
function global:PlaySound ($path) {
    (New-Object Media.SoundPlayer $Path).Play()
}


# output speech
function global:Speak (
    [string]$Text,
    [int]$Volume = 100,
    [int]$Rate = 0
) {
    $Voice = New-Object -ComObject SAPI.SpVoice
    $Voice.Volume = $Volume
    $Voice.Rate = $Rate
    $Voice.Speak($Text) > $Null
}


Set-Alias -Scope global Reversed Get-ReverseArray
Set-Alias -Scope global Reverse Get-ReverseArray
Set-Alias -Scope global Shuffle Get-ShuffleArray
Set-Alias -Scope global Pick Get-OrderedSubset


# get elevation status
function global:IsAdmin {
    ([Security.Principal.WindowsPrincipal] `
      [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}


# media file duration in seconds using AVPROBE
function global:Duration ($path) {
    $j = (avprobe.exe -v 0 -of json -show_format $path | ConvertFrom-Json)
    $j.format.duration
}


# Insert dashes to YYYYMMDD string.
function global:DateDashes ([string]$Ymd) {
    $Ymd.Insert(6,'-').Insert(4,'-')
}


# Replace invalid filename characters with underscore.
function global:SafeName ($s) {
    foreach ($c in [IO.Path]::GetInvalidFileNameChars()) {
        $s = $s.Replace($c, '_')
    };
    return $s;
}


# Change the extension of a file path
function global:SetExt ($path, $ext) {
    [IO.Path]::ChangeExtension($path, $ext)
}


# Measure total files, dirs and bytes of passed FileSystemInfo objects.
function global:Get-FileTotal
{
    begin {
        $a = [PSCustomObject]@{
            dirs=0
            files=0
            bytes=0
            size=''
        }
    }
    process {
        if ($_.PSIsContainer) {
            $a.dirs += 1
        }
        else {
            $a.files += 1
            $a.bytes += $_.Length
        }
    }
    end {
        $a.size = ConvertTo-NiceSize $a.bytes
        $a
    }
}


# Measure total count and length of non-container FileSystemInfo objects grouped by extension.
function global:Get-ExtensionInfo {
    # filter out directories and write warning if any were encountered
    function NoDirs {
        begin {
            $dirCount = 0
        }
        process {
            if ($_.PSIsContainer) {
                $dirCount += 1
            } else {
                $_
            }
        }
        end {
            if ($dirCount -gt 0) {
                Write-Warning "container objects ignored; count: $dirCount"
            }
        }
    }
    $input | NoDirs | Group-Object Extension | ForEach-Object {
        $x = $_.Group | Get-FileTotal
        [PSCustomObject]@{
            Count=$_.count
            Extension=$_.name
            Length=$x.bytes
            Size=$x.size 
        }
    }
}


if ($host.name -eq 'ConsoleHost') {

    enum PromptPath {
        Full  # full path
        Tail  # last component only
        None  # no path
    }

    # invert prompt text color intensities; helps tell each command apart
    function global:prompt {
        # Get value of global variable or default.
        function GetGlobal ($Name, $Def) {
            try {
                $var = Get-Variable -Name $Name -Scope Global -ErrorAction Ignore
                $var.Value
            } catch {
                $Def
            }
        }
        $pathPref = GetGlobal 'PromptPathPref' [PromptPath]::Full
        $homeRepl = GetGlobal 'PromptHomeRepl' $false
        # color options:
        #   ''      normal
        #   'i'     invert (swap fg and bg)
        #   '*'     toggle fg and bg intensity
        #   '*/'    toggle fg intensity
        #   '/*'    toggle bg intensity
        #   other   set to specified attrib, e.g. W/N, R+/G, etc.
        $color = GetGlobal 'PromptColor' '/*'
        $s = ''
        if ($pathPref -ne [PromptPath]::None) {
            $s = $ExecutionContext.SessionState.Path.CurrentLocation
            if ($homeRepl) {
                # replace home path with "~:"; since "~" alone is a valid
                # directory name, an extra, invalid path char (colon) is used
                $s = $s -replace ([RegEx]::Escape($HOME)+'(?:$|(?=\\))'),':~'
            }
            if ($pathPref -eq [PromptPath]::Tail) {
                $s = Split-Path -Leaf $s
            }
        }
        $jobs = @(Get-Job)
        if ($jobs) {
            $s += ':{0}j' -f $jobs.Count
        }
        $s += '>' * ($NestedPromptLevel + 1)
        $fg = $host.UI.RawUI.ForegroundColor
        $bg = $host.UI.RawUI.BackgroundColor
        switch ($color) {
            '' { break }
            'i' { $fg, $bg = $bg, $fg; break }
            '*' { $fg = $fg -bxor 8; $bg = $bg -bxor 8; break }
            '*/' { $fg = $fg -bxor 8; break }
            '/*' { $bg = $bg -bxor 8; break }
            default {
                $newFg, $newBg = global:Get-ColorAttribute $color
                if ($newFg) { $fg = $newFg }
                if ($newBg) { $bg = $newBg }
            }
        }
        if (IsAdmin) {
            Write-Host 'Admin:' -NoNewline -Fore white -Back darkred
        }
        Write-Host $s -NoNewline -ForegroundColor $fg -BackgroundColor $bg
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

    # toggle black & white mode; useful when running programs that output
    # colors and assuming a black background (e.g. pip)
    function global:MonoClr {
        if ([bool]$Env:MonoClr) {
            $Env:MonoClr = $null
        } else {
            $host.UI.RawUI.BackgroundColor = 'black'
            $Env:MonoClr = 'on'
        }
    }

    # Convert a color attribute (e.g. "w/n") to a pair of fg/bg colors.
    # Missing or invalid colors are set to $null.
    function global:Get-ColorAttribute ([string]$Spec)
    {
        $Colors = @{
            'n'='black';       'n+'='darkgray'
            'b'='darkblue';    'b+'='blue'
            'g'='darkgreen';   'g+'='green'
            'c'='darkcyan';    'c+'='cyan'
            'r'='darkred';     'r+'='red'
            'm'='darkmagenta'; 'm+'='magenta'
            'y'='darkyellow';  'y+'='yellow'
            'w'='gray';        'w+'='white'
        }
        $fg, $bg = $Spec -split '/',2
        if ($fg) { $Colors.Item($fg) } else { $null }
        if ($bg) { $Colors.Item($bg) } else { $null }
    }

    function global:Color ([string]$Spec) {
        $fore, $back = global:Get-ColorAttribute $Spec
        if ($fore) {
            $Host.UI.RawUI.ForegroundColor = $fore
        }
        if ($back) {
            $Host.UI.RawUI.BackgroundColor = $back
        }
    }

}


# get the last known home WAN IP
function global:HomeWan {
    $tail = Get-Content $Env:SyncMain\data\wan.log | Select-Object -last 1
    if ($tail -NotMatch '(\d+\.\d+\.\d+\.\d+)$') {
        # TODO: show error message instead
        throw 'no IP found in log tail'
    }
    $Matches[1]
}


function global:SnapshotDir ($Source, $Dest, $Name) {
    if (-not (Test-Path -Type Container $Source)) {
        Write-Error "source directory does not exist: $Source"
        return
    }
    if (-not (Test-Path -Type Container $Dest)) {
        Write-Error "destination directory does not exist: $Dest"
        return
    }
    $timestamp = Get-Date -Format FileDateTime
    $machine = $Env:ComputerName
    $outfile = Join-Path $Dest "$Name-$timestamp-$machine.7z"
    Push-Location $Source
    try {
        7z a $outfile -mtc=on *
    }
    finally {
        Pop-Location
    }
}


function global:New-DateDirectory {
    param(
        [string]$Parent = '.',  # parent path
        [switch]$Time,          # include time
        [switch]$Compact,       # compact format; minimize symbol chars
        [switch]$Stay           # stay in current location and return dir object instead
    )

    if ($Time) {
        $fmt = if ($Compact) { 'yyyMMdd-HHmmss' } else { 'yyy-MM-dd HH_mm_ss' }
    }
    else {
        $fmt = if ($Compact) { 'yyyMMdd' } else { 'yyy-MM-dd' }
    }

    $path = Join-Path $Parent (Get-Date -Format $fmt)
    $dir = New-Item -Type Directory $path
    if ($dir) {
        if ($Stay) {
            $dir
        }
        else {
            Set-Location $dir
        }
    }
}


# Create new directory path if it doesn't exist and switch to it.
function global:nd ([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container -IsValid)) {
        Write-Error "invalid path: $Path"
        return
    }
    if (Test-Path -LiteralPath $Path -PathType Container) {
        Write-Warning "directory already exists: $Path"
    } elseif (-not (mkdir $Path)) {
         return
    }
    Set-Location -LiteralPath $Path
}


function global:gvi { Get-VideoInfo.ps1 (Get-ChildItem -file) | Tee-Object -v a; $global:a = $a }


# Perform web search using all passed args in a single query.
function global:New-WebQuery {
    # Open DuckDuckGo search in new FireFox tab.
    # NOTES:
    # - Tried using Python's webbrowser builtin module to automatically
    #   use the default browser, but it launches IE11 instead. Explicitly
    #   requesting "firefox" or using its path does not work.
    # - Firefox's "-search" option only needs the query terms, but it does not
    #   work with the "-new-tab" option, so we need to build the whole
    #   query URL manually.
    $query = [Net.WebUtility]::UrlEncode(($Args -join ' '))
    $url = "https://duckduckgo.com/?q=$query"
    & 'C:\Program Files\Mozilla Firefox\firefox.exe' -new-tab $url
}


# Table of PowerShell verbs, grouped by group.
function global:Show-VerbGroup ([string[]]$Verb = '*')
{
    Get-Verb -Verb $Verb | Group-Object Group | Format-Table -Wrap @(
        @{name='Group'; expr='Name'}
        @{name='Verbs'; expr={$_.Group.Verb -join ', '}}
    )
}


# Run script block and print min/avg execution time.
function global:timeit {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [scriptblock]$Code,
        [int]$Iterations = 1
    )
    if ($Iterations -lt 1) {
        throw "iterations must be > 1"
    }
    $sw = [System.Diagnostics.Stopwatch]::new()
    $ticksAcc = 0
    $ticksMin = [double]::MaxValue
    for ($n = 0; $n -lt $Iterations; ++$n) {
        $sw.Restart()
        & $Code
        $sw.Stop()
        $ticks = $sw.ElapsedTicks
        $ticksAcc += $ticks
        if ($ticks -lt $ticksMin) {
            $ticksMin = $ticks
        }
    }
    $freq = [System.Diagnostics.Stopwatch]::Frequency
    $timeMin = ConvertTo-NiceSeconds ($ticksMin / $freq) -Decimals 6
    $timeAvg = ConvertTo-NiceSeconds ($ticksAcc / $freq / $Iterations) -Decimals 6
    Write-Host "min: $timeMin"
    Write-Host "avg: $timeAvg"
    Write-Host "iterations: $Iterations"
}


# Eject drive.
function global:eject {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Drive
    )
    $ssfDRIVES = 0x11  # "My Computer"
    $shell = New-Object -comObject Shell.Application
    $driveObj = $shell.Namespace($ssfDRIVES).ParseName($Drive)
    if (-not $driveObj) {
        throw "drive does not exist: $Drive"
    }
    $driveObj.InvokeVerb("Eject")  # NOTE: must be localized string
}


# String hashset of all lines of specified files.
# Missing files are ignored, unless -MustExist is specified.
function global:FileHashSet ([string[]]$Path, [switch]$MustExist) {
    $ret = [Collections.Generic.Hashset[string]]@()
    foreach ($curPath in $Path) {
        if ((Test-Path -LiteralPath $curPath) -or $MustExist) {
            $ret.UnionWith(
                [Collections.Generic.Hashset[string]]@(
                    Get-Content -LiteralPath $curPath
                )
            )
        }
    }
    ,$ret
}


# Wait until external network connection reestablishes.
function global:waitnet ([int]$WaitSeconds = 10, [switch]$Silent) {
    while (-not (myip)) {
        sleep $WaitSeconds
    }
    if (-not $Silent) {
        msgbeep.py ok
    }
}


# Edit text interactively.
#
# Return object properties:
# - [bool]Changed: shows whether user saved text in editor UI
# - [string]Value: resulting text, or original if user didn't save
function global:Edit-String {
    param(
        [string]$Text
    )

    $ret = [PSCustomObject]@{
        Value=$Text
        Changed=$false
    }

    # prepare temp file for editing
    $path = [System.IO.Path]::GetTempFileName()
    $Text | Set-Content -LiteralPath $path -Encoding Utf8 -NoNewLine
    $f = Get-Item -LiteralPath $path
    $f.Attributes -= [System.IO.FileAttributes]::Archive

    Start-Process -FilePath notepad -ArgumentList $f.FullName -Wait
    $f.Refresh()

    # get result from temp file and delete it
    $ret.Value = $f | Get-Content -Encoding Utf8 -Raw
    if ($f.Attributes -band [System.IO.FileAttributes]::Archive) {
        $ret.Changed = $true
    }
    $f | Remove-Item

    $ret
}


# start videos in MPC-HC
function global:Start-Video {
    param(
        [Parameter(Mandatory, ValueFromPipeline<#, ValueFromPipelineByPropertyName#>)]
        #[Alias('FullName')]
        [object[]]$InputObject,
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
        $filePaths = @()
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
        $filePaths += foreach ($item in $InputObject) {
            if ($item -is [System.IO.FileSystemInfo]) {
                $item.FullName
            } else {
                $item
            }
        }
    }
    end {
        & $exe $filePaths @opt
    }

}


function global:fb2k {
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


# Storage unit fudge factors, i.e. number to multiply advertised capacity
# (in decimal units) to get actual capacity (in binary units).
# Use a unit prefix (k,m,g,...) for a single factor or -List for summary.
function global:Get-DiskSizeFudgeFactor {
    [CmdletBinding()]
    param(
        [Parameter(ParameterSetName='unit', Position=0)]
        [ValidateSet('k','m','g','t','p','e','z','y')]
        [string]$Unit,
        
        [Parameter(ParameterSetName='list')]
        [switch]$List
    )
    $units = 'kmgtpezy'
    if ($List) {
        $i = 0
        foreach ($c in [char[]]$units) {
            [PSCustomObject]@{
                Unit = $units[$i]
                FactorBinary = 1 / [Math]::Pow(1.024, $i + 1)
            }
            ++$i
        }
    } else {
        1 / [Math]::Pow(1.024, $units.IndexOf($Unit.ToLower()) + 1)
    }
}


function global:NiceSum ([string]$Property = 'length') {
    ConvertTo-NiceSize ($input | measure -sum $Property | % sum)
}


function global:NiceDuration ([string]$Property = 'duration') {
    ConvertTo-NiceDuration ($input | measure -sum $Property | % sum)
}


# Extract year from paths of the form: "...\title (year).ext".
function global:GetReleaseYear {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipelineByPropertyName)]
        [Alias('FullName', 'PSPath')]
        $Path
    )
    process {
        if ($Path -match '\((\d{4})\)\.\w+$') {
            $Matches[1] -as [int]
        } else {
            Write-Error "could not detect year: ""$Path"""
        }
    }
}


# Number of pipeline objects.
function global:Count {
    $Input | Measure-Object | % count
}


# Create DateTime representing some hours/minutes/seconds ago from now.
function global:TimeAgo {
    [CmdletBinding()]
    param(
        [int]$Hours,
        [int]$Minutes,
        [int]$Seconds
    )
    (Get-Date) - [timespan]::new($Hours, $Minutes, $Seconds)
}


# Create DateTime representing some years/months/days/weeks ago from now.
function global:DateAgo {
    [CmdletBinding()]
    param(
        [int]$Years,
        [int]$Months,
        [int]$Days,
        [int]$Weeks
    )
    $d = Get-Date
    $Days += $Weeks * 7
    $d.AddYears(-$Years).AddMonths(-$Months).AddDays(-$Days)
}


# Select pipeline objects based on position.
function global:nth ([int[]]$Index) {
    $input | select -index $Index
}


# Timestamp in filename-safe format.
function global:Get-FileNameSafeTimestamp ([switch]$Utc) {
    $fmt = if ($Utc) { 'FileDateTimeUniversal' } else { 'FileDateTime' }
    Get-Date -Format $fmt
}


# Generate time/value objects of pipeline contents.
# Useful for timing program output. If non-output streams (e.g. error) are also
# needed, they should be merged with stdout beforehand (i.e. 2>&1).
function global:Get-TimedOutput {
    begin {
        $t = [System.Diagnostics.Stopwatch]::new()
        $t.Start()
    }
    process {
        [PSCustomObject]@{
            Elapsed = $t.Elapsed
            Object = $_
        }
    }
}


# Filter to add objects to clipboard and also send down the pipeline.
function global:tcb ([switch]$Append) {
    begin {
        if (-not $Append) {
            scb $null
        }
    }
    process {
        Write-Output $_
        scb $_ -Append
    }
}


Set-Alias -Scope global gip Get-IfProperty
Set-Alias -Scope global ndd New-DateDirectory
Set-Alias -Scope global gft Get-FileTotal
Set-Alias -Scope global ext Get-ExtensionInfo
Set-Alias -Scope global ddg New-WebQuery
Set-Alias -Scope Global ed  Edit-FileInNotepad
Set-Alias -Scope Global ec  Edit-FileInVSCode
Set-Alias -Scope Global eds Edit-ScriptInNotepad
Set-Alias -Scope Global ecs Edit-ScriptInVSCode
Set-Alias -Scope Global log ~\SimpleLog.ps1
Set-Alias -Scope Global ?p  Show-CommandParameter.ps1
Set-Alias -Scope global mpc Start-Video
Set-Alias -Scope global ts  'C:\Users\Elias\Desktop\stuff\assorted\torrent search\Search-Torrent.ps1'
Set-Alias -Scope global eatlines D:\projects\eatlines.exe
Set-Alias -Scope global ff Get-DiskSizeFudgeFactor
Set-Alias -Scope global espeak 'C:\Program Files (x86)\eSpeak\command_line\espeak.exe'
Set-Alias -Scope global nw ~\newwall.ps1
Set-Alias -Scope global fst Get-FileNameSafeTimestamp


$global:PromptPathPref = [PromptPath]::Tail
$global:PromptHomeRepl = $true
$global:PromptColor = '*'


# change default transfer protocols ("Ssl3, Tls"), both of which are insecure;
# note that TLS v1.1 has also been deprecated
[Net.ServicePointManager]::SecurityProtocol = 'Tls12, Tls13'


& "$Env:scripts\SmartFileSystem.Format.ps1"

Set-DefaultConsoleTitle

Set-PSReadLineKeyHandler `
    -Chord Enter `
    -BriefDescription 'AcceptLineSpecial' `
    -Description 'Execute command if non-empty. Otherwise, replace previous prompt with a blank line.' `
    -ScriptBlock {
        $line, $cursor = $null, $null
        [Microsoft.PowerShell.PSConsoleReadLine]::GetBufferState([ref]$line, [ref]$cursor)
        [Microsoft.PowerShell.PSConsoleReadLine]::AcceptLine()
        if ($line -eq '') {
            $Host.UI.RawUI.CursorPosition = [System.Management.Automation.Host.Coordinates]::new(
                0, $Host.UI.RawUI.CursorPosition.Y - 1
            )
            Write-Host -NoNewLine (' ' * $Host.UI.RawUI.BufferSize.Width)
        }
    }
