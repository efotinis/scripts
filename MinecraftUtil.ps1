param(
    [Parameter(ParameterSetName="Play", Position=0)]
    [switch]$Play,
    
    [Parameter(ParameterSetName="Backup", Position=0)]
    [switch]$Backup,

    [Parameter(ParameterSetName="Restore", Position=0)]
    [switch]$Restore,

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


if ($Play) {

    D:\games\MultiMC\MultiMC.exe -l $Env:MULTIMC_MAIN_INST

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
