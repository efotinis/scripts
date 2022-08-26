<#
.SYNOPSIS
    Minecraft CLI tools.

.DESCRIPTION
    Perform various Minecraft and MultiMC related functions.

.PARAMETER Play
    Launch game instance. If Instance is not specified, the last launched
    instance is used.

    A self-imposed moratorium is enforced if Env:MINECRAFT_MORATORIUM exists,
    which is a JSON string with the following properties:
    - start: the beginning datetime
    - days: the length (float)
    - reason: description

.PARAMETER Offline
    Play in offline mode with specified name.

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

.PARAMETER DocText
    Display *.TXT file contents in personal game docs matching name pattern.

.PARAMETER WikiSearch
    Perform search on minecraft.gamepedia.com using specified terms.

.PARAMETER VersionManifest
    Get version manifest from mojang.com, i.e. latest release/snapshot ID 
    and a list of all published versions.

.PARAMETER List
    Output MultiMC instances info.
#>

param(
    [Parameter(ParameterSetName="Play", Mandatory)]
    [switch]$Play,

    [Parameter(ParameterSetName="Play")]
    [string]$Offline,

    [Parameter(ParameterSetName="Pause", Mandatory)]
    [switch]$Pause,

    [Parameter(ParameterSetName="Resume", Mandatory)]
    [switch]$Resume,

    [Parameter(ParameterSetName="Backup", Mandatory)]
    [switch]$Backup,

    [Parameter(ParameterSetName="Restore", Mandatory)]
    [switch]$Restore,

        # almost works, but doesn't quote values with spaces and doesn't take into account partially typed string...
        <#[ArgumentCompleter({
            param($Command, $Parameter, $WordToComplete, $CommandAst, $FakeBoundParams)

            (Get-Content -LiteralPath D:\games\MultiMC\instances\instgroups.json | ConvertFrom-Json).groups.Vanilla.instances
        })]
        [ValidateScript({
            $_ -in (Get-Content -LiteralPath D:\games\MultiMC\instances\instgroups.json | ConvertFrom-Json).groups.Vanilla.instances
        })]#>
        [Parameter(ParameterSetName="Play", Position=0)]
        [Parameter(ParameterSetName="Backup", Position=0, Mandatory)]
        [Parameter(ParameterSetName="Restore", Position=0, Mandatory)]
        [string]$Instance,

        [Parameter(ParameterSetName="Backup", Position=1, Mandatory)]
        [Parameter(ParameterSetName="Restore", Position=1, Mandatory)]
        [string]$World,

    [Parameter(ParameterSetName="DocText", Mandatory)]
    [string]$DocText,

    [Parameter(ParameterSetName="WikiSearch", Mandatory)]
    [string]$WikiSearch,

    [Parameter(ParameterSetName="VersionManifest", Mandatory)]
    [switch]$VersionManifest,

    [Parameter(ParameterSetName="List", Mandatory)]
    [switch]$List

)


# only needed once, but running it every time seems fine
Update-FormatData -PrependPath "$Env:scripts\MinecraftUtil.Format.ps1xml"


Add-Type -TypeDefinition @"
    using int64 = System.Int64;
    using datetime = System.DateTime;
    using timespan = System.TimeSpan;
    public struct MmcInstance
    {
        public string   Version;
        public string   Folder;
        public string   Group;
        public string   Name;
        public datetime LastLaunch;
        public timespan TotalPlayed;
        public timespan LastPlayed;

        public MmcInstance(
            string version, string folder, string group, string name,
            datetime lastLaunch, timespan totalPlayed, timespan lastPlayed)
        {
            Version     = version;
            Folder      = folder;
            Group       = group;
            Name        = name;
            LastLaunch  = lastLaunch;
            TotalPlayed = totalPlayed;
            LastPlayed  = lastPlayed;
        }
    };
    public struct MinecraftVersion {
        public string Id;
        public string Type;
        public datetime Released;
        public datetime Updated;
        public string Url;
        
        public MinecraftVersion(
            string id, string type, datetime released, datetime updated, string url)
        {
            Id       = id;
            Type     = type;
            Released = released;
            Updated  = updated;
            Url      = url;
        }
    };
"@



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
        $_.Value.instances | % {
            $instInfo = LoadCfg "$MULTIMC_ROOT\instances\$_\instance.cfg"

            $version = InstanceVersion $_
            $folder = $_
            $group = $groupName
            $name = $instInfo.name
            $lastLaunch = ([datetime]::new(1970,1,1) + [timespan]::new([long]$instInfo.lastLaunchTime * 10000)).ToLocalTime()
            $totalPlayed = [timespan]::new(0, 0, [int]$instInfo.totalTimePlayed)
            $lastPlayed = [timespan]::new(0, 0, [int]$instInfo.lastTimePlayed)

            [MmcInstance]::new(
                $version,
                $folder,
                $group,
               #$hidden,
                $name,
                $lastLaunch,
                $totalPlayed,
                $lastPlayed
            )
        }
    }
}


function PrintDocs ([string]$Pattern) {
    $a = @(ls $LOCAL_DOCS_DIR\*.txt | ? name -like "*$DocText*")
    if (-not $a) {
        Write-Warning "no files match $DocText"
        return
    }
    function Header ([string]$Text) {
        $line = '=' * 8
        "$line $Text $line"
    }
    $a | % {
        Header $_.name
        $_ | gc
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


# Check moratorium and throw if it's in effect.
function EnforceMoratorium {
    $m = GetMoratorium
    if ($m) {
        $timeLeft = $m.EndDate - (Get-Date)
        if ($timeLeft -gt 0) {
            $time = ConvertTo-NiceAge $timeLeft -Simple
            throw "Moratorium in effect. Time remaining: $time. Reason: $($m.Reason)"
        }
    }
}


switch ($PSCmdlet.ParameterSetName) {
    'Play' {
        $instances = GetInstances
        if ($Instance) {
            if (-not ($instances | ? Folder -eq $Instance)) {
                Write-Error "instance does not exist: $Instance"
                return
            }
        } else {
            $last = GetInstances | sort LastLaunch | select -last 1 -exp Folder
            if (-not $last) {
                Write-Error 'no instance played previously'
                return
            }
            $playInstance = $last
        }
        EnforceMoratorium
        $opt = @(
            '--launch', $playInstance
            if ($Offline) {
                '--offline'
                '--name', $Offline
            }
        )
        MultiMC.exe @opt
    }
    'Pause' {
        if ($p = GetMinecraftProcess) {
            SetProcessRunningState $p $false
        }
    }
    'Resume' {
        if ($p = GetMinecraftProcess) {
            SetProcessRunningState $p $true
        }
    }
    'Backup' {
        backup.ps1 $Instance $World
    }
    'Restore' {
        backup.ps1 $Instance $World -RestoreLast
    }
    'DocText' {
        PrintDocs $DocText
    }
    'WikiSearch' {
        $url = 'https://minecraft.gamepedia.com/index.php?search={0}' -f (
            [uri]::EscapeDataString($WikiSearch)
        )
        Start-Process $url
    }
    'VersionManifest' {
        $url = 'https://launchermeta.mojang.com/mc/game/version_manifest.json'
        $info = Invoke-RestMethod -Uri $Url
        filter Conv {
            [MinecraftVersion]::new(
                $_.id,
                $_.type,
                (Get-Date -Date $_.releaseTime),
                (Get-Date -Date $_.time),
                $_.url
            )
        }
        $info.versions = $info.versions | Conv | Sort-Object -Property Released
        Write-Output $info
    }
    'List' {
        GetInstances
    }
    default {
        Write-Error "unexpected parameter set: $_"
    }
}
