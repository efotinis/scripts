var fso = new ActiveXObject("Scripting.FileSystemObject");
var wssh = new ActiveXObject("WScript.Shell");



var rootPath = "G:\\Backup\\ebooks";
var root = fso.GetFolder(rootPath);
var allFiles = [];
getAllFiles(root, allFiles)

allFiles.sort();
var msg = "";
for (var n = 0; n < allFiles.length; /**/) {
  var dups = countDups(allFiles, n);
  if (dups > 1) msg += dups + "\t" + allFiles[n] + "\n";
  n += dups;
}
if (msg == "") msg = "No duplicates found."
WScript.Echo(msg);


function countDups(a, i) {
  var n;
  var s = a[i].toUpperCase();
  for (n = i + 1; n < a.length && s == a[n].toUpperCase(); ++n)
    continue;
  return n - i;
}


function getAllFiles(folder, allFiles) {
  for (var e = new Enumerator(folder.Files); !e.atEnd(); e.moveNext())
    if (isBook(e.item().Name))
      allFiles.push(getBookTitle(e.item().Name));
  for (var e = new Enumerator(folder.SubFolders); !e.atEnd(); e.moveNext())
    getAllFiles(e.item(), allFiles);
}

function isBook(s) {
  var ext = fso.GetExtensionName(s).toUpperCase();
  return ext == "PDF" || ext == "CHM" || ext == "DJV" || ext == "DOC";
}

function getBookTitle(s) {
  s = fso.GetBaseName(s);
  var i = s.indexOf(" - ");
  if (i == -1)
    return s;
  else
    return s.substr(0, i);
}


/*
2	Anime Female Figure Drawing Tutorial
2	Borland JBuilder
2	Brain Facts, A Primer on the Brain and Nervous System, 4th Edition
2	Bram Stoker
2	Electricity
7	Electronics
9	Engineering
2	Introduction to 3D Game Engine Design Using DirectX 9 and C-Sharp
3	JRR Tolkien
2	LAN Switching First-Step
2	Networking
2	OpenGL Programming Guide, 2nd Edition
2	Physics
4	Scientific American Presents
2	Software Architecture in Practice, 2nd Edition
2	Software Engineering and Computer Games
2	The Art of C++
2	The Necronomicon Spellbook
2	Άρθουρ Μπλοχ
*/