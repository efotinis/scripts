<#
.SYNOPSIS
    Monitor free disk space.

.DESCRIPTION
    Displays changes of a drive's free space at regular intervals or when a key
    is pressed.

    Output starts with a line including the drive letter and label, followed by
    the current local time with timezone offset. The next line shows the update
    interval or a prompt for manual updates.

    Subsequent lines include the following information:
        - timestamp     Local date/time.
        - elapsed       Time since start.
        - free          Drive free space.
        - delta         Total change since start.
        - step          Change since previous check.

.PARAMETER Drive
    The drive to monitor. Can specify a letter with an optional colon.
    The default is the drive of the current location.

.PARAMETER PollMsec
    Interval in milliseconds to check for changes. Default is 500.

.PARAMETER Threshold
    Absolute value of minimum change to generate output for. If this is 0,
    output is generated for any (non-zero) change in free space. Default is 0.

.PARAMETER Manual
    Generate output only when Enter is pressed. Overrides PollMsec.

.PARAMETER InitialDelta
    Starting value of size delta to use when resuming an interrupted run.

.PARAMETER InitialElapsed
    Starting value of time elapsed to use when resuming an interrupted run.

.INPUTS
    None.

.OUTPUTS
    String.
#>

[CmdletBinding()]
param(
    [string]$Drive = (Get-Location).Drive.Name,

    [int]$PollMsec = 500,

    [uint64]$Threshold = 0,

    [switch]$Manual,

    [long]$InitialDelta = 0,

    [timespan]$InitialElapsed = 0
)

Set-StrictMode -Version Latest


# Condensed string of size value with optional plus for positive numbers.
function Size ([long]$n, [switch]$WithPlus) {
    $s = (PrettySize $n) -replace 'bytes','B'
    if ($WithPlus -and $n -gt 0) {
        '+' + $s
    } else {
        $s
    }
}


# Current time and free bytes of specified drive.
function GetState ($Drive) {
    @{ Time = Get-Date; Free = $Drive.Free }
}


# Build output line.
function StatusLine ($Current, $Previous, $Start) {
    '{0:G} {1} {2,10} {3,10} {4,11}' -f @(
        $Current.Time
        $Current.Time - $Start.Time
        Size $Current.Free
        Size -WithPlus ($Current.Free - $Start.Free)
        Size -WithPlus ($Current.Free - $Previous.Free)
    )
}


# Generate text lines shown before status output.
function OutputPreample ($Drive, $StartTime, $PollMsec, $Manual) {
    Write-Output ('Started tracking {0}: ({1}) at {2:o}' -f @(
        $Drive.Name
        $Drive.Description
        $StartTime
    ))
    if ($Manual) {
        Write-Output 'Press Enter to update or Ctrl-C to exit.'
    }
    else {
        Write-Output "Auto-update every $PollMsec msec. Press Ctrl-C to exit"
    }
    Write-Output ('{0,19:} {1,16:} {2,10} {3,10} {4,11}' -f @(
        'Time', 'Elapsed', 'Free', 'Delta', 'Step'
    ))
}


$driveObj = Get-PSDrive ($Drive.TrimEnd(':'))
if (-not $driveObj) { exit }

$start = GetState $driveObj
$start.Time -= $InitialElapsed
$start.Free -= $InitialDelta

OutputPreample $driveObj $start.Time $PollMsec $Manual | Write-Output

$previous = GetState $driveObj
$initOutput = $true
while ($true) {
    $current = GetState $driveObj
    if ($Manual) {
        $s = StatusLine $current $previous $start
        Read-Host $s | Out-Null
        $previous = $current
    } else {
        $step = $current.Free - $previous.Free
        if (
            $initOutput -or
            ($Threshold -and ([System.Math]::Abs($step) -ge $Threshold)) -or
            (-not $Threshold -and ($step -ne 0))
        ) {
            $initOutput = $false
            $s = StatusLine $current $previous $start
            Write-Output $s
            $previous = $current
        }

        Start-Sleep -Milliseconds $PollMsec
    }
}
