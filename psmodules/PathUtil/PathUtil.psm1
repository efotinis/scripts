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
function Get-AbsolutePath {
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


# Replace invalid filename characters with another (default: underscore).
function Get-SafeFileName ([string]$Name, [char]$Replacement = '_') {
    foreach ($c in [IO.Path]::GetInvalidFileNameChars()) {
        $Name = $Name.Replace($c, $Replacement)
    };
    Write-Output $Name
}


<#
.SYNOPSIS
    Timestamp in filename-safe format.
.DESCRIPTION
    Convert a datetime object to a filename-safe timestamp string. The output format is '<date>T<time>[Z]', where date is 'yyMMdd' and time is 'hhmmssffff'.
.PARAMETER InputObject
    Input datetime object. Can pass multiple values via the pipeline. If omitted, the current time is used.
.PARAMETER Utc
    Output in universal time format with a trailing 'Z' character.
.PARAMETER DateOnly
    Output only the date part.
.INPUTS
    datetime
.OUTPUTS
    string
#>
function Get-FileNameSafeTimestamp {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline)]
        [datetime]$InputObject = (Get-Date),

        [switch]$Utc,

        [switch]$DateOnly
    )
    process {
        $fmt = 'FileDate'
        if (-not $DateOnly) { $fmt += 'Time' }
        if ($Utc) { $fmt += 'Universal' }
        Get-Date -Date $InputObject -Format $fmt
    }
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
