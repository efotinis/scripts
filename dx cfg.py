"""Configure keys, video, etc. in a new DeusEx installation."""


import os


patch1 = 'deusex.ini', """
[WinDrv.WindowsClient]
    WindowedColorBits=32
    FullscreenViewportX=800
    FullscreenViewportY=600
    FullscreenColorBits=32
    Brightness=0.750000
[Galaxy.GalaxyAudioSubsystem]
    MusicVolume=122
[D3DDrv.D3DRenderDevice]
    UseTrilinear=True
"""

patch2 = 'user.ini', """
[DeusEx.DeusExPlayer]
    bAutoReload=False
    MenuThemeName=Starlight
    HUDThemeName=Starlight
[Engine.Input]
    Tilde=Talk
[Engine.PlayerPawn]
    Bob=0.000000
    MouseSensitivity=2.000000
[Extension.InputExt]
    SingleQuote=
    RightBracket=
    LeftBracket=
    Tilde=Talk
    Semicolon=
    NumPadPeriod=
    NumPad8=ToggleAugDisplay
    NumPad7=ToggleHitDisplay
    NumPad5=ToggleCrosshair
    NumPad4=ToggleCompass
    NumPad2=ToggleObjectBelt
    NumPad1=ToggleAmmoDisplay
    NumPad0=ReloadWeapon
    Unknown5D=Walking
    Z=
    X=
    W=
    V=
    t=
    S=ShowSkillsWindow
    R=
    Q=
    M=ShowImagesWindow
    L=ShowLogsWindow
    H=ShowHealthWindow
    F=
    E=
    D=
    C=ShowConversationsWindow
    A=ShowAugmentationsWindow
    Delete=LeanLeft
    Insert=ToggleScope
    home=SwitchAmmo
    End=ActivateAugmentation 9
    PageDown=LeanRight
    PageUp=ToggleLaser
    Space=
    Alt=
    Ctrl=Duck
    Shift=Jump
    Enter=
"""


def main():
    global patch1, patch2
    dir = r'D:\Games\DeusEx\System'
    for file, data in (patch1, patch2):
        orgSpec = os.path.join(dir, file)
        lines = [s.rstrip('\n') for s in open(orgSpec).readlines()]
        patches = parsePatchData(data)

        print patches

        filterIni(lines, patches)
        bakSpec = orgSpec + '.bak'
        os.rename(orgSpec, bakSpec)
        open(orgSpec, 'w').writelines([s + '\n' for s in lines])
        os.unlink(bakSpec)


def parsePatchData(patchData):
    """Convert patch string to something more useful.

    The input is an INIfile-like string.
    The output is a dict keyed by ('[section]','key') tuples;
    its values are the key values (strings).
    Note that the strings of the key tuple are converted to lowercase.
    """
    patches = {}
    curSection = ''
    for s in patchData.split('\n'):
        if not s:
            continue
        if s[:1] == '[':
            curSection = s.lower()
        else:
            item, data = s.lstrip().split('=', 1)
            patches[(curSection, item.lower())] = data
    return patches


def filterIni(lines, patches):
    """Patches an INI files's lines.

    'lines' is a list the INI lines, without the trailing '\n'.
    'patches' is a dict returned by parsePatchData().
    Nothing is returned; 'lines' is modified in-place.
    """
    curSection = ''
    for i in range(len(lines)):
        if lines[i][:1] == '[':
            curSection = lines[i].lower()
        elif lines[i]:  # non-empty
            lines[i] = filterIniLine(curSection, lines[i], patches)


def filterIniLine(curSection, s, patches):
    """Patches an INI file's key line (if needed).

    'curSection' is the current section (in *lowercase* and encased in '[]')
    's' is the INI line ('key=[value]')
    'patches' is a dict returned by parsePatchData().
    If the (curSection,key) tuple exists in 'patches' the key's value
    is modified. The original or modified line is returned.
    """
    key, data = s.split('=', 1)
    try:
        data = patches[(curSection, key.lower())]
        return '='.join((key, data))
    except KeyError:
        return s # key not found; return original line


main()
