<#
.SYNOPSIS
    Clear console buffer below specified line.

.DESCRIPTION
    Clears the console contents from a selected line all the way down to the end of the buffer. This is useful when a command produces a lot of unneeded results and they need to be cleared, while preserving output from previous commands.

    The starting line can be selected interactively by moving a blinking line indicator with the keyboard. Available keyboard actions:

        - Enter             Clear buffer and exit.
        - Esc               Exit without clearing.
        - Up/Down           Move 1 line.
        - Shift-Up/Down     Move 5 lines. Only works on legacy console.
        - PgUp/PgDn         Move 1 page (window height).
        - Ctrl-PgUp/PgDn    Move to start of previous/next paragraph (block of consecutive, non-empty lines).

.INPUTS
    None

.OUTPUTS
    None
#>

[CmdletBinding()]
param()


# Get next available console key.
function GetKey {
    $info = [Console]::ReadKey($true)
    [PSCustomObject]@{
        Key = $info.Key         # [System.ConsoleKey]: enum with 144 values
        Char = $info.KeyChar    # [System.Char]
        Mods = $info.Modifiers  # [System.ConsoleModifiers]: Alt, Shift, Control
    }
}


# Show blinking line indicator, until a key is pressed, which is then returned.
function WaitKey {
    $rect = [System.Management.Automation.Host.Rectangle]::new(
        0,
        [Console]::CursorTop,
        [Console]::BufferWidth - 1,
        [Console]::CursorTop
    )
    $origin = [System.Management.Automation.Host.Coordinates]::new(
        0,
        [Console]::CursorTop
    )
    $filler = [System.Management.Automation.Host.BufferCell]::new(
        '-',
        $Host.UI.RawUI.ForegroundColor,
        $Host.UI.RawUI.BackgroundColor,
        [System.Management.Automation.Host.BufferCellType]::Complete
    )
    $prevBuf = $null
    try {
        for (;;) {
            if ($null -eq $prevBuf) {
                $prevBuf = $Host.UI.RawUI.GetBufferContents($rect)
                $Host.UI.RawUI.SetBufferContents($rect, $filler)
            }
            else {
                $Host.UI.RawUI.SetBufferContents($origin, $prevBuf)
                $prevBuf = $null
            }
            if ([Console]::KeyAvailable) {
                return GetKey
            }
            [System.Threading.Thread]::Sleep(150)
        }
    }
    finally {
        if ($null -ne $prevBuf) {
            $Host.UI.RawUI.SetBufferContents($origin, $prevBuf)
        }
    }
}


$originalCursorTop = [Console]::CursorTop
$originalWindowTop = [Console]::WindowTop


# Test whether specified buffer row has no non-whitespace characters.
function IsEmpty ($Row) {
    $rect = [System.Management.Automation.Host.Rectangle]::new(
        0,
        $Row,
        [Console]::BufferWidth,
        $Row
    )
    $chars = $Host.UI.RawUI.GetBufferContents($rect).Character
    ($chars -join '').Trim() -eq ''
}

$LAST_ROW = [Console]::BufferHeight - 1

# Key/position testing.
function NoTop { [Console]::CursorTop -gt 0 }
function NoBottom { [Console]::CursorTop -lt $LAST_ROW }
function IsKey($Info, $Name, $Mods = 0) {
    $Info.Key -eq $Name -and $Info.Mods -eq $Mods
}

# Paragraph locating.
function SkipBackEmpty ($i) {
    while ($i -ge 0 -and (IsEmpty $i)) { --$i }; $i
}
function SkipBackNonEmpty ($i) {
    while ($i -ge 0 -and (-not (IsEmpty $i))) { --$i }; $i
}
function SkipNextNonEmpty ($i) {
    while ($i -le $LAST_ROW -and (-not (IsEmpty $i))) { ++$i }; $i
}
function SkipNextEmpty ($i) {
    while ($i -le $LAST_ROW -and (IsEmpty $i)) { ++$i }; $i
}


# Interactive line selection loop.
# Returns int if Enter is pressed, or $null for Esc.
function SelectLine { for (;;) {
    $k = WaitKey
    if ((IsKey $k 'Escape')) {
        [Console]::WindowTop = $originalWindowTop
        [Console]::CursorTop = $originalCursorTop
        return
    }
    elseif ((IsKey $k 'UpArrow') -and (NoTop)) {
        [Console]::CursorTop -= 1
    }
    elseif ((IsKey $k 'DownArrow') -and (NoBottom)) {
        [Console]::CursorTop += 1
    }
    elseif ((IsKey $k 'UpArrow' 'Shift') -and (NoTop)) {
        [Console]::CursorTop = [Math]::Max(0, [Console]::CursorTop - 5)
    }
    elseif ((IsKey $k 'DownArrow' 'Shift') -and (NoBottom)) {
        [Console]::CursorTop = [Math]::Min($LAST_ROW, [Console]::CursorTop + 5)
    }
    elseif ((IsKey $k 'PageUp') -and (NoTop)) {
        [Console]::CursorTop = [Math]::Max(0, [Console]::CursorTop - [Console]::WindowHeight)
    }
    elseif ((IsKey $k 'PageDown') -and (NoBottom)) {
        [Console]::CursorTop = [Math]::Min($LAST_ROW, [Console]::CursorTop + [Console]::WindowHeight)
    }
    elseif ((IsKey $k 'Enter')) {
        return [Console]::CursorTop
    }
    elseif ((IsKey $k 'PageUp' 'Control') -and (NoTop)) {
        $i = [Console]::CursorTop - 1
        $i = SkipBackEmpty $i
        $i = SkipBackNonEmpty $i
        [Console]::CursorTop = $i + 1
    }
    elseif ((IsKey $k 'PageDown' 'Control') -and (NoBottom)) {
        $i = [Console]::CursorTop + 1
        $i = SkipNextNonEmpty $i
        $i = SkipNextEmpty $i
        [Console]::CursorTop = [Math]::Min($i, $LAST_ROW)
    }
}}


$i = SelectLine
if ($null -ne $i) {
    $rect = [System.Management.Automation.Host.Rectangle]::new(
        0,
        $i,
        [Console]::BufferWidth - 1,
        $LAST_ROW
    )
    $fill = [System.Management.Automation.Host.BufferCell]::new(
        ' ',
        $Host.UI.RawUI.ForegroundColor,
        $Host.UI.RawUI.BackgroundColor,
        [System.Management.Automation.Host.BufferCellType]::Complete
    )
    $Host.UI.RawUI.SetBufferContents($rect, $fill)
}
