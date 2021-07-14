<#
.SYNOPSIS
    Download or list a directory from a GitHub repo using SVN CLI.

.DESCRIPTION
    Use SVN export/list commands to get the contents of a GitHub repo directory.

.PARAMETER Url
    Directory URL from GitHub web site.

.PARAMETER Repository
    Repository specified as 'USER/REPO'.

.PARAMETER Path
    Repository path(s). Use '/' for root.

.PARAMETER Destination
    Output directory.
    Default is the last part of Path or 'trunk' if Path is root.

.PARAMETER Recursive
    Include subdirectories recursively.

.PARAMETER Force
    Overwrite files in destination if it exists.

.PARAMETER List
    List information instead of downloading.

.NOTES

    Created by:
        Elias Fotinis (efotinis@gmail.com) on 2020-04-26

    Requirements:
        - Subversion commandline tools (svn.exe) in PATH.
          Tested with TortoiseSVN 1.7.9 and 1.14.1.

    Inspired by:
        - https://stackoverflow.com/questions/7106012/
         "Download a single folder or directory from a GitHub repo"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory, ParameterSetName='location')]
    [string]$Url,
    
    [Parameter(Mandatory, Position=0, ParameterSetName='parts')]
    [string]$Repository,
    
    [Parameter(Mandatory, Position=1, ParameterSetName='parts')]
    [string[]]$Path,
    
    [string]$Destination,
    
    [switch]$Recursive,
    
    [switch]$Force,
    
    [switch]$List
)


$svn = Get-Command svn.exe -ErrorAction Ignore
if (-not $svn) {
    Write-Error 'cannot find svn.exe; add Subversion CLI tools to PATH'
    return
}


switch ($PSCmdlet.ParameterSetName) {
    'location' {
        $Path = if ($Url -like '*/tree/master/*') {
            $Url -replace '/tree/master/','/trunk/'
        } else {
            $Url + '/trunk/'
        }
    }
    'parts' {
        $Path = $Path | ForEach-Object {
            "https://github.com/$Repository/trunk/$($_.TrimStart('/'))"
        }
    }
}


if ($List) {
    $opt = @(
        'list'
        '--xml'
        if ($Recursive) { '--depth=infinity' }
        $Path
    )
    ([xml](& $svn @opt)).lists.list.entry | % {
        [PSCustomObject]@{
            Name=$_.name
            Size=$_.size
            Kind=$_.kind
            Rev=$_.commit.revision
            Author=$_.commit.author
            Date=Get-Date $_.commit.date
        }
    }
} else {
    $Path | ForEach-Object {
        $opt = @(
            'export'
            if (-not $Recursive) { '--depth=files' }
            if ($Force) { '--force' }
            $_
            if ($Destination) { $Destination }
        )
        & $svn @opt
    }
}
