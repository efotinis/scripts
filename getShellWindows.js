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


/*
var sh = new ActiveXObject('Shell.Application');
var wnds = sh.Windows()
var s = ''
for (var i = 0; i < wnds.Count; ++i) {
    var ieObj = wnds.Item(i)
    WScript.Echo('item:' + i)
    WScript.Echo('name:' + ieObj.LocationName)
    WScript.Echo('url:' + ieObj.LocationURL)
    WScript.Echo('path:' + ieObj.Path)
    WScript.Echo('hwnd:' + ieObj.HWND)
    WScript.Echo()
    s += ieObj.HWND + ','
}
WScript.Echo(s)
*/

/*if url.beginswith('file:///')
    return path*/

/*
0x00000000-0x0000007F  0 xxxxxxx  
0x00000080-0x000007FF  110 xxxxx 10 xxxxxx  
0x00000800-0x0000FFFF  1110 xxxx 10 xxxxxx 10 xxxxxx  
0x00010000-0x001FFFFF  11110 xxx 10 xxxxxx 10 xxxxxx 10 xxxxxx  
*/

/*
function toUtf8(s) {
    var ret = ''
    for (var i = 0; i < s.length; ++i) {
        var n = s.charCodeAt(i)
        if (n < 0x80)
            ret += String.fromCharCode(n)
        else if (n < 0x800)
            ret += String.fromCharCode(0xC0 | (n & 0x1F),
                                       0x80 | (n >> 5))
        else if (n < 0x10000)
            ret += String.fromCharCode(0xE0 | (n & 0x0F),
                                       0x80 | ((n >> 4) & 0x3F),
                                       0x80 | (n >> 12))
        else
            ret += String.fromCharCode(0xF0 | (n & 0x07),
                                       0x80 | ((n >> 3) & 0x3F),
                                       0x80 | ((n >> 9) & 0x3F),
                                       0x80 | (n >> 15))
    }
    return ret
}
*/