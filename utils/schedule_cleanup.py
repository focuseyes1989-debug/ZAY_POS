# utils/schedule_cleanup.py

import os
import sys
import subprocess

def schedule_cleanup_on_reboot():
    """Schedule cleanup on system reboot using Task Scheduler."""
    try:
        # Create VBS script to delete MEI folders on boot
        vbs_path = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'cleanup_mei.vbs')
        with open(vbs_path, 'w') as f:
            f.write('''
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strTemp = objShell.ExpandEnvironmentStrings("%TEMP%")
Set objFolder = objFSO.GetFolder(strTemp)

For Each objFile In objFolder.SubFolders
    If Left(objFile.Name, 4) = "_MEI" Then
        objFile.Delete True
    End If
Next

' Delete this script
objFSO.DeleteFile WScript.ScriptFullName
''')
        
        # Run VBS script
        subprocess.Popen(
            ['wscript.exe', vbs_path],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        print(f"✅ Scheduled cleanup on boot")
        
    except Exception as e:
        print(f"⚠️ Could not schedule cleanup: {e}")