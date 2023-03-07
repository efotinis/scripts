<#
.SYNOPSIS
    Move up and erase previous console lines.

.DESCRIPTION
    Erases the specified number of lines above the current cursor location,
    then moves the cursor to the top of the erased area.

.PARAMETER Count
    Number of lines to erase. If more lines are specified than available, they
    are capped to the top of the console buffer. Nothing is done if Count is 0
    or less.

.INPUTS
    None.

.OUTPUTS
    None.
#>

[CmdletBinding()]
param(
    [int]$Count = 1
)

function GetClearCell {
    [System.Management.Automation.Host.BufferCell]::new(
        ' ',
        $Host.UI.RawUI.ForegroundColor,
        $Host.UI.RawUI.BackgroundColor,
        'Complete'
    )
}

function GetCoords ([int]$X, [int]$Y) {
    [System.Management.Automation.Host.Coordinates]::new($X, $Y)
}

function GetLinesSpanRect ([int]$Top, [int]$Bottom) {
    [System.Management.Automation.Host.Rectangle]::new(
        0,
        $Top,
        $Host.UI.RawUI.BufferSize.Width - 1,
        $Bottom
    )
}

function MoveCursorToLineStart ([int]$Line) {
    $Host.UI.RawUI.CursorPosition = GetCoords 0 $Line
}

function GetCursorLine {
    $Host.UI.RawUI.CursorPosition.Y
}

if ($Count -le 0) {
    return
}

$n = GetCursorLine
if ($n -eq 0) {
    return
}

$bottom = $n - 1
$top = $n - $Count
if ($top -lt 0) {
    $top = 0
}

$src = GetLinesSpanRect $top $bottom
$dst = GetCoords 0 ($top - ($bottom - $top) - 1)

$Host.UI.RawUI.ScrollBufferContents(
    $src, $dst, $src, (GetClearCell)
)

MoveCursorToLineStart $top
