#requires -Modules ConsoleUtil

<#
.SYNOPSIS
    GOG Galaxy game launcher.

.DESCRIPTION
    Displays all installed GOG games and launches the one selected.

    The most recently selected games appear at the top of the list.
    The rest are sorted alphabetically.

.PARAMETER HideConsole
    Temporarily hide console window while script is running.

.INPUTS
    None

.OUTPUTS
    None
#>
[CmdletBinding()]
param(
    [switch]$HideConsole
)


$CLIENT_PATH = 'C:\Program Files (x86)\GOG Galaxy\GalaxyClient.exe'
$GAMES_DIRS = @('D:\games')
$RECENT_LOG = '~\goglaunch-recent.txt'
$RECENT_MAX = 5
$UI_TITLE = 'Launch GOG game'


# Get id,name,path of games in specified directories.
function GamesInfo ([string[]]$Directory) {
    foreach ($path in $Directory) {
        # use Force, since some info files are hidden (e.g. Far Cry 2)
        Get-ChildItem "$path\*\goggame*.info" -Force | ForEach-Object {
            $a = Get-Content $_ | ConvertFrom-Json
            [PSCustomObject]@{
                Id = $a.gameid
                Name = $a.name
                Path = $_ | Split-Path -Parent
            }
        }
    }
}


# Sort objects with recent IDs to beginning of games array and add MRU index.
function AddMruInfo ([object[]]$Games, [object[]]$RecentIds) {
    $mruIndexFromId = [hashtable]::new()
    $RecentIds | % -begin { $i = 1 } -process {
        $mruIndexFromId[$_] = $i++
    }
    $recent, $other = $Games.Where({ $_.Id -in $RecentIds}, 'split')
    $recent = $recent | select @(
        @{ name='MRU'; expr={ $mruIndexFromId[$_.Id] } }
        'Id', 'Name', 'Path'
    )
    $other = $other | select @(
        @{ name='MRU'; expr={ '' } }
        'Id', 'Name', 'Path'
    )
    @($recent | sort -Property mru) + @($other)
}


# MRU list of game IDs.
class RecentGames {

    [System.Collections.ArrayList] $Ids

    # load, if any, up to max
    RecentGames () {
        $this.Ids = @(
            Get-Content -Path $script:RECENT_LOG -ErrorAction Ignore |
                select -first $script:RECENT_MAX
        )
    }

    # save up to max
    [void] Save () {
        $this.Ids |
            select -first $script:RECENT_MAX |
            Set-Content -Path $script:RECENT_LOG
    }

    # add (or move if existing) to beginning
    [void] Add ($Id) {
        $this.Ids.Remove($Id)
        $this.Ids.Insert(0, $Id)
    }
}


if ($HideConsole) {
    Hide-ConsoleWindow
}
try {
    $recent = [RecentGames]::new()
    $games = AddMruInfo (GamesInfo $GAMES_DIRS) $recent.Ids
    $sel = $games | Out-GridView -Title $UI_TITLE -OutputMode Single

    if ($sel) {
        $recent.Add($sel.Id)
        $recent.Save()
        $args = @(
            '/gameid=' + $sel.Id
            '/command=runGame'
            '/path="' + $sel.Path + '"'
        )
        & $CLIENT_PATH @args
    }
} finally {
    if ($HideConsole) {
        Show-ConsoleWindow
    }
}
