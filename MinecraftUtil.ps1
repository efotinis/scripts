param(
    [Parameter(ParameterSetName="Play", Position=0)]
    [switch]$Play,

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
    [switch]$Versions
    
)


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
            pssuspend -nobanner -r $Process.id
        } else {
            Write-Error 'process already resumed'
        }
    } else {
        if ($Process.Responding) {
            pssuspend -nobanner $Process.id
        } else {
            Write-Error 'process already suspended'
        }
    }
}


Set-Alias -Name pssuspend -Value 'C:\tools\sysinternals\pssuspend.exe'


if ($Play) {

    <#
    $MORATORIUM_START = Get-Date '2021-08-23 17:00'
    $MORATORIUM_LENGTH = [timespan]::new(7, 0, 0, 0)
    $now = Get-Date
    if ($now - $MORATORIUM_START -lt $MORATORIUM_LENGTH) {
        $end = $MORATORIUM_START + $MORATORIUM_LENGTH
        $left = ConvertTo-NiceAge -DateOrSpan ($now - $end)
        $msg = "playing is under moratorium until $($end.ToString()) (due $left) because you died a stupid death (fighting Endermen in the Nether above lava without a Fire potion); please be more careful"
        Write-Error $msg
        exit
    }
    #>

    #D:\games\MultiMC\MultiMC.exe -l $Env:MULTIMC_MAIN_INST
    D:\games\MultiMC\MultiMC.exe -l '1.17.1'

} elseif ($Pause) {

    if ($p = GetMinecraftProcess) {
        SetProcessRunningState $p $false
    }

} elseif ($Resume) {

    if ($p = GetMinecraftProcess) {
        SetProcessRunningState $p $true
    }

} elseif ($Backup) {

    E:\backups\minecraft\backup.ps1 $Instance $World

} elseif ($Restore) {

    E:\backups\minecraft\backup.ps1 $Instance $World -RestoreLast

} elseif ($Doc) {

    $a = ls D:\docs\games\pc\minecraft\*.txt | ? name -like "*$Item*"
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

} else {

    Write-Error 'no param set specified'

}
