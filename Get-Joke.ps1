<#
.SYNOPSIS
    Print random joke.
    
.DESCRIPTION
    Uses Sven Fehler's JokeAPI: https://github.com/Sv443/JokeAPI

.PARAMETER Category
    General joke category to select. One or more of:
        Any, Misc, Programming, Dark, Pun, Spooky, Christmas
        
    The default is Any and it overrides the rest.

.PARAMETER Blacklist
    Do not select jokes flagged as offensive, using one or more of:
        nsfw, religious, political, racist, sexist, explicit

.PARAMETER Type
    Type of joke to return:
        - Single: A simple joke.
        - TwoPart: A joke with separate setup and delivery parts.
        - Any: Either of the above. This is the default.

.INPUTS
    None.

.OUTPUTS
    Text.
#>
[CmdletBinding()]
param(
    [ValidateSet('Any', 'Misc', 'Programming', 'Dark', 'Pun', 'Spooky', 'Christmas')]
    [string[]]$Category,

    [ValidateSet('nsfw','religious','political','racist','sexist')]
    [string[]]$Blacklist,

    [ValidateSet('any', 'single', 'twopart')]
    [string]$Type
)

$url = 'https://sv443.net/jokeapi/v2/joke/'

if ('Any' -in $Category -or $Category.Count -eq 0) {
    $url += 'Any'
}
else {
    $url += $Category -join ','
}

$query = @{}
if ($Blacklist) {
    $query['blacklistFlags'] = $Blacklist -join ','
}
if ($Type -ne 'any') {
    $query['type'] = $Type
}

if ($query.Count) {
    $a = foreach ($item in $query.GetEnumerator()) {
        $Item.Key + '=' + $Item.Value
    }
    $url += '?' + ($a -join '&')
}

$r = Invoke-RestMethod $url
if ($r.type -eq 'single') {
    $r.joke
}
else {
    '- ' + $r.setup
    '- ' + $r.delivery
}
