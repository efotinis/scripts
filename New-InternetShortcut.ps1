#requires -Modules PathUtil

<#
.SYNOPSIS
    Create a URL shortcut.

.DESCRIPTION
    Creates an Internet shortcut file (.URL) for a specific web address.

.PARAMETER Url
    The remote location path to create a link for.

.PARAMETER Destination
    Directory to place the shortcut into. Must exist. Default is the current directory.

.PARAMETER Title
    Title of the webpage to be used as the name of the shortcut file. Any charcters that are not valid for file-system names are replaced.

    If omitted, the webpage is parsed to get the real page title. For PowerShell versions up to 5.1 this can be done natively. For later PowerShell versions, an internal Python script is used, which requires requests and beautifulsoup4.

.INPUTS
    None

.OUTPUTS
    None
#>

param(
    [Parameter(Mandatory)]
    [string]$Url,

    [string]$Destination = '.',

    [string]$Title = $null
)

Set-StrictMode -Version Latest

# Get webpage title natively or using Python.
function GetPageTitle ([string]$Uri) {
    if ($PSVersionTable.PSVersion -le '5.1') {
        # NOTE: Only PowerShell versions <=5.1 support page parsing.
        # See https://github.com/PowerShell/PowerShell/issues/5364
        $a = Invoke-WebRequest -Uri $Uri
        $a.ParsedHtml.title
    } else {
        $PYSCRIPT = @'
import sys, requests, bs4
url, = sys.argv[1:]
html = requests.get(url).content
title = bs4.BeautifulSoup(html).title.get_text(strip=True)
print(title, end='')
'@
        python -c $PYSCRIPT $Uri
    }
}

if (-not (Test-Path -LiteralPath $Destination -PathType Container)) {
    Write-Error "Destination directory does not exist: $Destination"
    return
}

if (-not $Title) {
    $Title = GetPageTitle $Url
}
if (-not $Title) {
    Write-Error "Could not determine webpage title: $Url"
    return
}

$Path = Join-Path $Destination ((Get-SafeFileName $Title) + '.url')

$Content = (
    '[InternetShortcut]',
    ('URL=' + $Url)
)

Set-Content -Encoding Unicode -LiteralPath $Path -Value $Content
