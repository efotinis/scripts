Set-StrictMode -Version Latest

Import-Module C:\scripts\EFUtil.psm1
Update-FormatData C:\scripts\EF.Format.ps1xml

# shorthands and aliases
function global:m ($i, $b, $c) {
    # multiply value by ten, preserving leading sign (if any);
    # note that $b/$c params will be either numeric or string,
    # depending on whether they include a leading sign or not
    function Value ($n) {
        if ($n -match '([+-])(.*)') {
            $Matches[1] + [int]([double]$Matches[2] * 10) 
        } else {
            $n * 10
        }
    }
    if ($b -ne $null) { $b = Value $b }
    if ($c -ne $null) { $c = Value $c }
    
    if ($i -eq $null) {
        monctl
    } elseif ($b -eq $null) {
        monctl -m $i
    } elseif ($c -eq $null) {
        monctl -m $i -b $b -c $b
    } else {
        monctl -m $i -b $b -c $c
    }
}
Function global:x { exit }
function global:z ($time) { c:\scripts\suspend.py -l $time }
Function global:.. { Set-Location .. }
Function global:... { Set-Location ..\.. }
Function global:?? ($Cmd) { help $Cmd -Full }
function global:yc { yps (gcb) }  # play youtube stream from clipboard url
function global:mc { mcver -d30 }  # show minecraft updates in the last 30 days
Set-Alias -Scope global yd C:\tools\youtube-dl.exe
Set-Alias -Scope global minf C:\tools\MediaInfo\MediaInfo.exe
Set-Alias -Scope global 7z "$Env:ProgramFiles\7-Zip\7z.exe"
Set-Alias -Scope global j "$Env:DROPBOX\jo.py"
Set-Alias -Scope global fn C:\scripts\filternames.ps1
Set-Alias -Scope global mpc (Get-ItemPropertyValue HKCU:\Software\MPC-HC\MPC-HC ExePath)
switch ($env:COMPUTERNAME) {
    'core' {
        Set-Alias -Scope global srip 'C:\Program Files (x86)\Streamripper\streamripper.exe'
        Set-Alias -Scope global slink 'C:\Program Files\Python37\Scripts\streamlink.exe'
    }
    'lap7' {
        Set-Alias -Scope global srip 'C:\tools\streamripper\streamripper.exe'
        Set-Alias -Scope global slink 'C:\Program Files\Python36-32\Scripts\streamlink.exe'
    }
}


# get/set console title
function global:WndTitle ($s) {
    if ($s -eq $null) {
        $Host.UI.RawUI.WindowTitle
    } else {
        $Host.UI.RawUI.WindowTitle = $s
    }
}


# play audio file
function global:PlaySound ($path) {
    (New-Object Media.SoundPlayer $Path).Play()
}


# output speech
function global:Speak (
    [string]$Text, 
    [int]$Volume = 100, 
    [int]$Rate = 0
) {
    $Voice = New-Object -ComObject SAPI.SpVoice
    $Voice.Volume = $Volume
    $Voice.Rate = $Rate
    $Voice.Speak($Text) > $Null
}


# reverse input sequence
# http://stackoverflow.com/questions/22771724/reverse-elements-via-pipeline
function global:Reversed
{
    $a = @($input)
    [array]::reverse($a)
    return $a
}


# get elevation status
function global:IsAdmin {
    ([Security.Principal.WindowsPrincipal] `
      [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}


# media file duration in seconds using AVPROBE
function global:Duration ($path) {
    $j = (avprobe.exe -v 0 -of json -show_format $path | ConvertFrom-Json)
    $j.format.duration
}


# Insert dashes to YYYYMMDD string.
function global:DateDashes ([string]$Ymd) {
    $Ymd.Insert(6,'-').Insert(4,'-')
}


# Replace invalid filename characters with underscore.
function global:SafeName ($s) {
    foreach ($c in [IO.Path]::GetInvalidFileNameChars()) {
        $s = $s.Replace($c, '_')
    };
    return $s;
}


# Change the extension of a file path
function global:SetExt ($path, $ext) {
    [IO.Path]::ChangeExtension($path, $ext)
}


# Pretty size of all file objects piped in.
function global:FSize {
    $m = $Input | Measure-Object -Sum -Property Length
    PrettySize $m.Sum
}


if ($host.name -eq 'ConsoleHost') {

    # invert prompt text color intensities; helps tell each command apart
    function global:prompt {
        $s = "$($ExecutionContext.SessionState.Path.CurrentLocation)$('>' * ($NestedPromptLevel + 1))"
        Write-Host  $s -NoNewline `
            -ForegroundColor ($host.UI.RawUI.ForegroundColor -bxor 8) `
            -BackgroundColor ($host.UI.RawUI.BackgroundColor -bxor 8)
        Write-Output ' '
    }

    if (IsAdmin) {
        $host.UI.RawUI.BackgroundColor = 'darkred'
        Clear-Host
    }

    # customize output stream colors
    function ConClr ($type, $fg, $bg = $host.UI.RawUI.BackgroundColor) {
        $host.PrivateData.$($type + 'ForegroundColor') = $fg
        $host.PrivateData.$($type + 'BackgroundColor') = $bg
    }
    ConClr Error   magenta
    ConClr Warning yellow
    ConClr Debug   cyan
    ConClr Verbose green

    # toggle black & white mode; useful when running programs that output
    # colors and assuming a black background (e.g. pip)
    function global:MonoClr {
        if ([bool]$Env:MonoClr) {
            if (IsAdmin) {
                $host.UI.RawUI.BackgroundColor = 'darkred'
            } else {
                $host.UI.RawUI.BackgroundColor = 'darkblue'
            }
            $Env:MonoClr = $null
        } else {
            $host.UI.RawUI.BackgroundColor = 'black'
            $Env:MonoClr = 'on'
        }
    }

    function global:Color ([string]$Spec) {
        $Colors = @{
            'n'='black';
            'b'='darkblue';
            'g'='darkgreen';
            'c'='darkcyan';
            'r'='darkred';
            'm'='darkmagenta';
            'y'='darkyellow';
            'w'='gray';
            'n+'='darkgray';
            'b+'='blue';
            'g+'='green';
            'c+'='cyan';
            'r+'='red';
            'm+'='magenta';
            'y+'='yellow';
            'w+'='white'
        }

        $fore, $back = (($spec + '/') -split '/')[0..1]
        if ($fore -in $Colors.Keys) {
            $Host.UI.RawUI.ForegroundColor = $Colors[$fore]
        }
        if ($back -in $Colors.Keys) {
            $Host.UI.RawUI.BackgroundColor = $Colors[$back]
        }
    }

}
