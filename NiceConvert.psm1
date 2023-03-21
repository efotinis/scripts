<#
.SYNOPSIS
    Convert a number of bytes to a human-readable size string.

.DESCRIPTION
    Converts a number of bytes to a value with 3 significant digits and a unit
    suffix. Values below roughly 1kb get the suffix "bytes" (or "byte").

.PARAMETER Bytes
    Input number. Can be negative in which case a "-" prefix is added.

.PARAMETER Style
    Suffix and calculation selection. One of:
        - jedec: Multiples of 1024, without "i", e.g. 1024 == 1.00 KB. Commonly used in Windows. Default.
        - iec: Multiples of 1024, with "i", e.g. 1024 == 1.00 KiB. Commonly used in Linux.
        - metric: Multiples of 1000, without "i", e.g. 1000 == 1.00 KB. Commonly used by storage device manufacturers.
        - bozo: Multiples of 1000, with "o", e.g. 1000 == 1.00 KoB. My own non-standard style to protest against the gibi-jibi silliness.

.INPUTS
    Long int.

.OUTPUTS
    String.
#>
function ConvertTo-NiceSize
{
    param (
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [Alias('Length')]
        [long]$Bytes,

        [ValidateSet('jedec', 'iec', 'metric', 'bozo')]
        [string]$Style = 'jedec'
    )
    process {
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
        } elseif ($Style -eq 'metric') {
            $MULTIPLIER = 1000
            $PREFIX_TAIL = 'B'
        } else {
            $MULTIPLIER = 1000
            $PREFIX_TAIL = 'oB'
        }

        [double]$n = $Bytes
        [string]$Unit = ''

        if ($n -le 999) {
            Write-Output ("$Sign$n byte" + $(if ($n -eq 1) { '' } else { 's' }))
            return
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
        Write-Output (('{0}{1:'+$Fmt+'} {2}{3}') -f ($Sign, $n, $Unit, $PREFIX_TAIL))
    }
}


<#
.SYNOPSIS
    Convert a human-readable size string to a number of bytes.

.DESCRIPTION
    Converts a human -readble string representation of a size to a number of
    bytes. This is the inverse of ConvertTo-NiceSize, but it's more lenient
    with the input string (there's no restriction on significant digits and
    whitespace is ignored).

.PARAMETER Size
    A human-readable size string with a unit.

.PARAMETER Base10
    Force interpretation of metric units (multiples of 1000) when no "i" is in
    the unit, e.g. "1.00 KB" -> 1000. By default, jedec units are assumed, e.g.
    "1.00 KB" -> 1024. This is ignored when units include "i" or "o".

.INPUTS
    String.

.OUTPUTS
    Long int.
#>
function ConvertFrom-NiceSize
{
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [Alias('Length')]
        [string]$Size,

        [switch]$Base10
    )
    process {
        $Size = $Size.ToLower() -replace '\s+', ''

        if (-not ($Size -match '^([0-9.]+)(.*)$')) {
            Write-Error ('invalid size: "{0}"' -f $Size)
            return
        }
        $Number, $Unit = $Matches[1..2]
        $Number = [double]$Number
        if ($Unit -in 'b','byte','bytes') {
            Write-Output ([long]$Number)
            return
        }

        if (-not ($Unit -match '^([kmgtpe])([io]?)b?$')) {
            Write-Error ('invalid unit: "{0}"' -f $Unit)
            return
        }
        $Unit, $Spec = $Matches[1..2]
        $Base = if ($Spec -eq 'o' -or ($Spec -eq '' -and $Base10)) {
            1000
        } else {
            1024
        }
        $Factor = [Math]::Pow($Base, 'kmgtpe'.IndexOf($Unit) + 1)
        Write-Output ([long]($Number * $Factor))
    }
}


<#
.SYNOPSIS
    Convert a number of seconds to a human-readable time string.

.DESCRIPTION
    Converts seconds to a representation of "[-]hh:mm:ss.fff".

.PARAMETER Seconds
    Input seconds. Negative and fractional numbers are allowed.

.PARAMETER Decimals
    Number of decimals in output. Default is 0.

.PARAMETER Plus
    Optional string prefix for positive output. Default is "".

.INPUTS
    Double.

.OUTPUTS
    String.
#>
function ConvertTo-NiceSeconds
{
    param(
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [Alias('Duration')]
        [double]$Seconds,

        [int]$Decimals = 0,

        [string]$Plus = ''
    )
    process {
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
        Write-Output ($Fmt -f $Sign,$Hours,$Minutes,($Seconds+$fract))
    }
}


<#
.SYNOPSIS
    Convert a number of seconds to a human-readable duration string.

.DESCRIPTION
    Converts seconds to a representation of "[[[h]h:]m]m:ss".

    The differences from ConvertTo-NiceSeconds are:
        - No fractional seconds are displayed.
        - The first part is never 0-padded.
        - When seconds are displayed and the hour part is zero, the latter is
        hidden, e.g. 600 -> "10:00".

.PARAMETER Seconds
    Input seconds. Negative and fractional numbers are allowed.

.PARAMETER HideSeconds
    Suppress seconds display. The output is always "[h]h:mm".

.PARAMETER Plus
    Optional string prefix for positive output. Default is "".

.INPUTS
    Int.

.OUTPUTS
    String.
#>
function ConvertTo-NiceDuration
{
    param(
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [Alias('Duration')]
        [int]$Seconds,

        [switch]$HideSeconds,

        [string]$Plus = ''
    )
    process {
        if ($Seconds -lt 0) {
            $Seconds = -$Seconds
            $Sign = '-'
        } else {
            $Sign = $Plus
        }
        if ($HideSeconds) {
            $Minutes = [System.Math]::Round($Seconds / 60)
            $Hours = [System.Math]::DivRem($Minutes, 60, [ref]$Minutes)
            Write-Output ('{0}{1:#0}:{2:00}' -f $Sign,$Hours,$Minutes)
        } else {
            $Minutes = [System.Math]::DivRem($Seconds, 60, [ref]$Seconds)
            $Hours = [System.Math]::DivRem($Minutes, 60, [ref]$Minutes)
            if ($Hours) {
                Write-Output ('{0}{1:#0}:{2:00}:{3:00}' -f $Sign,$Hours,$Minutes,$Seconds)
            }
            else {
                Write-Output ('{0}{1:#0}:{2:00}' -f $Sign,$Minutes,$Seconds)
            }
        }
    }
}


<#
.SYNOPSIS
    Convert a human-readable duration string to a number of seconds.

.DESCRIPTION
    Converts seconds from a representation of "[-][[[h]h:]m]m:ss".

.PARAMETER Duration
    A human-readable duration string.

.INPUTS
    String.

.OUTPUTS
    Int.
#>
function ConvertFrom-NiceDuration
{
    param(
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [string]$Duration
    )
    process {
        $Duration = $Duration.Trim()
        if (-not ($Duration -match '^(-)?(?:(\d+):)?(?:(\d\d?):)(\d\d)$')) {
            Write-Error ('invalid duration: "{0}"' -f $Duration)
            return
        }
        $Sign, $Hours, $Minutes, $Seconds = $Matches[1..4]
        $Hours = [int]$Hours
        $Minutes = [int]$Minutes
        $Seconds = [int]$Seconds
        $Sign = if ($Sign -eq '-') { -1 } else { 1 }
        Write-Output ($Sign * ((($Hours * 60) + $Minutes) * 60 + $Seconds))
    }
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


<#
.SYNOPSIS
    Convert a date or timespan to a human-readable age string.

.DESCRIPTION
    Convert a time span to a string representation using time parts.

.PARAMETER DateOrSpan
    The date or span of the age to output.

.PARAMETER Precision
    Number of most significant time parts to output. Default is 2.

    Time parts generated are:
        - c: centuries
        - y: years
        - mo: months
        - d: days
        - h: hours
        - m: minutes
        - s: seconds

    Note that centuries, years and months are approximates.

.PARAMETER Format
    Pair of format strings used to format output of past and future dates
    respectively as a sentence. Defaults are '{0} ago' and 'in {0}'.

.PARAMETER Joiner
    String to use between parts. Default is " ".

.PARAMETER Simple
    Output only time parts without sentence formatting.

.PARAMETER Tabulate
    Output only time parts without sentence formatting. Also inserts whitespace
    to align time parts for columnar output.

.PARAMETER Invert
    Swap interpretation of past and future dates.

.INPUTS
    Datetime or Timespan.

.OUTPUTS
    String.
#>
function ConvertTo-NiceAge
{
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        $DateOrSpan,

        [int]$Precision = 2,

        $Format = @('{0} ago','in {0}'),

        [string]$Joiner = ' ',

        [switch]$Simple,

        [switch]$Tabulate,

        [switch]$Invert
    )
    process {
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
            Write-Output ($Format[$negative] -f $whole)
        }
        else {
            Write-Output $whole
        }
    }
}


Export-ModuleMember -Function *-*
