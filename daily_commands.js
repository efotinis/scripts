var ForReading = 1;
var ForWriting = 2;
var ForAppending = 8;

var swHide = 0;                           // Hides the window and activates another window. 
var swShowNormal = 1, swNormal = 1;       // Activates and displays a window. If the window is minimized or maximized, the system restores it to its original size and position. An application should specify this flag when displaying the window for the first time. 
var swShowMinimized = 2;                  // Activates the window and displays it as a minimized window.  
var swShowMaximized = 3, swMaximize = 3;  // Activates the window and displays it as a maximized window.  (/  Maximizes the specified window.)
var swShowNoActivate = 4;                 // Displays a window in its most recent size and position. The active window remains active. This value is similar to SW_SHOWNORMAL, except the window is not actived.
var swShow = 5;                           // Activates the window and displays it in its current size and position. 
var swMinimize = 6;                       // Minimizes the specified window and activates the next top-level window in the Z order. 
var swShowMinNoActive = 7;                // Displays the window as a minimized window. The active window remains active. This value is similar to SW_SHOWMINIMIZED, except the window is not activated.
var swShowNA = 8;                         // Displays the window in its current state. The active window remains active. This value is similar to SW_SHOW, except the window is not activated.
var swRestore = 9;                        // Activates and displays the window. If the window is minimized or maximized, the system restores it to its original size and position. An application should specify this flag when restoring a minimized window. 
var swShowDefault = 10;                   // Sets the show-state based on the state of the program that started the application. Sets the show state based on the SW_ value specified in the STARTUPINFO structure passed to the CreateProcess function by the program that started the application. 
var swForceMinimize = 11;                 // Windows 2000/XP: Minimizes a window, even if the thread that owns the window is hung. This flag should only be used when minimizing windows from a different thread.


var fso = new ActiveXObject("Scripting.FileSystemObject");
var wssh = WScript.CreateObject("WScript.Shell");

var regPath = "HKCU\\Software\\Elias Fotinis\\daily_commands";
var regLastRun = regPath + "\\LastRun";


main();


// ------------------------------------------------
// ------------------------------------------------
function main() {
  // The hour that days are supposed to transition.
  // Formally days change at 00:00 (12:00am), but this can be set to a later hour if needed.
  // (especially handy for night owls :)
  var dayTransitionHour = 5;

  var lastDate = getLastRunDate();
  
  if (!lastDate || transitionOccured(lastDate, dayTransitionHour)) {
    //WScript.Echo("transition!");
    runPrograms();
    setLastRunDate(new Date);
  }

}


// ------------------------------------------------
// Returns the last run date.
// On error, throws a string msg.
// ------------------------------------------------
function getLastRunDate() {
  try {
    var s = wssh.RegRead(regLastRun);
    return new Date(s);
  }
  catch (x) {
    return null;
  }
}


// ------------------------------------------------
// Returns the last run date.
// On error, throws a string msg.
// ------------------------------------------------
function setLastRunDate(date) {
  wssh.RegWrite(regLastRun, date, "REG_SZ");
}


// ------------------------------------------------
// Checkes whether the current date has transitioned from
// the supplied date into a new day.
// ------------------------------------------------
function transitionOccured(lastDate, dayTransitionHour) {
  var transDate = new Date(lastDate);
  // increase hour until we get passed the transition
  do {
    transDate.setHours(transDate.getHours() + 1);
  } while (transDate.getHours() != dayTransitionHour)
  // zero min/sec/msec
  transDate.setMinutes(0, 0, 0);

  var now = new Date;
  
  /*
  var s = "";
  s += "Last date:\t" + lastDate + "\n";
  s += "Trans point:\t" + transDate + "\n";
  s += "Current date:\t" + now + "\n";
  WScript.Echo(s);
  */
  
  return now >= transDate;
}


// ------------------------------------------------
// Runs the "daily commands".
// ------------------------------------------------
function runPrograms() {
  var orgCurDir = wssh.CurrentDirectory;
  try {
    wssh.CurrentDirectory = "E:\\documents";
    wssh.Run("E:\\documents\\e-log.xls", swShowNormal);
    // BUG: Using WShell.Run() to launch XLS or DOC files registered with MS Office doesn't work properly.
    // One of the following seems to fix it:
    // - use the program name (e.g. Excel, WinWord) in addition to the document name in the cmd string.
    // - have Run() wait for the program to end, by setting the 3rd arg to true.
    // - put a Sleep after Run(), essentially preventing the script from terminating until the registered program launches.
    //   Different delays have different results:
    //   * 0..50msec:  Excel doesn't run at all
    //   * 50-250msec: Excel usually runs, but with no file opened
    //   * >250msec:   The file is opened in Excel.
    //   WinWord seems to need as many as 2000msec to successfully open a DOC file.
    WScript.Sleep(2000);
    
    //WScript.Echo("Command has run.");
  }
  catch (x) {
    WScript.Echo("Could not run program.\n" + x.description);
  }
  wssh.CurrentDirectory = orgCurDir;
}

