<#
.SYNOPSIS
    Convert directories into uncompressed archive files.

.DESCRIPTION
    Create archives from each directory under the source directory.
    The input directories are scanned recursively and the files are stored
    uncompressed.

    Returns file objects of successfully created archives.

.PARAMETER Source
    Source directory. Contains the input directories. Must exist.

.PARAMETER Destination
    Destination directory. Output archives are placed there.
    Will be created if needed. Default is the source directory.

.PARAMETER Filter
    Optional wildcard filter for selecting input directories.

.PARAMETER ArchiveType
    Type of archive to create. Either '7z' (default), 'zip'.

.PARAMETER Extension
    If set, overrides default archive extension. Leading dot is optional.

.PARAMETER Purge
    Remove source files if archive creation is succesful.

.INPUTS
    None

.OUTPUTS
    System.IO.FileInfo
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Source,

    [string]$Destination,

    [string]$Filter = '',

    [ValidateSet('7z', 'zip')]
    [Alias('Type')]
    [string]$ArchiveType = '7z',

    [string]$Extension,

    [switch]$Purge
)

Set-StrictMode -version latest

# TODO: replace Source/Filter with InputObject (directory object)

if (-not (Test-Path $Source -Type Container)) {
    Write-Error "source dir does not exist: $Source"
    return
}

if (-not $Destination) {
    $Destination = $Source
}

$d = Get-Item -Force -LiteralPath $Destination -ErrorAction SilentlyContinue
if (-not $d) {
    if (-not ($d = New-Item -Path $Destination -ItemType Container -Force)) {
        return
    }
} elseif (-not $d.PSIsContainer) {
    Write-Error "destination path is a file"
    return
}
# absolute path needed for 7-Zip invocation, since the CWD is changed
$Destination = $d.FullName

if ($Extension -and $Extension.Substring(0, 1) -ne '.') {
    $Extension = '.' + $Extension
} else {
    # NOTE: 7-Zip automatically adds the proper extension if not set,
    # but we need it in advance to check if the output files exist
    $Extension = switch ($ArchiveType) {
        '7z' { '.7z' }
        'zip' { '.zip' }
        default { throw "No extension set for archive type: $ArchiveType" }
    }
}

$dirs = Get-ChildItem -Directory -Path $Source -Filter $Filter
foreach ($dir in $dirs) {
    $outFile = Join-Path $Destination ($dir.Name + $Extension)
    if (Test-Path -LiteralPath $outFile -PathType Leaf) {
        Write-Error "Output file laready exists: $outFile"
        continue
    }
    $ok = $false
    try {
        Push-Location $dir.FullName
        Write-Verbose "Creating archive: $outFile"
        7z a "-t$ArchiveType" -mtc=on -mx=0 -r $outFile * > $null
        $ok = $?
        if ($ok) {
            Get-Item -LiteralPath $outFile
        }
    }
    finally {
        Pop-Location
    }
    if ($ok -and $Purge) {
        Write-Verbose "removing directory: $($dir.FullName)"
        Remove-Item -Recurse -Force $dir.FullName
    }
}
