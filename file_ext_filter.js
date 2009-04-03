var is = WScript.StdIn;
var os = WScript.StdOut;

//WScript.Quit(1);

while (!is.AtEndOfStream)
  os.WriteLine(getExt(is.ReadLine()));


function getExt(s) {
  var fnamePos = s.lastIndexOf("\\") + 1;  // this can be 0
  var lastDotPos = s.lastIndexOf(".");
  if (lastDotPos >= fnamePos)  // includes 'dotPos != -1', since 'fnamePos >= 0'
    return s.substr(lastDotPos);
  else
    return "";
}