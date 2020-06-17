Set-StrictMode -Version Latest

Import-Module $Env:Scripts\EFUtil.psm1
Import-Module $Env:Scripts\NiceConvert.psm1
Update-FormatData $Env:Scripts\EF.Format.ps1xml

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
Function global:x { exit }
function global:z ($time) { & $Env:Scripts\suspend.py -l $time }
Function global:.. { Set-Location .. }
Function global:... { Set-Location ..\.. }
function global:slc { Set-Location -LiteralPath (Get-Clipboard) }
Function global:?? ($Cmd) { help $Cmd -Full }
function global:yc {  # play youtube stream from clipboard url
    param(
        [switch]$HiDef,  # use high quality stream, if available
        [int]$TailView = 0  # if >0, prompt to launch in browser at specified seconds before end; useful to mark video as watched
    )
    Function GetYouTubeIdFromUrl ([string]$Url) {
        if ($Url -match 'https://www\.youtube\.com/watch\?v=(.{11})') {
            return $Matches[1]
        }
        if ($Url -match '(.{11})') {
            return $Matches[1]
        }
        Write-Error "could not find ID in URL: $Url"
    }
    $id = GetYouTubeIdFromUrl (Get-Clipboard)
    $fmt = if ($HiDef) { '22/18' } else { '18' }
    yps -f $fmt -- $id
    if ($TailView -gt 0) {
        Write-Host -NoNewLine "getting video info...`r"
        $info = yd -j -- $id | ConvertFrom-Json
        $timestamp = $info.duration - $TailView
        Read-Host 'press Enter to launch in browser' > $null
        Start-Process "https://youtube.com/watch?v=${id}&t=${timestamp}"
    }
}
if ($Env:COMPUTERNAME -eq 'CORE') {

    # launch current Minecraft instance
    function global:mc { D:\games\MultiMC\MultiMC.exe -l $Env:MULTIMC_MAIN_INST }
    # show Minecraft updates in the last 30 days (or launches version wiki)
    function global:mcv {
        param([switch]$Wiki)
        if ($Wiki) {
            Start-Process 'https://minecraft.gamepedia.com/Java_Edition_version_history/Development_versions'
        } else {
            mcver -d30
        }
    }
    # backup/restore main hardcore Minecraft world
    function global:mcb { E:\backups\minecraft\backup.ps1 19w03c Serendipity }
    function global:mcr { E:\backups\minecraft\backup.ps1 19w03c Serendipity -RestoreLast }

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
Set-Alias -Scope global yd C:\tools\youtube-dl.exe
Set-Alias -Scope global minf C:\tools\MediaInfo\MediaInfo.exe
Set-Alias -Scope global 7z "$Env:ProgramFiles\7-Zip\7z.exe"
Set-Alias -Scope global j "$Env:DROPBOX\jo.py"
Set-Alias -Scope global fn $Env:Scripts\filternames.ps1
Set-Alias -Scope global mpc (Get-ItemPropertyValue HKCU:\Software\MPC-HC\MPC-HC ExePath)
Set-Alias -Scope global g goto.ps1
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

function global:Edit-FileInNotepad ([string]$Path) {
    & "$Env:windir\system32\notepad.exe" $Path
}
function global:Edit-FileInVSCode ([string]$Path) {
    & "$Env:ProgramFiles\Microsoft VS Code\Code.exe" $Path > $null
}
function global:Edit-ScriptInNotepad ([string]$Name) {
    $path = global:Get-CommandFile $Name
    if ($path) { global:Edit-FileInNotepad $path }
}
function global:Edit-ScriptInVSCode ([string]$Name) {
    $path = global:Get-CommandFile $Name
    if ($path) { global:Edit-FileInVSCode $path }
}


# -------------------------------------


# get/set console title
function global:WndTitle ($s) {
    if ($null -eq $s) {
        $Host.UI.RawUI.WindowTitle
    } else {
        $Host.UI.RawUI.WindowTitle = $s
    }
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


# reverse input sequence
# http://stackoverflow.com/questions/22771724/reverse-elements-via-pipeline
function global:Reversed
{
    $a = @($input)
    [array]::reverse($a)
    return $a
}


function global:Shuffled
{
    $a = @($input)
    $a | Get-Random -Count $a.Length
}


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
        Write-Host $s -NoNewline -ForegroundColor $fg -BackgroundColor $bg
        Write-Output ' '
    }

    if (IsAdmin) {
        $host.UI.RawUI.BackgroundColor = 'darkred'
        Clear-Host
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
            if (IsAdmin) {
                $host.UI.RawUI.BackgroundColor = 'darkred'
            } else {
                $host.UI.RawUI.BackgroundColor = 'darkblue'
            }
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


# Count of characters in string.
function global:CharCount {
    param(
        [Parameter(ValueFromPipeline)]
        [string]$InputObject,
        
        [Parameter(Mandatory)]
        [char]$Character,
        
        [switch]$CaseSensitive
    )

    $count = 0
    if ($CaseSensitive) {
        for ($i = 0; $i -lt $InputObject.Length; ++$i) {
            if ($InputObject[$i] -ceq $Character) {
                ++$count
            }
        }
    }
    else {
        for ($i = 0; $i -lt $InputObject.Length; ++$i) {
            if ($InputObject[$i] -ieq $Character) {
                ++$count
            }
        }
    }
    $count
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

<#
Split array into sub-arrays, based on part size or count.
Last part may contain less items than the rest.
Based on:
    https://gallery.technet.microsoft.com/scriptcenter/Split-an-array-into-parts-4357dcc1
#>
function global:SplitArray { 
    param(
        $Items,
        [int]$Count,
        [int]$Size
    )
    if ($Count -gt 0) {
        $Size = [Math]::Ceiling($Items.Count / $Count)
    } elseif ($Size -gt 0) {
        $Count = [Math]::Ceiling($Items.Count / $Size)
    } else {
        $Count, $Size = 1, $Items.Count
    }
    for ($i = 0; $i -lt $Count; ++$i) {
        $beg = $i * $Size
        $end = [Math]::Min(($i + 1) * $Size, $Items.Count)
        ,@($Items[$beg..($end - 1)])
    }
}


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
function global:FileHashSet ([string[]]$Path) {
    $ret = [Collections.Generic.Hashset[string]]@()
    foreach ($curPath in $Path) {
        $ret.UnionWith(
            [Collections.Generic.Hashset[string]]@(Get-Content -LiteralPath $curPath)
        )
    }
    ,$ret
}


Set-Alias -Scope global ndd New-DateDirectory
Set-Alias -Scope global gft Get-FileTotal
Set-Alias -Scope global ddg New-WebQuery

Set-Alias -Scope Global ed  Edit-FileInNotepad
Set-Alias -Scope Global ec  Edit-FileInVSCode
Set-Alias -Scope Global eds Edit-ScriptInNotepad
Set-Alias -Scope Global ecs Edit-ScriptInVSCode


$global:PromptPathPref = [PromptPath]::Tail
$global:PromptHomeRepl = $true
$global:PromptColor = '*'


# change default transfer protocols ("Ssl3, Tls"), both of which are insecure;
# note that TLS v1.1 has also been deprecated
[Net.ServicePointManager]::SecurityProtocol = 'Tls12, Tls13'
