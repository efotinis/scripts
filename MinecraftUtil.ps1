<#
.SYNOPSIS
    Minecraft CLI tools.

.DESCRIPTION
    Perform various Minecraft and MultiMC related functions.

.PARAMETER Play
    Launch game instance. A self-imposed moratorium is enforced if 
    Env:MINECRAFT_MORATORIUM exists, which is a JSON string with the following 
    properties:
    - start: the beginning datetime
    - days: the length (float)
    - reason: description

.PARAMETER PromptForInstance
    Allow user selection of the MulitMC instance. By default, the instance 
    specified by Env:MINECRAFT_MULTIMC_DEFAULT_INST is used.

.PARAMETER Pause
    Pause the game, by forcibly suspending the Minecraft process. Requires 
    pssuspend.exe by SysInternals.

.PARAMETER Resume
    Resume the game, if previously suspended by -Pause.

.PARAMETER Backup
    Backup an instance's world (custom script).

.PARAMETER Restore
    Restore an instance's world to the latest backup (custom script).

.PARAMETER Instance
    Instance ID (folder name).

.PARAMETER World
    World ID (folder name).

.PARAMETER Doc
    Display file contents from personal game docs.

.PARAMETER Item
    Pattern of name. Only a single file must match.

.PARAMETER Wiki
    Perform search on minecraft.gamepedia.com.

.PARAMETER Query
    Search terms.

.PARAMETER Versions
    Run custom script to display game versions in the last 30 days.

.PARAMETER List
    Output MultiMC instances info.
#>

param(
    [Parameter(ParameterSetName="Play", Position=0)]
    [switch]$Play,

        [Parameter(ParameterSetName="Play", Position=1)]
        [switch]$PromptForInstance,
    
    [Parameter(ParameterSetName="Pause", Position=0)]
    [switch]$Pause,

    [Parameter(ParameterSetName="Resume", Position=0)]
    [switch]$Resume,

    [Parameter(ParameterSetName="Backup", Position=0)]
    [switch]$Backup,

    [Parameter(ParameterSetName="Restore", Position=0)]
    [switch]$Restore,

        # almost works, but doesn't quote values with spaces and doesn't take into account partially typed string...
        <#[ArgumentCompleter({
            param($Command, $Parameter, $WordToComplete, $CommandAst, $FakeBoundParams)

            (Get-Content -LiteralPath D:\games\MultiMC\instances\instgroups.json | ConvertFrom-Json).groups.Vanilla.instances
        })]
        [ValidateScript({
            $_ -in (Get-Content -LiteralPath D:\games\MultiMC\instances\instgroups.json | ConvertFrom-Json).groups.Vanilla.instances
        })]
        [Parameter(ParameterSetName="Play", Position=1)]#>
        [Parameter(ParameterSetName="Backup", Position=1, Mandatory)]
        [Parameter(ParameterSetName="Restore", Position=1, Mandatory)]
        [string]$Instance,

        [Parameter(ParameterSetName="Backup", Position=2, Mandatory)]
        [Parameter(ParameterSetName="Restore", Position=2, Mandatory)]
        [string]$World,
    
    [Parameter(ParameterSetName="Doc", Position=0)]
    [switch]$Doc,

        [Parameter(ParameterSetName="Doc", Position=1, Mandatory)]
        [string]$Item,
    
    [Parameter(ParameterSetName="Wiki", Position=0)]
    [switch]$Wiki,

        [Parameter(ParameterSetName="Wiki", Position=1, Mandatory)]
        [string]$Query,
    
    [Parameter(ParameterSetName="Versions", Position=0)]
    [switch]$Versions,
    
    [Parameter(ParameterSetName="List", Position=0)]
    [switch]$List
    
)


# Requirements and environment.
$MULTIMC_ROOT = 'D:\games\MultiMC'
$LOCAL_DOCS_DIR = 'D:\docs\games\pc\minecraft'
Set-Alias -Name MultiMC.exe   -Value "$MULTIMC_ROOT\MultiMC.exe"
Set-Alias -Name pssuspend.exe -Value 'C:\tools\sysinternals\pssuspend.exe'
Set-Alias -Name backup.ps1    -Value 'E:\backups\minecraft\backup.ps1'
Set-Alias -Name mcver.py      -Value 'D:\docs\scripts\mcver.py'


function GetMinecraftProcess {
    $proc = Get-Process javaw -ErrorAction Ignore |
        ? MainWindowTitle -like minecraft*
    if (-not $proc) {
        Write-Error 'could not find Minecraft process'
        return
    }
    $proc
}


function SetProcessRunningState ($Process, $Resumed) {
    if ($Resumed) {
        if (-not $Process.Responding) {
            pssuspend.exe -nobanner -r $Process.id
        } else {
            Write-Error 'process already resumed'
        }
    } else {
        if ($Process.Responding) {
            pssuspend.exe -nobanner $Process.id
        } else {
            Write-Error 'process already suspended'
        }
    }
}


# Hashtable of CFG file containing "key=value" lines.
function LoadCfg ($Path) {
    $a = @{}
    gc $Path | % {
        $k, $v = $_ -split '=',2
        $a.$k = $v
    }
    $a
}


function GetInstances {

    function InstanceVersion ($DirName) {
        $path = "$MULTIMC_ROOT\instances\$_\mmc-pack.json"
        $info = gc $path | ConvertFrom-Json
        $info.components | ? uid -eq net.minecraft | % version
    }

    $a = gc "$MULTIMC_ROOT\instances\instgroups.json" | ConvertFrom-Json
    $a.groups.PSObject.Properties | % {
        $groupName = $_.Name
        $hidden = $_.Value.hidden
        $_.Value.instances | % {
            $instInfo = LoadCfg "$MULTIMC_ROOT\instances\$_\instance.cfg"
            [PSCustomObject]@{
                Version = InstanceVersion $_
                Folder = $_
                Group = $groupName
                Hidden = $hidden
                Name = $instInfo.name
                LastLaunch = ([datetime]::new(1970,1,1) + [timespan]::new([long]$instInfo.lastLaunchTime * 10000)).ToLocalTime()
                TotalPlayed = [timespan]::new(0, 0, [int]$instInfo.totalTimePlayed)
                LastPlayed = [timespan]::new(0, 0, [int]$instInfo.lastTimePlayed)
                
            }
        }
    }
}


function GetMoratorium {
    $json = $Env:MINECRAFT_MORATORIUM
    if ($json) {
        $info = ConvertFrom-Json $json
        $from = Get-Date $info.start
        $span = [timespan]::new([double]$info.days, 0, 0, 0)
        [PSCustomObject]@{
            EndDate = $from + $span
            Reason = $info.reason
        }
    }
}


if ($Play) {

    $playInstance = if ($PromptForInstance) {
        $instances = GetInstances | Add-IndexMember -Start 1 -PassThru
        for (;;) {
            $instances | ft index,folder,version,group,name | Out-Host
            $n = Read-Host "select instance index (1..$($instances.count))"
            $n = $n.Trim()
            if ($n -notmatch '^-?\d+$') {
                Write-Error "invalid number: $n"
                continue
            }
            $n = $n -as [int]
            if ($null -eq $n) {
                Write-Error "invalid number: $n"
                continue
            }
            if ($n -lt 1 -or $n -gt $instances.count) {
                Write-Error "instance index out of range: $n"
                continue
            }
            break
        }
        $instances[$n - 1].Folder
    } else {
        $Env:MINECRAFT_MULTIMC_DEFAULT_INST
    }
    
    $m = GetMoratorium
    if ($m) {
        $timeLeft = $m.EndDate - (Get-Date)
        if ($timeLeft -gt 0) {
            $time = ConvertTo-NiceAge $timeLeft -Simple
            Write-Error "Moratorium in effect. Time remaining: $time. Reason: $($m.Reason)"
            return
        }
    }

    MultiMC.exe --launch $playInstance

} elseif ($Pause) {

    if ($p = GetMinecraftProcess) {
        SetProcessRunningState $p $false
    }

} elseif ($Resume) {

    if ($p = GetMinecraftProcess) {
        SetProcessRunningState $p $true
    }

} elseif ($Backup) {

    backup.ps1 $Instance $World

} elseif ($Restore) {

    backup.ps1 $Instance $World -RestoreLast

} elseif ($Doc) {

    $a = ls $LOCAL_DOCS_DIR\*.txt | ? name -like "*$Item*"
    if (-not $a) {
        Write-Error "no files match $Item"
    } elseif ($a.Count -gt 1) {
        $names = ($a | % { """$($_.BaseName)""" }) -join ', '
        Write-Error "multiple files match ${Item}: $names"
    } else {
        $a | cat
    }

} elseif ($Wiki) {

    $url = 'https://minecraft.gamepedia.com/index.php?search={0}' -f (
        [uri]::EscapeDataString($Query)
    )
    Start-Process $url

} elseif ($Versions) {

    mcver.py -d30

} elseif ($List) {

    GetInstances

} else {

    Write-Error 'no param set specified'

}
