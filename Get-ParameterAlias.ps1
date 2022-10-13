[CmdletBinding()]
param(
    [Parameter(Mandatory, HelpMessage='One or more command names or aliases. Wildcards allowed.')]
    [string[]] $Command,
    
    [Parameter(HelpMessage='Include common parameters and parameters without aliases.')]
    [switch] $All
)

$COMMON = [System.Collections.Generic.Hashset[string]]@(
    'Confirm'
    'Debug'
    'ErrorAction'
    'ErrorVariable'
    'InformationAction'
    'InformationVariable'
    'OutBuffer'
    'OutVariable'
    'PipelineVariable'
    'UseTransaction'
    'Verbose'
    'WarningAction'
    'WarningVariable'
    'WhatIf'
)


function GetCommandsFromParameter ([string[]]$Command) {
    foreach ($name in $Command) {
        $cmds = Get-Command -Name $name
        if ($? -and -not $cmds) {
            Write-Warning "not commands matched: $name"
            continue
        }
        $cmds
    }
}


function GetName ([System.Management.Automation.CommandInfo]$Command) {
    if ($Command.CommandType -eq 'Alias') {
        $Command.DisplayName
    } else {
        $Command.Name
    }
}


foreach ($cmd in (GetCommandsFromParameter $Command)) {
    $cmd.parameters.Values | % {
        if ($All -or ($_.aliases -and $_.name -notin $COMMON)) {
            [PSCustomObject]@{
                Command = GetName $cmd
                Parameter = $_.Name
                Aliases = $_.Aliases
            }
        }
    }
}
