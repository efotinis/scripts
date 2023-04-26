# Path-related functions.


<#
.SYNOPSIS
    Get absolute path.
.DESCRIPTION
    Returns absolute path by removing "." and ".." components. Respects
    PowerShell's current directory. Does not verify that the resulting path
    exists or is valid.
.PARAMETER InputObject
    Input path. Can pass multiple values via the pipeline.
.INPUTS
    String.
.OUTPUTS
    String.
.NOTES
    Source:
        https://stackoverflow.com/questions/495618/how-to-normalize-a-path-in-powershell
#>
function global:Get-AbsolutePath {
    param(
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [AllowEmptyString()]
        [Alias('Path', 'PSPath')]
        [string]$InputObject
    )
    process {
        $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath(
            $InputObject
        )
    }
}


# Replace invalid filename characters with underscore.
function Get-SafeFileName ($s) {
    foreach ($c in [IO.Path]::GetInvalidFileNameChars()) {
        $s = $s.Replace($c, '_')
    };
    return $s;
}


# Timestamp in filename-safe format.
function global:Get-FileNameSafeTimestamp ([switch]$Utc, [switch]$DateOnly) {
    $fmt = 'FileDate'
    if (-not $DateOnly) { $fmt += 'Time' }
    if ($Utc) { $fmt += 'Universal' }
    Get-Date -Format $fmt
}


# Change the extension of a path.
function Set-PathExtension ($path, $ext) {
    [IO.Path]::ChangeExtension($path, $ext)
}


# Add suffix to basename (stem) of a path.
function Add-BaseNameSuffix ($path, $suffix) {
    $ext = [IO.Path]::GetExtension($path)
    $path.Substring(0, $path.Length - $ext.Length) + $suffix + $ext
}


Export-ModuleMember -Function *-*
