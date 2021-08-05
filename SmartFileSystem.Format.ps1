function global:DaysToApproximateCYMD ([int]$d)
{
    $c = [Math]::DivRem($d, 36500, [ref]$d)
    $y = [Math]::DivRem($d, 365, [ref]$d)
    $m = [Math]::DivRem($d, 30, [ref]$d)
    $c, $y, $m, $d
}


function global:FileTableAge
{
    param(
        [Parameter(Mandatory)]
        [datetime]$Date,

        # max count of most significant parts to show
        [int]$Precision = 2
    )

    # calculate absolute timespan from current time and sign
    $span = (Get-Date) - $Date
    $sign = ''
    if ($span -lt 0) {
        $span = -$span
        $sign = '-'
    }

    # break timespan into (approximate) time components with 1-char labels
    $d, $h, $m, $s = $span.Days, $span.Hours, $span.Minutes, $span.Seconds
    $c, $y, $n, $d = DaysToApproximateCYMD $d
    $components = @(
        ,($c, 'c')
        ,($y, 'y')
        ,($n, 'n')
        ,($d, 'd')
        ,($h, 'h')
        ,($m, 'm')
        ,($s, 's')
    )
    
    # find first non-zero component, leaving enough for precision
    for ($i = 0; $i -lt ($components.Count - $Precision); ++$i) {
        if ($components[$i][0]) {
            break
        }
    }

    $parts = for ($j = $i; $j -lt $i + $Precision; ++$j) {
        if ($i -eq $j) {
            $sign + $components[$j][0].ToString('D') + $components[$j][1]
        } else {
            $components[$j][0].ToString('D2') + $components[$j][1]
        }
    }
    $parts -join ':'
}


Update-FormatData -PrependPath "$Env:scripts\SmartFileSystem.Format.ps1xml"
