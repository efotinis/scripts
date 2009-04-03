var is = WScript.StdIn;
var os = WScript.StdOut;

//WScript.Quit(1);

var lines = new Array;

var maxFirstTokLen = 0;
while (!is.AtEndOfStream) {
  var tokens = getTokens(is.ReadLine());
  lines.push(tokens);
  maxFirstTokLen = Math.max(maxFirstTokLen, tokens[0].length);
}

for (var n = 0; n < lines.length; ++n) {
  os.Write(lines[n][0]);
  var pad = maxFirstTokLen - lines[n][0].length + 1;
  os.Write(charStr(" ", pad));
  os.WriteLine(lines[n][1]);
}

function trimLeft(s) {
  return s.replace(/^ */, "");
}

function charStr(c, n) {
  var s = "";
  while (n-- > 0)
    s += c;
  return s;
}

function getTokens(s) {
  s = trimLeft(s);
  var i = s.indexOf(" ");
  var s1, s2;
  if (i != -1) {
    s1 = s.substr(0, i);
    s2 = trimLeft(s.substr(i + 1));
  }
  else {
    s1 = "";
    s2 = s;
  }
  return [s1, s2];
}

function getExt(s) {
  var fnamePos = s.lastIndexOf("\\") + 1;  // this can be 0
  var lastDotPos = s.lastIndexOf(".");
  if (lastDotPos >= fnamePos)  // includes 'dotPos != -1', since 'fnamePos >= 0'
    return s.substr(lastDotPos);
  else
    return "";
}