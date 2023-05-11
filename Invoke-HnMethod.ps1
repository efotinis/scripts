#requires -Modules NiceConvert

<#
.SYNOPSIS
    Hacker News API client.
.DESCRIPTION
    Implementation of Hacker News client API as described in
    <https://github.com/HackerNews/API>.
.PARAMETER Stories
    Get story IDs.
.PARAMETER Type
    Type of story IDs to get (up to number in parentheses):
        - top (500)
        - new (500)
        - best (500)
        - ask (200)
        - show (200)
        - job (200)
.PARAMETER Item
    Get item data. Stories, comments, jobs, Ask HNs and polls are all items.
.PARAMETER User
    Get user data.
.PARAMETER Id
    Item/user unique ID.
.PARAMETER MaxItem
    Current largest item ID. Previous items can be accessed by decrementing
    this ID.
.PARAMETER Updates
    Get changed items and profiles.
.INPUTS
    User/item IDs when using -User/-Item.
.OUTPUTS
    Varies.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ParameterSetName = 'Stories', Position = 0)]
    [switch]$Stories,

    [Parameter(Mandatory, ParameterSetName = 'Stories', Position = 1)]
    [ValidateSet('top', 'new', 'best', 'ask', 'show', 'job')]
    [string]$Type,

    [Parameter(Mandatory, ParameterSetName = 'Item', Position = 0)]
    [switch]$Item,

    [Parameter(Mandatory, ParameterSetName = 'User', Position = 0)]
    [switch]$User,

    [Parameter(Mandatory, ParameterSetName = 'Item', Position = 1, ValueFromPipeline)]
    [Parameter(Mandatory, ParameterSetName = 'User', Position = 1, ValueFromPipeline)]
    [string[]]$Id,

    [Parameter(Mandatory, ParameterSetName = 'MaxItem', Position = 0)]
    [switch]$MaxItem,

    [Parameter(Mandatory, ParameterSetName = 'Updates', Position = 0)]
    [switch]$Updates
)
begin {
    $APIBASE = 'https://hacker-news.firebaseio.com/v0/'
    $EPOCH = Get-Date -Date '1970-01-01'
    filter ParseDate ([string]$Property) {
        $_.$Property = [datetime]::SpecifyKind(
            $EPOCH.AddSeconds($_.$Property),
            [System.DateTimeKind]::Utc
        )
        Write-Output $_
    }
    function ApiV0 ([string]$Query) {
        Invoke-RestMethod -Uri ($APIBASE + $Query)
    }
    function MultiIdApiV0 ([string]$QueryFmt, [string[]]$Ids, [string]$Activity) {
        $index = 0
        $total = $Ids.Count
        foreach ($id in $Ids) {
            ++$index
            $pc = $index / $total * 100 -as [int]
            Write-Progress -Activity $Activity -Status "$index of $total" -PercentComplete $pc
            ApiV0 ($QueryFmt -f $id)
        }
        Write-Progress -Activity $Activity -Completed
    }
    if ($PSCmdlet.ParameterSetName -in 'Item','User') {
        $AllIds = [System.Collections.ArrayList]@()
    }
}
process {
    if ($PSCmdlet.ParameterSetName -in 'Item','User') {
        $AllIds += $Id
    }
}
end {
    switch ($PSCmdlet.ParameterSetName) {
        'Item' {
            MultiIdApiV0 'item/{0}.json' $AllIds 'Getting items' | ParseDate 'time'
        }
        'User' {
            MultiIdApiV0 'user/{0}.json' $AllIds 'Getting users' | ParseDate 'created'
        }
        'Stories' {
            ApiV0 "${Type}stories.json"
        }
        'MaxItem' {
            ApiV0 'maxitem.json'
        }
        'Updates' {
            ApiV0 'updates.json'
        }
    }
}

<#
ft @{n='age';e={convertto-niceage $_.time -tab -simple }},score,@{n='cmts';e='descendants'},title
#>
