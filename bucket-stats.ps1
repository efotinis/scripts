#requires -Modules NiceConvert

<#
Show group statistics for properties interpreted as size or time.
#>

#[CmdletBinding()]
param(
    [string[]]$Property,# input properties to process
    [int[]]$Group,      # bucket limits (upper, inclusive);
                        # need not be ordered or unique

    #[Parameter(Mandatory)]
    [ValidateSet('TimeSeconds', 'TimeMinutes', 'SizeBytes', 'SizeMiB')]
    [string]$ValueType

    <#
    [switch]$Time,      # treat input as seconds; output as 'hhh:mm:ss'
    [switch]$Minutes,   # treat groups as minutes; implies -Time

    [switch]$Size,      # treat input as size; output as 'N.NN ?B'
    [switch]$Mb         # treat groups as MiB; implies -Size
    #>
)

Set-StrictMode -Version Latest

switch ($ValueType) {
    'TimeSeconds' {
        $multiplier = 1
        Set-Alias valueFormatter ConvertTo-NiceDuration
    }
    'TimeMinutes' {
        $multiplier = 60
        Set-Alias valueFormatter ConvertTo-NiceDuration
    }
    'SizeBytes' {
        $multiplier = 1
        Set-Alias valueFormatter ConvertTo-NiceSize
    }
    'SizeMiB' {
        $multiplier = 1mb
        Set-Alias valueFormatter ConvertTo-NiceSize
    }
}

<#
$multiplier = 1
if ($Minutes) {
    $Time = $true
    $multiplier = 60
}
if ($Mb) {
    $Size = $true
    $multiplier = 1mb
}
if (-not ($Size -xor $Time)) {
    Write-Error 'exactly one of -Time,-Size options must be specified'
    return
}
if ($Size) {
    Set-Alias valueFormatter ConvertTo-NiceSize
}
if ($Time) {
    Set-Alias valueFormatter ConvertTo-NiceDuration
}
#>

# Create new list of buckets, consisting of upper limit and empty array.
# TODO: maybe optimize array to ArrayList, since it's getting appended often
function initBuckets ($groups, $multiplier) {
    $groups = $groups | Sort-Object -Unique
    $buckets = @()
    foreach ($g in $groups) {
        $buckets += ,@(($g * $multiplier), @())
    }
    $buckets += ,@([int]::MaxValue, @())
    return $buckets
}


# Add property values to buckets and return cached values.
function loadBuckets ($inputObj, $buckets, $property) {
    $cache = @()
    foreach ($item in $inputObj) {
        $value = $item.$property
        foreach ($b in $buckets) {
            if ($value -le $b[0]) {
                $b[1] += $value
                break
            }
        }
        $cache += $value
    }
    return $cache
}


# Create output info from buckets.
function outputBuckets ($buckets) {
    foreach ($b in $buckets) {
        [PSCustomObject]@{
            limit=$b[0]
            stats=$b[1] | Measure-Stats 2> $null
        }
    }
}


# String to display in Limit column.
function LimitStr ($n) {
    if ($n -eq [int]::MaxValue) {
        '>'
    }
    elseif ($n -eq [int]::MinValue) {
        'total'
    }
    else {
        valueFormatter $n
    }
}


foreach ($curProp in $Property) {

    $cache = $null  # input cache in case groups have to be processed first
    $output = @()

    # group stats
    if ($Group -ne $null) {
        $buckets = initBuckets $Group $multiplier
        $cache = loadBuckets $Input $buckets $curProp
        $output += outputBuckets $buckets
    }

    # total stats
    if ($cache -eq $null) {
        $stats = $Input | Measure-Stats $curProp
    }
    else {
        $stats = $cache | Measure-Stats
    }
    $output += [PSCustomObject]@{
        limit=[int]::MinValue
        stats=$stats
    }

    $output | Format-Table @(
        @{n='Limit'; a='r'; e={LimitStr $_.limit}}
        @{n='Count'; a='r'; e={$_.stats.Count}}
        @{n='Sum'; a='r'; e={valueFormatter $_.stats.Sum}}
        @{n='Average'; a='r'; e={valueFormatter $_.stats.Mean}}
        @{n='Stdev'; a='r'; e={valueFormatter $_.stats.Stdev}}
    )

}
