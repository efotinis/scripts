$script:OPTIONS_PATH = "$Env:LOCALAPPDATA\goggalaxy.json"


function Get-GogOption {
    [CmdletBinding()]
    param()
    $args = @{
        LiteralPath = $script:OPTIONS_PATH
        Encoding = 'UTF8'
        ErrorAction = 'Ignore'
    }
    $opt = Get-Content @args | ConvertFrom-Json
    if ($null -eq $opt) {
        @{}
    } else {
        $opt
    }
}


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


# Get id,name,path of games in specified directories.
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
        # use Force, since some info files are hidden (e.g. Far Cry 2)
        Get-ChildItem "$path\*\goggame*.info" -Force | ForEach-Object {
            $a = Get-Content $_ | ConvertFrom-Json
            $g = [PSCustomObject]@{
                Id = $a.gameid
                Name = $a.name
                Path = $_ | Split-Path -Parent
            }
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


function Start-GogGame {
    param(
        [Parameter(Mandatory, ValueFromPipelineByPropertyName)]
        [string]$Path,

        [Parameter(Mandatory, ValueFromPipelineByPropertyName)]
        [int]$Id
    )
    $args = @(
        '/gameid=' + $Id
        '/command=runGame'
        '/path="' + $Path + '"'
    )
    & (script:Get-GogOption).ClientPath @args
}
