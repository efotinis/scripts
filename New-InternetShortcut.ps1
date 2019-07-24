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

$Path = Join-Path $Destination ((SafeName $Title) + '.url')

$Content = (
    '[InternetShortcut]',
    ('URL=' + $Url)
)

Set-Content -Encoding Unicode -LiteralPath $Path -Value $Content
