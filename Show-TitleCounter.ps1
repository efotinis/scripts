#requires -Modules ConsoleUtil

<#
.SYNOPSIS
    Display counter during pipeline processing.

.DESCRIPTION
    Shows a running counter for the number of objects passed via the pipeline. This provides useful visual feedback, e.g. when assigning the lengthy output of a slow command to a variable.

    The input objects are output verbatim to continue pipeline processing.

.PARAMETER InputObject
    Input object. Use the pipeline to process all objects.

.PARAMETER UpdateMilliseconds
    Time in milliseconds between updates. Should be used to avoid excessive drawing. Default is 200 ms.

.PARAMETER Total
    Setting this to the total number of objects to be processed (when known in advance) will change the status from a simple counter to "<CURRENT> of <TOTAL> (<NNN> %)".

.PARAMETER Beep
    Play the system default sound when processing completes.

.INPUTS
    Object

.OUTPUTS
    Object

.EXAMPLE
    PS> $a = ls *.iso | Get-FileHash | .\Show-TitleCounter.ps1

    Here we calculate ISO file hashes and assign the results directly to a variable. Since this a lengthy operation that generates no output, there's no progress indication. Appending Show-TitleCounter to the pipeline provides the necessary feedback.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    $InputObject,

    [int]$UpdateMilliseconds = 200,

    [int]$Total,

    [switch]$Beep
)
begin {
    $oldTitle = Get-ConsoleTitle
    $n = 0
    $t = [System.Diagnostics.Stopwatch]::StartNew()
}
process {
    ++$n
    if ($t.ElapsedMilliseconds -ge $UpdateMilliseconds) {
        if ($Total -gt 0) {
            $p = ($n / $Total).ToString('P0')
            $status = "$n of $Total ($p)"
        } else {
            $status = "$n"
        }
        Set-ConsoleTitle "$status - $oldTitle"
        $t.Restart()
    }
    Write-Output $InputObject
}
end {
    Set-ConsoleTitle $oldTitle
    if ($Beep) {
        [System.Media.SystemSounds]::Beep.Play()
    }
}
