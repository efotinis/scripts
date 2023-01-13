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
        - drive         Drive free space.
        - delta         Total change since start.
        - step          Change since previous check.

.PARAMETER Drive
    The drive to monitor. Can specify a letter with an optional colon.
    The default is the drive of the current location.

.PARAMETER PollMsec
    Interval in milliseconds to check for changes. Output is only generate when
    there's an actual, non-zero change in free space. Default is 500.

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

    [switch]$Manual,

    [long]$InitialDelta = 0,

    [timespan]$InitialElapsed = 0
)

Set-StrictMode -Version Latest


function Size ([long]$n, [switch]$WithPlus) {
    $s = (PrettySize $n) -replace 'bytes','B'
    if ($WithPlus -and $n -ge 0) { $s = '+' + $s }
    $s
}


$t0 = Get-Date
$driveObj = Get-PSDrive ($Drive.TrimEnd(':'))
if (-not $driveObj) { exit }


echo ('started tracking {0}: ({1}) at {2:o}' -f @(
    $($driveObj.Name)
    $driveObj.Description
    $t0
))
if ($Manual) {
    echo 'hit Enter to update (Ctrl-C exits)'
}
else {
    echo "auto-update every $PollMsec msec (Ctrl-C exits)"
}


echo ('{0,19:} {1,16:} {2,10} {3,10} {4,11}' -f 'timestamp','elapsed','drive','delta','step')

$prevFree = $driveObj.Free
$delta = $InitialDelta
$first = $true
while ($true) {
    $timestamp = Get-Date
    $elapsed = $timestamp - $t0 + $InitialElapsed
    $free = $driveObj.Free
    $step = $free - $prevFree
    $prevFree = $free
    $delta += $step
    $prompt = '{0:G} {1} {2,10} {3,10} {4,11}' -f @(
        $timestamp
        $elapsed
        Size $free
        Size $delta
        Size $step -WithPlus
    )
    if ($Manual) {
        Read-Host $prompt | Out-Null
    }
    else {
        if ($step -or $first) {
            echo $prompt
            $first = $false
        }
        sleep -millisec $PollMsec
    }
}
