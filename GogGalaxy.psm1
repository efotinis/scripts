$script:CLIENT_PATH = 'C:\Program Files (x86)\GOG Galaxy\GalaxyClient.exe'


# Get id,name,path of games in specified directories.
function Get-GogGame {
    [CmdletBinding(DefaultParameterSetName = 'Name')]
    param(
        [Parameter(ParameterSetName = 'Name', Position = 0)]
        [string[]]$Name = '*',
        
        [Parameter(ParameterSetName = 'Id')]
        [int[]]$Id,
        
        [string[]]$Directory = 'D:\games'
    )
    foreach ($path in $Directory) {
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
    & $script:CLIENT_PATH @args
}
