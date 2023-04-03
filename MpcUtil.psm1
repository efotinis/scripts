Set-StrictMode -Version Latest


$ROOT = 'HKCU:\Software\MPC-HC\MPC-HC'
$REG_SETTINGS = "$ROOT\Settings"
$REG_HWACCEL = "$ROOT\Internal Filters\LAVVideo\HWAccel"
$REG_HISTORY = "$ROOT\MediaHistory"
$REG_FAVORITE = "$ROOT\Favorites\Files"


function UIn32ToInt32 ([UInt32]$Value) {
    [System.BitConverter]::ToInt32([System.BitConverter]::GetBytes($Value), 0)
}


function Int32ToUInt32 ([Int32]$Value) {
    [System.BitConverter]::ToUInt32([System.BitConverter]::GetBytes($Value), 0)
}


<#
.SYNOPSIS
    Get MPC configuration options.

.DESCRIPTION
    Returns a selected subset of MPC registry settings. See Set-MpcOption for
    properties and their possible values.

.PARAMETER AsHashtable
    Return settings as a hashtable. This object can later be used to reset all
    options to a previous state, by splatting it into Set-MpcOption.

    If not specified, the return type is PSCustomObject.

.INPUTS
    None

.OUTPUTS
    PSCustomObject or hashtable.
#>
function Get-MpcOption {
    [CmdletBinding()]
    param(
        [switch]$AsHashtable
    )

    $x = Get-ItemProperty $REG_SETTINGS @(
        'Mute', 'Volume', 'Balance'
        'AutoZoom', 'Zoom', 'AutoFitFactor'
        'Loop', 'LoopNum', 'AfterPlayback', 'LoopMode'
        'HideCaptionMenu', 'ControlState'
    )
    $HWAccel = Get-ItemProperty $REG_HWACCEL 'HWAccel' | % HWAccel

    $ret = [ordered]@{
        Mute = [bool]$x.Mute
        Volume = $x.Volume
        Balance = UIn32ToInt32 $x.Balance
        LoopMode = if (-not $x.Loop) {
            'Off'
        } elseif (-not $x.LoopMode) {
            'File'
        } else {
            'Playlist'
        }
        LoopCount = $x.LoopNum
        AfterPlayback = $(
            $a = 'DoNothing', 'PlayNextFile', 'Rewind', 'TurnMonitorOff', 'Close', 'Exit'
            $i = $x.AfterPlayback
            if ($i -ge 0 -and $i -lt $a.Count) {
                $a[$i]
            } else {
                $null
            }
        )
        AutoZoom = $(
            $a = '25%', '50%', '100%', '200%', 'AutoFit', 'AutoFitIfLarger'
            if (-not $x.AutoZoom) {
                'Off'
            } elseif ($x.Zoom -ge -1 -and $x.Zoom -lt ($a.Count - 2)) {
                $a[$x.Zoom + 1]
            } else {
                $null
            }
        )
        AutoFitFactor = $x.AutoFitFactor
        Chrome = switch ($x.HideCaptionMenu) {
            0 { 'Normal' }
            1 { 'HideMenu' }
            2 { 'HideCaption' }
            3 { 'HideBorder' }
        }
        Panels = @(
            $a = 'SeekBar', 'Controls', 'Information', 'Statistics', 'Status'
            for ($i = 0; $i -lt $a.Count; ++$i) {
                if ($x.ControlState -band (1 -shl $i)) {
                    $a[$i]
                }
            }
        )
        HardwareAcceleration = switch ($HWAccel) {
            0 { $false }
            4 { $true }
        }
    }
    if ($AsHashtable) {
        $ret = $ret -as [hashtable]
    } else {
        $ret = [PSCustomObject]$ret
    }
    <#$ret | Add-Member -Type ScriptProperty -Name ViewPreset -Value {
        switch ("$($this.HideCaptionMenu),$($this.ControlState)") {
            '0,19' { 'Normal' }
            '2,1' { 'Compact' }
            '3,0' { 'Minimal' }
            default { '(Custom)' }
        }
    }#>
    $ret
}


<#
.SYNOPSIS
    Set MPC configuration options.

.DESCRIPTION
    Allows modifying a selected subset of MPC registry settings.

.PARAMETER Mute
    Volume mute.

.PARAMETER Volume
    Volume level (0..100).

.PARAMETER Balance
    Volume balance (-100..100).

.PARAMETER LoopMode
    Loop mode. Possible values:
        - Off
        - File
        - Playlist

.PARAMETER LoopCount
    Nummber of loops when loop mode is File or Playlist.

.PARAMETER AfterPlayback
    Action at playback completion. One of:
        - DoNothing:    Leave current position at the end of the file.
        - PlayNextFile: Play next file in folder.
        - Rewind:       Move current position at the beginning of the file.
        - TurnMonitorOff: Turn monitor off.
        - Close:        Close file.
        - Exit:         Close player.

.PARAMETER AutoZoom
    Automatic zooming when playing a new file. One of:
        - Off
        - 25%
        - 50%
        - 100%
        - 200%
        - AutoFit
        - AutoFitIfLarger

.PARAMETER AutoFitFactor
    Percentage of screen height to use if auto zoom is set to AutoFit or
    AutoFitIfLarger (25..100).

.PARAMETER HardwareAcceleration
    Enable use of HWA when possible.

.PARAMETER Chrome
    Window chrome setting. One of:
        - Normal:       Show border, menu and caption.
        - HideMenu:     Show border and caption.
        - HideCaption:  Show border only.
        - HideBorder:   Hide all.

.PARAMETER Panels
    Parts of the player to display. Zero or more of:
        - SeekBar
        - Controls
        - Information
        - Statistics
        - Status

.INPUTS
    None.

.OUTPUTS
    None.
#>
function Set-MpcOption {
    [CmdletBinding(PositionalBinding = $false)]
    param(
        [bool]$Mute,

        [ValidateRange(0, 100)]
        [int]$Volume,

        [ValidateRange(-100, 100)]
        [int]$Balance,

        [ValidateSet('Off', 'File', 'Playlist')]
        [string]$LoopMode,

        [ValidateRange(0, 9999)]
        [int]$LoopCount,

        [ValidateSet('DoNothing', 'PlayNextFile', 'Rewind', 'TurnMonitorOff', 'Close', 'Exit')]
        [string]$AfterPlayback,

        [ValidateSet('Off', '25%', '50%', '100%', '200%', 'AutoFit', 'AutoFitIfLarger')]
        [string]$AutoZoom,

        [ValidateRange(25, 100)]
        [int]$AutoFitFactor,

        [bool]$HardwareAcceleration,

        [ValidateSet('Normal', 'HideMenu', 'HideCaption', 'HideBorder')]
        [string]$Chrome,

        [ValidateSet('SeekBar', 'Controls', 'Information', 'Statistics', 'Status')]
        [string[]]$Panels
    )

    # -- Volume --
    if ($PSBoundParameters.ContainsKey('Mute')) {
        Set-ItemProperty $REG_SETTINGS 'Mute' ([int]$Mute)
    }
    if ($PSBoundParameters.ContainsKey('Volume')) {
        Set-ItemProperty $REG_SETTINGS 'Volume' $Volume
    }
    if ($PSBoundParameters.ContainsKey('Balance')) {
        Set-ItemProperty $REG_SETTINGS 'Balance' (Int32ToUInt32 $Balance)
    }

    # -- Looping --
    if ($PSBoundParameters.ContainsKey('LoopMode')) {
        switch ($LoopMode) {
            'Off' {
                Set-ItemProperty $REG_SETTINGS 'Loop' 0
            }
            'File' {
                Set-ItemProperty $REG_SETTINGS 'Loop' 1
                Set-ItemProperty $REG_SETTINGS 'LoopMode' 0
            }
            'Playlist' {
                Set-ItemProperty $REG_SETTINGS 'Loop' 1
                Set-ItemProperty $REG_SETTINGS 'LoopMode' 1
            }
        }
    }
    if ($PSBoundParameters.ContainsKey('LoopCount')) {
        Set-ItemProperty $REG_SETTINGS 'LoopNum' $LoopCount
    }
    if ($PSBoundParameters.ContainsKey('AfterPlayback')) {
        $a = 'DoNothing', 'PlayNextFile', 'Rewind', 'TurnMonitorOff', 'Close', 'Exit'
        $i = $a.IndexOf($AfterPlayback)
        Set-ItemProperty $REG_SETTINGS 'AfterPlayback' $i
    }

    # -- Auto-zoom --
    if ($PSBoundParameters.ContainsKey('AutoZoom')) {
        $a = '25%', '50%', '100%', '200%', 'AutoFit', 'AutoFitIfLarger'
        $i = $a.IndexOf($AutoZoom)
        if ($i -eq -1) {
            Set-ItemProperty $REG_SETTINGS 'AutoZoom' 0
        } else {
            Set-ItemProperty $REG_SETTINGS 'AutoZoom' 1
            Set-ItemProperty $REG_SETTINGS 'Zoom' ($i - 1)
        }
    }
    if ($PSBoundParameters.ContainsKey('AutoFitFactor')) {
        Set-ItemProperty $REG_SETTINGS 'AutoFitFactor' $AutoFitFactor
    }

    # -- Window layout --
    if ($PSBoundParameters.ContainsKey('Chrome')) {
        $a = 'Normal', 'HideMenu', 'HideCaption', 'HideBorder'
        $i = $a.IndexOf($Chrome)
        Set-ItemProperty $REG_SETTINGS 'HideCaptionMenu' $i
    }
    if ($PSBoundParameters.ContainsKey('Panels')) {
        $a = @{
            'SeekBar' = 1
            'Controls' = 2
            'Information' = 4
            'Statistics' = 8
            'Status' = 16
        }
        $n = 0
        foreach ($s in $Panels) {
            $n = $n -bor $a[$s]
        }
        Set-ItemProperty $REG_SETTINGS 'ControlState' $n
    }

    # -- Misc --
    if ($PSBoundParameters.ContainsKey('HardwareAcceleration')) {
        $n = if ($HardwareAcceleration) { 4 } else { 0 }
        Set-ItemProperty $REG_HWACCEL 'HWAccel' $n
    }

    <#
    if ($PSBoundParameters.ContainsKey('ViewPreset')) {
        $HideCaptionMenu = switch ($ViewPreset) {
            'Minimal' { 3 }
            'Compact' { 2 }
            'Normal' { 0 }
        }
        $ControlState = switch ($ViewPreset) {
            'Minimal' { 0 }
            'Compact' { 1 }
            'Normal' { 19 }
        }
        Set-ItemProperty $REG_SETTINGS 'HideCaptionMenu' $HideCaptionMenu
        Set-ItemProperty $REG_SETTINGS 'ControlState' $ControlState
    }
    #>
}


<#
.SYNOPSIS
    Show MPC setting changes.

.DESCRIPTION
    Displays MPC setting changes by polling the registry. Can be used for
    debugging.

.PARAMETER IntervalSeconds
    Time in seconds between registry checks. Can be fractional. Default: 0.1s.

.PARAMETER ShowInitial
    Display all settings at the start.

.INPUTS
    None.

.OUTPUTS
    Text.
#>
function Watch-MpcOption {
    [CmdletBinding()]
    param(
        [float]$IntervalSeconds = 0.1,
        [switch]$ShowInitial
    )
    $a = @()
    $showNext = [bool]$ShowInitial
    for (;;) {
        $b = Get-ItemProperty $REG_SETTINGS * |
            Select-Object * -Exclude ps* |
            % psobject |
            % properties |
            % { '{0}: {1}' -f $_.name, $_.value }
        $changes = Compare-Object $a $b | ? sideindicator -eq '=>'
        if ($changes -and $showNext) {
            $changes.inputobject | out-string
        }
        $a = $b
        $showNext = $true
        Start-Sleep -Milliseconds ($IntervalSeconds * 1000 -as [int])
    }
}


function FavFromStr ([string]$Data) {
    # NOTE: only ';' is escaped to '\;'; nothing else (not even '\')
    $a = $Data -split '(?<!\\);'  # split on non-escaped semicolons
    [PSCustomObject]@{
        RelDrive = [bool][int]$a[2]
        Position = [timespan]::new([long]$a[1])
        Name = $a[0] -replace '\;',';'
        Path = $a[3] -replace '\;',';'
    }
}


function Get-MpcFavorite {
    [CmdletBinding()]
    param()
    $a = Get-ItemProperty $REG_FAVORITE Name*
    for ($i = 0; ; ++$i) {
        if (-not (Get-Member -InputObject $a -Name "Name$i")) {
            break
        }
        FavFromStr $a."Name$i"
    }
}


function Get-MpcHistory {
    # TODO: Other versions may store history differently. See mpcutil.py.
    Get-ChildItem -Path $REG_HISTORY | % {
        [PSCustomObject]@{
            LastOpened = Get-Date -Date $_.GetValue('LastOpened')
            Position = [timespan]::new($_.GetValue('FilePosition') * 10000)
            Path = $_.GetValue('Filename')
        }
    }
}


Export-ModuleMember -Function *-*
