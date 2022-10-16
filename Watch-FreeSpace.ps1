[CmdletBinding()]
param(
    [string]$Drive = (Get-Location).Drive.Name,  # drive letter; optional colon
    
    [int]$PollMsec = 500,  # auto-update rate
    
    [switch]$Manual,  # manually update by keypress

    [long]$InitialDelta = 0,  # assume this delta for restarting a previous session

    [timespan]$InitialElapsed = 0  # assume this elapsed for restarting a previous session
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
