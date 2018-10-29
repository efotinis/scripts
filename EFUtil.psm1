<#
function hms2sec ([string]$s) {
    $Hours, $Minutes, $Seconds = ($s -Split ':').foreach([int])
    (($Hours * 60) + $Minutes) * 60 + $Seconds
}
#>


# Convert bytes to '[-]N <unit>' where N always has 3 significant digits.
function ConvertTo-PrettySize {
    param (
        [Parameter(Mandatory)]
        [long]$Bytes
    )

    [string]$Sign = ''
    if ($Bytes -lt 0) {
        $Sign = '-'
        $Bytes = -$Bytes
    }

    [double]$n = $Bytes
    [string]$Unit = ''

    if ($n -le 999) {
        return "$Sign$n byte" + $(if ($n -eq 1) { '' } else { 's' })
    }

    foreach ($c in [char[]]'KMGTPE') {
        if ($n -ge 999.5) {
            $Unit = $c
            $n /= 1024
        }
    }
    [string]$Fmt = $(
        if ($n -lt 10) {
            'N2'
        } elseif ($n -lt 100) {
            'N1'
        } else {
            'N0'
        }
    )
    return ('{0}{1:'+$Fmt+'} {2}B') -f ($Sign, $n, $Unit)
}


function ConvertFrom-PrettySize {
    param(
        [Parameter(Mandatory)]
        [string]$Size,
        
        [switch]$Base10
    )
    
    $Size = $Size.ToLower() -replace '\s+', ''
    
    if (-not ($Size -match '^([0-9.]+)(.*)$')) {
        throw 'invalid size'
    }
    $Number, $Unit = $Matches[1..2]
    $Number = [double]$Number
    if ($Unit -in 'b','byte','bytes') {
        return [long]$Number
    }
    
    if (-not ($Unit -match '^([kmgtpe])(i?)b?$')) {
        throw 'invalid unit'
    }
    $Unit, $Iec = $Matches[1..2]
    $Base = if ($Base10 -or $Iec) { 1000 } else { 1024 }
    $Factor = [Math]::Pow($Base, 'kmgtpe'.IndexOf($Unit) + 1)
    return [long]($Number * $Factor)
}


# Convert seconds to "[-]hh:mm:ss.lll".
function ConvertTo-PrettySeconds {
    param(
        [Parameter(Mandatory)]
        [double]$Seconds,
        
        [int]$Decimals = 0,
        
        [string]$Plus = ''
    )
    if ($Seconds -lt 0) {
        $Seconds = -$Seconds
        $Sign = '-'
    } else {
        $Sign = $Plus
    }
    if ($Decimals -lt 0) {
        $Decimals = 0
    }
    $Minutes = [System.Math]::DivRem($Seconds, 60, [ref]$Seconds)
    $Hours = [System.Math]::DivRem($Minutes, 60, [ref]$Minutes)
    $Fmt = '{0}{1:00}:{2:00}:{3:00.' + ('0' * $Decimals) + '}'
    $Fmt -f $Sign,$Hours,$Minutes,$Seconds
}


# Convert seconds to "[[[h]h:]m]m:ss" (i.e. like video durations shown on YouTube).
function ConvertTo-PrettyDuration {
    param(
        [Parameter(Mandatory)]
        [int]$Seconds
    )
    if ($Seconds -lt 0) {
        $Seconds = -$Seconds
    }
    $Minutes = [System.Math]::DivRem($Seconds, 60, [ref]$Seconds)
    $Hours = [System.Math]::DivRem($Minutes, 60, [ref]$Minutes)
    if ($Hours) {
        '{0:#0}:{1:00}:{2:00}' -f $Hours,$Minutes,$Seconds
    }
    else {
        '{0:#0}:{1:00}' -f $Minutes,$Seconds
    }
}


Set-Alias PrettySize ConvertTo-PrettySize
Set-Alias PrettySec ConvertTo-PrettySeconds
Set-Alias PrettyDuration ConvertTo-PrettyDuration
