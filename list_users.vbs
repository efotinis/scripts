' Retrieve local computer name. 
Set oWshNet = CreateObject("Wscript.Network") 
sComputer = oWshNet.ComputerName 


' If you want to run it against a remote computer, use this instead 
'sComputer = "some name or IP" 


Const HKLM = &H80000002 
sProfileRegBase = "SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList" 


Set oReg = GetObject("WinMgmts:{impersonationLevel=impersonate}!//" _ 
                & sComputer & "/root/default:StdRegProv") 


Set oWMI = GetObject("WinMgmts:{impersonationLevel=impersonate}!//" _ 
                & sComputer & "/root/cimv2") 


Set colItems = oWMI.ExecQuery _ 
                ("Select Name,SID from Win32_UserAccount WHERE Domain = '" _ 
                & sComputer & "'",,48) 


For Each oItem In colItems 
  sAddInfo = "" 
  If Right(oItem.SID, 4) = "-500" Then 
    sAddInfo = "  ****** This is the administrator user   ******" 
  End If 
  Wscript.Echo "User name: " & oItem.Name & sAddInfo 
  oReg.GetExpandedStringValue HKLM, sProfileRegBase& "\" & oItem.SID, _ 
                  "ProfileImagePath", sProfilePath 


  If IsNull(sProfilePath) Then 
    sProfilePath = "(none defined)" 
  End If 
  Wscript.Echo "Profile path: " & sProfilePath 
  Wscript.Echo   ' blank line 
Next 

