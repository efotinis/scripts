<#
function hms2sec ([string]$s) {
    $Hours, $Minutes, $Seconds = ($s -Split ':').foreach([int])
    (($Hours * 60) + $Minutes) * 60 + $Seconds
}
#>


Set-Alias PrettySize ConvertTo-PrettySize
Set-Alias PrettySec ConvertTo-PrettySeconds
Set-Alias PrettyDuration ConvertTo-PrettyDuration
