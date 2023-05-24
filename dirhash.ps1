#requires -Modules NiceConvert

<#
.SYNOPSIS
    Output file hashes of complete directories.

.DESCRIPTION
    Generate lines of text consisting of a hash and a file path.

    Output file paths are relative to the current directory.

.PARAMETER Path
    One or more input directories. All their files are processed recursively. Default is the current directory.

.PARAMETER Algorithm
    Name of the algorithm to calculate hashes of. For valid values, see the Algorithm parameter of Get-FileHash. Default is 'SHA256'.

.PARAMETER Filter
    Selects specific files for processing. Each file is passed to this scriptblock as $_ and is only processed if a true value is returned.

.PARAMETER ProgressSeconds
    Seconds between progress output updates. If omitted, no progress is output.

.INPUTS
    None

.OUTPUTS
    String
#>

[CmdletBinding()]
param(
  [string[]]$Path = '.',

  [string]$Algorithm = 'SHA256',

  [scriptblock]$Filter = { $true },

  [double]$ProgressSeconds
)

$showProgress = $PSBoundParameters.ContainsKey('ProgressSeconds')

# select files to process and measure total length
$totalBytes = 0
$files = foreach ($topDir in $Path) {
    Get-ChildItem -Recurse -File -Path $topDir | ? $Filter | % {
        $totalBytes += $_.Length
        $_
    }
}

function PathToRelative ([string]$Path) {
    $s = Resolve-Path -Relative -LiteralPath $Path
    if ($s.StartsWith('.\')) {
        $s.Substring(2)
    } else {
        $s
    }
}


$doneFiles = 0
$doneBytes = 0
$progress = @{
    Activity = 'Generating file hashes'
    Status = ''
    CurrentOperation = ''
    PercentComplete = 0
}
$currentFileSize = 0

$progrTimer = [System.Diagnostics.Stopwatch]::new()
$progrTimer.Start()

filter PreHash {
    if ($showProgress -and $progrTimer.Elapsed.TotalSeconds -ge $ProgressSeconds) {
        $script:progress.CurrentOperation = PathToRelative $_.FullName
        $script:progress.Status = "Done: $script:doneFiles of $($files.Count); $(ConvertTo-NiceSize $script:doneBytes) of $(ConvertTo-NiceSize $totalBytes)"
        Write-Progress @script:progress
        $progrTimer.Restart()
    }
    $script:currentFileSize = $_.Length
    $_
}

filter PostHash {
    $script:doneFiles += 1
    $script:doneBytes += $script:currentFileSize
    $script:progress.PercentComplete = [int](100 * $script:doneBytes / $script:totalBytes)
    $_
}

$files | PreHash | Get-FileHash -Algorithm $Algorithm | PostHash | % {
    "$($_.hash) $(PathToRelative $_.path)"
}

if ($showProgress) {
    Write-Progress @script:progress -Completed
}
