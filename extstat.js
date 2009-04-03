// extstat.js
// Provides statistics based on file extensions.
/*
  [paths]  List of directories to examine. If ommitted, the current directory is used.
  [/S]     Recurse subdirectories.
  [/NH]    Suppress displaying of header.
  [/U:[B|K|M|G|T|P|E]]  Selects size display unit. If ommited, sizes are displayed in bytes.
  [/O:[[+|-]][N|S|C]]   Selects output order. +/- specify ascending/descending.
                        N, S, C stand for name, size, and count, respectively.
                        Default is ascending count.
*/

// globals
var stdIn  = WScript.StdIn;
var stdOut = WScript.StdOut;
var stdErr = WScript.StdErr;


var params = new CmdLineParams;





function CmdLineParams() {
  var args     = WScript.Arguments.Unnamed;
  var switches = WScript.Arguments.Named;

  this.paths = new Array;
  for (var n = 0; n < args.length; ++n)
    this.paths.push(args(n));
    
  this.header = !switches.Exists("NH");
  
  this.recurse = switches.Exists("S");
  
  var unit = switches.Exists("U") ? switches.Item("U") : "";
  var unitList = "BKMGTPE";
  var exp = unitList.indexOf(unit.toUpperCase());
  if (unit.length > 1 || exp == -1) {
    stdErr.WriteLine("ERR: Bad unit size.");
    Wscript.Quit(1);
  }
  this.sizeUnit = Math.pow(1024, exp);

  var order = switches.Exists("O") ? switches.Item("O") : "";
  var sign = order.substr(0, 1);
  this.ascending = true;
  if (sign == "+" || sign == "-") {
    this.ascending = sign == "+";
    order = order.substr(1);
  }
  var orderList = "NSC";
  var ord = orderList.indexOf(order.toUpperCase());
  if (order.length > 1 || ord == -1) {
    stdErr.WriteLine("ERR: Bad order type.");
    Wscript.Quit(1);
  }
  this.order = ord;
}


function ExtInfo() {
  this.name = "";
  this.count = 0;
  this.bytes = 0;
}