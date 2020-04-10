Set-StrictMode -Version Latest

Import-Module $Env:Scripts\EFUtil.psm1
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
    if ($b -ne $null) { $b = Value $b }
    if ($c -ne $null) { $c = Value $c }

    if ($i -eq $null) {
        monctl
    } elseif ($b -eq $null) {
        monctl -m $i
    } elseif ($c -eq $null) {
        monctl -m $i -b $b -c $b
    } else {
        monctl -m $i -b $b -c $c
    }
}
Function global:x { exit }
function global:z ($time) { & $Env:Scripts\suspend.py -l $time }
Function global:.. { Set-Location .. }
Function global:... { Set-Location ..\.. }
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
    $id = GetYouTubeIdFromUrl (gcb)
    $fmt = if ($HiDef) { '22/18' } else { '18' }
    yps -f $fmt -- $id
    if ($TailView -gt 0) {
        Write-Host -NoNewLine "getting video info...`r"
        $info = yd -j -- $id | ConvertFrom-Json
        $timestamp = $info.duration - $TailView
        Read-Host 'press Enter to launch in browser' > $null
        start "https://youtube.com/watch?v=${id}&t=${timestamp}"
    }
}
if ($Env:COMPUTERNAME -eq 'CORE') {

    # launch current Minecraft instance
    function global:mc { D:\games\MultiMC\MultiMC.exe -l $Env:MULTIMC_MAIN_INST }
    # show Minecraft updates in the last 30 days (or launches version wiki)
    function global:mcv {
        param([switch]$Wiki)
        if ($Wiki) {
            start 'https://minecraft.gamepedia.com/Java_Edition_version_history/Development_versions'
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
function global:ec ($Name) {  # edit command, if it's a file
    $cmd = Get-Command $Name
    function isTextScript ($cmd) {
        $ext = '.BAT;.CMD;.VBS;.JS;.WSH;.PY;.PYW' -split ';'
        return $cmd.CommandType -eq 'Application' -and
            $cmd.Extension -in $ext
    }
    if ($cmd.CommandType -eq 'ExternalScript' -or (isTextScript $cmd)) {
        notepad $cmd.path
    }
    else {
        throw 'cannot edit; not a text script'
    }
}
function global:fr ([int]$a, [int]$b) {
    # print simplified fraction a/b
    py -c '
import sys
import fractions
x, y = map(int, sys.argv[1:])
print(fractions.Fraction(x, y))
    ' $a $b
}
Set-Alias -Scope global ed $Env:windir\system32\notepad.exe
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


# get/set console title
function global:WndTitle ($s) {
    if ($s -eq $null) {
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


# Pretty size of all file objects piped in.
function global:FSize {
    $m = $Input | Measure-Object -Sum -Property Length
    PrettySize $m.Sum
}


# Pretty size and count of all file/dir objects piped in.
function global:FStats {
begin {
    $files, $dirs, $bytes = 0, 0, 0
}
process {
    if ($_.PSIsContainer) {
        $dirs += 1
    }
    else {
        $files += 1
        $bytes += $_.Length
    }
}
end {
    'dirs: {0:N0}, files: {1:N0}, size: {2} ({3:N0} byte(s))' -f (
        $dirs,
        $files,
        (PrettySize $bytes),
        $bytes
    )
}
}


if ($host.name -eq 'ConsoleHost') {

    enum PromptPath {
        Full  # full path
        Tail  # last component only
        None  # no path
    }
    $global:PromptPathPref = [PromptPath]::Full

    # invert prompt text color intensities; helps tell each command apart
    function global:prompt {
        try {
            $pp = (Get-Variable -Name PromptPathPref -Scope Global -ErrorAction Ignore).Value
        } catch {
            $pp = [PromptPath]::Full
        }
        $s = ''
        if ($pp -ne [PromptPath]::None) {
            $s = $ExecutionContext.SessionState.Path.CurrentLocation
            # replace home path with ~
            $s = $s -replace ([RegEx]::Escape($Env:USERPROFILE)+'(?:$|(?=\\))'),'~'
            if ($pp -eq [PromptPath]::Tail) {
                $s = Split-Path -Leaf $s
            }
        }
        $s += '>' * ($NestedPromptLevel + 1)
        Write-Host $s -NoNewline `
            -ForegroundColor ($host.UI.RawUI.ForegroundColor -bxor 8) `
            -BackgroundColor ($host.UI.RawUI.BackgroundColor -bxor 8)
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

    function global:Color ([string]$Spec) {
        $Colors = @{
            'n'='black';
            'b'='darkblue';
            'g'='darkgreen';
            'c'='darkcyan';
            'r'='darkred';
            'm'='darkmagenta';
            'y'='darkyellow';
            'w'='gray';
            'n+'='darkgray';
            'b+'='blue';
            'g+'='green';
            'c+'='cyan';
            'r+'='red';
            'm+'='magenta';
            'y+'='yellow';
            'w+'='white'
        }

        $fore, $back = (($spec + '/') -split '/')[0..1]
        if ($fore -in $Colors.Keys) {
            $Host.UI.RawUI.ForegroundColor = $Colors[$fore]
        }
        if ($back -in $Colors.Keys) {
            $Host.UI.RawUI.BackgroundColor = $Colors[$back]
        }
    }

}


# get the last known home WAN IP
function global:HomeWan {
    $tail = cat $Env:SyncMain\data\wan.log | select -last 1
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


function global:FancyPrompt {
    Set-Item Function:\prompt {
        Write-Host "$($ExecutionContext.SessionState.Path.CurrentLocation)" `
            -ForegroundColor ($host.UI.RawUI.ForegroundColor -bxor 8) `
            -BackgroundColor ($host.UI.RawUI.BackgroundColor -bxor 8) `
            -NoNewline
        Write-Output "$('>' * ($NestedPromptLevel + 1)) "
    }
}


function global:SimplePrompt {
    Set-Item Function:\prompt {
        '> '
    }
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

Set-Alias -Scope global ndd New-DateDirectory


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


function global:gvi { Get-VideoInfo.ps1 (ls -file) | tee -v a; $global:a = $a }

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
