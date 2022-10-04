<#
.SYNOPSIS
    Read INI files.
.DESCRIPTION
    Gets the contents of an INI file as a hashtable.
    This script works better with the common Windows specification of the INI
    format, i.e. no spaces around equal sign in key/value entries and inside
    brackets of section names.
.PARAMETER InputObject
    Path of INI file.
.INPUTS
    INI path.
.OUTPUTS
    Hashtable.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
    [Alias('FullName', 'PSPath')]
    [string]$InputObject
)

$file = Get-Item -LiteralPath $InputObject
if (-not $file) {
    return
}

$sectionExpr = [Regex]'^\s*\[\s*(.*?)\s*\]\s*$'
$entryExpr = [Regex]'^\s*([^=]+)\s*=(.*)$'
$whitespaceExpr = [Regex]'^\s*$'

$ret = @{}
$curSectName = ''
$file | Get-Content | ForEach-Object {
    $m = $sectionExpr.Match($_)
    if ($m.Success) {
        Write-Verbose "SECTION: $($m.Groups[1].Value)"
        $curSectName = $m.Groups[1].Value
        $ret[$curSectName] = @{}
        return
    }
    $m = $entryExpr.Match($_)
    if ($m.Success) {
        Write-Verbose "KEY/VAL: $($m.Groups[1].Value) / $($m.Groups[2].Value)"
        $ret[$curSectName][$m.Groups[1].Value] = $m.Groups[2].Value
        return
    }
    $m = $whitespaceExpr.Match($_)
    if (-not $m.Success) {
        Write-Warning "Unrecognized INI line: $_"
        return
    }
}
Write-Output $ret
