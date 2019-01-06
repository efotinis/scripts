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
        public string   Audio;
        public int64    Size;
        public string   Path;
        public VideoInfo(
            int width, int height, double duration, int bitrate, double framerate, 
            string video, string audio, int64 size, string path) 
        {
            Width = width;
            Height = height;
            Duration = duration;
            Bitrate = bitrate;
            Framerate = framerate;
            Video = video;
            Audio = audio;
            Size = size;
            Path = path;
        }
    }
"@

#Update-FormatData 'C:\Users\Elias\Dropbox\tools\new scripts\VideoInfo.Format.ps1xml'


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

$Path | % {
    $info = avprobe.exe $_ -show_format -show_streams -of json -v 0 | ConvertFrom-Json
    if (-not ($info | Get-Member format) -or -not ($info | Get-Member streams)) {
        Write-Error "could not get info: $_"
        return
    }
    $format = $info.format
    $video = $info.streams | IsVideoStream | select -first 1
    $audio = $info.streams | IsAudioStream | select -first 1

    $vcodec = $video.codec_name
    $acodec = & { if ($audio) { $audio.codec_name } else { $null } }

    [VideoInfo]::new(
        [int]$video.width, 
        [int]$video.height, 
        [double]$format.duration, 
        [int]$format.bit_rate, 
        (fps_value $video.avg_frame_rate), 
        $vcodec, 
        $acodec,
        [int64]$format.size, 
        $_
    )
}
