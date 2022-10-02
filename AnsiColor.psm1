# ANSI color sequence utiities.


Set-StrictMode -Version Latest


<#
.SYNOPSIS
    Convert ANSI color sequence to Clipper-style color spec.

.DESCRIPTION
    Converts ANSI color/attribute sequences to a more human readable format,
    inspired by dBase/Clipper color specs.

    NOTE: Due to PowerShell's object boxing, the return type may need to be
    cast to a string (e.g. when used as a value for Set-PSReadLineOption).

.PARAMETER InputObject
    ANSI color sequence in "ESC[...m" format. Can pass multiple values via the
    pipeline.

.INPUTS
    ANSI color sequence.

.OUTPUTS
    Clipper-style color string.
#>
function ConvertFrom-AnsiColor {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$InputObject
    )
    begin {
        # effects:
        #   normal, bold, faint, italic, underline,
        #   slow blink, fast blink, reverse
        $EFFECT = [char[]]'nbfiuabr'
        $CLR = 'nrgybmcw'
        # Extract first array element, decremented by base.
        function Pop ($a, $base = 0) {
            $ret = $a[0] - $base
            $a.RemoveAt(0)
            return $ret
        }
        # Remove first n array elements.
        function Skip ($a, $n = 1) {
            $a.RemoveRange(0, $n)
        }
        # Test if first array element is in [min,max].
        function InRange ($a, $min, $max) {
            return $a[0] -ge $min -and $a[0] -le $max
        }
        # Parse 8/24-bit color. Throws on error.
        function GetFancyColor ($a) {
            switch ($x = Pop $a) {
                5 {
                    $n = Pop $a
                    return "#$n"
                }
                2 {
                    $r = Pop $a
                    $g = Pop $a
                    $b = Pop $a
                    return "($r,$g,$b)"
                }
                default: {
                    throw "Invalid color space designator: $x. Should be 2 or 5."
                }
            }
        }
    }
    process {
        if ($InputObject -notmatch '^\e\[(.+)m$') {
            throw 'Not an ANSI color code.'
        }
        $ret = [ordered]@{
            Fore = ''
            Back = ''
            Effect = ''
        }
        $a = [System.Collections.ArrayList]@($Matches[1] -split ';').ForEach([int])
        while ($a.Count) {
            if (InRange $a 0 7) {
                $ret.Effect += $EFFECT[(Pop $a 0)]
            } elseif (InRange $a 30 37) {
                $ret.Fore = $CLR[(Pop $a 30)]
            } elseif (InRange $a 40 47) {
                $ret.Back = $CLR[(Pop $a 40)]
            } elseif (InRange $a 90 97) {
                $ret.Fore = $CLR[(Pop $a 90)] + '+'
            } elseif (InRange $a 100 107) {
                $ret.Back = $CLR[(Pop $a 100)] + '+'
            } elseif ($a[0] -eq 38) {
                Skip $a
                $ret.Fore = GetFancyColor $a
            } elseif ($a[0] -eq 48) {
                Skip $a
                $ret.Back = GetFancyColor $a
            } elseif ($a[0] -eq 39) {
                Pop $a
                $ret.Fore += '-'  # default
            } elseif ($a[0] -eq 49) {
                Pop $a
                $ret.Back += '-'  # default
            } else {
                throw "Unexpected code: $($a[0])"
            }
        }
        $ret = $ret.Fore + '/' + $ret.Back + '/' + $ret.Effect
        $ret = $ret -replace '/+$',''
        Write-Output $ret
    }
}


<#
.SYNOPSIS
    Convert Clipper-style color spec to ANSI color sequence.

.DESCRIPTION
    Converts dBase/Clipper color specs to ANSI color/attribute sequences.

    The Clipper-inspired color spec is defined as:
        [foreground ["/" background ["/" effects]]]

    Foreground/background can be one of the characters:
        'n', 'b', 'g', 'c', 'r', 'm', 'y', 'w'
    representing the darker versions of:
        black, blue, green cyan, red, magenta, yellow, gray.
    The addition of a '+' character modifies the color to represent the
    lighter versions, with 'n+' mapping to dark gray and 'w+' to white.

    Effect cab be one or more of the characters:
        'n', 'b', 'f', 'i', 'u', 'a', 'b', 'r'
    representing:
        normal, bold, faint, italic, underline, slow blink, fast blink, reverse.

    Whitespace and character case is ignored.

.PARAMETER InputObject
    Clipper-style color spec. Can pass multiple values via the pipeline.

.PARAMETER Substitute
    Use a substitute character instead of the initial \x1b to view the result
    without it getting interpreted as a sequence.

.INPUTS
    Clipper-style color string.

.OUTPUTS
    ANSI color sequence.
#>
function ConvertTo-AnsiColor {
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$InputObject,

        [switch]$Substitute
    )
    begin {
        function MakeSequence ([int[]]$a, [bool]$Fake) {
            $s = $a -join ';'
            $c = if ($Fake) {
                [char]0x2190  # Leftwards Arrow
            } else {
                [char]0x1b  # ESC
            }
            return "$c[${s}m"
        }
        function ParseSmallInt ($s, $name) {
            $n = [int]::Parse($s)
            if ($n -lt 0 -or $n -gt 255) {
                throw "Element out of range: $name"
            }
            return $n
        }
        function ParseColor ([string]$Spec, [bool]$Foreground) {
            switch -regex ($Spec) {
                '\((\d+),(\d+),(\d+)\)' {
                    $r = ParseSmallInt $Matches[1] 'red component'
                    $g = ParseSmallInt $Matches[2] 'green component'
                    $b = ParseSmallInt $Matches[3] 'blue component'
                    return @(
                        if ($Foreground) { 38 } else { 48 }
                        2, $r, $g, $b
                    )
                }
                '#(\d+)' {
                    $n = ParseSmallInt $Matches[1] 'Palette index'
                    return @(
                        if ($Foreground) { 38 } else { 48 }
                        5, $n
                    )
                }
                default {
                    if ($Spec.IndexOf('+') -ge 0) {
                        $intensity = $true
                        $Spec = $Spec -replace '\+',''
                    } else {
                        $intensity = $false
                    }
                    switch ($Spec) {
                        '' {
                            return @()
                        }
                        '-' {
                            return @(if ($Foreground) { 39 } else { 49 })
                        }
                        default {
                            if ($Spec.Length -gt 1) {
                                throw '4-bit color with more than 1 characters'
                            }
                            $n = 'nrgybmcw'.IndexOf($Spec)
                            if ($n -eq -1) {
                                throw 'Invalid 4-bit color spec'
                            }
                            $n += 30
                            if (-not $Foreground) {
                                $n += 10
                            }
                            if ($intensity) {
                                $n += 60
                            }
                            return @($n)
                        }
                    }
                }
            }
        }
        function ParseEffect ([string]$Effect) {
            foreach ($c in [char[]]$Effect) {
                $n = 'nbfiuabr'.IndexOf($c)
                if ($n -eq -1) {
                    throw "Invalid effect: $c"
                }
                Write-Output $n
            }
        }
    }
    process {
        $fore, $back, $effect = ($InputObject -replace '\s+','') -split '/',3
        try {
            $a = @(
                ParseColor $fore $true
                ParseColor $back $false
                ParseEffect $effect
            )
        } catch {
            Write-Error "Could not parse color: $InputObject"
            throw
        }
        Write-Output (MakeSequence $a $Substitute)
    }
}


Export-ModuleMember -Function *-*
