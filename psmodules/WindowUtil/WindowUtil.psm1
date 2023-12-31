<#
.SYNOPSIS
    Native window utilities.

.DESCRIPTION
    Provides functions to manipulate native windows.
#>


Add-Type -Namespace $null -Name WinApi -MemberDefinition @"

    public struct RECT
    {
        /*
        public RECT() {
            Left = Top = Right = Bottom = 0;
        }
        NOTE 1: Can't define parameter-less constructor for structs, only classes.
        NOTE 2: Can't change struct to class, since passing as [ref] crashes the runtime.
        NOTE 3: Can't remove the [ref], because PowerShell requires it.
        NOTE 4: Can't create using [...+RECT]::new(), but New-Object ...+RECT works.
        NOTE 5: I used to be good at this...
        */
        public RECT(int l, int t, int r, int b) {
            Left = l;
            Top = t;
            Right = r;
            Bottom = b;
        }

        public int Left;
        public int Top;
        public int Right;
        public int Bottom;

        public int Width {
            get { return Right - Left; }
        }
        public int Height {
            get { return Bottom - Top; }
        }
    }

    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool ShowWindow(IntPtr wnd, int cmd);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool MoveWindow(IntPtr wnd, int x, int y, int w, int h, bool repaint);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool GetWindowRect(IntPtr hwnd, out RECT lpRect);
"@


enum ShowStatus {
    Hide = 0
    ShowNormal = 1; Normal = 1
    ShowMinimized = 2
    ShowMaximized = 3; Maximize = 3
    ShowNoActivate = 4;
    Show = 5;
    Minimize = 6;
    ShowMinNoActive = 7;
    ShowNA = 8;
    Restore = 9;
    ShowDefault = 10;
    ForceMinimize = 11;
}


function Get-WindowRect ($HWnd) {
    $rect = New-Object WinApi+RECT
    if (-not [WinApi]::GetWindowRect($HWnd, [ref]$rect)) {
        Write-Error 'could not get window rect'
    }
    $rect
}


function Set-WindowRect ($HWnd, $Rect, $Redraw = $true) {
    if (-not [WinApi]::MoveWindow($HWnd, $Rect.Left, $Rect.Top, $Rect.Width, $Rect.Height, $Redraw)) {
        Write-Error 'could not set window rect'
    }
}


function Set-WindowShow ($HWnd, $Status) {
    # NOTE: Suppress the returned bool, since it is not a success indicator.
    [void][WinApi]::ShowWindow($HWnd, $Status)
}


Export-ModuleMember -Function *-*
