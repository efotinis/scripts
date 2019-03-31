param(
    [Parameter(Mandatory)]
    [string]$Url,
    
    [string]$Destination = '.',
    
    [string]$Title = $null
)

Set-StrictMode -Version Latest

if (-not $Title) {
    $Response = Invoke-WebRequest -Uri $Url
    $Title = $Response.ParsedHtml.nameProp
}

$Path = Join-Path $Destination ((SafeName $Title) + '.url')

$Content = (
    '[InternetShortcut]',
    ('URL=' + $Url)
)

Set-Content -Encoding Unicode -LiteralPath $Path -Value $Content
