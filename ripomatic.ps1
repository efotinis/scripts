<#
.SYNOPSIS
    Save web audio streams.
.DESCRIPTION
    Uses Streamripper to record web radio.
.PARAMETER Destination
    Base output directory. Each station recording is saved in a subdirectory
    named after the station. Defaults to the value of the SROUT environment
    variable (if it exists), otherwise to the current directory.
.INPUTS
    Nothing
.OUTPUTS
    Nothing
#>

[CmdletBinding()]
param(
    [string]$Destination
)


# assign default destination
$isDestSpecified = $PSBoundParameters.ContainsKey('Destination')
if (-not $isDestSpecified) {
    $destEnv = Get-Item -LiteralPath Env:SROUT -ErrorAction Ignore
    $Destination = if ($destEnv) {
        $destEnv.Value
    } else {
        '.'
    }
}

$Agent = 'foobar2000/1.3.16'
$CommonStations = (
    ('PopTron', 'http://ice3.somafm.com/poptron-64-aac'),
    ('1291AlternativeRock', 'http://listen.radionomy.com/1291AlternativeRock'),
    ('Radio Swiss Pop', 'http://stream.srg-ssr.ch/m/rsp/aacp_96'),
    ('Radio Paradise', 'http://stream-uk1.radioparadise.com/aac-64'),
    ('Another Music Project', 'http://radio.anothermusicproject.com:8000/idm')
)

# Search for and return the path of streamripper.exe in the usual locations.
function LocateExecutable {
    $path1 = "$Env:ProgramFiles\Streamripper\streamripper.exe"
    $path2 = "${Env:ProgramFiles(x86)}\Streamripper\streamripper.exe"
    if (Test-Path $path1) {
        Write-Output $path1
    } elseif (Test-Path $path2) {
        Write-Output $path2
    } else {
        Write-Error 'Could not locate streamripper.exe.'
    }
}

$Ripper = LocateExecutable
if (-not $Ripper) {
    return
}

# Select from menu of common station or get custom URL.
function SelectStream {
    Write-Host 'common stations:'
    $Index = 1
    foreach ($Station in $CommonStations) {
        Write-Host "  $Index. $($Station[0])"
        $Index += 1
    }
    while ($true) {
        $Resp = (Read-Host 'enter station number or custom URL').Trim()
        if ($Resp -match '^\d+$') {
            $Resp = [int]$Resp
            if ($Resp -gt 0 -and $Resp -le $CommonStations.Count) {
                return $CommonStations[$Resp - 1][1]
            }
            Write-Host 'invalid index'
        }
        elseif ($Resp) {
            return $Resp
        }
    }
}


# Select number of minutes to split output or 0 for no splitting
function SelectChunk {
    $Default = '180'
    while ($true) {
        $Resp = (Read-Host "enter chunk size in minutes (0 for continuous; default: $Default)").Trim()
        if (-not $Resp) {
            $Resp = $Default
        }
        if ($Resp -match '^\d+$') {
            return [int]$Resp
        }
        Write-Host 'bad value'
    }
}


$Stream = SelectStream
$ChunkMinutes = SelectChunk

$Args = @(
    $Stream
    '-d', $Destination  # output directory
    '-a', '-A'  # output single file, suppress individual files
    '-r', '-R', '0'  # create relay server without connection count limit
    '-u', $Agent  # hide Streamripper's identity
    '--codeset-id3=cp1253'  # use something that usually works
)

if ($ChunkMinutes) {
    $Args += @(
        '-l', ($ChunkMinutes*60)  # stop after specified minutes
    )
    $RunNo = 1
    while ($true) {
        $Start = Get-Date
        $End = (Get-Date) + (New-TimeSpan -Minutes $ChunkMinutes)
        $Host.UI.RawUI.WindowTitle = ('{0}-minute run #{1}, started on {2:G}, ends on {3:G}' -f ($ChunkMinutes, $RunNo, $Start, $End))
        & $Ripper @Args
        $RunNo += 1
    }
}
else {
    $Host.UI.RawUI.WindowTitle = ('infinite run, started on {0:G}' -f (Get-Date))
    & $Ripper @Args
}
