<#
.SYNOPSIS
    Create file hardlinks.

.DESCRIPTION
    Creates hardlinks of all input files to the specified directory.

.PARAMETER

.PARAMETER Destination
    Output directory. Must be specified and will be created if it does not
    exist.

.PARAMETER Force
    Overwrite existing output files.

.INPUTS
    Existing file objects.

.OUTPUTS
    New file objects.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    [IO.FileInfo]$File,

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
    $newPath = Join-Path $Destination $File.Name
    $srcPath = EscapeBrackets $File.FullName
    New-Item -Type HardLink -Path $newPath -Value $srcPath -Force:$Force
}
