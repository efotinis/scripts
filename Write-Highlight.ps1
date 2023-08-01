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

.PARAMETER Reverse
    Apply patterns in reverse specified order.

.PARAMETER NoNewLine
    Do not output newline at the end of input string.

.INPUTS
    String

.OUTPUTS
    None
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    [string]$InputObject,

    [Parameter(Mandatory, Position = 0)]
    [string[]]$Color,

    [Parameter(Mandatory, Position = 1)]
    [regex[]]$Pattern,

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
}
process {
    # Use an array of 0-based color indexes (-1 for non-colored) for each
    # character in the input string. It's not very efficient, but it works.
    $charClrs = @(-1) * $InputObject.Length
    $clrIndex = 0
    foreach ($p in $Pattern) {
        foreach ($m in $p.Matches($InputObject)) {
            $end = $m.Index + $m.Length
            for ($i = $m.Index; $i -lt $end; ++$i) {
                $charClrs[$i] = $clrIndex
            }
        }
        ++$clrIndex
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
