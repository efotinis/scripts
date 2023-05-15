<#
.SYNOPSIS
    String utilities.

.DESCRIPTION
    Various string functions.
#>


$RNG = [System.Random]::new()


<#
.SYNOPSIS
    Reverse string.
.DESCRIPTION
    Gets the reverse of the input string.
.PARAMETER Text
    Input string. Can pass multiple values via the pipeline.
.INPUTS
    String.
.OUTPUTS
    String.
#>
function Get-ReverseString {
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [AllowEmptyString()]
        [string]$Text
    )
    begin {
        $sb = [System.Text.StringBuilder]::new()
    }
    process {
        [void]$sb.Clear()
        [void]$sb.EnsureCapacity($Text.Length)
        for ($i = $Text.Length - 1; $i -ge 0; --$i) {
            [void]$sb.Append($Text[$i])
        }
        Write-Output $sb.ToString()
    }
}


# Alternate/randomize case of letters in input text.
function Get-CrazyCaseString {
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Text,

        [switch]$LowerStart,  # start alternating with lowercase

        [switch]$Random  # randomize case instead of alternating
    )
    begin {
        $charConv = @(
            [char]::ToUpper,
            [char]::ToLower
        )
    }
    process {
        $strBuf = [System.Text.StringBuilder]::new($Text)
        $state = if ($LowerStart) { 1 } else { 0 }
        for ($i = 0; $i -lt $strBuf.Length; ++$i) {
            if ([Char]::IsLetter($strBuf, $i)) {
                if ($Random) {
                    $strBuf[$i] = $charConv[$script:RNG.Next(2)].Invoke($strBuf[$i])
                } else {
                    $strBuf[$i] = $charConv[$state].Invoke($strBuf[$i])
                    $state = -$state + 1  # toggle between 0 and 1
                }
            }
        }
        $strBuf.ToString()
    }
}


# Number of matching characters.
function Get-CharacterCount {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [AllowEmptyString()]
        [string]$InputObject,

        [Parameter(Mandatory, Position = 0)]
        [char[]]$Character,

        [switch]$MatchCase
    )
    begin {
        $charSet = [System.Collections.Generic.HashSet[char]]::new($Character)
    }
    process {
        $count = 0
        if ($MatchCase) {
            for ($i = 0; $i -lt $InputObject.Length; ++$i) {
                if ($InputObject[$i] -cin $charSet) {
                    ++$count
                }
            }
        } else {
            for ($i = 0; $i -lt $InputObject.Length; ++$i) {
                if ($InputObject[$i] -iin $charSet) {
                    ++$count
                }
            }
        }
        $count
    }
}


# Convert numeric value to string of chararacter flags.
#
# Set bits in Value produce the corresponding character, with the
# least-significant bit corresponding to the right-most character. Unset bits
# produce '-'.
#
# Unused bits are marked in Characters as '-' and are excluded from the output,
# unless Fixed is set.
#
# Example:
#   sal ff ConvertTo-FlagField
#   $bits = 43   # 0b00101011
#   ff $bits        'n-ad-shr'  # -> '-a--hr'
#   ff $bits -fixed 'n-ad-shr'  # -> '--a---hr'
#
function ConvertTo-FlagField {
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [int]$Value,

        [Parameter(Mandatory)]
        [string]$Characters,

        [switch]$Fixed
    )
    process {
        $size = $Characters.Length
        $mask = 1 -shl ($size - 1)
        $ret = ''
        for ($i = 0; $i -lt $size; ++$i) {
            $c = $Characters[$i]
            if ($c -eq '-') {
                if ($Fixed) {
                    $ret += '-'
                }
            } elseif ($Value -band $mask) {
                $ret += $c
            } else {
                $ret += '-'
            }
            $mask = $mask -shr 1
        }
        $ret
    }
}


# Convert from Base64-encoded string.
function ConvertFrom-Base64 {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Data
    )
    process {
        [string]::new([System.Convert]::FromBase64String($Data))
    }
}


# Insert dashes to YYYYMMDD string.
function Add-DateSeparator ([string]$Ymd) {
    $Ymd.Insert(6,'-').Insert(4,'-')
}


# Double characters defined in PowerShell as single/double quotes.
# Can be used to embed arbitrary strings in literals.
# Character classification info taken from https://github.com/PowerShell/PowerShell/blob/master/src/System.Management.Automation/engine/parser/CharTraits.cs
function ConvertTo-DuplicateQuote {
    param(
        [Parameter(Mandatory, Position = 1, ValueFromPipeline)]
        [AllowEmptyString()]
        [string]$Text,

        [Parameter(Mandatory, Position = 0)]
        [ValidateSet('Single', 'Double')]
        [Alias('Type')]
        [string]$QuoteType
    )
    begin {
        $CHARS = switch ($QuoteType) {
            'Single' {
                -join @(
                    [char]0x0027  # APOSTROPHE
                    [char]0x2018  # LEFT SINGLE QUOTATION MARK
                    [char]0x2019  # RIGHT SINGLE QUOTATION MARK
                    [char]0x201a  # SINGLE LOW-9 QUOTATION MARK
                    [char]0x201b  # SINGLE HIGH-REVERSED- QUOTATION MARK
                )
            }
            'Double' {
                -join @(
                    [char]0x0022  # QUOTATION MARK
                    [char]0x201C  # LEFT DOUBLE QUOTATION MARK
                    [char]0x201D  # RIGHT DOUBLE QUOTATION MARK
                    [char]0x201E  # DOUBLE LOW-9 QUOTATION MARK
                )
            }
        }
    }
    process {
        $Text -replace "([$CHARS])",'$1$1'
    }
}


<#
.SYNOPSIS
    Get unique characters in string.

.DESCRIPTION
    Returns a string with all unique characters found in the input string. The characters in the output string are sorted.

.PARAMETER InputObject
    Source string. Can pass multiple strings via the pipeline.

.PARAMETER Concatenate
    Return single result for all of the input. By default, each input item returns a separate string,

.INPUTS
    String.

.OUTPUTS
    String.
#>
function Get-UniqueCharacter {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [AllowEmptyString()]
        [string]$InputObject,

        [switch]$Concatenate
    )
    begin {
        $CHS = [System.Collections.Generic.HashSet[char]]
        $h = $CHS::new()
        function Output ($Chars) {
            Write-Output (($Chars | Sort-Object) -join '')
        }
    }
    process {
        if (-not $Concatenate) {
            $h.Clear()
        }
        $h.UnionWith(($InputObject -as $CHS))
        if (-not $Concatenate) {
            Output $h
        }
    }
    end {
        if ($Concatenate) {
            Output $h
        }
    }
}


Export-ModuleMember -Function *-*
