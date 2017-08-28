<#
.SYNOPSIS
    Filter filenames.
.DESCRIPTION
    Scan directories recursively and list items that match the specified 
    filter.
.PARAMETER Source
    Directories to scan.
.PARAMETER Filter
    Name filter (wildcard).
.PARAMETER Flat
    Output absolute paths (one per line). If neither -Flat nor -Raw is 
    specified, output relative paths with a header for each source directory.
.PARAMETER Raw
    Output System.IO.FileSystemInfo objects as returned by Get-ChildItem.
.PARAMETER Directory
    Return only directories (ignore files).
.PARAMETER File
    Return only files (ignore directories).
.EXAMPLE
    C:\PS> 
    <Description of example>
.NOTES
    Author: Elias Fotinis
    Date:   2017-08-20
#>

[CmdletBinding()]
Param(
    [string[]] $Source = '.',
    [string] $Filter = '*',
    [switch] $Flat,
    [switch] $Raw,
    [switch] $Directory,
    [switch] $File
)

foreach ($Dir in $Source) {
    $Options = @{
        LiteralPath = $Dir;
        Filter = $Filter;
        Recurse = $True;
        File = $File;
        Directory = $Directory
    }

    if ($Raw) {
        ls @Options
    }
    elseif ($Flat) {
        (ls @Options).FullName
    }
    else {
        Echo "`n$Dir`n$('-'*$Dir.length)"
        ls @Options -Name
    }
}
