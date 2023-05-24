#requires -Modules NiceConvert

# calculate hashes of all files recursively
# and also prints relative paths

[CmdletBinding()]
param(
  [string[]]$Path = '.',
  [string]$Algorithm = 'sha256',
  [scriptblock]$Filter = { $true },
  [double]$ProgressSeconds
)

$showProgress = $PSBoundParameters.ContainsKey('ProgressSeconds')

$totalBytes = 0
$files = foreach ($topDir in $Path) {
    Get-ChildItem -Recurse -File -Path $topDir | ? $Filter | % {
        $totalBytes += $_.Length
        $_
    }
}

function PathToRelative ([string]$Path) {
    (Resolve-Path -Relative -LiteralPath $Path).Substring(2)
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
