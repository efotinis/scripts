[CmdletBinding()]
param(
    [string[]]$Path
)

Set-StrictMode -Version Latest


Add-Type -TypeDefinition @"
    using int64 = System.Int64;
    public struct VideoInfo
    {
        public int      Width;
        public int      Height;
        public double   Duration;
        public int      Bitrate;
        public double   Framerate;
        public string   Video;
        public string   VideoTag;
        public string   Audio;
        public int      Channels;
        public int64    Size;
        public string   Path;
        public VideoInfo(
            int width, int height, double duration, int bitrate, double framerate, 
            string video, string videoTag, string audio, int channels, int64 size, 
            string path) 
        {
            Width = width;
            Height = height;
            Duration = duration;
            Bitrate = bitrate;
            Framerate = framerate;
            Video = video;
            VideoTag = videoTag;
            Audio = audio;
            Channels = channels;
            Size = size;
            Path = path;
        }
    }
"@


filter IsVideoStream {
    if ($_.codec_type -eq 'video' -and $_.avg_frame_rate -ne '0/0') {
        $_
    }
}

filter IsAudioStream {
    if ($_.codec_type -eq 'audio') {
        $_
    }
}

function fps_value ($Ratio) {
    $a, $b = $Ratio -split '/',2
    $a / $b
}

function CodecTag ([string]$s) {
    $s -replace '\[0\]',"`0"
}


$progress = $null
$progressIndex = 0
if ($Path.Count -gt 15) {
    $progress = @{
        Activity='Extracting video information'
    }
}

$Path | % {
    if ($progress) {
        $progressIndex += 1
        $progress.CurrentOperation = $_
        $progress.Status = "$progressIndex of $($Path.Count)"
        $progress.PercentComplete = ($progressIndex - 1) / $Path.Count * 100
        Write-Progress @progress
    }
    
    if (-not (Test-Path -PathType Leaf -LiteralPath $_)) {
        Write-Error -Message 'path is not a file' `
            -TargetObject $_
        return
    }
    
    $info = avprobe.exe $_ -show_format -show_streams -of json -v 0 | ConvertFrom-Json
    if (-not ($info | Get-Member format) -or -not ($info | Get-Member streams)) {
        Write-Error -Message 'could not get video info' `
            -TargetObject $_
        return
    }
    $format = $info.format
    $video = $info.streams | IsVideoStream | select -first 1
    $audio = $info.streams | IsAudioStream | select -first 1

    if (-not $video) {
        Write-Error -Message 'could not find video stream' `
            -TargetObject $_
        return
    }

    $vcodec = $video.codec_name
    $acodec = & { if ($audio) { $audio.codec_name } else { $null } }
    $channels = & { if ($audio) { $audio.channels } else { $null } }

    [VideoInfo]::new(
        [int]$video.width, 
        [int]$video.height, 
        [double]$format.duration, 
        [int]$format.bit_rate, 
        (fps_value $video.avg_frame_rate), 
        $vcodec,
        (CodecTag $video.codec_tag_string),
        $acodec,
        $channels,
        [int64]$format.size, 
        $_
    )
}

if ($progress) {
    $progress.Completed = $true
    Write-Progress @progress
}
