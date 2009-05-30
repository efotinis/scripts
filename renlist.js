// Renames a set of files, using two file lists.
// The first param is a text file containing the source files
// and the second one contains the destinations.
// On the first error, the operation is aborted without any rollback.
//
// EF 2005-07-15

// TODO: convert to Python

var fso = new ActiveXObject("Scripting.FileSystemObject");
var ForReading = 1;


var ok;
try {
  ok = main();
}
catch (x) {
  ok = false;
}
WScript.Quit(ok ? 0 : 1);


function main() {
  // we need exactly 2 params
  var args = WScript.Arguments.Unnamed;
  if (args.length != 2) {
    WScript.Echo("ERR: Must specify two input list files.");
    return false;
  }

  // read the lines
  var srcNames = getFileLines(args(0));
  var dstNames = getFileLines(args(1));
  if (!srcNames || !dstNames) {
    WScript.Echo("ERR: Could not read input file(s).");
    return false;
  }
  
  // line counts must match
  if (srcNames.length != dstNames.length) {
    WScript.Echo("ERR: Input list files have different number of lines.");
    return false;
  }
  
  var cnt = srcNames.length;
  for (var n = 0; n < cnt; ++n) {
    try {
      fso.MoveFile(srcNames[n], dstNames[n]);
    }
    catch (x) {
      WScript.Echo("ERR: Renaming failed. Reason: " + x.description);
      WScript.Echo("\tSource: " + srcNames[n]);
      WScript.Echo("\tTarget: " + dstNames[n]);
      return false;
    }
  }

  return true;
}


// Returns an string array containing the lines of the specified file,
// or null if an error occurs.
function getFileLines(fname) {
  try {
    var a = new Array;
    var f = fso.OpenTextFile(fname, ForReading);
    while (!f.AtEndOfStream)
      a.push(f.ReadLine());
    return a;
  }
  catch (x) {
    //WScript.Echo("EXC: " + x.description);
    return null;
  }
}
