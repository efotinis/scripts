//339510

var fso = new ActiveXObject("Scripting.FileSystemObject");
var wssh = WScript.CreateObject("WScript.Shell");


main();


function main() {
  var extGroups = (new DirScanner).scan("E:\\documents");

  var tmpFile = getTempFileName();
  var results = [];
  for (var x in extGroups)
    results.push(testGroup(x, extGroups[x], tmpFile));
  delFile(tmpFile);
    
  p("");
    
  results.sort(grpResAvgOrder);
  for (var n = 0; n < results.length; ++n)
    p(results[n].avg + ", " + results[n].min + ", " + results[n].max + ", " + q(results[n].ext));
}


function p(s) {
  WScript.Echo(s);
}


function q(s) {
  return '"' + s + '"';
}


// scan() returns an associative array as follows:
//  key:      extension (incl. dot)
//  element:  string array of file paths
//
function DirScanner() {
  this._lastOut = new Date;
  this._scanCnt = 0;
  
  this.scan = function(dirPath) {
    var extGroups = [];
    WScript.Echo("scanning " + dirPath + "...");
    this._scan(fso.GetFolder(dirPath), extGroups);
    WScript.Echo();
    return extGroups;
  }
  
  this._scan = function(fld, extGroups) {
    var d = new Date;
    if (d - this._lastOut >= 1000) {

      //return;  // quick bailout for debugging ###############################################################

      WScript.StdOut.Write(this._scanCnt + " ");
      this._lastOut = d;
    }
    for (var e = new Enumerator(fld.Files); !e.atEnd(); e.moveNext(), ++this._scanCnt)
      this._addFile(e.item(), extGroups);
    for (var e = new Enumerator(fld.SubFolders); !e.atEnd(); e.moveNext(), ++this._scanCnt)
      this._scan(e.item(), extGroups);
  }
  
  this._addFile = function(file, extGroups) {
    var ext = this._getExt(file.Name).toUpperCase();
    var grp = extGroups[ext];
    if (!grp)
      extGroups[ext] = grp = [];
    grp.push(file.Path);
  }

  this._getExt = function(s) {
    var i = s.lastIndexOf(".");
    return i != -1 ? s.substr(i) : "";
  }
  
}


function GroupResult(ext) {
  this.ext = ext;
  this.avg = 0;
  this.min = 1;
  this.max = 0;
}


function grpResAvgOrder(a, b) {
  return a.avg - b.avg;
}


// Returns a GroupResult for the specified string array of file paths.
function testGroup(ext, files, tmpFile) {
  var sampleSize = 10;
  
  //p(files.length);
  //p(files.join("\n"));
  
  // suffle the array
  for (var n = 0; n < files.length; ++n) {
    var i = Math.floor(Math.random() * files.length);
    var j = Math.floor(Math.random() * files.length);
    var s = files[i];
    files[i] = files[j];
    files[j] = s;
  }
  var ret = new GroupResult(ext);
  var testCnt = Math.min(sampleSize, files.length);
  for (var n = 0; n < testCnt; ++n) {
    var comprRatio = testCompression(files[n], tmpFile);
    if (comprRatio < ret.min) ret.min = comprRatio;
    if (comprRatio > ret.max) ret.max = comprRatio;
    ret.avg += comprRatio;
  }
  ret.avg /= testCnt;
  return ret;
}


function testCompression(filePath, tmpFile) {
  delFile(tmpFile);

  var cmd = "7z.bat a " + q(tmpFile) + " " + q(filePath);
  var exec = wssh.Exec(cmd);
  while (exec.Status == 0)
    WScript.Sleep(100);
  if (exec.ExitCode != 0)
    throw "Cmd failed: " + cmd;
    
  cmd = "7z.bat l " + q(tmpFile);
  exec = wssh.Exec(cmd);
  while (exec.Status == 0)
    WScript.Sleep(100);
  if (exec.ExitCode != 0)
    throw "Cmd failed: " + cmd;

  // "------------------- ----- ------------ ------------  ------------"
  var sepRx = /-+(\s+-+)+/;
  // "2005-09-26 15:50:11 ....A      5203223      4146400  name..."
  var infoRx = /(?:\S+\s+){3}(\d+\s+)(\d+\s+)/;

  var m;
  while (!exec.StdOut.AtEndOfStream) {
    var s = exec.StdOut.ReadLine();
    if (s.match(sepRx)) {
      s = exec.StdOut.ReadLine();
      m = s.match(infoRx);
      break;
    }
  }
  
  var orgSize   = parseInt(m[1], 10);
  var comprSize = parseInt(m[2], 10);
  var ratio     = orgSize ? (1 - comprSize / orgSize) : 0;
  
  p(orgSize + " " + comprSize + " " + ratio + " " + filePath);
  
  //WScript.Quit(0);

  return ratio;
}


function getTempFileName() {
  return fso.BuildPath(wssh.ExpandEnvironmentStrings("%TEMP%"), "~EFCTT$$.$$$");
}


function delFile(filePath) {
  try {
    fso.DeleteFile(filePath);
  }
  catch (x) {}
}