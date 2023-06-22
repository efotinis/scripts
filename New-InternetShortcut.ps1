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

    If omitted, the webpage is parsed and the actual page title is used.

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

if (-not $Title) {
    # NOTE: can't use HtmlWebResponseObject.ParseHtml anymore;
    # see: https://github.com/PowerShell/PowerShell/issues/5364
    $Title = py -c @'
# print webpage title
import sys, requests, bs4
url, = sys.argv[1:]
print(bs4.BeautifulSoup(requests.get(url).content).title.get_text(strip=True), end='')
'@ $Url
}

$Path = Join-Path $Destination ((Get-SafeFileName $Title) + '.url')

$Content = (
    '[InternetShortcut]',
    ('URL=' + $Url)
)

Set-Content -Encoding Unicode -LiteralPath $Path -Value $Content
