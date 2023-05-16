Set-StrictMode -Version Latest

$Env:PSModulePath += ';D:\scripts\psmodules'

Update-FormatData $Env:Scripts\EF.Format.ps1xml
Update-FormatData $Env:Scripts\DataLength.Format.ps1xml

Update-FormatData -Prepend $Env:Scripts\CoreOverrides.ps1xml


# NOTE: this script is getting large; must break it up

if ($Env:COMPUTERNAME -eq 'VOID') {
    chcp 65001  # Win10 can handle UTF-8
}


Reset-ModPrompt


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
function global:.. { Set-Location .. }
function global:... { Set-Location ..\.. }
function global:sld { Set-Location ~\Desktop }
function global:slc { Set-Location -LiteralPath (Get-Clipboard) }
function global:glc { Get-Location | % Path | Set-Clipboard }
function global:?? ($Cmd) { help $Cmd -Full }
function global:cdef ([string]$Name) { gcm $Name | % Definition }
if ($Env:COMPUTERNAME -eq 'CORE') {
    # backup/list main Firefox profile
    function global:fxb { E:\backups\firefox\backup.ps1 kgfe1h9i.default-1510666418771 }
    function global:fxl { E:\backups\firefox\list_file_age.ps1 kgfe1h9i.default-1510666418771 }

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
Set-Alias -Scope global yd C:\tools\yt-dlp.exe
Set-Alias -Scope global 7z "$Env:ProgramFiles\7-Zip\7z.exe"
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


# get elevation status
function global:IsAdmin {
    ([Security.Principal.WindowsPrincipal] `
      [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
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


<#
.SYNOPSIS
    Eject drive.
.DESCRIPTION
    Dismounts removable and optical drives.
.PARAMETER InputObject
    Drive letter with optional colon or path whose drive to eject. Can specify multiple values via the pipeline.
.INPUTS
    String
.OUTPUTS
    None
#>
function global:Dismount-RemovableDrive {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [Alias('FullName')]
        [string]$InputObject
    )
    process {
        $Drive = [System.IO.DriveInfo]::new($InputObject)
        switch ($Drive.DriveType) {
            'Removable' {
                break
            }
            'CDRom' {
                break
            }
            'Unknown' {
                Write-Error "Drive type is unknown: $InputObject."
                return
            }
            'NoRootDirectory' {
                Write-Error "Drive does not exist: $InputObject."
                return
            }
            default {
                Write-Error "Drive $($Drive.Name) is $($Drive.DriveType), not Removable/CDRom."
                return
            }
        }
        $ssfDRIVES = 0x11  # "My Computer"
        $shell = New-Object -comObject Shell.Application
        $driveObj = $shell.Namespace($ssfDRIVES).ParseName($Drive.Name)
        if (-not $driveObj) {
            Write-Error "Could not get shell object of drive $($Drive.Name)."
            return
        }
        $driveObj.InvokeVerb("Eject")  # NOTE: localized string
    }
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


# Pipeline shorthands for count, first, last and indexed objects.
function global:Count {
    $Input | Measure-Object | % count
}
function global:First ([int]$Count = 1, [int]$Skip = 0) {
    $Input | Select-Object -First $Count -Skip $Skip
}
function global:Last ([int]$Count = 1, [int]$Skip = 0) {
    $Input | Select-Object -Last $Count -Skip $Skip
}
<#
.SYNOPSIS
    Select from pipeline by index.
.DESCRIPTION
    Get the n-th (0-based) pipeline object(s). If Ordered is not set, this is
    the same as `Select-Object -Index ...`: objects are matched in pipeline
    order and duplicate indexes are ignored.
.PARAMETER InputObject
    Input objects. Must be specified using the pipeline.
.PARAMETER Index
    List of indexes of input objects to be returned.
.PARAMETER Ordered
    Forces the returned objects to match the indexes exactly as specified and
    allows duplicate indexes to return the same object multiple times.
.INPUTS
    Objects.
.OUTPUTS
    Objects.
#>
function global:Nth {
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        $InputObject,

        [Parameter(Mandatory, Position = 0)]
        [int[]]$Index,

        [switch]$Ordered
    )
    begin {
        $items = [System.Collections.ArrayList]::new()
    }
    process {
        [void]$items.Add($InputObject)
    }
    end {
        if (-not $Ordered) {
            $items | Select-Object -Index $Index
        } else {
            $output = [object[]]::new($Index.Count)
            for ($i = 0; $i -lt $Index.Count; ++$i) {
                $output[$i] = $items[$Index[$i]]
            }
            $output
        }
    }
}
Set-Alias -Scope global rev Get-ReverseArray
Set-Alias -Scope global shuf Get-ShuffleArray
Set-Alias -Scope global pick Get-OrderedSubset


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


# Get the datetime of the next occurence of specified time.
function global:NextTime {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Time  # 'HH[:]mm' format
    )
    if ($Time -notmatch '^\s*(\d\d):?(\d\d)\s*$') {
        Write-Error "Invalid time string: $Time."
        return
    }
    $h, $m = $Matches[1..2].ForEach([int])
    if ($h -gt 23) {
        Write-Error "Invalid hour: $h."
        return
    }
    if ($m -gt 59) {
        Write-Error "Invalid minute: $m."
        return
    }
    $d = Get-Date
    $t = [timespan]::new($h, $m, 0)
    $tomorrow = $t -le $d.TimeOfDay
    [datetime]::new($d.Year, $d.Month, $d.Day, $h, $m, 0).AddDays($tomorrow)
}


# Generate time/value objects of pipeline contents.
# Useful for timing program output. If non-output streams (e.g. error) are also
# needed, they should be merged with stdout beforehand (i.e. 2>&1).
function global:Get-TimedOutput {
    begin {
        $t = [System.Diagnostics.Stopwatch]::new()
        $t.Start()
        $prev = [timespan]::new(0)
    }
    process {
        [PSCustomObject]@{
            Elapsed = $t.Elapsed
            Delta = $t.Elapsed - $prev
            Object = $_
        }
        $prev = $t.Elapsed
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


<#
.SYNOPSIS
    Pop random item(s) from collection.
.DESCRIPTION
    Removes and return one or more random items from the specified collection.
    The collection size must not be fixed.
.PARAMETER InputObject
    Source collection. Cannot be passed via the pipeline.
.PARAMETER Count
    Number of items to return. A warning is issued if less items were available
    than requested.
.INPUTS
    None.
.OUTPUTS
    Any object(s).
.NOTES
    If running in a loop, a check for an empty collection must be used as an
    exit condition.
#>
function global:Pop-RandomItem {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        $InputObject,

        [int]$Count = 1
    )
    for ($n = 0; $n -lt $Count; ++$n) {
        if ($InputObject.Count -eq 0) {
            Write-Warning "More items were requested than were available."
            break
        }
        $i = Get-Random -Maximum $InputObject.Count
        try {
            $item = $InputObject.Item($i)
            $InputObject.RemoveAt($i)
            Write-Output $item
        } catch {
            throw  # make any error terminating
        }
    }
}


<#
.SYNOPSIS
    Manage system volume using nircmd.exe.
.DESCRIPTION
    ...
.PARAMETER Level
    Set the sound level. Can specify one value to set both the left and right
    channels to the same level or two to set them individually.
    Valid range is 0..100. If Relative is set, the range is -100..100.
.PARAMETER Relative
    Set the sound level relative to the current value.
.PARAMETER Mute
    Set the mute state. Available options: on, off, toggle.
.PARAMETER Component
    The sound component to modify. One of: master, waveout, synth, cd,
    microphone, phone, aux, line, headphones, wavein.
.PARAMETER DeviceIndex
    Numeric index of sound device if there more than one installed. If omitted,
    the default device is used.
.INPUTS
    None.
.OUTPUTS
    None.
#>
function global:Set-SystemVolume {
    [CmdletBinding()]
    param(
        [Parameter(ParameterSetName = 'Level')]
        [ValidateCount(1, 2)]
        [ValidateRange(-100, 100)]
        [int[]]$Level,

        [Parameter(ParameterSetName = 'Level')]
        [switch]$Relative,

        [Parameter(ParameterSetName = 'Mute')]
        [ValidateSet('on', 'off', 'toggle')]
        [string]$Mute,

        [ValidateSet('master', 'waveout', 'synth', 'cd', 'microphone', 'phone',
            'aux', 'line', 'headphones', 'wavein')]
        [string]$Component = 'master',

        [int]$DeviceIndex
    )
    switch ($PSCmdlet.ParameterSetName) {
        'Level' {
            $cmdPfx = if ($Relative) { 'change' } else { 'set' }
            $cmdSfx = if ($Level.Count -eq 1) { '' } else { '2' }
            $args = @(
                $cmdPfx + 'sysvolume' + $cmdSfx
                $Level | % { [int]($_ / 100 * 65535) }
            )
        }
        'Mute' {
            $MUTEVAL = @{ 'off' = 0; 'on' = 1; 'toggle' = 2 }
            $args = @(
                'mutesysvolume'
                $MUTEVAL[$Mute]
            )
        }
    }
    $args += $Component
    if ($PSBoundParameters.ContainsKey('DeviceIndex')) {
        $args += $DeviceIndex
    }
    nircmdc.exe @args
}


# Toggle ModularPrompt path display between Full and Tail.
function global:tpd {
    $cur = (Get-ModPromptOption).PathDisplay
    $new = if ($cur -eq 'Tail') { 'Full' } else { 'Tail' }
    Set-ModPromptOption -PathDisplay $new
}


# List all available Windows SDK header folders.
function global:sdkhdr {
    gi 'C:\Program Files (x86)\Windows Kits\*\include\*'
}


<#
.SYNOPSIS
    Filter hashtable items.
.DESCRIPTION
    Returns a hashtable with a subset of items from an existing object.
.PARAMETER InputObject
    Source hashtable.
.PARAMETER Name
    List of key names to select. Missing keys in the source object are ignored.
.INPUTS
    Hashtable.
.OUTPUTS
    Hashtable.
#>
function global:Select-Hashtable {
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [System.Collections.Hashtable]$InputObject,

        [Parameter(Position = 0)]
        [string[]]$Name
    )
    begin {
        $keys = [System.Collections.Generic.HashSet[string]]$Name
    }
    process {
        $ret = @{}
        foreach ($e in $InputObject.GetEnumerator()) {
            if ($e.Name -in $keys) {
                $ret[$e.Name] = $e.Value
            }
        }
        $ret
    }
}


# Filter objects that are files/dirs/either.
# Input must have PSPath member.
filter global:IfFile ([switch]$Not) { if (($_ | Test-Path -PathType Leaf) -xor $Not) { $_ } }
filter global:IfDir ([switch]$Not) { if (($_ | Test-Path -PathType Container) -xor $Not) { $_ } }
filter global:IfExists ([switch]$Not) { if (($_ | Test-Path -PathType Any) -xor $Not) { $_ } }


# Create global tva..tvz functions that tee input to globals $a..$z.
# These match the behavior of Tee-Object, which depends on the number of processed objects:
#   - If 0, the global variable is not modified at all.
#   - If 1, the global variable is set to that exact object (even if $null).
#   - Otherwise, the global variable is set to an object array.
[char[]]'abcdefghijklmnopqrstuvwxyz' | % {
    $opt = @{
        Path = 'Function:\'
        Name = "global:tv${_}"
        Value = [scriptblock]::Create(@"
            begin { `$items = [System.Collections.ArrayList]::new() }
            process { Write-Output `$_; [void]`$items.Add(`$_) }
            end { if (`$items.Count -gt 0) {
                `$value = if (`$items.Count -eq 1) {
                    `$items[0]
                } else {
                    [object[]]`$items
                }
                New-Item -Path Variable:\ -Name "global:${_}" -Value `$value -Force > `$null
            } }
"@)
        Force = $true
    }
    New-Item @opt > $null
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
Set-Alias -Scope global mpc Invoke-MediaPlayerClassic
Set-Alias -Scope global fb Invoke-Foobar2000
Set-Alias -Scope global eatlines D:\projects\eatlines.exe
Set-Alias -Scope global ff Get-DiskSizeFudgeFactor
Set-Alias -Scope global espeak 'C:\Program Files (x86)\eSpeak\command_line\espeak.exe'
Set-Alias -Scope global nw ~\newwall.ps1
Set-Alias -Scope global fst Get-FileNameSafeTimestamp
Set-Alias -Scope global drv Get-DiskDrive
Set-Alias -Scope global sd Invoke-ShellDelete
Set-Alias -Scope global ej global:Dismount-RemovableDrive
Set-Alias -Scope global b64 ConvertFrom-Base64
Set-Alias -Scope global wm 'C:\Program Files (x86)\WinMerge\WinMergeU.exe'
Set-Alias -Scope global icls Clear-HostInteractive
Set-Alias -Scope global fscr Switch-ConsoleFullScreen
Set-Alias -Scope global ot Get-ObjectType
Set-Alias -Scope global gvi Get-VideoInfo
Set-Alias -Scope global gec Get-ExtensionCategory


# change default transfer protocols ("Ssl3, Tls"), both of which are insecure;
# note that TLS v1.1 has also been deprecated
[Net.ServicePointManager]::SecurityProtocol = 'Tls12, Tls13'


function global:EnablePythonUtf8Piping {
  $global:OutputEncoding = [System.Text.UTF8Encoding]::new($false)  # no BOM
  $Env:PYTHONUTF8 = 1
}


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
            if ([console]::CapsLock) {
                # TODO: Scroll window up 1 line if we were at the view bottom
                Clear-HostUp -Count 2
             } else {
                Clear-HostUp -Count 1
                Write-Host ''
                <#$Host.UI.RawUI.CursorPosition = [System.Management.Automation.Host.Coordinates]::new(
                    0, $Host.UI.RawUI.CursorPosition.Y - 1
                )
                Write-Host -NoNewLine (' ' * $Host.UI.RawUI.BufferSize.Width)
                #>
            }
        }
    }

# Add the "IBM Common User Access" variants for clipboard interaction.
# PSReadline 2.2.6 only includes the Paste one by default.
Set-PSReadLineKeyHandler -Key 'Shift+Delete' -Function Cut
Set-PSReadLineKeyHandler -Key 'Ctrl+Insert' -Function Copy
Set-PSReadLineKeyHandler -Key 'Shift+Insert' -Function Paste


<#
.SYNOPSIS
    Get PSReadLine colors.
.DESCRIPTION
    Returns a hashset of the current PSReadLine colors in extended Clipper
    color format. Note that the DefaultToken color is renamed as Default, to
    match the color-setting parameter name.
.INPUTS
    None.
.OUTPUTS
    Hashset.
#>
function global:Get-PSReadLineColor {
    [CmdletBinding()]
    param()
    $opt = Get-PSReadLineOption
    $ret = [ordered]@{}
    foreach ($s in ($opt | Get-Member *color | % Name)) {
        $setKey = $s -replace 'color$',''
        if ($setKey -eq 'DefaultToken') {
            $setKey = 'Default'
        }
        $ret[$setKey] = ConvertFrom-AnsiColor $opt.$s
    }
    Write-Output $ret
}


<#
.SYNOPSIS
    Set PSReadLine colors.
.DESCRIPTION
    Set one or more PSReadLine colors using extended Clipper color format.
.INPUTS
    None.
.OUTPUTS
    None.
#>
function global:Set-PSReadLineColor {
    [CmdletBinding()]
    param(
        [string]$Command,
        [string]$Comment,
        [string]$ContinuationPrompt,
        [string]$Default,
        [string]$Emphasis,
        [string]$Error,
        [string]$InlinePrediction,
        [string]$Keyword,
        [string]$ListPrediction,
        [string]$ListPredictionSelected,
        [string]$Member,
        [string]$Number,
        [string]$Operator,
        [string]$Parameter,
        [string]$Selection,
        [string]$String,
        [string]$Type,
        [string]$Variable
    )
    $colors = @{}
    foreach ($e in $PSBoundParameters.GetEnumerator()) {
        $colors[$e.Key] = [string](ConvertTo-AnsiColor $e.Value)
    }
    Set-PSReadLineOption -Colors $colors
}


# Set error prompt to double exclamation mark.
# NOTE: Ideally this should interface with ModularPrompt, but currently it just
# uses the single space between the prompt and command line.
Set-PSReadLineOption -PromptText ' ',([char]0x203c)

# Change default (n/w+), since the background intensity prevents the color
# from being interpreted properly and it shows the ANSI codes instead.
# Apparently this happens with all PSReadLine color settings.
# I think it used to work properly before ~2023-02-20, but I'm not sure
# if it did or what caused it to change. I only remember using Colortool
# to mess with the console colors before noticing this.
Set-PSReadLineColor -Selection n/w
