<#
.SYNOPSIS
    String utilities.

.DESCRIPTION
    Various string functions.
#>


$RNG = [System.Random]::new()


# Reverse input text.
function Get-ReverseString {
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Text
    )
    process {
        $len = $Text.Length
        $buf = [Text.StringBuilder]::new($len, $len)

        for ($i = $len; $i -ge 0; --$i) {
            [void]$buf.Append($Text[$i])
        }

        $buf.ToString()
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
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$InputObject,
        
        [Parameter(Mandatory)]
        [string]$Characters,
        
        [switch]$MatchCase
    )
    begin {
        $charSet = [System.Collections.Generic.HashSet[char]]$Characters
    }
    process {
        $count = 0
        if ($MatchCase) {
            for ($i = 0; $i -lt $InputObject.Length; ++$i) {
                #if ($InputObject[$i] -ceq $Character) {
                if ($InputObject[$i] -cin $charSet) {
                    ++$count
                }
            }
        } else {
            for ($i = 0; $i -lt $InputObject.Length; ++$i) {
                #if ($InputObject[$i] -ieq $Character) {
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


Export-ModuleMember -Function *-*
