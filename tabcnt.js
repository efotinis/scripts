// TODO: convert to Python

var fso = new ActiveXObject("Scripting.FileSystemObject");
var ForReading = 1;

var args = WScript.Arguments.Unnamed;
if (args.length < 1) {
  WScript.Echo("ERR: Must specified one or more files.");
  WScript.Quit(1);
}

for (var n = 0; n < args.length; ++n) {
  var fname = args.Item(n);
  var is = fso.OpenTextFile(fname, ForReading);
  var foundTab = false;
  while (!is.AtEndOfStream) {
    var s = is.ReadLine();
    if (s.indexOf("\t") != -1) {
      foundTab = true;
      break;
    }
  }
  //WScript.Echo((foundTab ? "*" : " ") + " " + fname);
  if (foundTab) WScript.Echo(fname);
}
