$script:OPTIONS_PATH = "$Env:LOCALAPPDATA\goggalaxy.json"


<#
.SYNOPSIS
    Get module options.

.DESCRIPTION
    Returns custom object with configuration options for the GogGalaxy module.
    See Set-GogOption for available options. Missing or non-configured options
    are set to $null.

.INPUTS
    None.

.OUTPUTS
    PSCustomObject.
#>
function Get-GogOption {
    [CmdletBinding()]
    param()
    $args = @{
        LiteralPath = $script:OPTIONS_PATH
        Encoding = 'UTF8'
        ErrorAction = 'Ignore'
    }
    $a = Get-Content @args | ConvertFrom-Json
    $t = [System.Management.Automation.PSCustomObject]
    if ($null -eq $a -or $a.GetType() -ne $t) {
        $a = [PSCustomObject]@{}
    }
    # Get object property if it exists, otherwise nothing (to convert to empty
    # array of needed).
    function TryGetProp ($obj, $name) {
        if (Get-Member -InputObject $obj -Name $name) {
            $obj.$name
        }
    }
    Write-Output ([PSCustomObject]@{
        GameDirectory = @(TryGetProp $a 'GameDirectory')
        ClientPath = TryGetProp $a 'ClientPath'
    })
}


<#
.SYNOPSIS
    Set module options.

.DESCRIPTION
    Sets one or more configuration options for the GogGalaxy module.

.PARAMETER GameDirectory
    List of directory paths containing GOG games. Subdirectories are scanned
    for game metadata when querying installed games.

.PARAMETER ClientPath
    Location of GalaxyClient.exe. Used when starting a game.

.INPUTS
    None.

.OUTPUTS
    None.
#>
function Set-GogOption {
    [CmdletBinding()]
    param(
        [string[]]$GameDirectory,
        [string]$ClientPath
    )
    $options = script:Get-GogOption
    if ($PSBoundParameters.ContainsKey('GameDirectory')) {
        $options.GameDirectory = $GameDirectory
    }
    if ($PSBoundParameters.ContainsKey('ClientPath')) {
        $options.ClientPath = $ClientPath
    }
    $options | ConvertTo-Json |
        Set-Content -LiteralPath $script:OPTIONS_PATH -Encoding UTF8
}


<#
.SYNOPSIS
    Get game objects.

.DESCRIPTION
    Returns info objects for games matching the specified criteria. If no
    criteria are specified, all games are returned.

    The returned object properties are:
        - Id: Unique game number ID.
        - Name: Game name.
        - Path: Game directory.

    Each object contains a Start method that can be used to launch the game.

.PARAMETER Name
    One of more names of games to return. Can contain wildcards.

.PARAMETER Id
    One of more IDs of games to return.

.PARAMETER Directory
    List of directories to scan for installed games.
    Overrides the GameDirectory configuration option.

.INPUTS
    None.

.OUTPUTS
    PSCustomObject.
#>
function Get-GogGame {
    [CmdletBinding(DefaultParameterSetName = 'Name')]
    param(
        [Parameter(ParameterSetName = 'Name', Position = 0)]
        [string[]]$Name = '*',

        [Parameter(ParameterSetName = 'Id')]
        [int[]]$Id,

        [string[]]$Directory
    )
    if (-not $PSBoundParameters.ContainsKey('Directory')) {
        $Directory = (script:Get-GogOption).GameDirectory
    }
    foreach ($path in $Directory) {
        if (-not (Test-Path -LiteralPath $path -PathType Container)) {
            Write-Warning "Game containing directory does not exist: $path"
            continue
        }
        $startMemberArgs = @{
            MemberType = 'ScriptMethod'
            Name = 'Start'
            Value = {
                $args = @(
                    '/gameid=' + $this.Id
                    '/command=runGame'
                    '/path="' + $this.Path + '"'
                )
                & (script:Get-GogOption).ClientPath @args
            }
        }
        # use Force, since some info files are hidden (e.g. Far Cry 2)
        Get-ChildItem "$path\*\goggame*.info" -Force | ForEach-Object {
            $a = Get-Content $_ | ConvertFrom-Json
            $g = [PSCustomObject]@{
                Id = $a.gameid
                Name = $a.name
                Path = $_ | Split-Path -Parent
            }
            $g | Add-Member @startMemberArgs
            switch ($PSCmdlet.ParameterSetName) {
                'Name' {
                    foreach ($p in $Name) {
                        if ($g.Name -like $p) {
                            Write-Output $g
                            break
                        }
                    }
                }
                'Id' {
                    if ($g.Id -in $Id) {
                        Write-Output $g
                        break
                    }
                }
            }
        }
    }
}
