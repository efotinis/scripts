#requires -Modules ColorUtil, PipelineUtil

<#
.SYNOPSIS
    Write string with colored parts.

.DESCRIPTION
    Output string to host by coloring substrings matching specified regular expressions.

.PARAMETER InputObject
    String to output. Can pass multiple objects via the pipeline.

.PARAMETER Color
    List of color specs ("<FG>/<BG>") to use for each corresponding pattern position. `ConvertTo-ConsoleColor` is used to interpret the values.

    Missing foreground/background colors and parts of the input string not matched by any pattern are output using the default console colors.

.PARAMETER Pattern
    List of regular expression patterns to match. The pattern count must match the color count.

    Each subsequent pattern overwrites any previously applied colors. See also Reverse.

.PARAMETER CaseSensitive
    Force case sensitivity in patterns.

.PARAMETER Reverse
    Apply patterns in reverse specified order.

.PARAMETER NoNewLine
    Do not output newline at the end of input string.

.INPUTS
    String

.OUTPUTS
    None

.EXAMPLE
    PS> Get-Help gci -Detailed | oss | Write-Highlight r,g '(?<!\b)-[A-Z]\w+','[A-Z]\w+-[A-Z]\w+' -CaseSensitive

    Highlights the detailed help output for `gci`, showing options (e.g. -Path) in red and cmdlets (e.g Get-ChildItem) in green.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    [AllowEmptyString()]
    [string]$InputObject,

    [Parameter(Mandatory, Position = 0)]
    [string[]]$Color,

    [Parameter(Mandatory, Position = 1)]
    [string[]]$Pattern,

    [switch]$CaseSensitive,

    [switch]$Reverse,

    [switch]$NoNewLine
)
begin {
    if ($Color.Count -eq 0) {
        throw 'No color specified.'
    }
    if ($Pattern.Count -eq 0) {
        throw 'No pattern specified.'
    }
    while ($Color.Count -ne $Pattern.Count) {
        throw 'Color count does not match pattern count.'
    }
    if ($Reverse) {
        $Color = $Color | Get-ReverseArray
        $Pattern = $Pattern | Get-ReverseArray
    }
    function GetMatches([int]$Index, [string]$Text) {
        $patt = $Pattern[$Index]
        $opt = if ($CaseSensitive) {
            0
        } else {
            'IgnoreCase'
        }
        [regex]::Matches($Text, $patt, $opt)
    }
}
process {
    # Use an array of 0-based color indexes (-1 for non-colored) for each
    # character in the input string. It's not very efficient, but it works.
    $charClrs = @(-1) * $InputObject.Length
    for ($clrIndex = 0; $clrIndex -lt $Color.Count; ++$clrIndex) {
        foreach ($m in (GetMatches $clrIndex $InputObject)) {
            $end = $m.Index + $m.Length
            for ($i = $m.Index; $i -lt $end; ++$i) {
                $charClrs[$i] = $clrIndex
            }
        }
    }
    # Output groups of subsequent characters having the same color.
    $i = 0
    $end = $InputObject.Length
    while ($i -lt $end) {
        $j, $c = $i, $charClrs[$i]
        do {
            ++$j
        } while ($j -lt $end -and $charClrs[$j] -eq $c)
        if ($c -ge 0) {
            $fg, $bg = ConvertTo-ConsoleColor $Color[$c]
        } else {
            $fg, $bg = $null, $null
        }
        $arg = @{
            Object = $InputObject.Substring($i, $j - $i)
            NoNewLine = $true
        }
        if ($null -ne $fg) {
            $arg.ForegroundColor = $fg
        }
        if ($null -ne $bg) {
            $arg.BackgroundColor = $bg
        }
        Write-Host @arg
        $i = $j
    }
    if (-not $NoNewLine) {
        Write-Host ''
    }
}
