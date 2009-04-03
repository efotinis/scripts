var wssh = new ActiveXObject("WScript.Shell");
var fso  = new ActiveXObject("Scripting.FileSystemObject");

// expansion needed for fso.OpenTextFile
var tempPath = wssh.ExpandEnvironmentStrings("%TEMP%\\~hdtemp.$$$");

WScript.Quit(main());


function main() {
  // check for help switch
  var switches = WScript.Arguments.Named;
  if (switches.Exists('?')) {
    help();
    return 0;
  }
  var args = WScript.Arguments.Unnamed;
  for (var i = 0; i < args.Length; ++i) {
    var n = parseInt(args(i), 10);
    if (isNaN(n)) {
      error(q(args(i)) + " is not a number.")
      continue;
    }
    if (!isValidDriveNo(n)) {
      error(q(n) + " is out of range.")
      continue;
    }
    checkDevice(devName(n));
  }
  // clean up
  if (fso.FileExists(tempPath))
    fso.DeleteFile(tempPath);
  return 0;
}


function help() {
  p('Display drive temperatures using SMARTCTL.');
  p('');
  p('HDT [drives]');
  p('');
  p('  drives  The list of drives to check.');
  p('          0 is /dev/hda, 1 is /dev/hdb, etc.');
}


function q(s) { return '"' + s + '"'; }
function p(s) { WScript.Echo(s); }
function p2(s) { WScript.StdErr.WriteLine(s); }


function error(s) {
  p2("ERROR: " + WScript.ScriptName + ": " + s);
}


function isValidDriveNo(n) {
  return n >= 0 && n <= 25;
}


// Return "/dev/hd?" given an index (0:'a', 1:'b', etc).
function devName(n) {
  if (!isValidDriveNo(n))
    throw "Invalid drive number.";
  return "/dev/hd" + String.fromCharCode("a".charCodeAt(0) + n);
}


function checkDevice(dev) {
  // send SMARTCTL output to a file (note: SMARTCTL never uses STDERR)
  var cmd = "cmd /c smartctl -A " + dev + " > " + q(tempPath);
  if (wssh.Run(cmd, 0, true) != 0) {
    error("smartctl call failed for " + dev + ".");
    return;
  }
  var ifs = fso.OpenTextFile(tempPath);
  while (!ifs.AtEndOfStream) {
    var s = ifs.ReadLine();
    if (s.toUpperCase().indexOf("TEMPERATURE") != -1) {
      p(dev + ": " + firstSpaceToken(s.substr(87)));
      break;
    }
  }
  ifs.close();
}


function firstSpaceToken(s) {
  var tokens = s.split(" ");
  for (var i in tokens)
    if (tokens[i])
      return tokens[i];
  return "";
}
