$Agent = 'foobar2000/1.3.16'
$CommonStations = (
    ('PopTron', 'http://ice3.somafm.com/poptron-64-aac'),
    ('1291AlternativeRock', 'http://listen.radionomy.com/1291AlternativeRock'),
    ('Radio Swiss Pop', 'http://stream.srg-ssr.ch/m/rsp/aacp_96'),
    ('Radio Paradise', 'http://stream-uk1.radioparadise.com/aac-64'),
    ('Another Music Project', 'http://radio.anothermusicproject.com:8000/idm')
)
switch ($Env:ComputerName) {
    'core' {
        $Ripper = 'C:\Program Files (x86)\Streamripper\streamripper.exe'
        $Outdir = 'E:\recs\streamripper'
    }
    'relic' {
        $Ripper = 'C:\Program Files\Streamripper\streamripper.exe'
        $Outdir = 'D:\sr'
    }
    default {
        Write-Host "no config in script for current machine ($Env:ComputerName)"
        return
    }
}


# Select from menu of common station or get custom URL.
function SelectStream {
    Write-Host 'common stations:'
    $Index = 1
    foreach ($Station in $CommonStations) {
        Write-Host "  $Index. $($Station[0])"
        $Index += 1
    }
    while ($true) {
        $Resp = (Read-Host 'enter station number or custom URL').Trim()
        if ($Resp -match '^\d+$') {
            $Resp = [int]$Resp
            if ($Resp -gt 0 -and $Resp -le $CommonStations.Count) {
                return $CommonStations[$Resp - 1][1]
            }
            Write-Host 'invalid index'
        }
        elseif ($Resp) {
            return $Resp
        }
    }
}


# Select number of minutes to split output or 0 for no splitting
function SelectChunk {
    $Default = '180'
    while ($true) {
        $Resp = (Read-Host "enter chunk size in minutes (0 for continuous; default: $Default)").Trim()
        if (-not $Resp) {
            $Resp = $Default
        }
        if ($Resp -match '^\d+$') {
            return [int]$Resp
        }
        Write-Host 'bad value'
    }
}


$Stream = SelectStream
$ChunkMinutes = SelectChunk

$Args = @(
    $Stream
    '-d', $OutDir  # destination dir
    '-a', '-A'  # output single file, suppress individual files
    '-r', '-R', '0'  # create relay server without connection count limit
    '-u', $Agent  # hide Streamripper's identity
    '--codeset-id3=cp1253'  # use something that usually works
)

if ($ChunkMinutes) {
    $Args += @(
        '-l', ($ChunkMinutes*60)  # stop after specified minutes
    )
    $RunNo = 1
    while ($true) {
        $Start = Get-Date
        $End = (Get-Date) + (New-TimeSpan -Minutes $ChunkMinutes)
        $Host.UI.RawUI.WindowTitle = ('{0}-minute run #{1}, started on {2:G}, ends on {3:G}' -f ($ChunkMinutes, $RunNo, $Start, $End))
        & $Ripper @Args
        $RunNo += 1
    }
}
else {
    $Host.UI.RawUI.WindowTitle = ('infinite run, started on {0:G}' -f (Get-Date))
    & $Ripper @Args
}
