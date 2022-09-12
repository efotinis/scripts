<#
.SYNOPSIS
    Create file hardlinks.

.DESCRIPTION
    Creates hardlinks of all input files to the specified directory.

.PARAMETER InputObject
    Source file path. Can pass multiple values via the pipeline.

.PARAMETER Destination
    Output directory. Will be created if it does not exist.

.PARAMETER Force
    Overwrite existing output files.

.INPUTS
    Existing file path(s).

.OUTPUTS
    New file objects.

#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
    [Alias('FullName', 'Path')]
    [string]$InputObject,

    [Parameter(Mandatory)]
    [string]$Destination,

    [switch]$Force
)
begin {
    try {
        $destExists = Test-Path -LiteralPath $Destination -Type Container
    } catch {
        Write-Error "Destination path is invalid: $Destination"
        exit
    }
    if (-not $destExists) {
        if (-not (New-Item -Path $Destination -Type Directory)) {
            exit
        }
    }
    function EscapeBrackets ([string]$s) {
        $s -replace '([[\]])','`$1'
    }
}
process {
    $name = Split-Path -Leaf -Path $InputObject
    $newPath = Join-Path -Path $Destination -ChildPath $Name
    $srcPath = EscapeBrackets $InputObject
    New-Item -Type HardLink -Path $newPath -Value $srcPath -Force:$Force
}
