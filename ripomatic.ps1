<#
.SYNOPSIS
    Save web audio streams.
.DESCRIPTION
    Uses Streamripper to record web radio.
.PARAMETER Uri
    Stream URI to record.
.PARAMETER ChunkMinutes
    Recording into parts of this length in minutes. Default is 0, which means
    no splitting.
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
    [Parameter(Mandatory)]
    [string]$Uri,
    
    [int]$ChunkMinutes = 0,

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


$Args = @(
    $Uri
    '-d', $Destination  # output directory
    '-a', '-A'  # output single file, suppress individual files
    '-r', '-R', '0'  # create relay server without connection count limit
    '-u', $Agent  # hide Streamripper's identity
    '--codeset-id3=cp1253'  # use something that usually works
)

if ($ChunkMinutes) {
    $Args += @(
        '-l', ($ChunkMinutes * 60)  # stop after specified minutes
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
