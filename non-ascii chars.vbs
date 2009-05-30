' TODO: convert to Python (with option to read input from clipboard)

title = "Non-ASCII character finder"
s = InputBox("Enter string", title)
msg = ""
For n = 1 to Len(s)
  c = AscW(Mid(s, n, 1))
  If c < 32 Or c > 127 Then
    msg = msg & Mid(s, 1, n) & " (" & Hex(c) & ")" & Chr(10)
  End If
Next
If Len(msg) = 0 Then
  msg = "None found"
Else
  msg = "Found:" & Chr(10) & Chr(10) & msg
End if
MsgBox msg, , title
