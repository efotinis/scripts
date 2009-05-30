function main() {

    var fso = new ActiveXObject('Scripting.FileSystemObject')
    //var wssh = new ActiveXObject('WScript.Shell')
    
    var outObj
    var args = WScript.Arguments.Unnamed
    if (!args.length)
        outObj = WScript.StdOut
    else
        outObj = fso.CreateTextFile(args(0), true/*overwrite*/, true/*unicode*/)

    var sh = new ActiveXObject('Shell.Application');
    var wnds = sh.Windows()
    for (var i = 0; i < wnds.Count; ++i) {
        var s = '' + wnds(i).HWND + ' ' + wnds(i).LocationURL
        outObj.WriteLine(s)
    }
}


try {
    main()
    WScript.Quit(0)
}
catch (x) {
    WScript.Quit(1)
}
