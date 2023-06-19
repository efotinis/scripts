<#
.SYNOPSIS
    Output unbroken words.

.DESCRIPTION
    Write a series of strings without breaking at the end of line.
    
    Any single item that exceeds the width of the console will necessarily be broken.

.PARAMETER InputObject
    Input word or text fragment. Use the pipeline to specify multiple items.

.PARAMETER Separator
    Text to insert between items. Default is a single space character.

.PARAMETER Width
    Set the output width (>= 1). By default, the console buffer width is used.

.PARAMETER PSHost
    Write directly to the output display using Write-Host. When this is set, the full width is available.
    
    By default, Write-Output is used to output strings that are one character less than the available width. This avoids displaying empty lines on the console.

.INPUTS
    String

.OUTPUTS
    String / None
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    [AllowEmptyString()]
    [string]$InputObject,
    
    [Parameter(Position = 0)]
    [string]$Separator = ' ',
    
    [int]$Width,
    
    [switch]$PSHost
)
begin {
    $conWidth = if ($Width -gt 0) {
        $Width
    } else {
        $Host.UI.RawUI.BufferSize.Width
    }
    $sepLen = $Separator.Length
    $line = [System.Text.StringBuilder]::new()

    function Flush ([bool]$WithoutEol) {
        if (-not $PSHost) {
            Write-Output $line.ToString()
        } elseif ($WithoutEol) {
            Write-Host -NoNewLine $line
        } else {
            Write-Host $line
        }
        [void]$line.Clear()
    }

    function Add ([string]$Item) {
        $n = $line.Length
        $sep = if ($n) { $Separator } else { '' }
        $newLen = $n + $sep.Length + $Item.Length
        if ($newLen -lt $conWidth) {
            [void]$line.Append($sep + $Item)
        } elseif ($PSHost -and ($newLen -eq $conWidth)) {
            [void]$line.Append($sep + $Item)
            Flush $true
        } else {
            Flush
            [void]$line.Append($Item)
        }
    }
}
process {
    Add $InputObject
}
end {
    if ($line.Length) {
        Flush
    }
}
