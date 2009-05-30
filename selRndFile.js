// todo:
//  cmdline params:
//    pathList
//    /S  include subdirs
//    /E  locate in Explorer
//    /C  count of files to select
//

// TODO: convert to Python

var fso = new ActiveXObject("Scripting.FileSystemObject");
var wssh = new ActiveXObject("WScript.Shell");

//WScript.Echo(!WScript.StdIn);
//WScript.Quit(0);
main();


function main() {
  //var rootPath = "F:\\games\\q2 stuff\\q2 ftp levels";

  var allFiles = [];

  var args = WScript.Arguments.Unnamed;
  if (args.length == 0) {
    WScript.Echo("No paths specified.");
    return;
  }
  for (var i = 0; i < args.length; ++i) {
    var root = fso.GetFolder(args(i));
    getAllFiles(root, allFiles);
  }

  if (allFiles.length == 0) {
    WScript.Echo("No files found.");
    return;
  }

  var i = Math.floor(Math.random() * allFiles.length);
  wssh.Run("explorer.exe /select," + allFiles[i]);
}


function getAllFiles(folder, allFiles) {
  for (var e = new Enumerator(folder.Files); !e.atEnd(); e.moveNext())
    allFiles.push(e.item().Path);
  for (var e = new Enumerator(folder.SubFolders); !e.atEnd(); e.moveNext())
    getAllFiles(e.item(), allFiles);
}
