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
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [Alias('Length')]
        [long]$Bytes,

        [ValidateSet('jedec', 'iec', 'metric')]
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
        } else {
            $MULTIPLIER = 1000
            $PREFIX_TAIL = 'B'
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


function ConvertFrom-NiceSize
{
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [Alias('Length')]
        [string]$Size,

        # Assume base-10, when not using IEC prefix (otherwise ignored).
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

        if (-not ($Unit -match '^([kmgtpe])(i?)b?$')) {
            Write-Error ('invalid unit: "{0}"' -f $Unit)
            return
        }
        $Unit, $Iec = $Matches[1..2]
        $Base = if ($Iec -or -not $Base10) { 1024 } else { 1000 }
        $Factor = [Math]::Pow($Base, 'kmgtpe'.IndexOf($Unit) + 1)
        Write-Output ([long]($Number * $Factor))
    }
}


# Convert seconds to "[-]hh:mm:ss.lll".
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


# Convert seconds to "[[[h]h:]m]m:ss" (i.e. like video durations shown on YouTube).
# If $HideSeconds is true, convert to "[h]h:mm".
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


function ConvertTo-NiceAge
{
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
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
