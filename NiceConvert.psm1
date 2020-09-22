<#
.SYNOPSIS
    Conversion to/from human-readable string representations.
.DESCRIPTION
    Provides utility functions to convert values like bytes, seconds and
    time spans into more human-readable strings and back.
.EXAMPLE
    PS> ...
    (explanation)
.INPUTS
    ...
.OUTPUTS
    ...
.NOTES
    The conversions are only intended for displaying and as such are not exact.
#>


# Convert bytes to '[-]N <unit>' where N always has 3 significant digits.
function ConvertTo-NiceSize
{
    param (
        [Parameter(Mandatory)]
        [long]$Bytes,
        
        [ValidateSet('jedec', 'iec', 'metric')]
        [string]$Style = 'jedec'
    )

    [string]$Sign = ''
    if ($Bytes -lt 0) {
        $Sign = '-'
        $Bytes = -$Bytes
    }
    
    if ($Style -eq 'jedec') {
        $MULTIPLIER = 1024
        $PREFIX_TAIL = 'B'
    } elseif ($Style -eq 'iec') {
        $MULTIPLIER = 1024
        $PREFIX_TAIL = 'iB'
    } else {
        $MULTIPLIER = 1000
        $PREFIX_TAIL = 'B'
    }

    [double]$n = $Bytes
    [string]$Unit = ''

    if ($n -le 999) {
        return "$Sign$n byte" + $(if ($n -eq 1) { '' } else { 's' })
    }

    foreach ($c in [char[]]'KMGTPE') {
        if ($n -ge 999.5) {
            $Unit = $c
            $n /= $MULTIPLIER
        }
    }
    [string]$Fmt = $(
        if ($n -lt 9.995) {
            'N2'
        } elseif ($n -lt 99.95) {
            'N1'
        } else {
            'N0'
        }
    )
    return ('{0}{1:'+$Fmt+'} {2}{3}') -f ($Sign, $n, $Unit, $PREFIX_TAIL)
}


function ConvertFrom-NiceSize
{
    param(
        [Parameter(Mandatory)]
        [string]$Size,
        
        # Assume base-10, when not using IEC prefix (otherwise ignored).
        [switch]$Base10
    )
    
    $Size = $Size.ToLower() -replace '\s+', ''
    
    if (-not ($Size -match '^([0-9.]+)(.*)$')) {
        throw ('invalid size: "{0}"' -f $Size)
    }
    $Number, $Unit = $Matches[1..2]
    $Number = [double]$Number
    if ($Unit -in 'b','byte','bytes') {
        return [long]$Number
    }
    
    if (-not ($Unit -match '^([kmgtpe])(i?)b?$')) {
        throw ('invalid unit: "{0}"' -f $Unit)
    }
    $Unit, $Iec = $Matches[1..2]
    $Base = if ($Iec -or -not $Base10) { 1024 } else { 1000 }
    $Factor = [Math]::Pow($Base, 'kmgtpe'.IndexOf($Unit) + 1)
    return [long]($Number * $Factor)
}


# Convert seconds to "[-]hh:mm:ss.lll".
function ConvertTo-NiceSeconds
{
    param(
        [Parameter(Mandatory)]
        [double]$Seconds,
        
        [int]$Decimals = 0,
        
        [string]$Plus = ''
    )
    if ($Seconds -lt 0) {
        $Seconds = -$Seconds
        $Sign = '-'
    } else {
        $Sign = $Plus
    }
    if ($Decimals -lt 0) {
        $Decimals = 0
    }
    # NOTE: save fractional part, since DivRem implicitly casts to int/long
    $fract = $Seconds - [System.Math]::Truncate($Seconds)
    $Minutes = [System.Math]::DivRem($Seconds, 60, [ref]$Seconds)
    $Hours = [System.Math]::DivRem($Minutes, 60, [ref]$Minutes)
    $Fmt = '{0}{1:00}:{2:00}:{3:00.' + ('0' * $Decimals) + '}'
    $Fmt -f $Sign,$Hours,$Minutes,($Seconds+$fract)
}


# Convert seconds to "[[[h]h:]m]m:ss" (i.e. like video durations shown on YouTube).
function ConvertTo-NiceDuration
{
    param(
        [Parameter(Mandatory)]
        [int]$Seconds,
        
        [string]$Plus = ''
    )
    if ($Seconds -lt 0) {
        $Seconds = -$Seconds
        $Sign = '-'
    } else {
        $Sign = $Plus
    }
    $Minutes = [System.Math]::DivRem($Seconds, 60, [ref]$Seconds)
    $Hours = [System.Math]::DivRem($Minutes, 60, [ref]$Minutes)
    if ($Hours) {
        '{0}{1:#0}:{2:00}:{3:00}' -f $Sign,$Hours,$Minutes,$Seconds
    }
    else {
        '{0}{1:#0}:{2:00}' -f $Sign,$Minutes,$Seconds
    }
}


function ConvertFrom-NiceDuration
{
    param(
        [Parameter(Mandatory)]
        [string]$Duration
    )
    
    $Duration = $Duration.Trim()
    if (-not ($Duration -match '^(-)?(?:(\d+):)?(?:(\d\d?):)(\d\d)$')) {
        throw ('invalid duration: "{0}"' -f $Duration)
    }
    $Sign, $Hours, $Minutes, $Seconds = $Matches[1..4]
    $Hours = [int]$Hours
    $Minutes = [int]$Minutes
    $Seconds = [int]$Seconds
    $Sign = if ($Sign -eq '-') { -1 } else { 1 }
    $Sign * ((($Hours * 60) + $Minutes) * 60 + $Seconds)
}


function DaysToApproximateCYMD ([int]$d)
{
    $c = [Math]::DivRem($d, 36500, [ref]$d)
    $y = [Math]::DivRem($d, 365, [ref]$d)
    $m = [Math]::DivRem($d, 30, [ref]$d)
    $c, $y, $m, $d
}


# If span < 1, get all.
function GetFirstNonZeroIndexes ([object[]]$Items, [int]$Span)
{
    if ($Span -lt 1) {
        $Span = $Items.Count
    }
    # skip any zeroes before the last item
    for ($i = 0; $i -lt ($Items.Count - 1) -and -not $Items[$i]; ++$i) {
    }
    # return the first index (either first nonzero or the last item)
    $i
    $i += 1
    # return the rest
    for ($end = [Math]::Min($Items.Count, $i + $Span - 1); $i -lt $end; ++$i) {
        if ($Items[$i]) {
            $i
        }
    }
}


function ConvertTo-NiceAge
{
    param(
        [Parameter(Mandatory)]
        $DateOrSpan,

        # max count of most significant parts to show
        [int]$Precision = 2,

        # output sentence formats
        $Format = @('{0} ago','in {0}'),

        # used between parts in sentence mode
        [string]$Joiner = ' ',

        # no sentence formatting; only add '-' for negative
        [switch]$Simple,

        # like simple, but also use spaces to align parts
        [switch]$Tabulate,

        # swap begin/end semantics
        [switch]$Invert
    )


    $ts = if ($DateOrSpan -is [datetime]) {
        (Get-Date) - $DateOrSpan
    } else {
        $DateOrSpan
    }
    
    if ($Invert) {
        $ts = -$ts
    }

    $negative = $false
    if ($ts -lt 0) {
        $negative = $true
        $ts = -$ts
    }

    $d, $h, $m, $s = $ts.Days, $ts.Hours, $ts.Minutes, $ts.Seconds
    $c, $y, $mo, $d = DaysToApproximateCYMD $d
    $values = @($c, $y, $mo, $d, $h, $m, $s)
    $names = @('c', 'y','mo','d','h','m','s')
    $indexes = GetFirstNonZeroIndexes $values $Precision

    $isSentence = -not ($Simple -or $Tabulate)
    $partFmt = if ($Tabulate) { '{0,2}{1,-2}' } else { '{0}{1}' }
    if ($negative -and -not $isSentence) { $values[$indexes[0]] = -$values[$indexes[0]] }
    $parts = foreach ($i in $indexes) { $partFmt -f $values[$i],$names[$i] }
    $whole = $parts -join $Joiner

    if ($isSentence) {
        $Format[$negative] -f $whole
    }
    else {
        $whole
    }
}


Export-ModuleMember -Function *-*
