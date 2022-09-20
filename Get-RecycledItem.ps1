<#
.SYNOPSIS
    Get Recycle Bin item info.
.DESCRIPTION
    ...
.EXAMPLE
    PS C:\> Get-RecycledItem
    Name                            Size_ DateDeleted_        OriginalLocation
    ----                            ----- ------------        ----------------
    backup - Copy.txt                 127 05/05/2020 21:22:00 C:\Users\Elias\Desktop
    ps notes - Copy.txt              8100 05/05/2020 21:22:00 C:\Users\Elias\Desktop
    bathroom faucet leak - Copy.txt    73 05/05/2020 21:22:00 C:\Users\Elias\Desktop
    bookmarks review - Copy.txt       147 05/05/2020 21:22:00 C:\Users\Elias\Desktop
    vs code tips - Copy.txt           378 05/05/2020 21:22:00 C:\Users\Elias\Desktop
    New Text Document - Copy.txt     1864 05/05/2020 21:22:00 C:\Users\Elias\Desktop
    todotxt - Copy.txt                138 05/05/2020 21:22:00 C:\Users\Elias\Desktop
.INPUTS
    --
.OUTPUTS
    [PSCustomObject[]], [string[]]
.NOTES
    Docs and refs:
        https://stackoverflow.com/questions/22816215/delete-old-files-in-recycle-bin-with-powershell
            Delete old files in recycle bin with powershell
        https://docs.microsoft.com/en-us/windows/win32/api/shlobj_core/nf-shlobj_core-ishelldetails-getdetailsof
            IShellDetails::GetDetailsOf method
        https://docs.microsoft.com/en-us/windows/win32/shell/folder-getdetailsof
            Folder.GetDetailsOf method
        https://docs.microsoft.com/en-us/windows/desktop/shell/shell-application
        https://docs.microsoft.com/en-us/windows/desktop/shell/shell-namespace
        https://docs.microsoft.com/en-us/windows/desktop/shell/folder
        https://docs.microsoft.com/en-us/windows/desktop/shell/folderitems
#>

[CmdletBinding()]
Param(
    [string[]] $Property = @('Name', 'Size', 'Date deleted', 'Original location'),

    # Handling of date/size strings.
    [ValidateSet('parsed', 'original', 'both')]
    [string] $Translatable = 'parsed',

    # Do not convert property names to simple name indentifiers.
    [switch] $KeepOriginalNames,

    # List available properties.
    [switch] $ListProperty
)


# Get the index and title of all available shell folder columns/properties.
function GetShellColumns ($Folder) {
    for ($index = 0; $index -lt 1000; ++$index) {
        $name = $Folder.GetDetailsOf($null, $index)
        if ($name) {
            [PSCustomObject]@{
                Index = $index
                Name = $name
            }
        }
    }
}


# Select properties in order of matching names.
# Emits a single warning for all invalid names.
function SelectPropertyByName([object[]]$Property, [string[]]$Name) {
    $invalid = @()
    $nameMap = @{}
    foreach ($p in $Property) {
        $nameMap[$p.Name] = $p
    }
    foreach ($s in $Name) {
        if ($nameMap.ContainsKey($s)) {
            Write-Output $nameMap[$s]
        } else {
            $invalid += $s
        }
    }
    if ($invalid.Count -gt 0) {
        Write-Warning "Invalid property names: $($invalid -join ', ')"
    }
}


function ParseSize ($s) {
    if ($s -notmatch '[\d]+(\.[\d]+)? [bytes|KB|MB|GB|TB]') {
        0
    }
    else {
        $s = $s -replace ' bytes',''
        $s = $s -replace ' ',''
        (Invoke-Expression $s) -as [int64]
    }
}


function ParseDate ($s) {
    try {
        get-date ($s -replace '\u200f|\u200e','')
    }
    catch {
        $null
    }
}


# Select value parser function based on property name, or $null.
function GetParser ($name) {
    switch -Wildcard ($name) {
        *date* { Get-Item Function:ParseDate }
        *size* { Get-Item Function:ParseSize }
    }
}


# Get shell item data.
function GetData ($Item, $Properties, $UseOriginalNames) {
    $a = [ordered]@{}
    $Parent = $Item.Parent
    foreach ($p in $Properties) {
        $value = $Parent.GetDetailsOf($Item, $p.index)
        $name = $p.name
        $parser = GetParser $name
        if (-not $UseOriginalNames) {
            $name = $name -replace '[^\w]',''
        }
        if ($Translatable -ne 'parsed' -or -not $parser) {
            $a[$name] = $value
        }
        if ($Translatable -ne 'original' -and $parser) {
            $a[$name + '_'] = & $parser $value
        }
    }
    [PSCustomObject]$a
}


$shellObj = New-Object -ComObject Shell.Application
$recycleBinFolder = $shellObj.NameSpace(0xa)
$allProperties = @(GetShellColumns($recycleBinFolder))

if ($ListProperty) {
    Write-Output $allProperties
    return
}

$reqProps = SelectPropertyByName -Property $allProperties -Name $Property

$progress = @{
    Activity='Retrieving Recycle Bin items'
}
$items = $recycleBinFolder.Items()
$total = $items.Count
$count = 0
foreach ($item in $items) {
    GetData $item $reqProps $KeepOriginalNames
    $count += 1
    if (($count % 100) -eq 0) {
        $progress.PercentComplete = $count / $total * 100
        $progress.Status = "items found: $count"
        Write-Progress @progress
    }
}
Write-Progress @progress -Completed
