var wssh = new ActiveXObject('WScript.Shell');

args = WScript.Arguments.Unnamed;
s = args.length ? args(0) : '';

wssh.Popup(s);
