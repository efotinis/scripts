<#
.SYNOPSIS
    Convert directories into uncompressed 7Z/CBZ files.

.DESCRIPTION
    Create archives from each directory under the source directory.
    The input directories are scanned recursively and the files are stored
    uncompressed.

.PARAMETER SourceDir
    Source directory. Contains the input directories. Must exist.

.PARAMETER DestDir
    Destination directory. Output archives are placed there. Must exist.
    Default is the source directory.

.PARAMETER Filter
    Optional wildcard filter for selecting input directories.

.PARAMETER Cbz
    Create CBZ archive instead of 7Z.

.PARAMETER Purge
    Remove source files if archive creation is succesful.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$SourceDir,

    [string]$DestDir,

    [string]$Filter = '',

    [switch]$Cbz,

    [switch]$Purge
)

Set-StrictMode -version latest


if (!(Test-Path $SourceDir -Type Container)) {
    Write-Error "source dir does not exist: $SourceDir"
    return
}

if (!$DestDir) {
    $DestDir = $SourceDir
}
if (!(Test-Path $DestDir -Type Container)) {
    Write-Error "destination dir does not exist: $DestDir"
    return
}

# convert to normalized, absolute path, since the current location is changed
# when invoking 7-Zip
$DestDir = [string](Resolve-Path $DestDir)

if ($Cbz) {
    $archiveType = '-tzip'
    $archiveExt = '.cbz'
} else {
    $archiveType = '-t7z'
    $archiveExt = '.7z'
}

$dirs = Get-ChildItem -Directory -Path $SourceDir -Filter $Filter
foreach ($dir in $dirs) {
    $OutFile = Join-Path $DestDir ($dir.Name + $archiveExt)
    try {
        Push-Location $dir.FullName
        Echo "creating archive: $OutFile"
        7z a $archiveType -mtc=on -mx=0 -r $OutFile * > $null
        $ok = $?
    }
    finally {
        Pop-Location
    }
    if ($ok -and $Purge) {
        Echo "removing directory: $($dir.FullName)"
        Remove-Item -Recurse -Force $dir.FullName
    }
}
