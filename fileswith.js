/*
List files either containing or not a string.

%0 [/C] [/N] "string" files[ ...]

  /C    Match case of string. By default, case is ignored.
  /N    Show files that do not contain the specified string.
  text  The text string to find.
  file  One or more files (wildcards allowed) to search.
*/

var args = WScript.Arguments.Unnamed;
if (args.length < 1) {
  WScript.Echo("ERR: No search string specified.");
  WScript.Quit(1);
}
else if (args.length < 2) {
  WScript.Echo("ERR: No files specified.");
  WScript.Quit(1);
}

var matchCase = false;
var showNonContaining = false;

var switches = wscriptNamedArgsArray();
for (var n = 0; n < switches.length; ++n) {
  switch (switches[n][0].toUpperCase()) {
    case "C":
      matchCase = true;
      break;
    case "N":
      showNonContaining = true;
      break;
    default:
      WScript.Echo("ERR: Invalid switch: " + switches[n][0]);
      WScript.Quit(1);
      break; // unreachable
  }
}

var searchStr = quote(unquote(args(0)));
var filesList = "";
for (var n = 1; n < args.length; ++n)
  filesList += ' ' + quote(unquote(args(n)));

var cmd = "FOR %f IN (";
cmd += filesList;
cmd += ") DO @(FIND ";
cmd += matchCase ? "" : "/I ";
cmd += searchStr;
cmd += " %f > NUL "
cmd += showNonContaining ? "|| " : "&& ";
cmd += "ECHO %f)";

//WScript.Echo(cmd);
var wshShell = new ActiveXObject("WScript.Shell");
var exec = wshShell.Exec("CMD /C " + cmd);
while (!exec.StdOut.AtEndOfStream)
 WScript.Echo(exec.StdOut.ReadLine()); 
 
//while (exec.Status == 0) {
//  WScript.Sleep(100);
//}



function quote(s) {
  return '"' + s + '"';
}


function unquote(s) {
  var n = s.length;
  if (n >= 2 && s.charAt(0) == '"' && s.charAt(n - 1))
    s = s.substr(1, n - 2);
  return s;
}


function wscriptNamedArgsArray() {
  var ret = new Array;
  var args = WScript.Arguments.Named;
  for (var e = new Enumerator(args); !e.atEnd(); e.moveNext()) {
    var name  = e.item();
    var value = args.Item(name);
    ret.push([name, value]);
  }
  return ret;
}
