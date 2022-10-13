function GetKey {
    $info = [Console]::ReadKey($true)
    [PSCustomObject]@{
        Key = $info.Key         # [System.ConsoleKey]: enum with 144 values
        Char = $info.KeyChar    # [System.Char]
        Mods = $info.Modifiers  # [System.ConsoleModifiers]: Alt, Shift, Control
    }
}

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

for (;;) {
    $k = WaitKey
    if ($k.Key -eq 'Escape') {
        [Console]::WindowTop = $originalWindowTop
        [Console]::CursorTop = $originalCursorTop
        break
    }
    elseif ($k.Key -eq 'UpArrow' -and $k.Mods -eq 0 -and [Console]::CursorTop -gt 0) {
        [Console]::CursorTop -= 1
    }
    elseif ($k.Key -eq 'DownArrow' -and $k.Mods -eq 0 -and [Console]::CursorTop -lt $LAST_ROW) {
        [Console]::CursorTop += 1
    }
    elseif ($k.Key -eq 'UpArrow' -and $k.Mods -eq 'Shift' -and [Console]::CursorTop -gt 0) {
        [Console]::CursorTop = [Math]::Max(0, [Console]::CursorTop - 5)
    }
    elseif ($k.Key -eq 'DownArrow' -and $k.Mods -eq 'Shift' -and [Console]::CursorTop -lt $LAST_ROW) {
        [Console]::CursorTop = [Math]::Min($LAST_ROW, [Console]::CursorTop + 5)
    }
    elseif ($k.Key -eq 'PageUp' -and $k.Mods -eq 0 -and [Console]::CursorTop -gt 0) {
        [Console]::CursorTop = [Math]::Max(0, [Console]::CursorTop - [Console]::WindowHeight)
    }
    elseif ($k.Key -eq 'PageDown' -and $k.Mods -eq 0 -and [Console]::CursorTop -lt $LAST_ROW) {
        [Console]::CursorTop = [Math]::Min($LAST_ROW, [Console]::CursorTop + [Console]::WindowHeight)
    }
    elseif ($k.Key -eq 'Enter' -and $k.Mods -eq 0) {
        $rect = [System.Management.Automation.Host.Rectangle]::new(
            0, 
            [Console]::CursorTop, 
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
        break
    }
    elseif ($k.Key -eq 'PageUp' -and $k.Mods -eq 'Control' -and [Console]::CursorTop -gt 0) {
        $i = [Console]::CursorTop - 1
        while ($i -ge 0 -and (IsEmpty $i)) {
            --$i
        }
        while ($i -ge 0 -and (-not (IsEmpty $i))) {
            --$i
        }
        [Console]::CursorTop = $i + 1
    }
    elseif ($k.Key -eq 'PageDown' -and $k.Mods -eq 'Control' -and [Console]::CursorTop -lt $LAST_ROW) {
        $i = [Console]::CursorTop + 1
        while ($i -le $LAST_ROW -and (-not (IsEmpty $i))) {
            ++$i
        }
        while ($i -le $LAST_ROW -and (IsEmpty $i)) {
            ++$i
        }
        [Console]::CursorTop = [Math]::Min($i, $LAST_ROW)
    }
    # A,B: range of lines to clear and shift content after B up
}


<#
hasmods (on, off, ignore)

hasmods (on, mask)

want:
    nothing or Shift, not Alt/Ctrl
    if 
#>
