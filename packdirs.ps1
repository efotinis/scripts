<#
.SYNOPSIS
    Convert directories into uncompressed 7Z/CBZ files.

.DESCRIPTION
    Create archives from each directory under the source directory.
    The input directories are scanned recursively and the files are stored
    uncompressed.

.PARAMETER Source
    Source directory. Contains the input directories. Must exist.

.PARAMETER Destination
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
    [string]$Source,

    [string]$Destination,

    [string]$Filter = '',

    [switch]$Cbz,

    [switch]$Purge
)

Set-StrictMode -version latest

# TODO: create destination if it does not exist
# TODO: replace Source/Filter with InputObject (directory object)

if (-not (Test-Path $Source -Type Container)) {
    Write-Error "source dir does not exist: $Source"
    return
}

if (-not $Destination) {
    $Destination = $Source
}
if (-not (Test-Path $Destination -Type Container)) {
    Write-Error "destination dir does not exist: $Destination"
    return
}

# convert to normalized, absolute path, since the current location is changed
# when invoking 7-Zip
$Destination = [string](Resolve-Path $Destination)

if ($Cbz) {
    $archiveType = '-tzip'
    $archiveExt = '.cbz'
} else {
    $archiveType = '-t7z'
    $archiveExt = '.7z'
}

$dirs = Get-ChildItem -Directory -Path $Source -Filter $Filter
foreach ($dir in $dirs) {
    $OutFile = Join-Path $Destination ($dir.Name + $archiveExt)
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
