<#
.SYNOPSIS
    Output unbroken words.

.DESCRIPTION
    Write a series of strings without breaking them at the end of lines.

    Any single item that exceeds the width of the console will necessarily be broken.

.PARAMETER InputObject
    Input word or text fragment. Use the pipeline to specify multiple items.

.PARAMETER Separator
    Text to insert between items. Default is a single space character.

.PARAMETER Width
    Set the output width. If omitted or set to <= 0, the console buffer width is used.

    In this mode, Write-Output is used to generate strings that are (when possible) one less than the specified width. This ensures that, when displayed on the console, no extra empty lines will ever be shown.

.PARAMETER PSHost
    Use Write-Host to write directly to the console using the whole buffer width.

.INPUTS
    String

.OUTPUTS
    String (PSHost omitted)
    None (PSHost specified)
#>
[CmdletBinding(DefaultParameterSetName = 'Output')]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    [AllowEmptyString()]
    [string]$InputObject,

    [Parameter(Position = 0)]
    [string]$Separator = ' ',

    [Parameter(ParameterSetName = 'Output')]
    [ValidateRange(1, [int]::MaxValue)]
    [int]$Width,

    [Parameter(ParameterSetName = 'Host')]
    [switch]$PSHost
)
begin {
    switch ($PSCmdlet.ParameterSetName) {
        'Output' {
            $hostMode = $false
            $outWidth = if ($Width -gt 0) {
                $Width
            } else {
                $Host.UI.RawUI.BufferSize.Width
            }
        }
        'Host' {
            $hostMode = $true
            $outWidth = $Host.UI.RawUI.BufferSize.Width
        }
    }
    $sepLen = $Separator.Length
    $line = [System.Text.StringBuilder]::new()

    function Flush {
        if ($line.Length) {
            if (-not $hostMode) {
                Write-Output $line.ToString()
            } elseif ($line.Length -eq $outWidth) {
                Write-Host -NoNewLine $line
            } else {
                Write-Host $line
            }
            [void]$line.Clear()
        }
    }

    function Add ([string]$Item) {
        $n = $line.Length
        $sep = if ($n) { $Separator } else { '' }
        $newLen = $n + $sep.Length + $Item.Length
        if ($newLen -lt $outWidth) {
            [void]$line.Append($sep + $Item)
        } elseif ($hostMode -and ($newLen -eq $outWidth)) {
            [void]$line.Append($sep + $Item)
            Flush
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
    Flush
}
