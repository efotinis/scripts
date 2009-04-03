/* ===========================================================================
Handler script for CD-ROM error event triggers.
Displays and logs current time and mounted CD-ROM drives.

Install with:
  eventtriggers /create /tr "CD-ROM error" /l system /eid 7 /t error /so cdrom /tk "%SystemRoot%\System32\wscript.exe SCRIPT_PATH" /ru USER_NAME /rp USER_PSW
where:
  SCRIPT_PATH  the location of this script
  USER_NAME    the account to run the script under
  USER_PSW     the account's password

Successful or failed invocations of this script are logged by the system to:
  %SystemRoot%\system32\wbem\logs\CmdTriggerConsumer.log

23/03/2006  Elias Fotinis
=========================================================================== */

// globals
var fso = new ActiveXObject('Scripting.FileSystemObject');
var wssh = new ActiveXObject('WScript.Shell');

// constants
var DRIVETYPE_CDROM = 4;
var MB_WARNING = 48;
var MB_ERROR = 16;
var ForReading = 1;
var ForAppending = 8;
var ERROR_INVALID_HANDLE = -2147024890;
var SW_HIDE = 0;
var errorTriggerName = "CD-ROM error";
var warningTriggerName = "CD-ROM warning";
var errorTriggerDescr = "Log CD-ROM error and notify user.";
var warningTriggerDescr = "Log CD-ROM warning and notify user.";


main();


function main() {
  var switches = WScript.Arguments.Named;
  if (switches.Exists('?')) {
    showHelp();
    return 0;
  }
  doReg = switches.Exists('reg');
  doUnreg = switches.Exists('unreg');
  if (doReg && doUnreg) {
    errLn('Both REG and UNREG switches specified.');
    return 1;
  }
  if (doReg)
    return register() ? 0 : 1;
  else if (doUnreg)
    return unregister() ? 0 : 1;
  
  if (switches.Exists('trigger'))
    return handler(switches.Item('trigger'));
  
  return 0;  // nop
}


function showHelp() {
  var name = WScript.ScriptName.toUpperCase();
  var s = 
    'CD-ROM error/warning event logger.\n' + 
    'Elias Fotinis 2006-03-23 (revised in 2006-04-15)\n' + 
    '\n' + 
    name + ' /REG username password\n' + 
    name + ' /UNREG\n' + 
    '\n' + 
    '  /REG    Register. Must specify user name and password.\n' + 
    '  /UNREG  Unregister.\n' + 
    '\n' + 
    'When registered, events are logged in a .LOG file with the same name and\n' + 
    'in the same directory as this script. Each log entry contains a timestamp\n' + 
    'and a list of mounted CD-ROM volumes; check the Event Viewer for more details.';
  WScript.Echo(s);
}


function errLn(s) {
  try {
    WScript.StdErr.WriteLine('ERROR: ' + s);
  }
  catch (x) {
    if (x.number == ERROR_INVALID_HANDLE) {
      // probably running under WSCRIPT
      wssh.Popup(s, 0, WScript.ScriptName.toUpperCase(), MB_ERROR);
      return;
    }
    throw x;
  }
}


function getUnnamedArgsList() {
  var ret = [];
  var args = WScript.Arguments.Unnamed;
  for (var i = 0; i < args.Length; ++i)
    ret.push(args.Item(i));
  return ret;
}


function register() {
  // must unregister existing triggers first
  unregister();
  
  var args = getUnnamedArgsList();
  if (args.length < 2) {
    errLn('User name and password must be specified.');
    return false;
  }
  
  var user = args[0];
  var psw  = args[1];

  var failedCreates = 0;
  if (!createTrigger(errorTriggerName, errorTriggerDescr, 'error', user, psw, '/trigger:error'))
    ++failedCreates;
  if (!createTrigger(warningTriggerName, warningTriggerDescr, 'warning', user, psw, '/trigger:warning'))
    ++failedCreates;

  return failedCreates == 0;
}


function createTrigger(name, descr, type, user, psw, params) {
  var scriptEng = '%SystemRoot%\\System32\\wscript.exe';
  if (typeof(params) == 'undefined')
    params = '';
  var cmd = "eventtriggers /create"
    + " /tr " + quote(name)
    + " /d " + quote(descr)
    + " /l system"
    + " /so cdrom"
    + " /t " + type
    + " /tk " + quote(escapeDoubleQuotes(quote(scriptEng) + ' ' + quote(WScript.ScriptFullName) + ' ' + params))
    + " /ru " + user
    + " /rp " + psw;

  var rc = runCmd(cmd);
  if (rc.exitCode != 0) {
    errLn(indentedStr('Could not create trigger ' + quote(name), rc.stderr));
    return false;
  }
  return true;
}


function escapeDoubleQuotes(s) {
  return s.split('"').join('\\"');
}


function indentedStr(header, indentedLines) {
  var a = indentedLines.slice(0);  // copy array contents
  a.splice(0, 0, header);          // insert header at beginning
  return a.join('\n  ');           // return indented
}


function unregister() {
  var rc = runCmd('eventtriggers /query /fo:csv /nh');
  if (rc.exitCode != 0) {
    errLn(indentedStr('Could not query existing event triggers.', rc.stderr));
    return false;
  }
  var a = parseEventTriggersCsvList(rc.stdout);
  var failedDeletes = 0;
  // find ids of our triggers and delete them
  for (var i = 0; i < a.length; ++i) {
    if (strimatch(a[i][1], errorTriggerName) || strimatch(a[i][1], warningTriggerName)) {
      var id = parseInt(a[i][0], 10);
      if (!deleteTrigger(id))
        ++failedDeletes;
    }
  }
  return failedDeletes == 0;
}


function deleteTrigger(numId) {
  var rc = runCmd('eventtriggers /delete /tid ' + numId);
  if (rc.exitCode != 0) {
    errLn(indentedStr('Could not delete trigger with id ' + numId + '.', rc.stderr));
    return false;
  }
  return true;
}


/*
//register();
//WScript.Echo(escapeDoubleQuotes(WScript.Arguments.Unnamed.Item(0)));
WScript.Echo(escapeDoubleQuotes('"f"oo"'));
WScript.Echo(WScript.ScriptFullName);


//WScript.Quit(main());

//WScript.Echo(wssh.Run('cmd /c eventtriggers /query /fo:csv /nh', 0, true));

x = runCmd('eventtriggers /query /fo:csv /nh');
//WScript.Echo(x.exitCode);
for (var i = 0; i < x.stdout.length; ++i) {
  s = x.stdout[i];
  if (s) {
    var a = parseEventTriggersCsvLine(s);
    for (var n = 0; n < a.length; ++n)
      WScript.StdOut.Write('<' + a[n] + '> ');
    WScript.Echo();
  }
}
*/


function handler(eventType) {
  // collect cur date and a list of mounted cd-rom drives
  var infoStr = 'event type: ' + eventType + '\n';
  infoStr += 'time: ' + (new Date).toString() + '\n';
  infoStr += 'mounted cd-roms:\n';
  for (var e = new Enumerator(fso.Drives); !e.atEnd(); e.moveNext()) {
    var drive = e.item();
    if (drive.DriveType == DRIVETYPE_CDROM && drive.IsReady) {
      infoStr += '\t';
      infoStr += drive.Path + '\t'
      infoStr += hex32(drive.SerialNumber) + '\t';
      infoStr += Math.round(drive.TotalSize/1024/1024) + ' MiB' + '\t';
      infoStr += drive.VolumeName + '\n';
    }
  }
  infoStr += '\n';

  // append to logfile and get any error
  var logErr = appendLog(infoStr);

  // notify user about event (and any logging failure)
  var s = infoStr;
  if (logErr)
    s += '\n(logging failed: ' + logErr.description + ')';
  wssh.Popup(s, 0, 'CD-ROM event detected', MB_WARNING);
}


// Return a hex str of a 32-bit int (negative ints are handled ok).
function hex32(n) {
  var digits = '0123456789ABCDEF';
  var s = '';
  if (n < 0)
    n += 0x100000000;
  for (var i = 0; i < 8; ++i) {
    s = digits.substr(n & 0xF, 1) + s;
    n /= 16;
  }
  return s;
}


// Append passed string to a file named as the current script with a '.log' ext.
// On error, return Error obj; otherwise null.
function appendLog(s) {
  try {
    var log = replaceExt(WScript.ScriptFullName, '.log');
    var f = fso.OpenTextFile(log, ForAppending, true);
    f.Write(s.split('\n').join('\r\n'));  // replace LFs with CRLFs
    return null;
  }
  catch (x) {
    return x;
  }
}


// Replace extension of path 's'.
function replaceExt(s, ext) {
  // add dot to extension if missing
  if (ext.length > 0 && ext.substr(0,1) != '.')
    ext = '.' + ext;
  return fso.BuildPath(fso.GetParentFolderName(s), fso.GetBaseName(s)) + ext;
}


// Return the name of a temp file.
// 'id' is an optional marker in case multiple temp files are needed.
function getTempFile(id) {
  if (typeof(id) == "undefined")
    id = '';
  return fso.BuildPath(
    wssh.ExpandEnvironmentStrings('%temp%'), 
    id + replaceExt(WScript.ScriptName, '$$$'));
}


// Run a command via the command interpreter and return a RunCmdRet object.
function runCmd(s) {
  var out = getTempFile('out');
  var err = getTempFile('err');
  var cmdLine = 'cmd /c ' + s + ' > ' + quote(out) + ' 2> ' + quote(err);
  var exitCode = wssh.Run(cmdLine, SW_HIDE, true);
  var ret = new RunCmdRet(exitCode, readFileLines(out), readFileLines(err));
  if (fso.FileExists(out)) fso.DeleteFile(out);
  if (fso.FileExists(err)) fso.DeleteFile(err);
  return ret;
}


// The results of runCmd().
function RunCmdRet(exitCode, outLines, errLines) {
  this.exitCode = exitCode;
  this.stdout = outLines;
  this.stderr = errLines;
}


function quote(s) {
  return '"' + s + '"';
}


// Return an array of lines from a file. Errors are ignored.
function readFileLines(path) {
  var ret = [];
  try {
    var ifs = fso.OpenTextFile(path, ForReading);
    while (!ifs.AtEndOfStream)
      ret.push(ifs.ReadLine());
    ifs.Close();
  }
  catch (x) {
  }
  return ret;
}


function parseEventTriggersCsvList(a) {
  var ret = []
  for (var i = 0; i < a.length; ++i)
    if (a[i])
      ret.push(parseEventTriggersCsvLine(a[i]));
  return ret;
}


// Parse a (buggy) eventtriggers CVS output line.
// Return a 3-element string array.
function parseEventTriggersCsvLine(s) {
  var first = parseEventTriggersCsvItem(s, 0);
  var second = parseEventTriggersCsvItem(s, first[1]);
  // the last item may contain unescaped special chars,
  // so we just read what's left and remove the enclosing quotes
  var last = s.substr(second[1]);
  last = last.substr(1, last.length - 2);
  return [first[0], second[0], last];
}
// Parse the next item from an 'eventtriggers' CVS line, starting at the specified offset.
// Return [item:string, nextOffset:num]
function parseEventTriggersCsvItem(s, offset) {
  var ret = '';
  if (offset < s.length) {
    ++offset;  // skip opening quotes
    var i = s.indexOf('"', offset);
    if (i == -1) {
      // oops, no closing quotes;
      ret = s.substr(offset);
      offset = s.length;
    }
    else {
      ret = s.substring(offset, i);
      offset = i + 1;  // skip closing quotes
      if (s.substr(offset, 1) == ',')
        ++offset;  // skip comma
    }
  }
  return [ret, offset];
}

/*function buildCsvLine(a) {
}*/


function strimatch(s1, s2) {
  return s1.toLowerCase() == s2.toLowerCase();
}
